"""Internal persistence for Project-owned project records."""

from dataclasses import dataclass
from uuid import UUID, uuid4

import psycopg


@dataclass(frozen=True)
class Project:
    id: UUID
    owner_user_id: UUID
    title: str
    description: str | None


def create_project(
    connection: psycopg.Connection,
    owner_user_id: UUID,
    title: str,
    description: str | None = None,
) -> Project:
    project = Project(uuid4(), owner_user_id, title, description)
    connection.execute(
        "INSERT INTO project.projects (id, owner_user_id, title, description) "
        "VALUES (%s, %s, %s, %s)",
        (project.id, project.owner_user_id, project.title, project.description),
    )
    return project


def get_project(
    connection: psycopg.Connection, project_id: UUID, owner_user_id: UUID
) -> Project | None:
    row = connection.execute(
        "SELECT id, owner_user_id, title, description FROM project.projects "
        "WHERE id = %s AND owner_user_id = %s",
        (project_id, owner_user_id),
    ).fetchone()
    return Project(*row) if row is not None else None
