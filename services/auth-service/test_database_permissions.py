import os
import subprocess
import sys
import unittest
from pathlib import Path

import psycopg

SERVICE_DIR = Path(__file__).resolve().parent
BOOTSTRAP_PATH = SERVICE_DIR / "database" / "bootstrap.sql"
ADMIN_DATABASE_URL = os.environ.get("AUTH_TEST_ADMIN_DATABASE_URL")
RUNTIME_DATABASE_URL = os.environ.get("AUTH_TEST_RUNTIME_DATABASE_URL")


@unittest.skipUnless(
    ADMIN_DATABASE_URL
    and RUNTIME_DATABASE_URL
    and os.environ.get("MIGRATION_DATABASE_URL"),
    "Set disposable Auth test database URLs to run PostgreSQL integration tests",
)
class AuthDatabaseMigrationTest(unittest.TestCase):
    def test_empty_database_migration_and_role_boundaries(self):
        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            connection.execute(BOOTSTRAP_PATH.read_text(encoding="utf-8"), prepare=False)

        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=SERVICE_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
            tables = connection.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_name = 'alembic_version'"
            ).fetchall()
            self.assertEqual(
                tables,
                [("auth", "alembic_version")],
                result.stdout
                + result.stderr
                + repr(
                    connection.execute(
                        "SELECT schema_name FROM information_schema.schemata"
                    ).fetchall()
                ),
            )
            version = connection.execute(
                "SELECT version_num FROM auth.alembic_version"
            ).fetchone()
            self.assertEqual(version, ("0001_auth_baseline",))

            identity = connection.execute(
                "SELECT current_user, session_user"
            ).fetchone()
            self.assertEqual(identity, ("postgres", "postgres"))
            connection.execute("CREATE ROLE acadence_project_owner NOLOGIN")
            connection.execute(
                "CREATE SCHEMA project AUTHORIZATION acadence_project_owner"
            )
            connection.execute("SET ROLE acadence_project_owner")
            connection.execute("CREATE TABLE project.owner_probe (value text)")
            connection.execute("INSERT INTO project.owner_probe VALUES ('protected')")
            connection.execute("RESET ROLE")
            connection.execute(
                "GRANT USAGE ON SCHEMA project TO acadence_auth_runtime"
            )
            connection.execute(
                "GRANT SELECT ON project.owner_probe TO acadence_auth_runtime"
            )
            connection.execute("SET ROLE acadence_auth_migrator")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute(
                    "CREATE TABLE project.migration_write_probe (value text)"
                )
            connection.execute("SET ROLE acadence_auth_owner")
            connection.execute("CREATE TABLE auth.permission_probe (value text)")
            connection.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE "
                "ON auth.permission_probe TO acadence_auth_runtime"
            )
            connection.execute("RESET ROLE")

        with psycopg.connect(RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            self.assertTrue(
                connection.execute(
                    "SELECT has_schema_privilege(current_user, 'auth', 'USAGE')"
                ).fetchone()[0]
            )
            self.assertFalse(
                connection.execute(
                    "SELECT has_schema_privilege(current_user, 'auth', 'CREATE')"
                ).fetchone()[0]
            )
            connection.execute("INSERT INTO auth.permission_probe VALUES ('allowed')")
            self.assertEqual(
                connection.execute(
                    "SELECT value FROM auth.permission_probe"
                ).fetchone(),
                ("allowed",),
            )
            self.assertEqual(
                connection.execute("SELECT value FROM project.owner_probe").fetchone(),
                ("protected",),
            )

            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE auth.runtime_ddl_probe (value text)")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE public.runtime_write_probe (value text)")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("INSERT INTO project.owner_probe VALUES ('denied')")
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                connection.execute("CREATE TABLE project.runtime_write_probe (value text)")
