import base64
import hashlib
import os
import secrets
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi import HTTPException
from fastapi.testclient import TestClient
from google.auth import crypt, exceptions as google_auth_exceptions, jwt

from main import (
    GOOGLE_AUTHORIZATION_ENDPOINT,
    GOOGLE_CALLBACK_PATH,
    GOOGLE_ISSUER,
    app,
    oauth_cookie_names,
    verify_google_id_token,
)
from users import AuthSession, User


GOOGLE_SETTINGS = {
    "APP_ENV": "development",
    "GOOGLE_OAUTH_CLIENT_ID": "synthetic-client-id",
    "GOOGLE_OAUTH_CLIENT_SECRET": "synthetic-client-secret",
    "GOOGLE_OAUTH_REDIRECT_URI": (
        "http://localhost:8001/v1/auth/google/callback"
    ),
}


class GoogleOIDCTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.private_key_pem = cls.private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "synthetic issuer")])
        certificate = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(cls.private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
            .sign(cls.private_key, hashes.SHA256())
        )
        cls.certificate_pem = certificate.public_bytes(
            serialization.Encoding.PEM
        ).decode("ascii")
        cls.signer = crypt.RSASigner.from_string(
            cls.private_key_pem,
            key_id="synthetic-key",
        )

    def setUp(self):
        self.environment = patch.dict(os.environ, GOOGLE_SETTINGS, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.bound_users: dict[str, User] = {}

    def begin_flow(self):
        response = self.client.get("/v1/auth/google/start")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

        query = parse_qs(urlparse(response.json()["authorization_url"]).query)
        state = query["state"][0]
        state_cookie, nonce_cookie, verifier_cookie = oauth_cookie_names(state)
        nonce = response.cookies.get(nonce_cookie)
        verifier = response.cookies.get(verifier_cookie)
        self.assertEqual(urlparse(response.json()["authorization_url"]).scheme, "https")
        self.assertEqual(
            urlparse(response.json()["authorization_url"]).netloc,
            urlparse(GOOGLE_AUTHORIZATION_ENDPOINT).netloc,
        )
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["openid"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["code_challenge"], [self.pkce_challenge(verifier)])
        self.assertEqual(response.cookies.get(state_cookie), state)
        self.assertTrue(nonce)
        self.assertTrue(verifier)
        cookie_headers = response.headers.get_list("set-cookie")
        self.assertEqual(len(cookie_headers), 3)
        self.assertTrue(
            all(
                "httponly" in cookie.lower()
                and "samesite=lax" in cookie.lower()
                and "max-age=600" in cookie.lower()
                and "path=/v1/auth/google/callback" in cookie.lower()
                for cookie in cookie_headers
            )
        )
        return state, nonce, verifier

    @staticmethod
    def pkce_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def callback_claims(self, subject: str, nonce: str) -> dict[str, object]:
        return {
            "sub": subject,
            "iss": GOOGLE_ISSUER,
            "aud": GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
            "exp": 4_102_444_800,
            "nonce": nonce,
        }

    def signed_id_token(self, **overrides: object) -> str:
        claims: dict[str, object] = {
            "iss": GOOGLE_ISSUER,
            "aud": GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
            "exp": int(time.time()) + 300,
            "iat": int(time.time()) - 10,
            "sub": "synthetic-google-subject",
            "nonce": "synthetic-nonce",
        }
        claims.update(overrides)
        return jwt.encode(self.signer, claims, key_id="synthetic-key").decode("ascii")

    def persist_synthetic_identity(self, subject: str) -> tuple[User, bool]:
        user = self.bound_users.get(subject)
        if user is not None:
            return user, False
        user = User(uuid4(), datetime.now(timezone.utc))
        self.bound_users[subject] = user
        return user, True

    def finish_flow(self, subject: str, accept: str = "*/*"):
        state, nonce, verifier = self.begin_flow()
        with (
            patch(
                "main.exchange_google_code",
                new_callable=AsyncMock,
                return_value="synthetic-id-token",
            ) as exchange,
            patch(
                "main.verify_google_id_token",
                return_value=self.callback_claims(subject, nonce),
            ),
            patch(
                "main.persist_google_identity",
                side_effect=self.persist_synthetic_identity,
            ),
            patch(
                "main.persist_session",
                return_value=(
                    "synthetic-session-token",
                    AuthSession(
                        uuid4(),
                        datetime.now(timezone.utc) + timedelta(hours=8),
                    ),
                ),
            ),
        ):
            response = self.client.get(
                GOOGLE_CALLBACK_PATH,
                params={"code": "synthetic-authorization-code", "state": state},
                headers={"Accept": accept},
                follow_redirects=accept != "text/html",
            )
        expected_status = 303 if accept == "text/html" else 200
        self.assertEqual(response.status_code, expected_status, response.text)
        exchange.assert_awaited_once_with(
            "synthetic-authorization-code",
            verifier,
            GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
            GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_SECRET"],
            GOOGLE_SETTINGS["GOOGLE_OAUTH_REDIRECT_URI"],
        )
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertIn("acadence_session=synthetic-session-token", response.headers["set-cookie"])
        return response

    def test_first_and_repeat_sign_in_reuse_subject_binding(self):
        first = self.finish_flow("synthetic-google-subject-a")
        repeated = self.finish_flow("synthetic-google-subject-a")

        self.assertTrue(first.json()["created"])
        self.assertFalse(repeated.json()["created"])
        self.assertEqual(first.json()["user_id"], repeated.json()["user_id"])
        self.assertEqual(set(first.json()), {"user_id", "created"})

    def test_browser_callback_sets_session_and_redirects_to_dashboard(self):
        response = self.finish_flow(
            "synthetic-google-subject-a",
            accept="text/html",
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://localhost:3001/dashboard")
        self.assertIn("httponly", response.headers["set-cookie"].lower())
        self.assertIn("samesite=lax", response.headers["set-cookie"].lower())

    def test_distinct_google_subjects_create_distinct_users(self):
        first = self.finish_flow("synthetic-google-subject-a")
        second = self.finish_flow("synthetic-google-subject-b")

        self.assertNotEqual(first.json()["user_id"], second.json()["user_id"])
        self.assertTrue(first.json()["created"])
        self.assertTrue(second.json()["created"])

    def test_rejected_google_id_token_does_not_create_a_user(self):
        state, _, _ = self.begin_flow()
        with (
            patch(
                "main.exchange_google_code",
                new_callable=AsyncMock,
                return_value="invalid-synthetic-id-token",
            ),
            patch(
                "main.verify_google_id_token",
                side_effect=ValueError("Invalid signature"),
            ),
            patch("main.persist_google_identity") as persist,
        ):
            response = self.client.get(
                GOOGLE_CALLBACK_PATH,
                params={"code": "synthetic-code", "state": state},
            )

        self.assertEqual(response.status_code, 401)
        persist.assert_not_called()
        self.assertEqual(response.json()["code"], "UNAUTHENTICATED")

    def test_invalid_state_is_rejected_before_google_calls(self):
        self.begin_flow()
        with patch("main.exchange_google_code", new_callable=AsyncMock) as exchange:
            response = self.client.get(
                GOOGLE_CALLBACK_PATH,
                params={
                    "code": "synthetic-code",
                    "state": secrets.token_urlsafe(32),
                },
            )

        self.assertEqual(response.status_code, 400)
        exchange.assert_not_awaited()

    def test_callback_rejection_diagnostics_are_fixed_and_redacted(self):
        state = "S" * 43
        state_cookie, nonce_cookie, verifier_cookie = oauth_cookie_names(state)
        nonce = "synthetic-private-nonce"
        verifier = "synthetic-private-verifier"
        code = "synthetic-private-authorization-code"
        cases = (
            ("invalid_state", None, state, nonce, verifier, code, None),
            ("invalid_state", "bad-state", state, nonce, verifier, code, None),
            ("state_cookie_missing", state, None, nonce, verifier, code, None),
            ("state_cookie_missing", state, "", nonce, verifier, code, None),
            ("state_cookie_mismatch", state, "different-state", nonce, verifier, code, None),
            ("authorization_incomplete", state, state, nonce, verifier, None, None),
            ("authorization_incomplete", state, state, nonce, verifier, code, "denied"),
            ("nonce_cookie_missing", state, state, None, verifier, code, None),
            ("nonce_cookie_missing", state, state, None, None, code, None),
            ("pkce_cookie_missing", state, state, nonce, None, code, None),
        )
        for reason, callback_state, state_value, nonce_value, verifier_value, auth_code, error in cases:
            with self.subTest(reason=reason, error=error):
                self.client.cookies.clear()
                cookies = {
                    state_cookie: state_value,
                    nonce_cookie: nonce_value,
                    verifier_cookie: verifier_value,
                }
                cookie_header = "; ".join(
                    f"{name}={value}" for name, value in cookies.items() if value is not None
                )
                params = {}
                if callback_state is not None:
                    params["state"] = callback_state
                if auth_code is not None:
                    params["code"] = auth_code
                if error is not None:
                    params["error"] = error
                with (
                    self.assertLogs("uvicorn.error", level="WARNING") as captured,
                    patch("main.exchange_google_code", new_callable=AsyncMock) as exchange,
                ):
                    response = self.client.get(
                        GOOGLE_CALLBACK_PATH,
                        params=params,
                        headers={"Cookie": cookie_header, "X-Request-ID": "oauth_test_id"},
                    )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["code"], "HTTP_400")
                self.assertEqual(response.json()["message"], "Request could not be completed.")
                self.assertEqual(response.json()["request_id"], "oauth_test_id")
                self.assertEqual(
                    [record.getMessage() for record in captured.records],
                    [f"request_id=oauth_test_id reason={reason}"],
                )
                for sensitive in (
                    *GOOGLE_SETTINGS.values(),
                    state,
                    callback_state,
                    state_cookie,
                    nonce_cookie,
                    verifier_cookie,
                    nonce,
                    verifier,
                    code,
                    "different-state",
                    str(response.request.url),
                ):
                    if sensitive:
                        self.assertNotIn(sensitive, "\n".join(captured.output))
                self.assertIsNone(captured.records[0].exc_info)
                exchange.assert_not_awaited()

    def test_later_callback_rejection_diagnostics_are_redacted(self):
        cases = (
            ("oauth_configuration_unavailable", 503),
            ("code_exchange_failed", 502),
            ("id_token_verification_unavailable", 502),
            ("id_token_invalid", 401),
            ("id_token_nonce_or_subject_invalid", 401),
            ("identity_persistence_failed", 503),
            ("session_persistence_failed", 503),
            ("frontend_return_unavailable", 503),
        )
        for reason, status in cases:
            with self.subTest(reason=reason):
                self.client.cookies.clear()
                state, nonce, verifier = self.begin_flow()
                code = "synthetic-private-authorization-code"
                raw_token = "synthetic-private-id-token"
                private_error = "synthetic-private-error"
                failure = HTTPException(status_code=status, detail=private_error)
                user = User(uuid4(), datetime.now(timezone.utc))
                session = AuthSession(
                    uuid4(), datetime.now(timezone.utc) + timedelta(hours=8)
                )
                claims = self.callback_claims("synthetic-private-subject", nonce)
                if reason == "id_token_nonce_or_subject_invalid":
                    claims["nonce"] = "different-synthetic-nonce"
                verify_failure = None
                if reason == "id_token_verification_unavailable":
                    verify_failure = google_auth_exceptions.TransportError(private_error)
                elif reason == "id_token_invalid":
                    verify_failure = ValueError(private_error)
                with (
                    patch(
                        "main.google_oauth_settings",
                        side_effect=failure if reason == "oauth_configuration_unavailable" else None,
                        return_value=("synthetic-client-id", "synthetic-client-secret",
                                      GOOGLE_SETTINGS["GOOGLE_OAUTH_REDIRECT_URI"], GOOGLE_ISSUER),
                    ),
                    patch(
                        "main.exchange_google_code",
                        new_callable=AsyncMock,
                        side_effect=failure if reason == "code_exchange_failed" else None,
                        return_value=raw_token,
                    ),
                    patch("main.verify_google_id_token", side_effect=verify_failure, return_value=claims),
                    patch(
                        "main.persist_google_identity",
                        side_effect=failure if reason == "identity_persistence_failed" else None,
                        return_value=(user, True),
                    ),
                    patch(
                        "main.persist_session",
                        side_effect=failure if reason == "session_persistence_failed" else None,
                        return_value=("synthetic-private-session", session),
                    ),
                    patch(
                        "main.frontend_app_url",
                        side_effect=failure if reason == "frontend_return_unavailable" else None,
                        return_value="http://localhost:3001",
                    ),
                    self.assertLogs("uvicorn.error", level="WARNING") as captured,
                ):
                    response = self.client.get(
                        GOOGLE_CALLBACK_PATH,
                        params={"state": state, "code": code},
                        headers={"Accept": "text/html", "X-Request-ID": "oauth_test_id"},
                    )

                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()["request_id"], "oauth_test_id")
                self.assertEqual(
                    [record.getMessage() for record in captured.records],
                    [f"request_id=oauth_test_id reason={reason}"],
                )
                for sensitive in (
                    *GOOGLE_SETTINGS.values(),
                    *oauth_cookie_names(state),
                    state,
                    nonce,
                    verifier,
                    code,
                    raw_token,
                    private_error,
                    "synthetic-private-subject",
                    "synthetic-private-session",
                    str(response.request.url),
                ):
                    self.assertNotIn(sensitive, "\n".join(captured.output))
                self.assertIsNone(captured.records[0].exc_info)

    def test_callback_rejection_diagnostics_are_disabled_outside_development(self):
        for environment in ("staging", "production"):
            with self.subTest(environment=environment):
                with (
                    patch.dict(app.state._state, {"app_env": environment}),
                    self.assertNoLogs("uvicorn.error", level="WARNING"),
                ):
                    response = self.client.get(
                        GOOGLE_CALLBACK_PATH,
                        params={"state": "invalid"},
                    )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["code"], "HTTP_400")

    def test_successful_callback_has_no_rejection_diagnostic(self):
        with self.assertNoLogs("uvicorn.error", level="WARNING"):
            self.finish_flow("synthetic-google-subject-a")

    def test_nonce_mismatch_is_rejected(self):
        state, _, _ = self.begin_flow()
        with (
            patch(
                "main.exchange_google_code",
                new_callable=AsyncMock,
                return_value="synthetic-id-token",
            ),
            patch(
                "main.verify_google_id_token",
                return_value=self.callback_claims(
                    "synthetic-google-subject-a", "different-synthetic-nonce"
                ),
            ),
            patch("main.persist_google_identity") as persist,
        ):
            response = self.client.get(
                GOOGLE_CALLBACK_PATH,
                params={"code": "synthetic-code", "state": state},
            )

        self.assertEqual(response.status_code, 401)
        persist.assert_not_called()

    def test_google_auth_verifies_signature_issuer_audience_and_expiry(self):
        with patch(
            "main.google_id_token._fetch_certs",
            return_value={"synthetic-key": self.certificate_pem},
        ):
            verified = verify_google_id_token(
                self.signed_id_token(),
                GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
                GOOGLE_ISSUER,
            )
            self.assertEqual(verified["iss"], GOOGLE_ISSUER)
            self.assertEqual(
                verified["aud"], GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"]
            )
            self.assertEqual(verified["sub"], "synthetic-google-subject")

            invalid_signer_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            invalid_signer_pem = invalid_signer_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
            invalid_signer = crypt.RSASigner.from_string(
                invalid_signer_pem,
                key_id="synthetic-key",
            )
            invalid_tokens = {
                "signature": jwt.encode(
                    invalid_signer,
                    {
                        "iss": GOOGLE_ISSUER,
                        "aud": GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
                        "exp": int(time.time()) + 300,
                        "iat": int(time.time()) - 10,
                        "sub": "synthetic-google-subject",
                    },
                    key_id="synthetic-key",
                ).decode("ascii"),
                "issuer": self.signed_id_token(iss="https://attacker.example"),
                "audience": self.signed_id_token(aud="another-client"),
                "expiry": self.signed_id_token(exp=int(time.time()) - 1),
            }
            for failure, token in invalid_tokens.items():
                with self.subTest(failure=failure):
                    with self.assertRaises(
                        (ValueError, google_auth_exceptions.GoogleAuthError)
                    ):
                        verify_google_id_token(
                            token,
                            GOOGLE_SETTINGS["GOOGLE_OAUTH_CLIENT_ID"],
                            GOOGLE_ISSUER,
                        )
