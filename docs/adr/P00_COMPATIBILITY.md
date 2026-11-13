# P00 compatibility status

**Status as of 13 November 2026: IN_PROGRESS.** The local probes ran with synthetic data. The roadmap's P00 gate calls for live proof-of-concept deployments and recorded decisions.

The original stack v2.2, system architecture v1.1, multi-agent architecture v1.1, and roadmap v1.0 are in `docs/`. The Cursor rules establish version precedence. The UI handoff and clickable AI Mentor prototype are included as implementation references. The AI orchestration service and report job examples now use the architecture's `orchestration` schema, and the visual service example uses `visual`.

| Roadmap item | Verified locally | Remaining evidence |
| --- | --- | --- |
| ADR-001 Frontend and Worker | Next.js 16.4.6, React 19.3.1, and Vinext 1.4.5 passed the spike compatibility scan and production build. Local Cloudflare preview returned the App Router page, static SVG, both SSE progress events, and the expected `HttpOnly`, `Secure`, and `SameSite=Lax` cookie attributes. Versions are locked in the spike. | Deploy to a Cloudflare dev Worker. Verify HTTPS session behavior, streaming through the live edge, asset and image optimization, and Tailwind, shadcn/ui and RTK Query together. |
| ADR-002 Cloud Run ingress | A Python 3.13.5 FastAPI fixture passed `/healthz` and OpenAPI checks. | Prove Worker-to-Cloud Run authentication without private service-account keys and verify Cloud Run service-to-service IAM, including rejection of unauthorized calls. |
| ADR-003 Template editor | Tiptap 3 and ProseMirror round-tripped heading and bold text. dnd-kit reordered fixture pages without mutating the original list. | Exercise drag-and-drop in a browser with keyboard and touch, prototype headers/footers and auto-pagination, and decide on a custom layout engine or Tiptap Pages after testing constraints. |
| ADR-004 Documents | One fixture produced HTML, DOCX, PDF, and LaTeX. Checked HTML text and DOCX structure. Verified two pages and expected text in both the ReportLab PDF and the PDF compiled with pdfLaTeX. | Check layout parity in a browser, Word and the selected production renderers. Evaluate pagination, fonts, tables, page numbering and bibliography in realistic templates. |
| ADR-005 Report job resume | LangGraph paused for student input, saved the checkpoint in SQLite, and completed in a separate process after receiving the answer. | Use the PostgreSQL checkpointer on a dedicated dev database and prove exit/resume across two Cloud Run Job executions. |
| ADR-006 Database and assets | Embedded PostgreSQL enforced auth/project schema isolation in both directions. Boto3 generated valid-format five-minute R2 PUT and GET signatures offline with dummy credentials and signed the upload content type. | Test Neon credentials, migrations and pooling. Verify private signed PUT/GET, CORS and expiry against a dev R2 bucket. |
| ADR-007 Visuals | Mermaid strict mode parsed a valid diagram and rejected malformed input. DOMPurify removed an inline event handler from a separate sample SVG. | Render and sanitize actual Mermaid output in the chosen runtime. Evaluate the vision and image providers for privacy, cost and quality. FLUX.2 remains a candidate. |

For ADR-001, the Vinext-generated typed Cloudflare configuration produced an assets-only local preview and returned 404 for the page. Vinext's Wrangler configuration generated a Worker entrypoint and passed the local route checks. This configuration choice is scoped to the P00 spike.

For ADR-005, `P00_TEST_CHECKPOINT_DATABASE_URL` switches the probe to `PostgresSaver` and initializes its checkpoint tables. Use a dedicated test database when running it. The SQLite fixture and embedded PostgreSQL checks provide local evidence for two separate risks.

## Decisions to verify before dependent work

| Decision | Dependent work |
| --- | --- |
| OTP provider and delivery settings | Mobile signup and login |
| Payment gateway, renewals, entitlement periods and refunds | Paid plans and checkout |
| Licensed similarity provider, corpus coverage and report handling | Plagiarism checking |
| Clinical and other sensitive uploads, consent and retention | Student uploads and vision |
| STT/TTS provider and language/device coverage | Speaking Mentor |
| Page layout engine, PDF conversion and LaTeX toolchain | Template pagination and export parity |
| Exact language, embedding, vision and image models and their data retention | Report generation, checking and visuals |

## Next verification

Deploy the frontend fixture to a development Cloudflare Worker and the health fixture to a private Cloud Run service. Confirm that the intended Worker identity can invoke the service and that anonymous requests are rejected. A dev Neon database and R2 bucket are needed for the subsequent checkpoint and asset tests. This workspace has no authenticated cloud environment. The probes require no student data or model-provider keys.
