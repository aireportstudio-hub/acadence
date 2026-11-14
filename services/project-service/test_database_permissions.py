import os
import subprocess
import sys
import unittest
from pathlib import Path

import psycopg

SERVICE_DIR = Path(__file__).resolve().parent
AUTH_DIR = SERVICE_DIR.parent / "auth-service"
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

        self.run_migration(AUTH_DIR, AUTH_MIGRATION_DATABASE_URL, "upgrade", "head")
        self.run_migration(SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "upgrade", "head")

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
                ("0001_auth_baseline",),
            )
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0001_project_baseline",),
            )

        self.run_migration(SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "downgrade", "base")
        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            self.assertEqual(
                connection.execute("SELECT version_num FROM auth.alembic_version").fetchone(),
                ("0001_auth_baseline",),
            )
        self.run_migration(SERVICE_DIR, PROJECT_MIGRATION_DATABASE_URL, "upgrade", "head")

        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            self.assertEqual(
                connection.execute("SELECT version_num FROM project.alembic_version").fetchone(),
                ("0001_project_baseline",),
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
            self.assertEqual(
                connection.execute("SELECT value FROM project.permission_probe").fetchone(),
                ("project",),
            )
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO project.permission_probe VALUES ('denied')")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("UPDATE project.permission_probe SET value = 'denied'")
