import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from users import (
    create_session,
    create_user,
    get_active_session,
    get_or_create_google_user,
    get_user,
    revoke_session,
)

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
            if os.environ.get("AUTH_TEST_SET_ROLE_PASSWORDS") == "1":
                for role, url in (
                    ("acadence_auth_runtime", RUNTIME_DATABASE_URL),
                    ("acadence_auth_migrator", os.environ["MIGRATION_DATABASE_URL"]),
                ):
                    conninfo = url.replace("postgresql+psycopg://", "postgresql://")
                    password = conninfo_to_dict(conninfo)["password"]
                    connection.execute(
                        sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                            sql.Identifier(role), sql.Literal(password)
                        )
                    )

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
            self.assertEqual(version, ("0004_auth_sessions",))
            privileges = connection.execute(
                "SELECT has_table_privilege('acadence_auth_runtime', 'auth.users', p) "
                "FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', "
                "'TRUNCATE', 'REFERENCES', 'TRIGGER']) AS p"
            ).fetchall()
            self.assertEqual(
                privileges,
                [(True,), (True,), (False,), (False,), (False,), (False,), (False,)],
            )
            binding_privileges = connection.execute(
                "SELECT has_table_privilege("
                "'acadence_auth_runtime', 'auth.identity_bindings', p) "
                "FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', "
                "'TRUNCATE', 'REFERENCES', 'TRIGGER']) AS p"
            ).fetchall()
            self.assertEqual(
                binding_privileges,
                [(True,), (True,), (False,), (False,), (False,), (False,), (False,)],
            )
            session_privileges = connection.execute(
                "SELECT has_table_privilege('acadence_auth_runtime', 'auth.sessions', p) "
                "FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', "
                "'TRUNCATE', 'REFERENCES', 'TRIGGER']) AS p"
            ).fetchall()
            self.assertEqual(
                session_privileges,
                [(True,), (True,), (True,), (False,), (False,), (False,), (False,)],
            )

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

        for revision in ("0001_auth_baseline", "head"):
            result = subprocess.run(
                [
                    sys.executable, "-m", "alembic",
                    "downgrade" if revision != "head" else "upgrade", revision,
                ],
                cwd=SERVICE_DIR,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
                users_exist = connection.execute(
                    "SELECT to_regclass('auth.users')"
                ).fetchone()[0]
                bindings_exist = connection.execute(
                    "SELECT to_regclass('auth.identity_bindings')"
                ).fetchone()[0]
                sessions_exist = connection.execute(
                    "SELECT to_regclass('auth.sessions')"
                ).fetchone()[0]
                self.assertEqual(users_exist is not None, revision == "head")
                self.assertEqual(bindings_exist is not None, revision == "head")
                self.assertEqual(sessions_exist is not None, revision == "head")
                version = connection.execute(
                    "SELECT version_num FROM auth.alembic_version"
                ).fetchone()
                expected_version = (
                    "0004_auth_sessions"
                    if revision == "head"
                    else revision
                )
                self.assertEqual(version, (expected_version,))

        with psycopg.connect(RUNTIME_DATABASE_URL) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            rolled_back = create_user(connection)
            connection.rollback()
            connection.execute("SET ROLE acadence_auth_runtime")
            user = create_user(connection)
            google_subject = f"synthetic-google-{uuid4()}"
            first_google_user, first_created = get_or_create_google_user(
                connection, google_subject
            )
            session_token, session = create_session(connection, user.id, 3600)
            self.assertEqual(session.user_id, user.id)
            self.assertEqual(get_active_session(connection, session_token), session)
            self.assertTrue(revoke_session(connection, session_token))
            self.assertIsNone(get_active_session(connection, session_token))
            expired_token, _ = create_session(connection, user.id, -1)
            self.assertIsNone(get_active_session(connection, expired_token))
            repeated_google_user, repeated_created = get_or_create_google_user(
                connection, google_subject
            )
            distinct_google_user, distinct_created = get_or_create_google_user(
                connection, f"synthetic-google-{uuid4()}"
            )

        self.assertEqual(user.id.version, 4)
        self.assertIsNotNone(user.created_at.tzinfo)
        self.assertTrue(first_created)
        self.assertFalse(repeated_created)
        self.assertEqual(first_google_user.id, repeated_google_user.id)
        self.assertTrue(distinct_created)
        self.assertNotEqual(first_google_user.id, distinct_google_user.id)

        concurrent_subject = None
        if os.environ.get("AUTH_TEST_SKIP_CONCURRENCY") != "1":
            concurrent_subject = f"synthetic-google-race-{uuid4()}"
            start_together = Barrier(2)

            def register_concurrently():
                with psycopg.connect(RUNTIME_DATABASE_URL) as connection:
                    connection.execute("SET ROLE acadence_auth_runtime")
                    start_together.wait(timeout=10)
                    return get_or_create_google_user(connection, concurrent_subject)

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: register_concurrently(), range(2)))
            self.assertEqual(results[0][0].id, results[1][0].id)
            self.assertCountEqual([created for _, created in results], [True, False])

        with psycopg.connect(RUNTIME_DATABASE_URL, autocommit=True) as connection:
            connection.execute("SET ROLE acadence_auth_runtime")
            self.assertEqual(get_user(connection, user.id), user)
            with self.assertRaises(psycopg.errors.UniqueViolation):
                connection.execute(
                    "INSERT INTO auth.identity_bindings (provider, subject, user_id) "
                    "VALUES ('google', %s, %s)",
                    (google_subject, first_google_user.id),
                )
            if concurrent_subject is not None:
                self.assertEqual(
                    connection.execute(
                        "SELECT count(*) FROM auth.identity_bindings "
                        "WHERE provider = 'google' AND subject = %s",
                        (concurrent_subject,),
                    ).fetchone(),
                    (1,),
                )
            self.assertIsNone(get_user(connection, rolled_back.id))
            self.assertIsNone(get_user(connection, uuid4()))
            for operation in (
                "UPDATE auth.users SET created_at = now()",
                "DELETE FROM auth.users",
                "ALTER TABLE auth.users ADD COLUMN forbidden text",
            ):
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    connection.execute(operation)
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
