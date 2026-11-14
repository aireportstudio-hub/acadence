# P02 local database foundation

This runbook covers the schema, role and Alembic baseline foundation only. It
does not create product tables or mark the full P02 gate complete.

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
runs every empty baseline, and verifies that the version table is service-owned.
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

## Remaining P02 work

This local foundation does not complete P02. Product persistence (including
versioned contracts, audit/event patterns, document metadata and the
orchestration job ledger), retention ownership, and backup/restore drills
remain pending. No production credentials, cloud migrations, Neon pooling, or
cloud backup/restore behavior were tested.
