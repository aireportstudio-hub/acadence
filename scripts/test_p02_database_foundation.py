"""Verify all service-owned PostgreSQL baselines against one fresh local database.

Set P02_TEST_ADMIN_DATABASE_URL to a disposable database URL, then run:
    python scripts/test_p02_database_foundation.py
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

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
PERSISTENCE_REVISIONS = {
    "auth": "0004_auth_sessions",
    "project": "0003_project_events",
    "orchestration": "0002_orch_persistence",
    "document": "0002_doc_metadata",
}


def role_name(schema: str, purpose: str) -> str:
    return f"acadence_{schema}_{purpose}"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


class LocalDeliveryInterrupted(RuntimeError):
    pass


class LocalTestTransport:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self.interrupt_after_first_accept = True

    def send(self, event: dict[str, Any]) -> None:
        self.messages.append(event)
        if self.interrupt_after_first_accept:
            self.interrupt_after_first_accept = False
            raise LocalDeliveryInterrupted("simulated dispatcher interruption")


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


def runtime_url(admin_url: URL, username: str, password: str) -> str:
    runtime_endpoint = make_url(
        os.environ.get("P02_TEST_RUNTIME_DATABASE_URL")
        or admin_url.render_as_string(hide_password=False)
    )
    return URL.create(
        "postgresql",
        username=username,
        password=password,
        host=runtime_endpoint.host,
        port=runtime_endpoint.port,
        database=runtime_endpoint.database,
        query=dict(runtime_endpoint.query),
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
                expected_revision = (
                    PERSISTENCE_REVISIONS.get(schema, f"0001_{schema}_baseline")
                    if persistence_tables
                    else f"0001_{schema}_baseline"
                )
                require(
                    version == [(expected_revision,)],
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
        runtime_connection_url = runtime_url(
            make_url(admin_url), runtime, runtime_password
        )
        with psycopg.connect(runtime_connection_url, autocommit=True) as connection:
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


def verify_persistence_fixtures(
    admin_url: str,
    passwords: dict[tuple[str, str], str],
) -> None:
    admin_url_parts = make_url(admin_url)
    project_runtime = runtime_url(
        admin_url_parts,
        role_name("project", "runtime"),
        passwords[("project", "runtime")],
    )
    auth_runtime = runtime_url(
        admin_url_parts,
        role_name("auth", "runtime"),
        passwords[("auth", "runtime")],
    )
    orchestration_runtime = runtime_url(
        admin_url_parts,
        role_name("orchestration", "runtime"),
        passwords[("orchestration", "runtime")],
    )
    document_runtime = runtime_url(
        admin_url_parts,
        role_name("document", "runtime"),
        passwords[("document", "runtime")],
    )

    project_id = uuid4()
    fact_id = uuid4()
    event_id = uuid4()
    owner_id = uuid4()
    with psycopg.connect(auth_runtime, autocommit=True) as connection:
        connection.execute("INSERT INTO auth.users (id) VALUES (%s)", (owner_id,))
    with psycopg.connect(project_runtime, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO project.projects (id, owner_user_id, title) "
            "VALUES (%s, %s, 'Synthetic P02 cleanup project')",
            (project_id, owner_id),
        )
    event_payload = {
        "event_id": str(event_id),
        "event_type": "project.facts.updated",
        "event_version": 1,
        "aggregate_id": str(project_id),
        "aggregate_version": 7,
        "occurred_at": "2026-11-14T12:00:00+00:00",
        "data": {
            "fact_snapshot_version": 7,
            "changed_fact_ids": [str(fact_id)],
        },
    }
    with psycopg.connect(project_runtime, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO project.outbox_events "
            "(event_id, aggregate_id, aggregate_version, event_type, event_version, payload) "
            "VALUES (%s, %s, 7, 'project.facts.updated', 1, %s)",
            (event_id, project_id, psycopg.types.json.Jsonb(event_payload)),
        )
        connection.execute(
            "INSERT INTO project.audit_events "
            "(id, actor_id, service_identity, project_id, object_type, object_id, "
            "action, result) "
            "VALUES (%s, %s, 'project', %s, 'outbox_event', %s, 'enqueued', 'success')",
            (uuid4(), owner_id, project_id, str(event_id)),
        )
        require(
            connection.execute(
                "SELECT payload ->> 'event_type', payload -> 'data' ->> "
                "'fact_snapshot_version' FROM project.outbox_events WHERE event_id = %s",
                (event_id,),
            ).fetchone()
            == ("project.facts.updated", "7"),
            "Project runtime could not read its persisted event contract payload",
        )
        require_denied(
            connection,
            sql.SQL(
                "UPDATE project.outbox_events SET payload = payload WHERE event_id = {}"
            ).format(sql.Literal(str(event_id))),
            "Project runtime changing immutable outbox payload",
        )
        require(
            connection.execute("SELECT count(*) FROM project.audit_events").fetchone()
            == (1,),
            "Project audit fixture was not readable",
        )

    job_id = uuid4()
    report_id = f"opaque-report-{uuid4()}"
    section_id = uuid4()
    section_version_id = uuid4()
    orchestration_audit_id = uuid4()
    with psycopg.connect(orchestration_runtime, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO orchestration.report_jobs "
            "(id, report_id, project_id, owner_id, status, graph_thread_id) "
            "VALUES (%s, %s, %s, %s, 'queued', %s)",
            (job_id, report_id, project_id, owner_id, f"thread-{job_id}"),
        )
        connection.execute(
            "INSERT INTO orchestration.job_attempts "
            "(id, job_id, attempt_number, status) VALUES (%s, %s, 1, 'running')",
            (uuid4(), job_id),
        )
        connection.execute(
            "INSERT INTO orchestration.section_versions "
            "(id, job_id, section_id, version_number, status, content, output_sha256) "
            "VALUES (%s, %s, %s, 1, 'draft', '{}'::jsonb, %s)",
            (section_version_id, job_id, section_id, "a" * 64),
        )
        connection.execute(
            "INSERT INTO orchestration.input_version_refs "
            "(id, job_id, scope, source_service, resource_type, resource_id, version) "
            "VALUES (%s, %s, 'job', 'project', 'fact_snapshot', %s, '7')",
            (uuid4(), job_id, str(project_id)),
        )
        connection.execute(
            "INSERT INTO orchestration.input_version_refs "
            "(id, job_id, section_version_id, scope, source_service, resource_type, "
            "resource_id, version) "
            "VALUES (%s, %s, %s, 'section', 'quality', 'verdict', 'opaque-verdict', '3')",
            (uuid4(), job_id, section_version_id),
        )
        connection.execute(
            "INSERT INTO orchestration.progress_events "
            "(job_id, project_id, event_type, event_version, stage, safe_message) "
            "VALUES (%s, %s, 'job.queued', 1, 'queued', 'Queued'), "
            "(%s, %s, 'job.started', 1, 'starting', 'Started')",
            (job_id, project_id, job_id, project_id),
        )
        connection.execute(
            "INSERT INTO orchestration.checkpoint_references "
            "(id, job_id, thread_id, checkpoint_namespace, checkpoint_id) "
            "VALUES (%s, %s, %s, '', 'checkpoint-fixture')",
            (uuid4(), job_id, f"thread-{job_id}"),
        )
        connection.execute(
            "INSERT INTO orchestration.audit_events "
            "(id, actor_id, service_identity, project_id, object_type, object_id, "
            "action, result) "
            "VALUES (%s, %s, 'orchestration', %s, 'report_job', %s, 'created', 'success')",
            (orchestration_audit_id, owner_id, project_id, str(job_id)),
        )
        require_denied(
            connection,
            sql.SQL(
                "UPDATE orchestration.report_jobs SET report_id = report_id WHERE id = {}"
            ).format(sql.Literal(str(job_id))),
            "Orchestration runtime changing opaque report reference",
        )
        require_denied(
            connection,
            sql.SQL(
                "UPDATE orchestration.audit_events SET action = action WHERE object_id = {}"
            ).format(sql.Literal(str(job_id))),
            "Orchestration runtime changing audit history",
        )

        require(
            connection.execute(
                "SELECT report_id, project_id FROM orchestration.report_jobs WHERE id = %s",
                (job_id,),
            ).fetchone()
            == (report_id, project_id),
            "Orchestration runtime could not read its persisted report job",
        )
        require(
            connection.execute(
                "SELECT count(*) FROM orchestration.input_version_refs WHERE job_id = %s",
                (job_id,),
            ).fetchone()
            == (2,),
            "Orchestration did not retain the job and section input versions",
        )
        progress = connection.execute(
            "SELECT event_id FROM orchestration.progress_events "
            "WHERE job_id = %s ORDER BY event_id",
            (job_id,),
        ).fetchall()
        require(
            len(progress) == 2 and progress[0][0] < progress[1][0],
            "Orchestration progress events are not ordered by their durable cursor",
        )
        for table in (
            "job_attempts",
            "section_versions",
            "checkpoint_references",
            "audit_events",
        ):
            require(
                connection.execute(
                    sql.SQL("SELECT count(*) FROM orchestration.{}").format(
                        sql.Identifier(table)
                    )
                ).fetchone()
                == (1,),
                f"Orchestration fixture was not readable from {table}",
            )

    document_id = uuid4()
    document_version_id = uuid4()
    document_access_id = uuid4()
    document_audit_id = uuid4()
    with psycopg.connect(document_runtime, autocommit=True) as connection:
        connection.execute(
            "INSERT INTO document.document_objects "
            "(id, owner_id, project_id, report_id, document_type) "
            "VALUES (%s, %s, %s, %s, 'report_export')",
            (document_id, owner_id, project_id, report_id),
        )
        connection.execute(
            "INSERT INTO document.document_versions "
            "(id, document_object_id, version_number, r2_bucket, r2_object_key, "
            "checksum_sha256, size_bytes, media_type) "
            "VALUES (%s, %s, 1, 'private-documents', %s, %s, 1024, 'application/pdf')",
            (document_version_id, document_id, f"reports/{report_id}/v1/report.pdf", "b" * 64),
        )
        connection.execute(
            "INSERT INTO document.document_access_history "
            "(id, document_version_id, actor_id, access_action, result, request_id) "
            "VALUES (%s, %s, %s, 'preview', 'success', 'req_fixture')",
            (document_access_id, document_version_id, owner_id),
        )
        connection.execute(
            "INSERT INTO document.audit_events "
            "(id, actor_id, service_identity, project_id, object_type, object_id, "
            "action, result) "
            "VALUES (%s, %s, 'document', %s, 'document_version', %s, "
            "'metadata_created', 'success')",
            (document_audit_id, owner_id, project_id, str(document_version_id)),
        )
        require(
            connection.execute(
                "SELECT r2_object_key, checksum_sha256, size_bytes "
                "FROM document.document_versions WHERE id = %s",
                (document_version_id,),
            ).fetchone()
            == (f"reports/{report_id}/v1/report.pdf", "b" * 64, 1024),
            "Document runtime could not read its private R2 metadata fixture",
        )
        require_denied(
            connection,
            sql.SQL(
                "UPDATE document.document_versions SET checksum_sha256 = checksum_sha256 "
                "WHERE id = {}"
            ).format(sql.Literal(str(document_version_id))),
            "Document runtime changing immutable version metadata",
        )
        for table in ("document_objects", "document_access_history", "audit_events"):
            require(
                connection.execute(
                    sql.SQL("SELECT count(*) FROM document.{}").format(
                        sql.Identifier(table)
                    )
                ).fetchone()
                == (1,),
                f"Document fixture was not readable from {table}",
            )

    verify_local_event_delivery(
        admin_url,
        project_runtime,
        orchestration_runtime,
        event_id,
    )

    for source, target in (
        ("project", "orchestration"),
        ("orchestration", "project"),
        ("orchestration", "document"),
        ("document", "orchestration"),
        ("project", "document"),
        ("document", "project"),
    ):
        connection_url = {
            "project": project_runtime,
            "orchestration": orchestration_runtime,
            "document": document_runtime,
        }[source]
        with psycopg.connect(connection_url, autocommit=True) as connection:
            require_denied(
                connection,
                sql.SQL(
                    "INSERT INTO {}.audit_events "
                    "(id, service_identity, object_type, object_id, action, result) "
                    "VALUES ({}, {}, 'boundary_probe', 'denied', 'write', 'denied')"
                ).format(
                    sql.Identifier(target),
                    sql.Literal(str(uuid4())),
                    sql.Literal(source),
                ),
                f"{source} runtime writing {target}.audit_events",
            )

    verify_proposed_deletion(
        admin_url,
        owner_id,
        project_id,
        event_id,
        job_id,
        document_id,
        document_version_id,
        document_access_id,
        document_audit_id,
        orchestration_audit_id,
    )

    print(
        "PASS P02 report-job, document metadata, audit/outbox/inbox fixtures, "
        "local event retry/deduplication, proposed deletion cleanup, and "
        "cross-schema write denial"
    )


def verify_local_event_delivery(
    admin_url: str,
    project_runtime: str,
    orchestration_runtime: str,
    event_id: UUID,
) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("SET ROLE acadence_orchestration_owner")
        connection.execute(
            "CREATE TABLE orchestration.p02_delivery_effect_probe ("
            "event_id uuid PRIMARY KEY, fact_snapshot_version integer NOT NULL)"
        )
        connection.execute("RESET ROLE")
        connection.execute(
            "GRANT SELECT, INSERT ON orchestration.p02_delivery_effect_probe "
            "TO acadence_orchestration_runtime"
        )

    transport = LocalTestTransport()
    with psycopg.connect(project_runtime, autocommit=True) as connection:
        event = connection.execute(
            "SELECT payload FROM project.outbox_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()[0]

    try:
        transport.send(event)
    except LocalDeliveryInterrupted:
        with psycopg.connect(project_runtime, autocommit=True) as connection:
            connection.execute(
                "UPDATE project.outbox_events SET attempt_count = attempt_count + 1, "
                "next_attempt_at = now() + interval '1 second' "
                "WHERE event_id = %s AND published_at IS NULL",
                (event_id,),
            )
    else:
        raise RuntimeError("The local transport interruption was not simulated")

    with psycopg.connect(project_runtime, autocommit=True) as connection:
        require(
            connection.execute(
                "SELECT attempt_count, published_at IS NULL, next_attempt_at IS NOT NULL "
                "FROM project.outbox_events WHERE event_id = %s",
                (event_id,),
            ).fetchone()
            == (1, True, True),
            "Interrupted outbox delivery was not left pending for retry",
        )
        connection.execute(
            "UPDATE project.outbox_events SET next_attempt_at = now() - interval '1 second' "
            "WHERE event_id = %s",
            (event_id,),
        )
        due_event = connection.execute(
            "SELECT payload FROM project.outbox_events "
            "WHERE event_id = %s AND published_at IS NULL AND next_attempt_at <= now()",
            (event_id,),
        ).fetchone()
        require(due_event is not None, "Interrupted outbox event was not retryable")
        transport.send(due_event[0])
        connection.execute(
            "UPDATE project.outbox_events SET attempt_count = attempt_count + 1, "
            "published_at = now(), next_attempt_at = NULL WHERE event_id = %s",
            (event_id,),
        )

    committed_effects = 0
    for delivery in transport.messages:
        with psycopg.connect(orchestration_runtime) as connection:
            inserted = connection.execute(
                "INSERT INTO orchestration.inbox_deduplication "
                "(producer_service, event_id, event_type, event_version, processing_status) "
                "VALUES ('project', %s, 'project.facts.updated', 1, 'received') "
                "ON CONFLICT (producer_service, event_id) DO NOTHING "
                "RETURNING event_id",
                (delivery["event_id"],),
            ).fetchone()
            if inserted is None:
                continue
            connection.execute(
                "INSERT INTO orchestration.p02_delivery_effect_probe "
                "(event_id, fact_snapshot_version) VALUES (%s, %s)",
                (
                    delivery["event_id"],
                    delivery["data"]["fact_snapshot_version"],
                ),
            )
            connection.execute(
                "UPDATE orchestration.inbox_deduplication SET "
                "processing_status = 'processed', processed_at = now() "
                "WHERE producer_service = 'project' AND event_id = %s",
                (delivery["event_id"],),
            )
            committed_effects += 1

    require(len(transport.messages) == 2, "Interrupted publish was not retried")
    require(committed_effects == 1, "Duplicate delivery committed more than one effect")
    with psycopg.connect(orchestration_runtime, autocommit=True) as connection:
        require(
            connection.execute(
                "SELECT count(*) FROM orchestration.inbox_deduplication "
                "WHERE producer_service = 'project' AND event_id = %s "
                "AND processing_status = 'processed'",
                (event_id,),
            ).fetchone()
            == (1,),
            "The duplicate event did not produce one processed inbox row",
        )
        require(
            connection.execute(
                "SELECT count(*) FROM orchestration.p02_delivery_effect_probe "
                "WHERE event_id = %s",
                (event_id,),
            ).fetchone()
            == (1,),
            "The duplicate event did not produce exactly one committed effect",
        )
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("SET ROLE acadence_orchestration_owner")
        connection.execute("DROP TABLE orchestration.p02_delivery_effect_probe")
        connection.execute("RESET ROLE")

    print("PASS local outbox interruption retry and transactional inbox deduplication")


def verify_proposed_deletion(
    admin_url: str,
    owner_id: UUID,
    project_id: UUID,
    event_id: UUID,
    job_id: UUID,
    document_id: UUID,
    document_version_id: UUID,
    document_access_id: UUID,
    document_audit_id: UUID,
    orchestration_audit_id: UUID,
) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("SET ROLE acadence_project_owner")
        connection.execute(
            "DELETE FROM project.outbox_events WHERE event_id = %s AND published_at IS NOT NULL",
            (event_id,),
        )
        connection.execute(
            "UPDATE project.audit_events SET actor_id = NULL, project_id = NULL, "
            "object_id = 'redacted', action = 'deletion_completed', metadata = '{}'::jsonb "
            "WHERE object_id = %s",
            (str(event_id),),
        )
        connection.execute("DELETE FROM project.projects WHERE id = %s", (project_id,))
        connection.execute("RESET ROLE")

        connection.execute("SET ROLE acadence_orchestration_owner")
        connection.execute(
            "DELETE FROM orchestration.inbox_deduplication "
            "WHERE producer_service = 'project' AND event_id = %s",
            (event_id,),
        )
        connection.execute(
            "UPDATE orchestration.audit_events SET actor_id = NULL, project_id = NULL, "
            "object_id = 'redacted', action = 'deletion_completed' WHERE id = %s",
            (orchestration_audit_id,),
        )
        connection.execute("DELETE FROM orchestration.report_jobs WHERE id = %s", (job_id,))
        connection.execute("RESET ROLE")

        connection.execute("SET ROLE acadence_document_owner")
        try:
            connection.execute(
                "DELETE FROM document.document_versions WHERE id = %s",
                (document_version_id,),
            )
        except psycopg.errors.ForeignKeyViolation:
            pass
        else:
            raise RuntimeError(
                "Document version cleanup ignored its access-history reference"
            )
        connection.execute(
            "DELETE FROM document.document_access_history WHERE id = %s",
            (document_access_id,),
        )
        connection.execute(
            "DELETE FROM document.document_versions WHERE id = %s",
            (document_version_id,),
        )
        connection.execute(
            "UPDATE document.audit_events SET actor_id = NULL, project_id = NULL, "
            "object_id = 'redacted', action = 'deletion_completed' WHERE id = %s",
            (document_audit_id,),
        )
        connection.execute(
            "DELETE FROM document.document_objects WHERE id = %s",
            (document_id,),
        )
        connection.execute("RESET ROLE")

        connection.execute("SET ROLE acadence_auth_owner")
        connection.execute("DELETE FROM auth.users WHERE id = %s", (owner_id,))
        connection.execute("RESET ROLE")

        for query, params, label in (
            ("SELECT count(*) FROM project.projects WHERE id = %s", (project_id,), "project"),
            (
                "SELECT count(*) FROM project.outbox_events WHERE event_id = %s",
                (event_id,),
                "outbox event",
            ),
            (
                "SELECT count(*) FROM orchestration.report_jobs WHERE id = %s",
                (job_id,),
                "report job",
            ),
            (
                "SELECT count(*) FROM orchestration.job_attempts WHERE job_id = %s",
                (job_id,),
                "job attempts",
            ),
            (
                "SELECT count(*) FROM orchestration.section_versions WHERE job_id = %s",
                (job_id,),
                "section versions",
            ),
            (
                "SELECT count(*) FROM orchestration.input_version_refs WHERE job_id = %s",
                (job_id,),
                "input version references",
            ),
            (
                "SELECT count(*) FROM orchestration.progress_events WHERE job_id = %s",
                (job_id,),
                "progress events",
            ),
            (
                "SELECT count(*) FROM orchestration.checkpoint_references WHERE job_id = %s",
                (job_id,),
                "checkpoint references",
            ),
            (
                "SELECT count(*) FROM orchestration.inbox_deduplication "
                "WHERE producer_service = 'project' AND event_id = %s",
                (event_id,),
                "inbox event",
            ),
            (
                "SELECT count(*) FROM document.document_versions "
                "WHERE id = %s OR document_object_id = %s",
                (document_version_id, document_id),
                "document versions",
            ),
            (
                "SELECT count(*) FROM document.document_access_history "
                "WHERE id = %s",
                (document_access_id,),
                "document access history",
            ),
            (
                "SELECT count(*) FROM document.document_objects WHERE id = %s",
                (document_id,),
                "document metadata",
            ),
            ("SELECT count(*) FROM auth.users WHERE id = %s", (owner_id,), "Auth user"),
        ):
            require(
                connection.execute(query, params).fetchone() == (0,),
                f"Proposed cleanup left synthetic {label} rows behind",
            )

        for schema, table, audit_id in (
            ("project", "audit_events", None),
            ("orchestration", "audit_events", orchestration_audit_id),
            ("document", "audit_events", document_audit_id),
        ):
            if schema == "project":
                row = connection.execute(
                    "SELECT actor_id, project_id, object_id, action FROM project.audit_events "
                    "WHERE action = 'deletion_completed'"
                ).fetchone()
            else:
                row = connection.execute(
                    sql.SQL(
                        "SELECT actor_id, project_id, object_id, action FROM {}.audit_events "
                        "WHERE id = %s"
                    ).format(sql.Identifier(schema)),
                    (audit_id,),
                ).fetchone()
            require(
                row == (None, None, "redacted", "deletion_completed"),
                f"{schema}.{table} did not retain only the synthetic deletion audit",
            )

    print("PASS proposed synthetic account/project cleanup and minimal audit retention")


def verify_independent_rollback(
    admin_url: str, urls: dict[str, str]
) -> None:
    for service_name, schema, _ in SERVICES:
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
    for service_name, schema, _ in SERVICES:
        run_migration(ROOT / "services" / service_name, migration_urls[schema], "upgrade", "head")
    assert_baseline_versions(admin_url, schemas, persistence_tables=True)
    assert_role_configuration(admin_url)
    create_permission_fixtures(admin_url)
    verify_owner_boundaries(admin_url)
    verify_login_boundaries(admin_url, passwords)
    verify_persistence_fixtures(admin_url, passwords)
    verify_independent_rollback(admin_url, migration_urls)
    print("PASS all nine service schemas, role boundaries, and migration checks")


if __name__ == "__main__":
    main()
