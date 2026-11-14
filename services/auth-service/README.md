# Auth Service database

Auth owns the `auth` PostgreSQL schema. Provision `database/bootstrap.sql` once
per local PostgreSQL database using an administrator connection. It creates a
non-login schema owner, a separate non-inheriting Alembic login, and a distinct
runtime login. The migration role can assume only the Auth schema owner; the
runtime role has schema `USAGE` only and cannot create objects. Future table
migrations must grant the runtime role only the table/sequence operations that
the Auth API needs. No identity tables are introduced by this baseline; Google
OIDC and mobile OTP persistence are deferred to their own implementation step.

Set passwords for both login roles through the PostgreSQL administrator's
interactive `\password` command or an approved secret manager. Keep both
connection URLs out of Git. `MIGRATION_DATABASE_URL` is used only by Alembic;
the Auth API will use `DATABASE_URL` with the runtime role.

Install migration dependencies in the environment used to run Alembic:

```powershell
python -m pip install -r requirements-migrations.txt
```

For development and tests, install `requirements-dev.txt` instead; it includes
both runtime and migration dependencies. The runtime container installs only
`requirements.txt`.

From `services/auth-service`, apply or roll back the current revision with:

```powershell
python -m alembic upgrade head
python -m alembic downgrade base
```

The database must have been provisioned first, and
`MIGRATION_DATABASE_URL` must identify the migration login. The Auth Service
container does not run migrations at startup.

For a disposable native local PostgreSQL database, create a new database, then
run the following from `services/auth-service` as its administrator:

```powershell
psql --dbname acadence_auth_local -v ON_ERROR_STOP=1 -f .\database\bootstrap.sql
psql --dbname acadence_auth_local
```

In the interactive `psql` session, run `\password acadence_auth_migrator` and
`\password acadence_auth_runtime`. Keep each connection URL in local process
configuration; do not pass an administrator URL to the Auth API.

## Local migration and permission test

The disposable-database integration test uses the repository's existing
PGlite setup and its PostgreSQL wire-protocol adapter. From the repository
root, install the tooling dependencies and run:

```powershell
npm ci --prefix .\spikes\tooling
$env:PYTHON = "$PWD\.venv\Scripts\python.exe"
npm run test:auth-db --prefix .\spikes\tooling
```

This creates an empty in-memory database, runs the bootstrap SQL, applies
Alembic through psycopg, and checks Auth runtime CRUD on a specifically granted
table while rejecting DDL and writes through `public` or a separate `project`
schema. PGlite's wire adapter uses explicit `SET ROLE` checks for the two
service roles; password authentication is configured separately on a real
local PostgreSQL instance. The test does not connect to Google Cloud or use
billing-enabled resources.

## Initial local verification

The first migration records the schema's Alembic baseline without guessing
identity fields or enabling authentication providers. The empty-database
migration and permission checks passed against disposable local PGlite on
14 November 2026. The Auth test suite passed (10 tests; its database test is
skipped without integration-test URLs), and the dedicated PGlite migration
test passed (1 test). `git diff --check` and Alembic offline SQL generation
also passed.

On 14 November 2026 the existing Auth and Project database permission tests
also passed against a disposable PostgreSQL 16.16 Docker container bound to
localhost. Temporary passwords were assigned to the test-created logins; both
services migrated using their own logins and retained separate schema-local
version tables. Direct runtime password logins passed own-probe CRUD and were
denied writes to the other service's existing probe. An Auth test row and
revision `0001_auth_baseline` remained unchanged through Project's downgrade
and reapply. The container and its anonymous volume were removed.

P02 follow-ups remain: Auth identity/session tables and narrowly scoped
production grants, migrations for the other seven schemas, Neon credentials
and pooling, and backup/restore drills. No cloud migration, Google sign-in,
or OTP behavior is implemented here.
