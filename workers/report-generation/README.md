# Report-generation worker skeleton

P01 provides a local Python 3.13 startup check only. It does not generate
reports or load an environment file or credentials. Running without
`--smoke-check` exits nonzero because report generation is not implemented.
The existing `.env.example` names are reserved for later work and are not
read by this skeleton.

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe workers\report-generation\main.py --smoke-check
.\.venv\Scripts\python.exe -m unittest discover -s workers\report-generation -p "test_*.py"
docker build -t acadence-report-generation workers\report-generation
docker run --rm --network none acadence-report-generation --smoke-check
```

The Docker build may need network access to obtain the Python base image;
the smoke check itself needs no network. No configuration is required for
either startup check.

## Local verification (2026-11-13)

- The unittest command above passed both tests with Python 3.13.17.
- The local startup check and Docker build succeeded.
- The Docker startup check succeeded with `--network none`; running the image
  without `--smoke-check` exited 1 without running a report job.

## Scope and open decisions

LangGraph execution, PostgreSQL checkpoints, R2, job dispatch, and Cloud Run
deployment are not implemented. P00's PostgreSQL checkpoint and Cloud Run
exit/resume proof remains open; see `docs/adr/P00_COMPATIBILITY.md` at the
repository root. This startup check does not satisfy the P01 deployment gate.
