# Auth Service database

Auth owns the `auth` PostgreSQL schema. Provision `database/bootstrap.sql` once
per local PostgreSQL database using an administrator connection. It creates a
non-login schema owner, a separate non-inheriting Alembic login, and a distinct
runtime login. The migration role can assume only the Auth schema owner; the
runtime role has schema `USAGE` only and cannot create objects. Future table
migrations must grant the runtime role only the table/sequence operations that
the Auth API needs. Revision `0002_auth_users` creates `auth.users` with an
Auth-issued UUIDv4 and a creation timestamp, and grants runtime only `SELECT`
and `INSERT`. Revision `0003_google_identity_bindings` adds provider/subject
bindings with database uniqueness constraints and the same narrow runtime
permissions.

The internal `users.py` functions take a runtime psycopg connection.
`create_user` inserts a user and `get_user` reads by ID.
`get_or_create_google_user` uses a transaction-scoped PostgreSQL advisory lock
and the unique `(provider, subject)` key so concurrent first sign-ins return
one Auth UUIDv4 user. It never uses an email address to associate users.

Set passwords for both login roles through the PostgreSQL administrator's
interactive `\password` command or an approved secret manager. Keep both
connection URLs out of Git. `MIGRATION_DATABASE_URL` is used only by Alembic;
the Auth API will use `DATABASE_URL` with the runtime role.

## P03 Task 2: Google sign-in

The server-side OAuth authorization-code flow is exposed by
`GET /v1/auth/google/start` and `GET /v1/auth/google/callback`. Start creates
per-flow HTTP-only, short-lived state, nonce, and PKCE verifier cookies and
returns a Google authorization URL using PKCE S256. The callback validates
state, exchanges the code with the verifier, validates the Google ID token
signature/issuer/audience/expiry with `google-auth`, compares the nonce, and
binds only the verified `sub` claim. It issues an Auth-owned browser session
in an HTTP-only cookie; only the SHA-256 token hash is persisted. Browser
callbacks redirect to the configured frontend dashboard, while non-browser
callbacks retain the minimal `{user_id, created}` JSON response.

Use the existing Auth environment names:

```text
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8001/v1/auth/google/callback
OIDC_ISSUER=https://accounts.google.com
DATABASE_URL=<Auth runtime-role connection URL>
FRONTEND_APP_URL=http://localhost:3001
```

`GOOGLE_OAUTH_REDIRECT_URI` must match the Google OAuth web-client redirect
exactly. HTTP is accepted only for localhost in development; non-development
deployments require HTTPS. `FRONTEND_APP_URL` must be the exact trusted
frontend origin. Set `COOKIE_DOMAIN` only when the frontend and Auth service
use sibling subdomains. Apply `python -m alembic upgrade head` with
`MIGRATION_DATABASE_URL` set before starting the API.

Local tests use synthetic Google subjects and mocked code-exchange/token
verification; they make no Google requests. To repeat the live verification,
create a Google Cloud project, configure the OAuth consent
screen and add the tester account, create a **Web application** OAuth client,
register the exact redirect URI above, apply the Auth migrations to a
disposable PostgreSQL database, and run the Auth service on `localhost:8001`
with the five settings above. Open `/v1/auth/google/start` in a browser and
copy the `authorization_url` from its JSON response into the same browser to
complete Google consent; the callback returns JSON with the resulting `user_id`.
Repeat the flow to verify the same Google subject returns the same ID. Use a
second Google test account to verify it receives a different user ID. Never
use a production database for this check.

**Live Google smoke test passed on 2026-11-15:** first sign-in returned
`created: true`; repeat sign-in returned the same Acadence UUID and
`created: false`. This confirms live subject-to-user reuse; it does not claim
a second-account test.

On Windows, with PostgreSQL 17 in `C:\Program Files\PostgreSQL\17`, the
repository `.venv` dependencies installed, and `GOOGLE_OAUTH_CLIENT_ID` and
`GOOGLE_OAUTH_CLIENT_SECRET` already set in the current terminal, run:

```powershell
.\scripts\start-google-smoke.ps1
```

The script creates a disposable loopback-only cluster, runs the Auth bootstrap
and migrations, and starts Auth on port 8001. Stop Auth with Ctrl+C; the script
stops PostgreSQL and removes the cluster. The live Google smoke test passed
on 2026-11-15 as recorded above.

After provisioning a fresh disposable cluster and database as described below,
run the following in PowerShell from the repository root. Enter the local URLs
and Google settings at the prompts; URL-encode special characters in database
passwords. The migration URL must use the SQLAlchemy
`postgresql+psycopg://` scheme; the runtime URL uses `postgresql://`.
Install `requirements-dev.txt` first if the virtual environment does not have
the Auth runtime and migration dependencies.

```powershell
Set-Location .\services\auth-service
$python = (Resolve-Path ..\..\.venv\Scripts\python.exe).Path
$env:MIGRATION_DATABASE_URL = [System.Net.NetworkCredential]::new('', (Read-Host 'Migration database URL' -AsSecureString)).Password
& $python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Auth migration failed' }
Remove-Item Env:MIGRATION_DATABASE_URL
$env:DATABASE_URL = [System.Net.NetworkCredential]::new('', (Read-Host 'Runtime database URL' -AsSecureString)).Password
$env:GOOGLE_OAUTH_CLIENT_ID = Read-Host 'Google OAuth client ID'
$env:GOOGLE_OAUTH_CLIENT_SECRET = [System.Net.NetworkCredential]::new('', (Read-Host 'Google OAuth client secret' -AsSecureString)).Password
$env:GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8001/v1/auth/google/callback'
$env:OIDC_ISSUER = 'https://accounts.google.com'
$env:APP_ENV = 'development'
& $python -m uvicorn main:app --host 127.0.0.1 --port 8001 --no-access-log
```

In the browser, open `http://localhost:8001/v1/auth/google/start`, then follow
the `authorization_url` in that same browser. After testing, stop the server
with Ctrl+C and clear the local process settings or close the PowerShell window.

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
python -m alembic downgrade 0001_auth_baseline
```

The database must have been provisioned first, and
`MIGRATION_DATABASE_URL` must identify the migration login. The Auth Service
container does not run migrations at startup. Downgrading this revision drops
`auth.users` and its data; use it only when that data can be discarded or restored.

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
schema. It also checks sequential Google-subject reuse and the binding
uniqueness constraint. PGlite's wire adapter uses explicit `SET ROLE` checks
for the two service roles; password authentication is configured separately on
a real local PostgreSQL instance. The PGlite harness skips the two-connection
race test; set the Auth test URLs against a disposable native PostgreSQL
database to run that test. The test does not connect to Google Cloud or use
billing-enabled resources.

For the native test, use a fresh disposable PostgreSQL cluster/database with
the Auth administrator, runtime, and migrator URLs in
`AUTH_TEST_ADMIN_DATABASE_URL`, `AUTH_TEST_RUNTIME_DATABASE_URL`, and
`MIGRATION_DATABASE_URL`. Set `AUTH_TEST_SET_ROLE_PASSWORDS=1` if the bootstrap
must assign the URL passwords to the newly created Auth roles, then run
`python -m unittest test_database_permissions.AuthDatabaseMigrationTest -v`
from this directory. The test creates Auth roles and schemas in that database;
do not point it at a shared or production cluster.

On 2026-11-15, this test passed on a fresh disposable PostgreSQL 17.6 cluster
with SCRAM-authenticated logins. Its two concurrent first sign-ins returned
the same user UUID, one newly created and one reused. An additional database
count confirmed one race binding and associated user, with no extra orphan;
the only unbound user was the test's separate standalone user. The server was
stopped and the cluster files were removed.

## Initial P02 local verification (historical)

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

P02 follow-ups remain: narrowly scoped production grants, remaining product
persistence, Neon credentials and pooling, and backup/restore drills. The
stable UUIDv4 user ID contract and Google subject mapping are documented in the
[P02 database foundation runbook](../../docs/runbooks/P02_DATABASE_FOUNDATION.md).
Live Google-provider verification passed on 15 November 2026. P03 Task 3
implements Google-issued browser sessions and dashboard protection; OTP and
project endpoints remain outside this task.

## P03 Task 3: Google session and protected dashboard

The Google callback creates a random opaque session token and persists only
its SHA-256 hash in `auth.sessions`, linked to the Auth user with an eight-hour
expiry. The `acadence_session` cookie is HTTP-only, SameSite=Lax, scoped to
`/`, and Secure outside development. `GET /v1/auth/session` validates expiry
and revocation centrally. `POST /v1/auth/logout` requires the configured
frontend Origin, revokes the session, and clears the cookie. Browser callbacks
redirect to `/dashboard`; the dashboard validates the session server-side
before rendering. The frontend exposes only a narrow same-origin proxy for
Google start, session lookup, and logout. It does not expose project endpoints;
those remain for P03 Task 4.

For local development, set `AUTH_SERVICE_URL=http://localhost:8001` in
`apps/frontend/.dev.vars`, and set `FRONTEND_APP_URL=http://localhost:3001`
in the Auth environment. Set `COOKIE_DOMAIN` only for an approved shared
parent domain when frontend and Auth are on sibling subdomains. Apply
`python -m alembic upgrade head` before starting Auth.

### Development callback diagnostics and fresh retry

In development only, a rejected Google callback emits a warning containing
only `request_id` and a fixed `reason` label. The public error response and
OAuth checks are unchanged. The labels for HTTP 400 are `invalid_state`,
`state_cookie_missing`, `state_cookie_mismatch`, `authorization_incomplete`,
`nonce_cookie_missing`, and `pkce_cookie_missing`. Labels also distinguish
later token, configuration, and persistence failures. Staging and production
do not emit these diagnostics. Configure the server's logging level to allow
warnings, and disable access logs for the callback at the server and any
intermediaries: access logs can contain the callback query string.

For a single fresh local browser retry:

1. Keep the frontend running on `localhost:3001`. In the terminal running the
   Auth smoke script, stop it with Ctrl+C, then restart it from the repository
   root with `.\scripts\start-google-smoke.ps1`. The script uses
   `--no-access-log`; it destroys and recreates its disposable database, so
   existing smoke-test users and sessions do not persist. Ensure the Google
   client settings are already available in that terminal without printing
   them. If using another Auth startup method, restart it with `APP_ENV` set to
   `development` and Uvicorn's `--no-access-log` option.
2. In the same browser, open `http://localhost:3001/sign-in`, select
   **Continue with Google**, and complete Google sign-in once. Do not refresh
   or reuse a previous callback: the transaction cookies are short-lived and
   cleared after a callback.
3. If it fails, copy only the response `request_id` and the matching Auth
   terminal warning's fixed `reason` label. Do not share the browser address,
   callback query, cookies, credentials, authorization code, or tokens. A
   successful sign-in redirects to the dashboard and emits no rejection
   diagnostic.

Automated Auth verification on 2026-11-15: 29 tests ran, 28 passed and the
disposable PostgreSQL integration test was skipped because its test URLs were
not configured. The tests cover the diagnostic labels, redaction, environment
gate, and unchanged callback responses. A subsequent live Google sign-in
reached the dashboard, as reported by the user; live refresh, sign-out, and
access after sign-out remain pending.
