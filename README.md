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
