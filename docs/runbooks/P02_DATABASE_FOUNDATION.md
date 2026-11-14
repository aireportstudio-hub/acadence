# P02 local database foundation

This runbook records the schema, role and Alembic baseline foundation and the
Auth, Project, AI Orchestration, and Document persistence revisions. It does
not mark the full P02 gate complete.

## Local verification

Use a fresh, disposable local PostgreSQL database and a database administrator
login. Do not point this verifier at Neon, Google Cloud, or any database with
data to retain. The script refuses to run if any of the nine service schemas or
Acadence roles already exist. It creates random migration/runtime role
passwords in memory, then connects through each role separately.

```powershell
$env:P02_TEST_ADMIN_DATABASE_URL = "postgresql://postgres:<local-password>@127.0.0.1:<port>/<fresh-database>"
.\.venv\Scripts\python.exe scripts\test_p02_database_foundation.py
Remove-Item Env:\P02_TEST_ADMIN_DATABASE_URL
```

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
lookup must use a future API or verified projection.

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
The PostgreSQL container was removed. Google Cloud, Neon, and R2 were not
contacted; no billing was enabled.

## Remaining P02 work

This batch does not complete P02. Remaining work includes the report-record
issuer/lookup contract, additional service API/event contracts and event
delivery implementation, live R2 upload/download and signed-URL verification,
retention/deletion ownership, production Neon and cloud migration checks, and
backup/restore drills. No production credentials or cloud services were used.
