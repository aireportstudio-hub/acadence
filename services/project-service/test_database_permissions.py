import os
import subprocess
import sys
import unittest
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from projects import create_project, get_project, list_projects

SERVICE_DIR = Path(__file__).resolve().parent
AUTH_DIR = SERVICE_DIR.parent / "auth-service"
sys.path.insert(0, str(AUTH_DIR))
from users import create_user, get_user
sys.path.pop(0)

ADMIN_DATABASE_URL = os.environ.get("PROJECT_TEST_ADMIN_DATABASE_URL")
PROJECT_RUNTIME_DATABASE_URL = os.environ.get("PROJECT_TEST_RUNTIME_DATABASE_URL")
AUTH_RUNTIME_DATABASE_URL = os.environ.get("AUTH_TEST_RUNTIME_DATABASE_URL")
PROJECT_MIGRATION_DATABASE_URL = os.environ.get("PROJECT_MIGRATION_DATABASE_URL")
AUTH_MIGRATION_DATABASE_URL = os.environ.get("AUTH_MIGRATION_DATABASE_URL")


@unittest.skipUnless(
    all(
        (
            ADMIN_DATABASE_URL,
            PROJECT_RUNTIME_DATABASE_URL,
            AUTH_RUNTIME_DATABASE_URL,
            PROJECT_MIGRATION_DATABASE_URL,
            AUTH_MIGRATION_DATABASE_URL,
        )
    ),
    "Set disposable Auth and Project test database URLs to run PostgreSQL integration tests",
)
class ProjectDatabaseMigrationTest(unittest.TestCase):
    def run_migration(self, service_dir, database_url, *args):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=service_dir,
            env={**os.environ, "MIGRATION_DATABASE_URL": database_url},
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_database_migrations_and_role_boundaries(self):
        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            for service_dir in (AUTH_DIR, SERVICE_DIR):
                bootstrap = service_dir / "database" / "bootstrap.sql"
                connection.execute(bootstrap.read_text(encoding="utf-8"), prepare=False)
            if os.environ.get("PROJECT_TEST_SET_ROLE_PASSWORDS") == "1":
                for role, url in (
                    ("acadence_project_runtime", PROJECT_RUNTIME_DATABASE_URL),
                    ("acadence_auth_runtime", AUTH_RUNTIME_DATABASE_URL),
                    ("acadence_project_migrator", PROJECT_MIGRATION_DATABASE_URL),
                    ("acadence_auth_migrator", AUTH_MIGRATION_DATABASE_URL),
                ):
                    conninfo = url.replace("postgresql+psycopg://", "postgresql://")
                    password = conninfo_to_dict(conninfo)["password"]
                    connection.execute(
                        sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                            sql.Identifier(role), sql.Literal(password)
                        )
                    )

        self.run_migration(AUTH_DIR, AUTH_MIGRATION_DATABASE_URL, "upgrade", "head")
        self.run_migration(
            SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "upgrade", "0001_project_baseline"
        )

        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            tables = connection.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_name = 'alembic_version' ORDER BY table_schema"
            ).fetchall()
            self.assertEqual(
                tables, [("auth", "alembic_version"), ("project", "alembic_version")]
            )
            self.assertEqual(
                connection.execute("SELECT version_num FROM auth.alembic_version").fetchone(),
                ("0004_auth_sessions",),
            )
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0001_project_baseline",),
            )

        self.run_migration(SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "upgrade", "head")
        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0003_project_events",),
            )
        self.run_migration(
            SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "downgrade", "0001_project_baseline"
        )
        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            self.assertEqual(
                connection.execute("SELECT version_num FROM auth.alembic_version").fetchone(),
                ("0004_auth_sessions",),
            )
            self.assertIsNone(
                connection.execute("SELECT to_regclass('project.projects')").fetchone()[0]
            )
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0001_project_baseline",),
            )
        self.run_migration(SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "upgrade", "head")

        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0003_project_events",),
            )
            self.assertEqual(
                connection.execute(
                    "SELECT has_schema_privilege('acadence_project_runtime', 'auth', 'USAGE'), "
                    "has_schema_privilege('acadence_auth_runtime', 'project', 'USAGE')"
                ).fetchone(),
                (False, False),
            )
            self.assertFalse(
                connection.execute(
                    "SELECT has_table_privilege("
                    "'acadence_project_runtime', 'project.alembic_version', 'SELECT')"
                ).fetchone()[0]
            )
            privileges = connection.execute(
                "SELECT has_table_privilege('acadence_project_runtime', 'project.projects', p) "
                "FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', "
                "'TRUNCATE', 'REFERENCES', 'TRIGGER']) AS p"
            ).fetchall()
            self.assertEqual(
                privileges,
                [(True,), (True,), (False,), (False,), (False,), (False,), (False,)],
            )
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM pg_constraint "
                    "WHERE conrelid = 'project.projects'::regclass AND contype = 'f'"
                ).fetchone(),
                (0,),
            )
            connection.execute("SET ROLE acadence_auth_owner")
            connection.execute("CREATE TABLE auth.permission_probe (value text)")
            connection.execute("INSERT INTO auth.permission_probe VALUES ('auth')")
            connection.execute("RESET ROLE")
            connection.execute("SET ROLE acadence_project_owner")
            connection.execute("CREATE TABLE project.permission_probe (value text)")
            connection.execute("INSERT INTO project.permission_probe VALUES ('project')")
            connection.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE "
                "ON project.permission_probe TO acadence_project_runtime"
            )
            connection.execute("RESET ROLE")
            connection.execute("GRANT USAGE ON SCHEMA auth TO acadence_project_runtime")
            connection.execute("GRANT SELECT ON auth.permission_probe TO acadence_project_runtime")
            connection.execute("GRANT USAGE ON SCHEMA project TO acadence_auth_runtime")
            connection.execute("GRANT SELECT ON project.permission_probe TO acadence_auth_runtime")

            connection.execute("SET ROLE acadence_project_migrator")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE auth.migration_probe (value text)")
            connection.execute("RESET ROLE")
            connection.execute("SET ROLE acadence_project_owner")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO auth.permission_probe VALUES ('denied')")
            connection.execute("RESET ROLE")
            connection.execute("SET ROLE acadence_auth_owner")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO project.permission_probe VALUES ('denied')")
            connection.execute("RESET ROLE")

        with psycopg.connect(AUTH_RUNTIME_DATABASE_URL) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            user = create_user(connection)
        with psycopg.connect(AUTH_RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            self.assertEqual(get_user(connection, user.id), user)
        owner_id = user.id
        self.assertEqual(owner_id.version, 4)
        other_owner_id = uuid4()
        with psycopg.connect(PROJECT_RUNTIME_DATABASE_URL) as connection:
            connection.execute("SET ROLE acadence_project_runtime")
            rolled_back = create_project(connection, owner_id, "Rolled back")
            connection.rollback()
        with psycopg.connect(PROJECT_RUNTIME_DATABASE_URL) as connection:
            connection.execute("SET ROLE acadence_project_runtime")
            project = create_project(connection, owner_id, "A project", "Student description")
            without_description = create_project(connection, owner_id, "Another project")

        with psycopg.connect(PROJECT_RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_project_runtime")
            self.assertEqual(get_project(connection, project.id, owner_id), project)
            self.assertEqual(
                list_projects(connection, owner_id), [project, without_description]
            )
            self.assertEqual(list_projects(connection, other_owner_id), [])
            self.assertEqual(
                get_project(connection, without_description.id, owner_id), without_description
            )
            self.assertIsNone(get_project(connection, project.id, other_owner_id))
            self.assertIsNone(get_project(connection, uuid4(), owner_id))
            self.assertIsNone(get_project(connection, rolled_back.id, owner_id))
            for operation in (
                "UPDATE project.projects SET title = 'denied'",
                "DELETE FROM project.projects",
                "ALTER TABLE project.projects ADD COLUMN forbidden text",
                "INSERT INTO auth.users (id) VALUES ('00000000-0000-4000-8000-000000000001')",
                "UPDATE auth.users SET created_at = now()",
                "DELETE FROM auth.users",
            ):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    connection.execute(operation)

        with psycopg.connect(PROJECT_RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_project_runtime")
            connection.execute("INSERT INTO project.permission_probe VALUES ('allowed')")
            connection.execute(
                "UPDATE project.permission_probe SET value = 'updated' WHERE value = 'allowed'"
            )
            self.assertEqual(
                connection.execute(
                    "SELECT value FROM project.permission_probe WHERE value = 'updated'"
                ).fetchone(),
                ("updated",),
            )
            connection.execute("DELETE FROM project.permission_probe WHERE value = 'updated'")
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM project.permission_probe WHERE value = 'updated'"
                ).fetchone(),
                (0,),
            )
            self.assertEqual(
                connection.execute("SELECT value FROM auth.permission_probe").fetchone(),
                ("auth",),
            )
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE project.runtime_probe (value text)")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("ALTER TABLE project.permission_probe ADD COLUMN extra text")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("ALTER SCHEMA project RENAME TO project_renamed")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE public.runtime_probe (value text)")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO auth.permission_probe VALUES ('denied')")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("UPDATE auth.permission_probe SET value = 'denied'")

        with psycopg.connect(AUTH_RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute(
                    "INSERT INTO project.projects (id, owner_user_id, title) VALUES (%s, %s, %s)",
                    (uuid4(), owner_id, "denied"),
                )
            self.assertEqual(
                connection.execute("SELECT value FROM project.permission_probe").fetchone(),
                ("project",),
            )
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO project.permission_probe VALUES ('denied')")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("UPDATE project.permission_probe SET value = 'denied'")
