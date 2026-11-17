import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from main import SESSION_COOKIE_NAME, app
from users import AuthSession, get_active_session, revoke_session


class AuthSessionTest(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "FRONTEND_APP_URL": "http://localhost:3001",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.session = AuthSession(
            uuid4(),
            datetime.now(timezone.utc) + timedelta(hours=8),
        )

    def test_signed_out_user_cannot_read_session(self):
        with patch("main.lookup_session") as lookup:
            response = self.client.get("/v1/auth/session")

        self.assertEqual(response.status_code, 401)
        lookup.assert_not_called()

    def test_malformed_session_cookie_is_rejected(self):
        self.client.cookies.set(SESSION_COOKIE_NAME, "not-a-session-token")
        with patch("main.lookup_session") as lookup:
            response = self.client.get("/v1/auth/session")

        self.assertEqual(response.status_code, 401)
        lookup.assert_not_called()

    def test_non_ascii_session_token_is_rejected_without_database_access(self):
        connection = Mock()

        self.assertIsNone(get_active_session(connection, "\u00e9"))
        self.assertFalse(revoke_session(connection, "\u00e9"))
        connection.execute.assert_not_called()

    def test_valid_session_returns_minimal_identity(self):
        self.client.cookies.set(SESSION_COOKIE_NAME, "v" * 43)
        with patch("main.lookup_session", return_value=self.session):
            response = self.client.get("/v1/auth/session")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user_id"], str(self.session.user_id))
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_expired_or_revoked_session_is_rejected(self):
        self.client.cookies.set(SESSION_COOKIE_NAME, "inactive-session-token")
        with patch("main.lookup_session", return_value=None):
            response = self.client.get("/v1/auth/session")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "UNAUTHENTICATED")

    def test_sign_out_invalidates_session_and_clears_cookie(self):
        valid_token = "v" * 43
        active_tokens = {valid_token}

        def find_session(token: str) -> AuthSession | None:
            return self.session if token in active_tokens else None

        def revoke(token: str) -> None:
            active_tokens.discard(token)

        self.client.cookies.set(SESSION_COOKIE_NAME, valid_token)
        with (
            patch("main.lookup_session", side_effect=find_session),
            patch("main.invalidate_session", side_effect=revoke) as invalidate,
        ):
            before_logout = self.client.get("/v1/auth/session")
            logout = self.client.post(
                "/v1/auth/logout",
                headers={"Origin": "http://localhost:3001"},
            )
            after_logout = self.client.get("/v1/auth/session")

        self.assertEqual(before_logout.status_code, 200)
        self.assertEqual(logout.status_code, 204)
        self.assertEqual(after_logout.status_code, 401)
        invalidate.assert_called_once_with(valid_token)
        self.assertIn("max-age=0", logout.headers["set-cookie"].lower())

    def test_sign_out_rejects_cross_origin_request(self):
        with patch("main.invalidate_session") as invalidate:
            response = self.client.post(
                "/v1/auth/logout",
                headers={"Origin": "https://attacker.example"},
            )

        self.assertEqual(response.status_code, 403)
        invalidate.assert_not_called()
