import base64
import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlencode, urlparse
from uuid import UUID, uuid4

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from starlette.exceptions import HTTPException as StarletteHTTPException

from users import (
    AuthSession,
    User,
    create_session,
    get_active_session,
    get_or_create_google_user,
    is_valid_session_token,
    revoke_session,
)


GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_CALLBACK_PATH = "/v1/auth/google/callback"
GOOGLE_ISSUER = "https://accounts.google.com"
OAUTH_COOKIE_PREFIX = "acadence_google"
OAUTH_TRANSACTION_TTL_SECONDS = 600
OAUTH_STATE_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}\Z")
SESSION_COOKIE_NAME = "acadence_session"
SESSION_TTL_SECONDS = 28800


class BoundedGoogleAuthRequest(GoogleAuthRequest):
    def __call__(
        self,
        url: str,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: object,
    ):
        return super().__call__(
            url,
            method=method,
            body=body,
            headers=headers,
            timeout=timeout or 5,
            **kwargs,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app_env = os.environ.get("APP_ENV", "development")
    if app_env not in {"development", "staging", "production"}:
        raise ValueError("APP_ENV must be development, staging, or production")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")

    app.state.app_env = app_env
    app.state.log_level = log_level
    yield


app = FastAPI(title="Acadence Auth Service", lifespan=lifespan)


def oauth_cookie_names(state: str) -> tuple[str, str, str]:
    suffix = f"_{state}"
    return (
        f"{OAUTH_COOKIE_PREFIX}_state{suffix}",
        f"{OAUTH_COOKIE_PREFIX}_nonce{suffix}",
        f"{OAUTH_COOKIE_PREFIX}_pkce{suffix}",
    )


def google_oauth_settings() -> tuple[str, str, str, str]:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI")
    issuer = os.environ.get("OIDC_ISSUER", GOOGLE_ISSUER)
    parsed_redirect = urlparse(redirect_uri or "")

    if (
        not client_id
        or not client_secret
        or not redirect_uri
        or issuer != GOOGLE_ISSUER
        or not parsed_redirect.hostname
        or parsed_redirect.username is not None
        or parsed_redirect.password is not None
        or parsed_redirect.path != GOOGLE_CALLBACK_PATH
        or parsed_redirect.query
        or parsed_redirect.fragment
        or (
            parsed_redirect.scheme != "https"
            and not (
                os.environ.get("APP_ENV", "development") == "development"
                and parsed_redirect.scheme == "http"
                and parsed_redirect.hostname in {"localhost", "127.0.0.1"}
            )
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not configured.",
        )

    return client_id, client_secret, redirect_uri, issuer


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def new_oauth_transaction() -> tuple[str, str, str]:
    return (
        secrets.token_urlsafe(32),
        secrets.token_urlsafe(32),
        secrets.token_urlsafe(64),
    )


async def exchange_google_code(
    code: str,
    code_verifier: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": code_verifier,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Google sign-in could not be completed.",
        ) from exc

    try:
        token_response = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Google sign-in could not be completed.",
        ) from exc

    if not isinstance(token_response, dict) or not isinstance(
        token_response.get("id_token"), str
    ):
        raise HTTPException(
            status_code=502,
            detail="Google sign-in could not be completed.",
        )
    return token_response["id_token"]


def verify_google_id_token(
    token: str,
    client_id: str,
    issuer: str,
) -> dict[str, object]:
    claims = google_id_token.verify_oauth2_token(
        token,
        BoundedGoogleAuthRequest(),
        audience=client_id,
    )
    expiration = claims.get("exp")
    subject = claims.get("sub")
    if (
        claims.get("iss") != issuer
        or claims.get("aud") != client_id
        or not isinstance(expiration, (int, float))
        or expiration <= time.time()
        or not isinstance(subject, str)
        or not subject
        or len(subject) > 255
    ):
        raise ValueError("Google ID token claims are invalid")
    return claims


def persist_google_identity(subject: str) -> tuple[User, bool]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not available.",
        )

    try:
        with psycopg.connect(database_url) as connection:
            return get_or_create_google_user(connection, subject)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is temporarily unavailable.",
        ) from exc


def persist_session(user_id: UUID) -> tuple[str, AuthSession]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is not available.",
        )

    try:
        with psycopg.connect(database_url) as connection:
            return create_session(connection, user_id, SESSION_TTL_SECONDS)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in is temporarily unavailable.",
        ) from exc


def lookup_session(token: str) -> AuthSession | None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="Authentication is temporarily unavailable.",
        )

    try:
        with psycopg.connect(database_url) as connection:
            return get_active_session(connection, token)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Authentication is temporarily unavailable.",
        ) from exc


def invalidate_session(token: str) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="Sign-out is temporarily unavailable.",
        )

    try:
        with psycopg.connect(database_url) as connection:
            revoke_session(connection, token)
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=503,
            detail="Sign-out is temporarily unavailable.",
        ) from exc


def frontend_app_url() -> str:
    configured_url = os.environ.get("FRONTEND_APP_URL")
    if not configured_url and os.environ.get("APP_ENV", "development") == "development":
        configured_url = "http://localhost:3001"
    parsed_url = urlparse(configured_url or "")
    if (
        not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.path not in {"", "/"}
        or parsed_url.query
        or parsed_url.fragment
        or (
            parsed_url.scheme != "https"
            and not (
                os.environ.get("APP_ENV", "development") == "development"
                and parsed_url.scheme == "http"
                and parsed_url.hostname in {"localhost", "127.0.0.1"}
            )
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="The application return address is not configured.",
        )
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


@app.middleware("http")
async def request_correlation(request: Request, call_next):
    incoming_ids = request.headers.getlist("X-Request-ID")
    if len(incoming_ids) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", incoming_ids[0]):
        request.state.request_id = incoming_ids[0]
    else:
        request.state.request_id = uuid4().hex

    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    if request.url.path == GOOGLE_CALLBACK_PATH:
        state = request.query_params.get("state", "")
        if OAUTH_STATE_PATTERN.fullmatch(state):
            for name in oauth_cookie_names(state):
                response.delete_cookie(
                    name,
                    path=GOOGLE_CALLBACK_PATH,
                    secure=request.app.state.app_env != "development",
                    httponly=True,
                    samesite="lax",
                )
    return response


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "request_id": request.state.request_id,
            "details": {},
        },
        headers=headers,
    )
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    reason = getattr(request.state, "google_callback_rejection_reason", None)
    if reason is not None and request.app.state.app_env == "development":
        logging.getLogger("uvicorn.error").warning(
            "request_id=%s reason=%s", request.state.request_id, reason
        )
    codes = {
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        502: "UPSTREAM_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return error_response(
        request,
        exc.status_code,
        codes.get(exc.status_code, f"HTTP_{exc.status_code}"),
        "Request could not be completed.",
        exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed.")


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(request, 500, "INTERNAL_SERVER_ERROR", "Internal server error.")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readiness() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/v1/auth/google/start")
def google_sign_in_start(request: Request, response: Response) -> dict[str, str]:
    client_id, _, redirect_uri, _ = google_oauth_settings()
    state, nonce, verifier = new_oauth_transaction()
    state_cookie, nonce_cookie, verifier_cookie = oauth_cookie_names(state)
    secure_cookie = request.app.state.app_env != "development"
    for name, value in (
        (state_cookie, state),
        (nonce_cookie, nonce),
        (verifier_cookie, verifier),
    ):
        response.set_cookie(
            name,
            value,
            max_age=OAUTH_TRANSACTION_TTL_SECONDS,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            path=GOOGLE_CALLBACK_PATH,
        )

    authorization_url = GOOGLE_AUTHORIZATION_ENDPOINT + "?" + urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid",
            "state": state,
            "nonce": nonce,
            "code_challenge": pkce_challenge(verifier),
            "code_challenge_method": "S256",
        }
    )
    response.headers["Cache-Control"] = "no-store"
    return {"authorization_url": authorization_url}


@app.get(GOOGLE_CALLBACK_PATH)
async def google_sign_in_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> dict[str, object]:
    request.state.google_callback_rejection_reason = "invalid_state"
    if state is None or OAUTH_STATE_PATTERN.fullmatch(state) is None:
        raise HTTPException(status_code=400, detail="Invalid Google sign-in state.")

    state_cookie, nonce_cookie, verifier_cookie = oauth_cookie_names(state)
    state_value = request.cookies.get(state_cookie, "")
    if not hmac.compare_digest(state, state_value):
        request.state.google_callback_rejection_reason = (
            "state_cookie_missing" if not state_value else "state_cookie_mismatch"
        )
        raise HTTPException(status_code=400, detail="Invalid Google sign-in state.")

    request.state.google_callback_rejection_reason = "authorization_incomplete"
    if error is not None or not code:
        raise HTTPException(status_code=400, detail="Google sign-in was not completed.")

    nonce = request.cookies.get(nonce_cookie, "")
    verifier = request.cookies.get(verifier_cookie, "")
    if not nonce or not verifier:
        request.state.google_callback_rejection_reason = (
            "nonce_cookie_missing" if not nonce else "pkce_cookie_missing"
        )
        raise HTTPException(status_code=400, detail="Invalid Google sign-in state.")

    request.state.google_callback_rejection_reason = "oauth_configuration_unavailable"
    client_id, client_secret, redirect_uri, issuer = google_oauth_settings()
    request.state.google_callback_rejection_reason = "code_exchange_failed"
    raw_id_token = await exchange_google_code(
        code,
        verifier,
        client_id,
        client_secret,
        redirect_uri,
    )
    try:
        claims = await run_in_threadpool(
            verify_google_id_token,
            raw_id_token,
            client_id,
            issuer,
        )
    except google_auth_exceptions.TransportError as exc:
        request.state.google_callback_rejection_reason = "id_token_verification_unavailable"
        raise HTTPException(
            status_code=502,
            detail="Google sign-in could not be verified.",
        ) from exc
    except (ValueError, google_auth_exceptions.GoogleAuthError) as exc:
        request.state.google_callback_rejection_reason = "id_token_invalid"
        raise HTTPException(
            status_code=401,
            detail="Google ID token was rejected.",
        ) from exc

    token_nonce = claims.get("nonce")
    subject = claims.get("sub")
    if (
        not isinstance(token_nonce, str)
        or not hmac.compare_digest(nonce, token_nonce)
        or not isinstance(subject, str)
    ):
        request.state.google_callback_rejection_reason = "id_token_nonce_or_subject_invalid"
        raise HTTPException(status_code=401, detail="Google ID token was rejected.")

    request.state.google_callback_rejection_reason = "identity_persistence_failed"
    user, created = persist_google_identity(subject)
    request.state.google_callback_rejection_reason = "session_persistence_failed"
    session_token, session = persist_session(user.id)
    if "text/html" in request.headers.get("accept", ""):
        request.state.google_callback_rejection_reason = "frontend_return_unavailable"
        result: Response = RedirectResponse(
            f"{frontend_app_url()}/dashboard",
            status_code=303,
            headers={"Cache-Control": "no-store"},
        )
    else:
        result = JSONResponse(
            content={"user_id": str(user.id), "created": created},
            headers={"Cache-Control": "no-store"},
        )
    cookie_domain = os.environ.get("COOKIE_DOMAIN") or None
    result.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=request.app.state.app_env != "development",
        samesite="lax",
        path="/",
        domain=cookie_domain,
    )
    return result


@app.get("/v1/auth/session")
def current_session(request: Request, response: Response) -> dict[str, str]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token or not is_valid_session_token(token):
        raise HTTPException(status_code=401, detail="A valid session is required.")

    session = lookup_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="A valid session is required.")

    response.headers["Cache-Control"] = "no-store"
    return {
        "user_id": str(session.user_id),
        "expires_at": session.expires_at.isoformat(),
    }


@app.post("/v1/auth/logout", status_code=204)
def sign_out(request: Request) -> Response:
    origin = request.headers.get("origin")
    if not origin or origin.rstrip("/") != frontend_app_url():
        raise HTTPException(status_code=403, detail="Sign-out request was rejected.")

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and is_valid_session_token(token):
        invalidate_session(token)

    result = Response(status_code=204, headers={"Cache-Control": "no-store"})
    result.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        domain=os.environ.get("COOKIE_DOMAIN") or None,
        secure=request.app.state.app_env != "development",
        httponly=True,
        samesite="lax",
    )
    return result
