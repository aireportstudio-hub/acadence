# P02 local database foundation

This runbook covers the schema, role and Alembic baseline foundation and the
first Project persistence revision. It does not mark the full P02 gate complete.

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
runs every empty baseline, then applies the Project persistence revision and
verifies that each version table is service-owned.
Temporary `permission_probe` tables and cross-schema `USAGE`/`SELECT` grants
exist only in this disposable database. The test checks runtime CRUD on its
explicitly granted table, denies foreign-schema writes and own-schema DDL,
denies migration metadata access, and checks that owner and migration logins
cannot cross-write. It downgrades and reapplies each of the seven new baselines
while verifying that the other eight remain at their recorded versions.

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

## Proposed stable Auth user ID contract

The approved architecture assigns users and verified identity bindings to Auth,
and defines `user_identities.user_id`, unique provider subjects, and unique
verified phone identities. It does not specify the internal user ID's format.
The P02 roadmap requires stable user identifiers, and Project migration
`0002_project_projects` defines `project.projects.owner_user_id` as
non-nullable PostgreSQL `UUID`.

**Proposal, pending explicit approval:** Auth issues one permanent, immutable
UUIDv4 as each user's internal ID. Google OIDC identities map to that ID by
their provider and provider subject; verified phone identities map to the same
ID by normalized E.164 phone number. Auth owns those identity bindings.
Linking Google and phone identities to an existing account requires verifying
both identities; a provider subject or phone number is not itself the internal
user ID. This allows either login method to resolve to the same Auth user
without changing the user's ID.

Project stores the Auth-issued value in `owner_user_id` as an opaque owner
reference. It does not resolve Google/phone identities or create a cross-schema
foreign key; authorization uses the verified Auth principal's user ID. UUIDv4
is compatible with the migration's UUID column, which does not itself enforce
the UUID version. This is a proposed cross-service contract, not an approved
or implemented Auth behavior; Auth identity/session tables and P03 identity
linking remain future work.

## Remaining P02 work

This local foundation does not complete P02. Remaining product persistence (including
versioned contracts, audit/event patterns, document metadata and the
orchestration job ledger), retention ownership, formal approval and
implementation of the stable-ID contract, and backup/restore drills remain
pending. No production credentials, cloud migrations, Neon pooling, or cloud
backup/restore behavior were tested.
