# P02 local database foundation

This runbook records the schema, role and Alembic baseline foundation and the
Auth, Project, AI Orchestration, and Document persistence revisions. It does
not mark the full P02 gate complete.

## P02 gate status (2026-11-15)

**Status: BLOCKED — P02 is not complete.** The recorded database and backup
evidence below passes the database exit criteria; the live R2 check and three
explicit approvals remain open.

| Exit criterion or gate | Status | Evidence or blocker |
| --- | --- | --- |
| Nine empty-database baselines and migrations to head | **PASS** | Local and hosted Neon runs passed for all nine services. |
| Independent migration downgrade/reapply | **PASS** | Local and hosted Neon runs passed for all nine services. |
| Service-role isolation and no cross-service writes | **PASS** | Local and hosted Neon role checks passed. |
| No credentials committed in the P02 changes | **PASS** | The reviewed changes contain no live credentials or signed URLs; environment inspection found no R2 credential variables. |
| Backup and restore exercised | **PASS — local logical drill** | The 2026-11-14 PostgreSQL 16 drill restored all nine schemas and checked revisions, synthetic rows, and role boundaries. It does not prove managed Neon PITR or R2 payload recovery. |
| Hosted Neon verification | **PASSED — reuse recorded result** | Full nine-service direct/pooler verification is recorded below as passed on 2026-11-15. It was not rerun for this batch. |
| Private R2 signed upload/download, unsigned denial, expiry, and cleanup | **BLOCKED** | No R2 credentials are configured, no dedicated private test bucket is confirmed, and no product signing endpoint is implemented. Only the offline dummy-credential signature probe exists. |
| Project/account deletion retention | **OPEN — approval required** | No retention periods or production deletion workflow are selected. |
| Canonical report ID issuer and lookup contract | **OPEN — approval required** | Document-issued UUIDv4 is a proposal; no authoritative Document report record/API exists. |
| Production `project.facts.updated` transport | **OPEN — approval required** | Cloud Tasks is the one-target recommendation; no production relay or consumer is implemented. |

### Validation for this status update

`git diff --check` passed. The P02 verifier's Python syntax check passed, and
the added diff was checked for R2 credential assignments, signed URL
signatures, and credentialed PostgreSQL URLs; none were found. No application
code was changed in this status update, so the recorded local PostgreSQL,
service-suite, and hosted Neon results above were reused rather than rerun.
Google Cloud billing remained off.

## Local verification

For local verification, use a fresh, disposable local PostgreSQL database and a
database administrator login. For hosted Neon, follow the separate preflight
below; never use a database with data to retain. The script refuses to run if
any of the nine service schemas or Acadence roles already exist. It creates
random migration/runtime role passwords in memory, then connects through each
role separately.

Supply `P02_TEST_ADMIN_DATABASE_URL` through a secure process environment,
without placing connection strings or passwords in commands or logs. Optionally
supply `P02_TEST_RUNTIME_DATABASE_URL` the same way for the same disposable
database. PostgreSQL 16 or newer is required for per-membership SET and
INHERIT options. The bootstrap login must own the database, have CREATEROLE,
and be able to grant membership in the owner roles it creates.

```powershell
.\.venv\Scripts\python.exe scripts\test_p02_database_foundation.py
Remove-Item Env:\P02_TEST_ADMIN_DATABASE_URL
Remove-Item Env:\P02_TEST_RUNTIME_DATABASE_URL -ErrorAction SilentlyContinue
```

Each bootstrap explicitly grants its owner role to the bootstrap administrator
with SET enabled and inheritance disabled, then assumes that owner for
schema grants. Each migrator can assume only its own service owner; runtime
roles do not receive owner membership. The administrator must be treated as
privileged because it can assume all nine owners.

For the optional runtime endpoint, only its host, port, database, and connection
options are used; the verifier injects each generated runtime role and password.
The branch must therefore accept those generated roles through the pooler.

The test database must be discarded after the run. The script does not create or
remove containers, volumes, or databases. It bootstraps all nine service schemas,
runs each empty baseline, then upgrades every service to head. The Auth,
Project, AI Orchestration, and Document persistence revisions are included.
It verifies that each version table is service-owned.
Temporary `permission_probe` tables and cross-schema `USAGE`/`SELECT` grants
exist only in this disposable database. The test checks runtime CRUD on its
explicitly granted table, denies foreign-schema writes and own-schema DDL,
denies migration metadata access, and checks that owner and migration logins
cannot cross-write. It creates and reads the new report-job, document metadata,
audit and event fixtures through the owning runtime logins; verifies ordered
progress cursors and duplicate-event rejection; and explicitly denies writes
between the Project, Orchestration, and Document data schemas. It downgrades
and reapplies each of the nine service migrations independently.

## Evidence recorded

Local run on 2026-11-14 with the cached PostgreSQL 16 Alpine image:

| Service | Schema | Fresh baseline | Independent downgrade/reapply | Service tests |
| --- | --- | --- | --- | --- |
| Auth | `auth` | Passed | Existing baseline not part of this change | Not run for this change |
| Billing | `billing` | Passed | Passed | 10 passed |
| Project | `project` | Passed | Existing baseline not part of this change | Not run for this change |
| Template | `template` | Passed | Passed | 10 passed |
| AI Orchestration | `orchestration` | Passed | Passed | 10 passed |
| Quality | `quality` | Passed | Passed | 10 passed |
| Visual AI | `visual` | Passed | Passed | 10 passed |
| Document | `document` | Passed | Passed | 10 passed |
| Notification | `notification` | Passed | Passed | 10 passed |

The all-nine run used separate migration and runtime login roles. Role checks
passed for all nine services, including test-only foreign-table read grants with
cross-write denial, owner/migrator cross-write denial, runtime schema DDL
denial, and isolation of each schema's `alembic_version`. Python compilation
and Git whitespace checks passed for the new files. The temporary PostgreSQL
container and volume were removed. Google Cloud and Neon were not contacted.

On 2026-11-14, the updated verifier also passed on a fresh local PostgreSQL 16
Alpine container with the new Project revision applied. A separate disposable
PostgreSQL container passed the full Project Service suite (11 tests), including
password-authenticated migration and runtime logins, separate-connection
create/read, owner isolation, Auth write denial and new-revision
downgrade/reapply. Both containers were removed. See the
[Project Service README](../../services/project-service/README.md) for the
Project migration and test details.

On 2026-11-14, separate disposable PostgreSQL 16 Alpine containers passed the
Auth and Project suites (11 tests each) and the all-service verifier with both
persistence revisions. Auth's UUIDv4 survived commit and a separate-connection
read; Project stored it as an owner reference, and its runtime role could not
write `auth.users`. Auth's new revision was downgraded and reapplied; runtime
permissions and caller-managed rollback were checked. The Auth Docker image
passed health, readiness and persistence-module import checks. The disposable
containers and volumes were removed; Google Cloud and Neon were not contacted.

## Stable Auth user ID contract

The approved architecture assigns users and verified identity bindings to Auth,
and defines `user_identities.user_id`, unique provider subjects, and unique
verified phone identities. It does not specify the internal user ID's format.
The P02 roadmap requires stable user identifiers, and Project migration
`0002_project_projects` defines `project.projects.owner_user_id` as
non-nullable PostgreSQL `UUID`.

**Decision:** Auth issues one permanent, immutable UUIDv4 as each user's
internal ID. The Auth-owned `auth.users` table persists the ID and creation
timestamp. Google OIDC identities are intended to map to that ID by their
provider and provider subject; verified phone identities are intended to map
to the same ID by normalized E.164 phone number. Auth owns those identity bindings.
Linking Google and phone identities to an existing account requires verifying
both identities; a provider subject or phone number is not itself the internal
user ID. This allows either login method to resolve to the same Auth user
without changing the user's ID.

Project stores the Auth-issued value in `owner_user_id` as an opaque owner
reference. It does not resolve Google/phone identities or create a cross-schema
foreign key; authorization uses the verified Auth principal's user ID. UUIDv4
is compatible with the migration's UUID column, which does not itself enforce
the UUID version. Auth identity/session tables and P03 identity linking remain
future work; no sign-in behavior is implemented here.

## P02 persistence additions (2026-11-14)

**Report identifiers:** The approved architecture assigns report-job lifecycle
and checkpoint/retry/progress state to AI Orchestration. The roadmap and
architecture do not assign an authoritative issuer or format to `report_id`.
The persistence schema stores the Orchestration-owned `job_id` as a PostgreSQL
UUID and stores `report_id` as a non-empty opaque string, without a cross-schema
foreign key or UUID-format assumption. Project, owner, and Billing reservation
IDs are opaque references. This storage choice does not decide which service
creates or owns the report record; that contract remains open. `report_id`
lookup must use a future API or verified projection. A proposal based on the
existing ownership boundaries is recorded below; it does not change this
storage contract or constitute approval.

**Event contract:** Project's `project.facts.updated` v1 event is the only
producer/consumer pair explicitly named for this work in the architecture:
Project writes the transactional outbox and AI Orchestration records delivery
deduplication. The event carries opaque project/fact IDs and the fact snapshot
version, not fact values. Its uniqueness key is `(producer_service, event_id)`.
Transport, publish ordering, retry/dead-letter policy, retention, actor-context
authorization, and the consumer's stale-output transaction remain undecided;
no publisher, subscriber, or public API is implemented here.

**Document metadata:** Document owns opaque metadata IDs, immutable version
references, SHA-256 checksums, private R2 bucket/key references, and append-only
access history. R2 object keys are not URLs. Local fixtures verify metadata
constraints and separate-connection create/read only; they do not prove live
R2 uploads/downloads, signed URL authorization or expiry, cleanup, deletion,
or retention.

**Verification evidence:** The final verifier run on a disposable local
PostgreSQL 16 Alpine container passed all nine fresh baseline/head migrations,
all nine independent downgrade/reapplies, the persistence fixtures and event
deduplication, and cross-schema write denial. Project Service tests passed
with one environment-dependent database integration test skipped; its two
event-contract cases ran. AI Orchestration and Document Service tests passed.
Python compilation, `git diff --check`, and the new-file whitespace scan passed.
The PostgreSQL container was removed. This local run did not contact Google
Cloud, Neon, or R2; no billing was enabled. The later hosted Neon result is
recorded in §4 below.

## Local logical backup and restore drill (2026-11-14)

**Result: PASS.** Two disposable `postgres:16-alpine` containers ran PostgreSQL
16.16, bound only to loopback-assigned ports. The source verifier migrated all
nine service schemas from empty baselines to head and passed its independent
downgrade/reapply and role-boundary checks. The target was provisioned from
each service's `database/bootstrap.sql` before restore; temporary migration
and runtime role passwords were generated in memory. The custom-format archive
was restored with ownership and ACL restoration enabled (no `--no-owner`).

The source was seeded through the Auth, Project, AI Orchestration, and Document
runtime logins. These values identify the synthetic rows included in the
restored-data comparison:

| Record | ID |
| --- | --- |
| Auth user | `25bcea05-c0d3-4294-af7c-5e143dbe61a5` |
| Project | `fb14b405-3ffb-46be-8ff3-871a0a5d314b` |
| Report job | `9612e537-5dac-4dc7-adfb-48b580eb41f6` |
| Report ID (opaque string) | `p02-drill-report-93fd4806-f569-4a0c-9ee8-70c4c63098f6` |
| Document object | `eb7a94f2-b6ac-43c4-a4ef-2bdffb5d7016` |
| Document version | `5024e53b-8416-4682-979f-cd8659aff2c1` |
| Document access-history row | `dc26c466-8859-4663-ad4e-18c95ba8c55b` |

The source and restored target had exactly these Alembic revisions:

| Schema | Revision |
| --- | --- |
| `auth` | `0002_auth_users` |
| `billing` | `0001_billing_baseline` |
| `project` | `0003_project_events` |
| `template` | `0001_template_baseline` |
| `orchestration` | `0002_orch_persistence` |
| `quality` | `0001_quality_baseline` |
| `visual` | `0001_visual_baseline` |
| `document` | `0002_doc_metadata` |
| `notification` | `0001_notification_baseline` |

The compared Auth, Project, report-job, Document object, version, and
access-history rows matched field-for-field, including the Auth creation
timestamp. Source and target reported PostgreSQL `16.16`. The existing
`verify_login_boundaries` verifier passed against the restored target for all
nine migration and runtime logins: each runtime could use its own restored
permission fixture, foreign-schema writes were denied, and runtime DDL and
migration-metadata access were denied. The actual Auth, Project,
Orchestration, and Document runtime logins also read their respective seeded
records; all 12 cross-schema write attempts among those four services were
denied. The custom-format archive was 76,023 bytes.

### Commands and cleanup

The following is the executed command sequence with generated names, ports,
archive path, and credentials redacted. The temporary passwords were supplied
through process environment/in-memory role setup only; they were not written to
the repository or runbook.

The temporary inline Python harness also applied the nine target bootstrap
files, generated role passwords, seeded the source records through runtime
logins, compared source/target rows and revisions, and called the existing
`verify_login_boundaries(target_url, target_role_passwords)` against the
restored target. The helper code and credential values were not saved.

```powershell
docker volume create <source-volume>
docker volume create <target-volume>
docker run --detach --name <source> --publish 127.0.0.1::5432 `
  --env POSTGRES_PASSWORD --env POSTGRES_DB=acadence `
  --volume <source-volume>:/var/lib/postgresql/data postgres:16-alpine
docker run --detach --name <target> --publish 127.0.0.1::5432 `
  --env POSTGRES_PASSWORD --env POSTGRES_DB=acadence `
  --volume <target-volume>:/var/lib/postgresql/data postgres:16-alpine

$env:P02_TEST_ADMIN_DATABASE_URL = "postgresql://postgres:<ephemeral-secret>@127.0.0.1:<source-port>/acadence"
.\.venv\Scripts\python.exe scripts\test_p02_database_foundation.py
Remove-Item Env:\P02_TEST_ADMIN_DATABASE_URL

# Applied each services\<service>\database\bootstrap.sql on the target as
# postgres, then set temporary migrator/runtime login passwords.
docker exec <source> pg_dump --username=postgres --dbname=acadence `
  --format=custom --file=/tmp/<archive>
docker cp <source>:/tmp/<archive> <temporary-local-archive>
docker cp <temporary-local-archive> <target>:/tmp/<archive>
docker exec <target> pg_restore --username=postgres --dbname=acadence `
  --clean --if-exists --exit-on-error /tmp/<archive>

# After verification:
docker rm --force <source> <target>
docker volume rm <source-volume> <target-volume>
Remove-Item <temporary-local-archive>
```

Both containers, their named volumes, and the local archive were removed after
the successful run. Google Cloud, Neon, and R2 were not contacted.

**Limitations:** This proves a local logical database dump/restore on the same
PostgreSQL major version. `pg_dump` does not include cluster-global roles or
passwords; the target's service roles were provisioned separately from the
service bootstrap SQL before restoring ownership and grants. This does not
exercise managed Neon backup/PITR, physical backups, cross-version restore,
production credentials, large-database recovery time, or R2 object payload
recovery. The Document check covers metadata only, not an R2 object.

## Remaining P02 work

The local logical backup/restore drill and hosted Neon verification pass; do
not rerun Neon for this batch. P02 remains blocked by the live private R2 check
and approval of the retention, report-ID, and production event-transport
recommendations below. Local PostgreSQL tests cover synthetic row cleanup and
the at-least-once delivery/deduplication shape, but no production deletion
worker, publisher, or consumer is implemented. The backup/restore drill does
not verify managed Neon recovery, retention, or R2 payload recovery.

### Decisions already recorded

- The nine service boundaries, service-owned schemas, and no-cross-service
  write rule are selected architectural requirements and passed the recorded
  role checks.
- Auth's permanent UUIDv4 user ID is implemented and recorded in the roadmap
  and this runbook.
- `project.facts.updated` v1, Project outbox ownership, Orchestration inbox
  deduplication, and the at-least-once/idempotent local test are recorded.
- The technology stack prefers Cloud Tasks for one-recipient async dispatch and
  Pub/Sub only for justified fan-out. This is an architectural direction, not
  approval of a production queue/configuration for this event.
- The local logical backup/restore drill passed. It is not a managed Neon PITR
  or R2 payload recovery approval.

## P02 batch proposals and verification (2026-11-14)

### 1. Project/account deletion and retention proposal — **OPEN; approval required**

Deletion is a service-owned workflow, not cross-schema SQL from Auth or
Project. A request should first be authorized and recorded, then fan out
idempotent deletion commands to each owning service. Each service deletes only
its own rows and reports completion. Auth may coordinate account deletion, but
must not directly delete Project, Orchestration, or Document rows. Project
deletion should cancel affected report jobs before removing their data.

| Data | Proposed cleanup |
| --- | --- |
| Auth account | Revoke sessions/identity bindings, then remove Auth-owned identity and user rows after dependent service cleanup is confirmed. |
| Project | Remove project-owned facts, answers, project metadata, unpublished/delivered outbox payloads after dispatch is settled, and upload references. Do not retain fact values in deletion events or logs. |
| Report jobs | Orchestration cancels active Cloud Run executions, removes job/attempt/section/progress/checkpoint state and its own references, and reconciles any separate LangGraph checkpoint rows. Billing reservations are released only through Billing's API. |
| Documents and R2 | Document enumerates all private object versions, deletes each R2 object idempotently, verifies absence, then removes version/object metadata. Failed object deletes stay retryable and visible; do not report deletion complete while an object remains. |
| Audit and access history | Retain only the minimum deletion/security record allowed by the approved policy. Pseudonymize actor/project/object references and metadata before the retained record becomes unlinkable; delete version-bound access rows before deleting their referenced versions (`ON DELETE RESTRICT`). |
| Backups | Do not promise immediate erasure from an immutable backup. Expire backups on the approved schedule, retain deletion tombstones through that window, and replay tombstones before a restored database or object store becomes available. Restore procedures must cover R2 separately. |

No retention interval is selected. Approval is required for: live project/account
deletion completion SLA; pending deletion/tombstone duration; outbox and inbox
deduplication retention; job, checkpoint, and failed-export retention; upload,
report, and temporary R2 object retention; access-history and audit retention;
and Neon/R2 backup or point-in-time recovery retention and deletion replay
window. Legal holds, billing records, security investigations, and recovery
requirements need an explicit exception and access policy before retention
values are set.

**Concrete recommendation (not approved):** Keep account and project content
until the student requests deletion; do not expire an active project for
inactivity. On request, revoke access and cancel active jobs immediately, then
purge the account's live Auth, Project, Orchestration, Document, and R2 data
within 30 calendar days, removing identity rows only after every owning service
confirms completion. Expire abandoned uploads after 24 hours and failed exports
after 7 days. Retain completed job/checkpoint records and delivered outbox or
processed inbox rows for 30 days after terminal completion; retain only
minimal, pseudonymized audit/access metadata for 365 days. Use a 35-day rolling
database-backup window and retain deletion tombstones for 45 days after live
purge, replaying them before a restored database is exposed. Delete all R2
object versions during the 30-day purge; do not claim R2 backup recovery until
it is separately designed and tested. Legal holds and legally required
financial records require a documented, access-restricted exception.

**Exact approval wording:** “Approve the P02 retention recommendation: active
account/project content has no inactivity expiry; deletion immediately revokes
access and cancels work, then purges live data and all R2 object versions
within 30 calendar days, with Auth identity rows removed after owning-service
confirmation; abandoned uploads expire after 24 hours; failed exports after 7
days; completed jobs/checkpoints and delivered/processed outbox/inbox rows
after 30 days; minimal pseudonymized audit/access metadata after 365 days;
database backups expire after 35 days; deletion tombstones remain for 45 days
after live purge and are replayed before restore; legal holds and legally
required financial records are restricted exceptions. R2 backup recovery is
not promised without separate tested coverage.”

The local synthetic cleanup check seeds an Auth user, Project and outbox rows,
an Orchestration job with dependent rows, and Document metadata/access rows.
Using each schema's owner role, it removes those rows in owner-local order,
checks the Orchestration cascades, and verifies that only redacted
`deletion_completed` audit fixtures remain. This is a database behavior test,
not a production deletion API or a runtime-role permission grant. It cannot
delete or verify an R2 payload, Cloud Run execution, external checkpoint, or
backup. No retention timer was advanced or tested.

The Document fixture creates two access-history rows for one synthetic
version. A nested transaction savepoint verifies that the named RESTRICT
constraint blocks deletion without changing those rows; cleanup then deletes
all history by version ID and asserts that the version is deleted. This
fixture does not establish a production retention or deletion policy.

### 2. Report ID contract proposal — **OPEN; approval required**

The migrations contain two references and no authoritative report record:
`orchestration.report_jobs.report_id` is non-empty `TEXT` (not unique, because
multiple jobs may refer to a report), and `document.document_objects.report_id`
is nullable non-empty `TEXT` (also not unique, because a report can have
multiple document objects). Both remain opaque references without a foreign
key. `report_jobs.id` is the Orchestration-owned UUID job ID; document object
and version IDs are Document-owned UUIDs. No existing endpoint or projection
resolves a `report_id`.

**Recommendation, not a recorded decision:** Document should issue the
`report_id` when creating the canonical report record, because Document owns
the canonical report tree and export metadata. Use a lowercase canonical
UUIDv4 string to align with the existing Auth and Project UUIDv4 identifiers,
but continue storing and transporting it as opaque text; consumers must not
parse it or derive ownership from its value. AI Orchestration continues to
issue `job_id` and receives `report_id` from Document. Other services resolve
report metadata through an authenticated, owner-scoped Document API; add a
verified local projection only if a measured read need justifies it. A future
Document API/migration must define uniqueness on its canonical report record
and test ownership, retries, and lookup before this recommendation is adopted.

**Exact approval wording:** “Approve the P02 report-ID contract: Document
Service issues the canonical lowercase UUIDv4 `report_id`; services store and
transport it as an opaque string without a cross-schema foreign key;
Orchestration continues to issue `job_id` and receives `report_id` from
Document; report lookup is through an authenticated, owner-scoped Document
API; and a unique canonical Document report record is required before
report-creation paths ship.”

### 3. `project.facts.updated` delivery proposal and local test — **OPEN; approval required**

Project writes the existing v1 event and its fact snapshot update in one
Project transaction. A Project-owned relay validates the existing
`project.facts.updated` v1 schema, preserves the event ID and payload across
attempts, and delivers to AI Orchestration at least once. Publish in
`aggregate_version` order per project. Orchestration validates the envelope
and, in one transaction, inserts `(producer_service, event_id)` into
`inbox_deduplication`, commits the single business effect, and marks the inbox
row processed. A duplicate key is acknowledged as a no-op. A failed handler
transaction must roll back the inbox insert and effect together so the same
event can be retried. The consumer reads the pinned fact snapshot from Project
using the event's opaque IDs/version; fact values are not copied into this event.

**Transport recommendation, not approved:** Use Cloud Tasks for this
single-recipient dispatch, with one queue per environment and an OIDC-authenticated
task to the private AI Orchestration endpoint. Keep delivery at least once and
preserve the same event ID/payload on retries. Serialize dispatch per project
and enforce `aggregate_version` at the consumer because Cloud Tasks does not
promise per-project ordering. Use a 30-second handler deadline, at most 12
attempts, and bounded exponential backoff from 1 to 300 seconds. Before
production dispatch, add an approved database claim/lease and expiry recovery
scanner. On exhaustion, retain the outbox row as operator-visible unresolved
work, alert, and allow audited replay; never silently drop it. The consumer
commits inbox deduplication and its single business effect in one transaction.
Do not add Pub/Sub unless multi-subscriber fan-out is separately justified and
approved. No Google Cloud API, resource, or billing change is part of this
documentation decision.

**Exact approval wording:** “Approve Cloud Tasks as the production transport
for Project's `project.facts.updated` v1 event to AI Orchestration: one
environment-specific queue, OIDC-authenticated private delivery, at-least-once
retries preserving event ID and payload, per-project serialized dispatch with
consumer `aggregate_version` checks, a 30-second handler deadline, at most 12
attempts with 1–300-second bounded exponential backoff, and an expiry-recovering
outbox lease. After exhaustion retain and alert on unresolved work for audited
replay; commit consumer deduplication and its business effect atomically; do
not use Pub/Sub without separately approved fan-out. This approval does not
authorize enabling Google Cloud billing.”

The nine-service verifier now uses a local in-process test transport and the
existing PostgreSQL outbox/inbox tables. It simulates the transport accepting
the first copy followed by a dispatcher interruption before `published_at` is
recorded, makes the pending event due, retries the same event, then delivers
both copies to the consumer. The consumer commits its inbox record and
test-only effect together; the run asserts two transport deliveries, one
processed inbox row, and exactly one committed effect. No broker or cloud
service is contacted. This verifies the proposed at-least-once/idempotency
shape, not a deployed relay, real transport ordering, concurrency, or
dead-letter behavior.

### 4. Hosted Neon verification — **PASSED**

**Result (2026-11-15):** The full nine-service verifier passed against a
disposable Neon database. It used the direct endpoint for preflight, bootstrap,
and migrations, and the pooled endpoint for runtime connections. Verification
passed for all nine services, including role isolation, synthetic Document
cleanup, and independent downgrade/reapply. Connection URLs and credentials
are intentionally omitted from this runbook.

Earlier hosted attempts stopped before completing Document cleanup; that
failure is superseded by the successful full run recorded above. The verifier
preflights all nine service schemas and 27 Acadence owner, migrator, and runtime
roles, including schemas hidden from the administrator's information-schema
view, and refuses to continue if any exist. Roles are cluster-wide, not
database-local. Do not blindly drop existing roles or schemas: use a fresh
dedicated branch or arrange cleanup only after confirming ownership and impact.

On 2026-11-15, a disposable local PostgreSQL 17.6 cluster reproduced
`must be able to SET ROLE "acadence_auth_owner"` with a non-superuser database
owner having CREATEROLE. After the fix, all nine baseline and head migrations,
independent downgrade/reapply, explicit administrator memberships, actual
migrator/runtime login identity and owner-role boundaries, runtime CRUD and
cross-schema/DDL denial, event retry/deduplication, and synthetic cleanup
passed. The preflight also rejected an existing local setup and a partial
schema invisible to `information_schema`. The runtime
endpoint configuration for this local run pointed to the same local direct
server, not a real pooler; those local results alone do not prove Neon pooled
connectivity or password authentication. Hosted coverage is recorded above.

**Update 2026-11-15, Document RESTRICT fix:** The reported previous hosted run
passed nine migrations, service-role checks, and outbox retry/deduplication,
then failed at Document cleanup with `RestrictViolation` on
`document_access_history_document_version_id_fkey`; its retry hit the
freshness guard. This earlier failure preceded the successful full hosted run
recorded above. Do not reuse or alter that earlier branch.

Local PostgreSQL 17.6 produced `ForeignKeyViolation` (`23503`) for the same
RESTRICT relationship, so the unmodified verifier passed there. A test-only
trigger raising `23001` reproduced the reported exception escaping the
unmodified handler; this is a simulation, not a hosted run. After the fix,
the complete verifier passed on two fresh, separate PostgreSQL 17.6 clusters:
one with the native constraint and one with that test-only trigger. Both used
a non-superuser database owner with CREATEROLE and SCRAM-authenticated
connections. Each passed all nine baselines and head migrations, owner and
login boundaries, event retry/deduplication, two-row Document cleanup, and
all nine independent downgrade/reapply checks. Each retry was rejected by the
freshness guard. The separate runtime URL used the same local server, not a
pooler. Both clusters were stopped and removed. Pylance syntax validation and
`git diff --check` passed. The hosted handoff's PowerShell and Python syntax
passed, and offline checks rejected mismatched endpoint IDs, mismatched databases,
and a host-override option.

For any future rerun, provide a disposable branch with no Acadence service
schemas or roles, an administrator connection allowed to create the nine
schemas/owner, migrator, and runtime roles, and the branch's PostgreSQL
version/endpoint details. Set `P02_TEST_ADMIN_DATABASE_URL` to the direct,
non-pooled admin endpoint and `P02_TEST_RUNTIME_DATABASE_URL` to the same
disposable database's pooled endpoint. The verifier uses the direct endpoint
for bootstrap/migrations
and separate generated service login/passwords through the runtime endpoint.
Run `scripts/test_p02_database_foundation.py`; it must pass fresh baselines,
all migrations, independent downgrade/reapply, runtime CRUD, cross-service
write denial, and its event/cleanup fixtures. Then verify pooled runtime
connections for all nine roles and observe that `session_user` is the intended
runtime login, not the admin or migrator. Do not point either URL at shared,
staging, or production data. Record Neon PostgreSQL version, pooler mode, role
checks, migration revisions, and cleanup of the disposable branch without
logging URLs, usernames/passwords, or tokens.

After independently creating and confirming a new disposable Neon branch, run
the following from the repository root. The read-only preflight requires standard
Neon direct/pooler hostnames for the same endpoint and the same database,
checks both connections, and refuses existing service schemas or roles before
the verifier writes anything. Custom domains or multiple endpoint IDs require
separate branch-identity verification rather than bypassing this check.

```powershell
if ((Read-Host 'Type DISPOSABLE after confirming a NEW empty Neon branch') -cne 'DISPOSABLE') {
    throw 'Stopped: a new disposable branch must be confirmed.'
}
try {
    $env:P02_TEST_ADMIN_DATABASE_URL = [System.Net.NetworkCredential]::new('', (Read-Host 'Direct URL' -AsSecureString)).Password
    $env:P02_TEST_RUNTIME_DATABASE_URL = [System.Net.NetworkCredential]::new('', (Read-Host 'Pooled URL' -AsSecureString)).Password
    @'
import os
import sys
import psycopg
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from scripts.test_p02_database_foundation import SERVICES, role_name

try:
    direct, pooled = [make_url(os.environ[name]) for name in (
        "P02_TEST_ADMIN_DATABASE_URL", "P02_TEST_RUNTIME_DATABASE_URL"
    )]
except (ArgumentError, ValueError):
    sys.exit("Invalid endpoint URL; no database was changed.")
for url in (direct, pooled):
    if (url.drivername not in ("postgres", "postgresql") or not url.host
        or not url.database or not url.username or not url.password
        or set(url.query) - {"sslmode", "channel_binding"}
        or url.query.get("sslmode") not in ("require", "verify-ca", "verify-full")):
        sys.exit("Endpoint URL or TLS options rejected; no database was changed.")
host = direct.host.lower()
first, sep, suffix = host.partition(".")
if (not sep or not first.startswith("ep-") or first.endswith("-pooler")
    or not host.endswith(".neon.tech")
    or pooled.host.lower() != first + "-pooler." + suffix
    or direct.port != pooled.port or direct.database != pooled.database):
    sys.exit("Endpoints are not the matching Neon direct/pooler pair and database.")
try:
    results = []
    for name in ("P02_TEST_ADMIN_DATABASE_URL", "P02_TEST_RUNTIME_DATABASE_URL"):
        with psycopg.connect(os.environ[name], autocommit=True) as conn:
            results.append(conn.execute(
                "SELECT current_database(), current_setting('server_version')"
            ).fetchone())
            if name == "P02_TEST_ADMIN_DATABASE_URL":
                schemas = [schema for _, schema, _ in SERVICES]
                roles = [role_name(schema, purpose) for schema in schemas
                         for purpose in ("owner", "migrator", "runtime")]
                if (conn.execute("SELECT 1 FROM pg_namespace WHERE nspname = ANY(%s)", (schemas,)).fetchone()
                    or conn.execute("SELECT 1 FROM pg_roles WHERE rolname = ANY(%s)", (roles,)).fetchone()):
                    sys.exit("Acadence schemas or roles exist; stop and use a new branch.")
    if results[0] != results[1] or results[0][0] != direct.database:
        sys.exit("Endpoints disagree on database or PostgreSQL version; stopped.")
    print("PASS read-only endpoint and freshness preflight; PostgreSQL", results[0][1])
except psycopg.Error as error:
    sys.exit(f"Preflight database error: {type(error).__name__} (SQLSTATE {error.sqlstate or 'unavailable'}).")
'@ | .\.venv\Scripts\python.exe -
    if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; verifier was not started.' }
    .\.venv\Scripts\python.exe scripts\test_p02_database_foundation.py
    if ($LASTEXITCODE -ne 0) { throw 'Verifier failed; do not retry on this branch.' }
} finally {
    Remove-Item Env:\P02_TEST_ADMIN_DATABASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\P02_TEST_RUNTIME_DATABASE_URL -ErrorAction SilentlyContinue
}
```

### 5. Live private R2 verification — **BLOCKED; credentials/bucket unavailable**

On 2026-11-15, process-environment inspection found none of
`R2_ACCOUNT_ID`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`, or `R2_BUCKET_NAME`; no R2 or Cloudflare environment
variables were present. The checked-in `.env.example` files contain empty
account, endpoint, and access-key placeholders and the example bucket name
`acadence-dev`, which does not establish that a dedicated private test bucket
exists. No R2 endpoint was contacted. Google Cloud billing remained off.

The repository has no production upload/download signing endpoint yet.
[`r2_probe.py`](../../spikes/python/r2_probe.py) generates five-minute
signatures with dummy credentials offline; it does not contact R2. The
interactive [`test_r2_private_bucket.py`](../../scripts/test_r2_private_bucket.py)
performs a direct live S3-compatible check with a dedicated private
non-production bucket and scoped credentials. It asks for the account ID,
matching HTTPS endpoint, bucket name, access-key ID, and secret access key;
both credential prompts are hidden. It asks you to retype the bucket name to
confirm the target is private and non-production. Values are held only in
process memory and are not printed. Confirm that a five-minute signed URL
lifetime is acceptable for the test bucket before running it. The script does
not invoke a product signing endpoint.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\test_r2_private_bucket.py
```

The script uploads one synthetic object through a signed PUT, downloads it
with a signed GET and verifies its SHA-256, then checks anonymous read denial
on that same object and anonymous write denial. The unsigned checks accept
HTTP 401/403 or HTTP 400 with R2 XML code `InvalidArgument` and exact message
`Authorization`; other 400 responses fail. Separately, it checks that
five-second signed GET and PUT URLs fail after expiry (only 401/403 count as
denial), and deletes and
verifies absence of all objects under a unique `acadence-r2-check` prefix,
including repeated-delete idempotence. It reports cleanup success or failure
even when an earlier check fails, but never credentials, signed URLs, raw
response bodies, or object contents.
Metadata-only PostgreSQL fixtures do not satisfy this live check. Until a
successful run is recorded, the P02 R2 gate remains **BLOCKED**.

The reported live attempt ended with unverified cleanup and three
`InvalidArgument` errors. The cause remains open; the cleanup calls use
`delete_object(Bucket=..., Key=...)` and `head_object(Bucket=..., Key=...)`,
matching [Cloudflare's boto3 examples](https://developers.cloudflare.com/r2/examples/aws/boto3/).
The runner now reports the first check failure before separate cleanup failures,
including the HTTP status and R2 error code when available. If cleanup is not
verified, inspect and remove the reported synthetic prefix in the confirmed
test bucket; do not assume the objects were removed.

Offline regression evidence (2026-11-15): eleven mocked tests passed, including
unsigned 400 acceptance/rejection, expiry rejection, and simultaneous check and
cleanup failures, without a live R2 request:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s scripts\tests -p test_r2_private_bucket.py -v
```

### Batch test evidence

On 2026-11-14, the nine-service verifier passed twice on fresh disposable local
PostgreSQL 16 Alpine databases: all nine empty baselines/head migrations,
independent downgrade/reapply, runtime-role isolation, synthetic cleanup, and
interrupted local event delivery with duplicate suppression. One run also set
`P02_TEST_RUNTIME_DATABASE_URL` to the same loopback endpoint to exercise the
separate-endpoint configuration; this is not evidence of Neon pooling.
Project Service tests passed (13 tests, one database integration test skipped
because its separate test URLs were not configured); AI Orchestration and
Document Service tests passed (10 each). Python compilation and `git diff
--check` passed. Docker containers were stopped and auto-removed. Neon, R2, and
Google Cloud were not contacted; Google Cloud billing stayed off.
