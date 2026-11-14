"""Verify all service-owned PostgreSQL baselines against one fresh local database.

Set P02_TEST_ADMIN_DATABASE_URL to a disposable database URL, then run:
    python scripts/test_p02_database_foundation.py
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[1]
SERVICES = (
    ("auth-service", "auth", "auth"),
    ("billing-service", "billing", "billing"),
    ("project-service", "project", "project"),
    ("template-service", "template", "template"),
    ("ai-orchestration-service", "orchestration", "orchestration"),
    ("quality-service", "quality", "quality"),
    ("visual-ai-service", "visual", "visual"),
    ("document-service", "document", "document"),
    ("notification-service", "notification", "notification"),
)
NEW_SERVICES = {
    "billing",
    "template",
    "orchestration",
    "quality",
    "visual",
    "document",
    "notification",
}


def role_name(schema: str, purpose: str) -> str:
    return f"acadence_{schema}_{purpose}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_denied(
    connection: psycopg.Connection, statement: sql.Composable, label: str
) -> None:
    try:
        connection.execute(statement)
    except psycopg.errors.InsufficientPrivilege:
        return
    raise RuntimeError(f"Expected permission denial: {label}")


def migration_url(admin_url: URL, username: str, password: str) -> str:
    return URL.create(
        "postgresql+psycopg",
        username=username,
        password=password,
        host=admin_url.host,
        port=admin_url.port,
        database=admin_url.database,
        query=dict(admin_url.query),
    ).render_as_string(hide_password=False)


def run_migration(service_dir: Path, database_url: str, *arguments: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=service_dir,
        env={**os.environ, "MIGRATION_DATABASE_URL": database_url},
        capture_output=True,
        text=True,
        check=False,
    )
    require(
        result.returncode == 0,
        f"Alembic {arguments} failed in {service_dir.name}:\n"
        f"{result.stdout}{result.stderr}",
    )


def bootstrap_services(
    admin_url: str, passwords: dict[tuple[str, str], str]
) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        schemas = [schema for _, schema, _ in SERVICES]
        roles = [
            role_name(schema, purpose)
            for schema in schemas
            for purpose in ("owner", "migrator", "runtime")
        ]
        existing_schemas = connection.execute(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name = ANY(%s)",
            (schemas,),
        ).fetchall()
        existing_roles = connection.execute(
            "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
            (roles,),
        ).fetchall()
        require(
            not existing_schemas and not existing_roles,
            "The database is not fresh: one or more Acadence schemas or roles exist.",
        )

        for service_name, _, schema in SERVICES:
            bootstrap = (
                ROOT
                / "services"
                / service_name
                / "database"
                / "bootstrap.sql"
            ).read_text(encoding="utf-8")
            connection.execute(bootstrap, prepare=False)
            for purpose in ("migrator", "runtime"):
                name = role_name(schema, purpose)
                password = passwords[(schema, purpose)]
                connection.execute(
                    sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                        sql.Identifier(name), sql.Literal(password)
                    )
                )


def assert_baseline_versions(
    admin_url: str, expected_schemas: set[str], persistence_tables: bool = False
) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        for _, schema, _ in SERVICES:
            exists = connection.execute(
                "SELECT to_regclass(%s)",
                (f"{schema}.alembic_version",),
            ).fetchone()[0]
            if schema in expected_schemas:
                require(exists is not None, f"{schema} is missing its version table")
                version = connection.execute(
                    sql.SQL("SELECT version_num FROM {}.alembic_version").format(
                        sql.Identifier(schema)
                    )
                ).fetchall()
                require(
                    version
                    == [(
                        {"auth": "0002_auth_users", "project": "0002_project_projects"}[schema]
                        if schema in ("auth", "project") and persistence_tables
                        else f"0001_{schema}_baseline",
                    )],
                    f"{schema} has unexpected migration version(s): {version!r}",
                )
            elif exists is not None:
                versions = connection.execute(
                    sql.SQL("SELECT version_num FROM {}.alembic_version").format(
                        sql.Identifier(schema)
                    )
                ).fetchall()
                require(not versions, f"{schema} retained a version during downgrade")


def assert_only_baseline_tables(admin_url: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        for _, schema, _ in SERVICES:
            tables = connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
                (schema,),
            ).fetchall()
            require(
                tables == [("alembic_version",)],
                f"{schema} has unexpected pre-test tables: {tables!r}",
            )


def assert_role_configuration(admin_url: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        for _, schema, _ in SERVICES:
            rows = connection.execute(
                "SELECT rolname, rolcanlogin, rolinherit FROM pg_roles "
                "WHERE rolname = ANY(%s) ORDER BY rolname",
                (
                    [
                        role_name(schema, "owner"),
                        role_name(schema, "migrator"),
                        role_name(schema, "runtime"),
                    ],
                ),
            ).fetchall()
            require(
                rows
                == [
                    (role_name(schema, "migrator"), True, False),
                    (role_name(schema, "owner"), False, True),
                    (role_name(schema, "runtime"), True, False),
                ],
                f"{schema} has unexpected owner/migrator/runtime roles: {rows!r}",
            )
            owner = connection.execute(
                "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = %s",
                (schema,),
            ).fetchone()
            require(owner == (role_name(schema, "owner"),), f"{schema} has wrong owner")


def create_permission_fixtures(admin_url: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        for _, schema, _ in SERVICES:
            owner = role_name(schema, "owner")
            connection.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(owner)))
            connection.execute(
                sql.SQL("CREATE TABLE {}.permission_probe (value text)").format(
                    sql.Identifier(schema)
                )
            )
            connection.execute(
                sql.SQL("INSERT INTO {}.permission_probe VALUES (%s)").format(
                    sql.Identifier(schema)
                ),
                (schema,),
            )
            connection.execute("RESET ROLE")

        for _, source_schema, _ in SERVICES:
            runtime = role_name(source_schema, "runtime")
            connection.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE ON {}.permission_probe TO {}"
                ).format(
                    sql.Identifier(source_schema),
                    sql.Identifier(runtime),
                )
            )
            for _, target_schema, _ in SERVICES:
                if target_schema == source_schema:
                    continue
                connection.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(target_schema),
                        sql.Identifier(runtime),
                    )
                )
                connection.execute(
                    sql.SQL("GRANT SELECT ON {}.permission_probe TO {}").format(
                        sql.Identifier(target_schema),
                        sql.Identifier(runtime),
                    )
                )


def verify_owner_boundaries(admin_url: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        for _, schema, _ in SERVICES:
            connection.execute(
                sql.SQL("SET ROLE {}").format(sql.Identifier(role_name(schema, "owner")))
            )
            for _, other_schema, _ in SERVICES:
                if other_schema == schema:
                    continue
                require_denied(
                    connection,
                    sql.SQL("INSERT INTO {}.permission_probe VALUES ('denied')").format(
                        sql.Identifier(other_schema)
                    ),
                    f"{schema} owner writing {other_schema}",
                )
            connection.execute("RESET ROLE")


def verify_login_boundaries(
    admin_url: str,
    passwords: dict[tuple[str, str], str],
) -> None:
    for _, schema, _ in SERVICES:
        migrator = role_name(schema, "migrator")
        with psycopg.connect(
            admin_url,
            user=migrator,
            password=passwords[(schema, "migrator")],
            autocommit=True,
        ) as connection:
            require(
                connection.execute(
                    "SELECT session_user, current_user"
                ).fetchone()
                == (migrator, migrator),
                f"{schema} migration ran without its separate login",
            )
            for _, other_schema, _ in SERVICES:
                if other_schema == schema:
                    continue
                require_denied(
                    connection,
                    sql.SQL("INSERT INTO {}.permission_probe VALUES ('denied')").format(
                        sql.Identifier(other_schema)
                    ),
                    f"{schema} migrator writing {other_schema}",
                )

        runtime = role_name(schema, "runtime")
        runtime_password = passwords[(schema, "runtime")]
        with psycopg.connect(
            admin_url,
            user=runtime,
            password=runtime_password,
            autocommit=True,
        ) as connection:
            require(
                connection.execute(
                    "SELECT session_user, current_user"
                ).fetchone()
                == (runtime, runtime),
                f"{schema} runtime did not use its separate login",
            )
            require(
                connection.execute(
                    "SELECT has_schema_privilege(current_user, %s, 'USAGE'), "
                    "has_schema_privilege(current_user, %s, 'CREATE')",
                    (schema, schema),
                ).fetchone()
                == (True, False),
                f"{schema} runtime schema privileges are incorrect",
            )
            own_table = sql.SQL("{}.permission_probe").format(sql.Identifier(schema))
            connection.execute(
                sql.SQL("INSERT INTO {} VALUES ('runtime')").format(own_table)
            )
            connection.execute(
                sql.SQL("UPDATE {} SET value = 'updated' WHERE value = 'runtime'").format(
                    own_table
                )
            )
            require(
                connection.execute(
                    sql.SQL("SELECT value FROM {} WHERE value = 'updated'").format(
                        own_table
                    )
                ).fetchone()
                == ("updated",),
                f"{schema} runtime could not use its explicitly granted table",
            )
            connection.execute(
                sql.SQL("DELETE FROM {} WHERE value = 'updated'").format(own_table)
            )

            for _, other_schema, _ in SERVICES:
                if other_schema == schema:
                    continue
                foreign_table = sql.SQL("{}.permission_probe").format(
                    sql.Identifier(other_schema)
                )
                require(
                    connection.execute(
                        sql.SQL("SELECT value FROM {}").format(foreign_table)
                    ).fetchone()
                    == (other_schema,),
                    f"{schema} runtime could not read its test-only foreign grant",
                )
                for operation in (
                    sql.SQL("INSERT INTO {} VALUES ('denied')").format(foreign_table),
                    sql.SQL("UPDATE {} SET value = 'denied'").format(foreign_table),
                    sql.SQL("DELETE FROM {}").format(foreign_table),
                ):
                    require_denied(
                        connection,
                        operation,
                        f"{schema} runtime writing {other_schema}",
                    )

            require_denied(
                connection,
                sql.SQL("CREATE TABLE {}.runtime_ddl_probe (value text)").format(
                    sql.Identifier(schema)
                ),
                f"{schema} runtime creating in its schema",
            )
            require_denied(
                connection,
                sql.SQL("ALTER TABLE {} ADD COLUMN forbidden text").format(own_table),
                f"{schema} runtime altering its table",
            )
            require_denied(
                connection,
                sql.SQL("ALTER SCHEMA {} RENAME TO p02_forbidden_schema").format(
                    sql.Identifier(schema)
                ),
                f"{schema} runtime altering its schema",
            )
            require_denied(
                connection,
                sql.SQL("SELECT version_num FROM {}.alembic_version").format(
                    sql.Identifier(schema)
                ),
                f"{schema} runtime reading migration metadata",
            )


def verify_independent_rollback(
    admin_url: str, urls: dict[str, str]
) -> None:
    for service_name, schema, _ in SERVICES:
        if schema not in NEW_SERVICES:
            continue
        service_dir = ROOT / "services" / service_name
        run_migration(service_dir, urls[schema], "downgrade", "base")
        assert_baseline_versions(
            admin_url, {s for _, s, _ in SERVICES} - {schema}, persistence_tables=True
        )
        run_migration(service_dir, urls[schema], "upgrade", "head")
        assert_baseline_versions(
            admin_url, {s for _, s, _ in SERVICES}, persistence_tables=True
        )
        print(f"PASS {schema}: independent downgrade and reapply")


def main() -> None:
    admin_url = os.environ.get("P02_TEST_ADMIN_DATABASE_URL")
    require(
        bool(admin_url),
        "Set P02_TEST_ADMIN_DATABASE_URL to a fresh, disposable local PostgreSQL database.",
    )
    admin_url_parts = make_url(admin_url)
    require(
        bool(admin_url_parts.host and admin_url_parts.database),
        "P02_TEST_ADMIN_DATABASE_URL must use a TCP host and name a database.",
    )
    passwords = {
        (schema, purpose): secrets.token_urlsafe(32)
        for _, schema, _ in SERVICES
        for purpose in ("migrator", "runtime")
    }

    bootstrap_services(admin_url, passwords)
    migration_urls = {}
    for service_name, schema, _ in SERVICES:
        url = migration_url(
            admin_url_parts,
            role_name(schema, "migrator"),
            passwords[(schema, "migrator")],
        )
        migration_urls[schema] = url
        run_migration(
            ROOT / "services" / service_name, url, "upgrade", f"0001_{schema}_baseline"
        )
        print(f"PASS {schema}: empty-database baseline upgrade")

    schemas = {schema for _, schema, _ in SERVICES}
    assert_baseline_versions(admin_url, schemas)
    assert_only_baseline_tables(admin_url)
    for service_name, schema in (("auth-service", "auth"), ("project-service", "project")):
        run_migration(ROOT / "services" / service_name, migration_urls[schema], "upgrade", "head")
    assert_baseline_versions(admin_url, schemas, persistence_tables=True)
    assert_role_configuration(admin_url)
    create_permission_fixtures(admin_url)
    verify_owner_boundaries(admin_url)
    verify_login_boundaries(admin_url, passwords)
    verify_independent_rollback(admin_url, migration_urls)
    print("PASS all nine service schemas, role boundaries, and migration checks")


if __name__ == "__main__":
    main()
