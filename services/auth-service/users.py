"""Internal persistence for Auth-owned users."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class User:
    id: UUID
    created_at: datetime


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
