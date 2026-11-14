# Project Service

P01 startup validation reads only the process environment. `APP_ENV` defaults
to `development` and accepts `development`, `staging`, or `production`.
`LOG_LEVEL` defaults to `INFO` and accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`,
or `CRITICAL`, case-insensitively. Empty or invalid values stop startup.
Validation does not configure logging, load an env file, or require credentials.

Every HTTP response includes `X-Request-ID`. A single incoming ID is reused if
it contains 1–64 ASCII letters, digits, hyphens, or underscores; otherwise a
new ID is generated. HTTP, validation, and unexpected errors return `code`,
`message`, `request_id`, and `details`, with the same ID in the header and
body. Messages are generic and `details` is currently empty; exception text
and submitted values are not returned. HTTP error headers such as `Allow` and
`WWW-Authenticate` are preserved.

## P01 test evidence

From the repository root, the following passed on 13 November 2026:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\services\project-service -p "test_*.py" -v
.\scripts\test-services.ps1 -Service project-service
```

The unit tests cover configuration validation, health responses, request IDs,
router errors, protocol headers, request validation, and sanitized 500 errors.
The container smoke test builds the image and checks both health endpoints.
This is only the Project Service configuration and error-handling slice of P01,
not the P01 gate. Distributed tracing and rollout to other services remain
future work; Cloudflare-to-Cloud Run ingress remains an open P00/P01 decision.

## P02 database foundation

Project owns the `project` PostgreSQL schema. An administrator provisions
`database/bootstrap.sql` once per database: it creates a non-login schema
owner, a separate non-inheriting Alembic login, and a distinct runtime login.
The migrator can assume the Project owner; runtime has schema `USAGE` but
cannot create objects. Future migrations must explicitly grant only the table
and sequence operations needed by the Project API. The baseline creates no
product tables, fact snapshots, or API changes; Alembic's version table is
kept in `project`.

Set login passwords using the PostgreSQL administrator's interactive
`\password` command or an approved secret manager. Keep connection URLs out
of Git. `MIGRATION_DATABASE_URL` is only for Alembic, using the migrator
login; the future API database connection uses `DATABASE_URL` with the
runtime login. The container does not install migration dependencies or run
migrations at startup.

From `services/project-service`, install `requirements-migrations.txt` for
migrations, or `requirements-dev.txt` for development and tests. Provision a
local database and apply or roll back the baseline:

```powershell
python -m pip install -r requirements-dev.txt
psql --dbname acadence_local -v ON_ERROR_STOP=1 -f .\database\bootstrap.sql
psql --dbname acadence_local
# In psql: \password acadence_project_migrator
# In psql: \password acadence_project_runtime
# Set MIGRATION_DATABASE_URL in the local process environment, then:
python -m alembic upgrade head
python -m alembic downgrade base
```

The database administrator must be able to create roles and schemas. Roles
are cluster-wide in PostgreSQL, so provision them only once in a fresh local
cluster or coordinate their management separately. Never run the disposable
test against an existing application database.

### Local migration and permission checks

From the repository root, using the existing local PGlite tooling:

```powershell
npm ci --prefix .\spikes\tooling
$env:PYTHON = "$PWD\.venv\Scripts\python.exe"
npm run test:project-db --prefix .\spikes\tooling
npm run test:auth-db --prefix .\spikes\tooling
```

The Project check creates a fresh in-memory database, bootstraps and migrates
both services, and checks their separate version tables and Project's
independent downgrade/upgrade. It creates disposable probe tables as the
respective owners, grants Project runtime CRUD on its probe, and grants each
runtime read-only access to the other probe solely to demonstrate that writes
remain denied even when the table is reachable. These grants and tables are
test fixtures, not product migrations. The check also rejects runtime DDL
and cross-service owner writes. No cloud or billing resources are used.

For native PostgreSQL, use a **fresh disposable database and cluster** with
no existing Acadence roles. Set `PROJECT_TEST_ADMIN_DATABASE_URL`,
`PROJECT_TEST_RUNTIME_DATABASE_URL`, `AUTH_TEST_RUNTIME_DATABASE_URL`,
`PROJECT_MIGRATION_DATABASE_URL`, and `AUTH_MIGRATION_DATABASE_URL` to
connections to that database. The administrator must be able to create and
assume the test roles. Since the test creates these roles itself, use a
local-only disposable-cluster authentication configuration that accepts those
new logins without passwords. The migration URLs use the
`postgresql+psycopg://` SQLAlchemy dialect; runtime and administrator URLs use
`postgresql://`. From the repository root run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\services\project-service -p "test_database_permissions.py" -v
```

Test real password authentication separately after provisioning roles and
setting passwords. PGlite's adapter uses explicit `SET ROLE` and does not
establish password authentication or Neon compatibility.

### Evidence and remaining decisions

On 14 November 2026 both service suites passed (10 tests each, with their
database integration test skipped without URLs); the separate Auth and Project
PGlite migration/permission checks passed.

The existing Auth and Project permission tests also passed on disposable
PostgreSQL 16.16 in a localhost-bound Docker container, with temporary
passwords assigned to their test-created roles. Both baselines were applied
using their respective migration logins, and each version table was in its own
schema. Direct password-authenticated runtime logins passed CRUD on their
explicitly granted probe tables and were denied writes to the other service's
existing probe table. Before Project's downgrade an Auth probe row
(`auth-p02-preservation-20261114`) and revision (`0001_auth_baseline`) were
recorded; both were unchanged after downgrade and after reapply. The container
and its anonymous volume were removed. The probe tables and cross-schema
read grants were test fixtures only.

Neon credentials and pooling, and backup/restore drills remain unverified. The
other seven service schemas, Project product tables and explicit production
table grants remain P02 follow-ups; this is not the P02 gate. Provisioning and
secret management for the eventual Neon environment remain open.
