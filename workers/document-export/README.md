# Document-export worker skeleton

P01 provides a local Python 3.13 startup check only. It does not generate
documents or load an environment file or credentials. Running without
`--smoke-check` exits nonzero because export execution is not implemented.
The existing `.env.example` names are reserved for later work and are not
read by this skeleton.

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe workers\document-export\main.py --smoke-check
.\.venv\Scripts\python.exe workers\document-export\main.py
.\.venv\Scripts\python.exe -m unittest discover -s workers\document-export -p "test_*.py" -v
docker build -t acadence-document-export workers/document-export
docker run --rm --network none acadence-document-export --smoke-check
docker run --rm --network none acadence-document-export
```

Both invocations without `--smoke-check` should exit nonzero. In PowerShell,
inspect `$LASTEXITCODE` immediately after either command to verify its status.
The Docker build may need network access to obtain the Python base image;
the smoke check itself needs no network. No configuration is required for
either startup check.

## Local verification (2026-11-13)

- Both unittest cases passed with Python 3.13.17.
- The local startup check and Docker build succeeded.
- The Docker startup check succeeded with `--network none`; running the image
  without `--smoke-check` exited 1 without running an export job.

## Scope and open decisions

Document generation, PostgreSQL, R2, job dispatch, and Cloud Run deployment
are not implemented. Page layout, PDF conversion, and the LaTeX toolchain
remain open decisions; see `docs/adr/P00_COMPATIBILITY.md` at the repository
root. This startup check does not satisfy the P01 deployment gate.
