# Acadence

This Cursor starter contains the agreed architecture, UI handoff, component-specific environment examples, and runnable P00 compatibility probes. See [P00 compatibility status](docs/adr/P00_COMPATIBILITY.md) for test results and the deployment gates.

## Open in Cursor

1. Extract the ZIP and open the `acadence` folder in Cursor.
2. Start with the [development roadmap](docs/ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md) and the P00 compatibility status. Cursor loads the project rules from `.cursor/rules/`.
3. Run any of the checks below. They use synthetic data and run locally with no cloud credentials. Use Node.js 24 and Python 3.13 for the spike commands.

The full architecture, stack, UI references, and environment guide are in `docs/`. The app and service directories contain environment examples for later phases. Real secrets belong in local ignored environment files or the deployment secret manager.

## Run the local probes

From the repo root, in PowerShell on Windows:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r spikes/python/requirements.lock.txt
.venv\Scripts\python.exe spikes/python/api_probe.py
$thread = [guid]::NewGuid().ToString()
.venv\Scripts\python.exe spikes/python/graph_probe.py pause --thread $thread
.venv\Scripts\python.exe spikes/python/graph_probe.py resume --thread $thread --answer "A reading diary"
.venv\Scripts\python.exe spikes/python/document_probe.py .p00-output/documents
.venv\Scripts\python.exe spikes/python/r2_probe.py
```

On macOS or Linux, create the environment with `python3.13 -m venv .venv`, use `.venv/bin/python`, and choose a fresh thread ID for each pause/resume pair. The two commands use the same ID to demonstrate persistence across processes. The document probe compiles LaTeX when a usable pdfLaTeX installation is available.

Run the Node checks and build the local Worker:

```text
npm --prefix spikes/tooling ci
npm --prefix spikes/tooling run check
npm --prefix spikes/frontend ci
npm --prefix spikes/frontend run check
npm --prefix spikes/frontend run build:vinext
npm --prefix spikes/frontend run start:vinext -- --host 127.0.0.1 --port 4313
```

From a separate terminal, check the Worker page and progress stream:

```text
curl -i http://127.0.0.1:4313/
curl -i http://127.0.0.1:4313/fixture.svg
curl -i -N http://127.0.0.1:4313/api/probe
```

The route emits a synthetic progress stream and a sample cookie. On Windows PowerShell, use `curl.exe` if `curl` is an alias. Production auth, provider accounts, and deployable service implementations belong to later roadmap tasks.

## P01 backend checks

On 13 November 2026, all nine service unit suites passed locally with Python
3.13.17 (nine tests per service). From the repository root, run each suite in
a separate process after installing its `requirements-dev.txt`:

```powershell
Get-ChildItem .\services -Directory | ForEach-Object {
    .\.venv\Scripts\python.exe -m unittest discover -s $_.FullName -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed for $($_.Name)" }
}
```

The suites include startup, error handling, and isolated production OpenAPI
checks for the service title and health/readiness 200 responses. The backend
workflow runs the suites on Ubuntu with Python 3.13 alongside the existing
Docker smoke job; its first GitHub run is still needed to verify CI. This is
only part of P01, not its completion gate. Cloudflare-to-Cloud Run ingress
authentication remains an open P00/P01 decision.
