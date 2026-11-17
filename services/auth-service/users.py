"""Internal persistence for Auth-owned users."""

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class User:
    id: UUID
    created_at: datetime


@dataclass(frozen=True)
class AuthSession:
    user_id: UUID
    expires_at: datetime


SESSION_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}\Z")


def is_valid_session_token(token: str) -> bool:
    return SESSION_TOKEN_PATTERN.fullmatch(token) is not None


def session_token_hash(token: str) -> str | None:
    if not is_valid_session_token(token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def create_session(
    connection: psycopg.Connection, user_id: UUID, ttl_seconds: int
) -> tuple[str, AuthSession]:
    token = secrets.token_urlsafe(32)
    token_hash = session_token_hash(token)
    if token_hash is None:
        raise RuntimeError("Generated Auth session token has an invalid format")
    row = connection.execute(
        "INSERT INTO auth.sessions (token_hash, user_id, expires_at) "
        "VALUES (%s, %s, now() + (%s * interval '1 second')) "
        "RETURNING expires_at",
        (token_hash, user_id, ttl_seconds),
    ).fetchone()
    if row is None:
        raise RuntimeError("Auth session insert did not return a row")
    return token, AuthSession(user_id, row[0])


def get_active_session(
    connection: psycopg.Connection, token: str
) -> AuthSession | None:
    token_hash = session_token_hash(token)
    if token_hash is None:
        return None
    row = connection.execute(
        "SELECT user_id, expires_at FROM auth.sessions "
        "WHERE token_hash = %s AND expires_at > now() AND revoked_at IS NULL",
        (token_hash,),
    ).fetchone()
    return AuthSession(*row) if row is not None else None


def revoke_session(connection: psycopg.Connection, token: str) -> bool:
    token_hash = session_token_hash(token)
    if token_hash is None:
        return False
    cursor = connection.execute(
        "UPDATE auth.sessions SET revoked_at = now() "
        "WHERE token_hash = %s AND revoked_at IS NULL",
        (token_hash,),
    )
    return cursor.rowcount == 1


def get_or_create_google_user(
    connection: psycopg.Connection, subject: str
) -> tuple[User, bool]:
    if not subject or len(subject) > 255:
        raise ValueError("Google subject must contain 1 to 255 characters")

    with connection.transaction():
        connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (subject,))
        row = connection.execute(
            "SELECT users.id, users.created_at "
            "FROM auth.identity_bindings AS bindings "
            "JOIN auth.users AS users ON users.id = bindings.user_id "
            "WHERE bindings.provider = 'google' AND bindings.subject = %s",
            (subject,),
        ).fetchone()
        if row is not None:
            return User(*row), False

        user = create_user(connection)
        connection.execute(
            "INSERT INTO auth.identity_bindings (provider, subject, user_id) "
            "VALUES ('google', %s, %s)",
            (subject, user.id),
        )
        return user, True


def create_user(connection: psycopg.Connection) -> User:
    row = connection.execute(
        "INSERT INTO auth.users (id) VALUES (%s) RETURNING id, created_at",
        (uuid4(),),
    ).fetchone()
    if row is None:
        raise RuntimeError("Auth user insert did not return a row")
    return User(*row)


def get_user(connection: psycopg.Connection, user_id: UUID) -> User | None:
    row = connection.execute(
        "SELECT id, created_at FROM auth.users WHERE id = %s",
        (user_id,),
    ).fetchone()
    return User(*row) if row is not None else None
