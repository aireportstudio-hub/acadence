# Acadence — Technology Stack & Feature Coverage v2.2

**Status:** Agreed design baseline; provider selections and exact package patches remain subject to licensing, compatibility, cost, and security checks.  
**Previous version:** v2.1, preserved in full in this file and separately in the Library.  
**Companion references:** `ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md` and `ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`.

> **Read-first / precedence rule.** This v2.2 update is authoritative wherever it changes v2.1. Everything else from v2.1 remains required, including all feature requirements and statuses. The complete v2.1 text is reproduced later under **Preserved v2.1 baseline**; its older single-API deployment description is historical wherever it conflicts with the nine independently deployable services below. Do not treat suggested providers, conditional tools, or untested dependencies as finalized purchases or production-validated integrations.

## v2.2 change register — no features removed

| Decision | v2.2 status | Notes |
|---|---|---|
| **Nine separately deployable backend microservices** | **SELECTED** | Auth, Billing, Project, Template, AI Orchestration, Quality, Visual AI, Document, Notification. Monorepo allowed; independent Docker builds, deployments, scaling and identities required. |
| **Cloudflare Workers for Next.js frontend** | **SELECTED, unchanged** | Frontend + optional BFF/API-routing layer; not Cloudflare Pages. Next.js 16 + vinext remains **VERIFY**, not presumed compatible. |
| **FastAPI + Python 3.13, Cloud Run Services** | **SELECTED, expanded** | Each of nine services is a separately deployed Cloud Run Service, with appropriate Cloud Run Jobs for long tasks. |
| **Cloud Run Jobs + LangGraph** | **SELECTED, unchanged** | AI worker executions; checkpoint/exit while waiting for student input. Separate document/visual jobs when justified. |
| **Thirty-six logical roles** | **SELECTED as architecture** | Preserve all original 31 responsibilities; add #32–#36 for diagrams, rendering, visual understanding, image generation and figure management. They are not 36 servers or always-on chatbots. |
| **Student image upload as project input** | **ADD — required** | Student-owned screenshots, hardware photos, diagrams, university formatting samples, research figures; capture consent/licensing, provenance and ownership. |
| **Mermaid JS library** | **ADD — primary diagram option** | Flowchart, architecture, sequence, ER, state and similar structured diagrams; render safe SVG for preview and export-compatible figures. |
| **Mermaid CLI / headless rendering** | **ADD — export rendering candidate** | Version-pinned renderer for consistent server-side assets; assess container size, browser dependencies and fonts. |
| **Mermaid hosted API** | **CONDITIONAL** | Only if local library/CLI fails specific needs; avoid a required paid dependency or unnecessary external data transfer. |
| **AI image generation API** | **ADD — provider VERIFY** | FLUX.2 via Cloudflare AI/Workers AI or Black Forest Labs direct is a candidate, not a guarantee; fal.ai/Stability alternatives. No generation of fake student results. |
| **Multimodal image understanding** | **ADD — model VERIFY** | LLM vision model extracts *candidate observations*, never trusted project facts until student confirms. |
| **Charts from real datasets** | **ADD** | Matplotlib or Plotly based on student-supplied verified numeric data; never synthetic results presented as measurements. |
| **Visual asset registry** | **ADD** | Asset source/origin (student, AI, verified source), version, caption, alt text, approval, usage rights, source IDs, owner, report/section binding and R2 key. |
| **Interservice trust/communication** | **ADD** | IAM/OIDC for private Cloud Run-to-Cloud Run calls; Cloud Tasks for one-to-one asynchronous dispatch, Pub/Sub only when fan-out justified, transactional outbox/idempotency as appropriate. |
| **Independent service data ownership** | **ADD** | Per-service schemas and restricted DB credentials in Neon initially; never allow cross-service direct writes. Shared instance is a remaining blast radius. |
| **Core v2.1 features** | **PRESERVED** | Authentication/one-account policy, Hobby/Pro/Premium, all protected routes, 3 templates, editor, adaptive questions, voice mentor, AI report, QA/citations/plagiarism, preview, DOCX/PDF/LaTeX, recovery, storage, monitoring and tests. |

## Selected deployable boundaries and compute

| Deployment | Responsibilities and libraries | Host |
|---|---|---|
| Frontend and BFF | Next.js App Router, React, TypeScript, Tailwind, shadcn/ui, Redux Toolkit/RTK Query if needed, React Hook Form + Zod, Tiptap/ProseMirror, dnd-kit, Mermaid browser preview | **Cloudflare Workers** |
| `auth-service` | FastAPI, Google OIDC, mobile OTP adapter, session/JWT/rotation, user/email/phone uniqueness, device-risk controls | **Cloud Run Service** |
| `billing-service` | FastAPI, payment adapter (provider not finalized), plan entitlements, trial rules, verified webhooks, ledger and quota reservation | **Cloud Run Service** |
| `project-service` | FastAPI, student academic context, projects, questions/answers, confirmed facts and provenance, uploaded asset intake metadata | **Cloud Run Service** |
| `template-service` | FastAPI, university-style defaults, max 3 saved custom initial-page templates, ordered page blocks, immutable template snapshots, formatting settings | **Cloud Run Service** |
| `ai-orchestration-service` | FastAPI control endpoints, LangGraph/LangChain/LangSmith, Claude/Groq/OpenAI adapters, LangGraph Postgres checkpointer, report memory, job/section orchestration | **Cloud Run Service** + **Cloud Run Job** for generation |
| `quality-service` | FastAPI, facts/consistency/repetition/originality/citation checks, structured verdicts, optional research verification and licensed external plagiarism provider | **Cloud Run Service** (Jobs if costly) |
| `visual-ai-service` | FastAPI, Mermaid spec validation/rendering, vision-based image analysis, approved diffusion generation, chart construction, asset metadata checks | **Cloud Run Service** + optional Jobs |
| `document-service` | FastAPI, canonical report model, layout checks, previews, python-docx, ReportLab or validated PDF converter, Tectonic/LaTeX, final R2 outputs and authorized exports | **Cloud Run Service** + **Cloud Run Job** for heavy exports |
| `notification-service` | FastAPI, event-driven OTP send workflow, payment/report/error notices; never source of truth for OTP verification or payment success | **Cloud Run Service** |

**Cross-cutting dependencies retained:** Neon PostgreSQL + SQLAlchemy 2/Alembic/psycopg 3; pgvector/Voyage AI when appropriate; Upstash Redis cache/throttling; Cloudflare R2; Docker; Git/GitHub/GitHub Actions; Google Cloud Logging/Monitoring; Sentry/OpenTelemetry; LangSmith; pytest, Ruff, Pyright, Vitest, React Testing Library and Playwright; Cursor rules and ADRs. No replacement of these agreed selections.

**Database isolation:** Start with **one Neon PostgreSQL instance and nine service-owned schemas/roles** if cost dictates, not nine separate databases by default. Strict per-schema read/write permissions, service-owned migrations, and API/event integration; no direct cross-service writes. A shared database, shared cloud region, shared R2 account, or gateway can still be a failure domain. Separate instances later only if needed. Ownership of the `report_job` lifecycle stays in AI orchestration; ownership of payment, paid project allowance, and quota ledger stays in Billing; no distributed cross-schema transactions assumed.

**BFF caveat:** A Cloudflare Worker cannot be presumed to call a private Cloud Run endpoint using native Google service identity automatically. Choose and test a secure ingress design (public narrowly scoped gateway with robust application auth and protective controls, or a configured workload identity federation/token broker alternative). Private GCP-to-GCP service calls should use per-service IAM identities with audience-bound identity tokens; no service account key files baked into images.

## New visual pipeline and exact boundaries

**A. Student-uploaded assets (required):**
1. Student selects project screenshots, prototype photos, diagrams, data charts, university formatting examples, or other eligible image files during intake or adaptive questions. Respect consent and privacy of third parties and restrictions on patient/clinical material. Student may identify whether a file is for project evidence, report insertion, or university layout reference.
2. API requests a time-limited private R2 upload grant after auth, plan/project ownership, size/count/type limits and quota policy. Browser uploads directly to R2; backend verifies actual file signature, dimensions, format, size and ownership. Protect against decompression bombs, EXIF/GPS leakage, malicious files, SVG/script content, and image metadata that should not be retained; malware screening according to threat model. Never use public bucket URLs for private student material.
3. `visual-ai-service` processes the eligible image with a vetted multimodal model. Store **candidate observations** with image ID, crop/region when available, uncertainty and provenance. Confirm important observations with the student before promoting to `confirmed_project_fact` via Project Service. OCR is a fallback/structured extraction technique, not unquestioned truth.
4. Store the asset and its immutable versions in R2; visual metadata in the owning service schema; expose only versioned asset references to the LangGraph workflow. The uploaded image can be used in report figures only after appropriate rights, relevance, and student approval.

**B. Deterministic diagrams from confirmed facts (required):**
1. AI orchestration requests a typed `DiagramSpec` (type, nodes, edges, labels, evidence/fact IDs, target section) from role **#32 Diagram Generation Agent**. No undocumented database/algorithm/component may be introduced.
2. Visual Service role **#33 Diagram Validation & Rendering** checks `DiagramSpec` semantically and compiles Mermaid text. Use safe rendering (`securityLevel: strict`/isolated environment), input-size limits, no untrusted links or script labels, SVG sanitization and a reproducible renderer. Reject syntax and unsupported layout rather than embedding broken figures.
3. Output preview SVG and approved export-compatible SVG/PNG (raster fallback). Store visual asset versions and details with role **#36**. Inserting into the canonical document requires caption, alt text, figure number and a clear source/AI illustration label. Some complex academic illustrations may need other vetted tools; do not force Mermaid to draw everything.

**C. Generative images (required as feature, provider pending):**
1. Role **#35 AI Image Generation Agent** requests conceptual illustrations only, with section purpose, source/fact constraints, cost and content policy. FLUX.2 via Cloudflare AI or another vetted provider is a **candidate**; validate pricing, terms, sensitive-image policy and availability.
2. Prompt → provider → store as `origin=ai_generated, depiction=illustrative` → optional QA/approval → caption/alt text → insert when relevant. Never generate fake experiments, clinical scans, participant photos, test screenshots or fabricated evidence disguised as authentic results.
3. Image generation is non-blocking when optional; if it fails, preserve content and report real pending/error state. Do not generate images for a student who did not request/authorize that use where user controls require approval.

**D. Real-data charts (required capability):** Use Matplotlib/Plotly with verified user-supplied dataset and labels. Never infer numeric results from a topic. Store chart data provenance and units. Validate missing data and category names before rendering.

**E. Privacy/security:** Uploaded student data and sensitive visuals are untrusted, never silently forwarded to external providers without an approved privacy basis, never cross-tenant. Restrict access by project ID, validate output SVG against XSS and prompt injection, strip unintended metadata, retain audit events, and provide deletion/retention controls.

## Updated acceptance gates (in addition to every v2.1 gate)

- [ ] All **nine** Cloud Run services have independent Docker build/deploy pipelines, identities, health checks, scopes and rollback; frontend stays on Cloudflare Workers.
- [ ] An Auth/Billing/Visual/Document service failure does not corrupt report state or bypass access rules; degrade safely when dependencies are critical.
- [ ] No cross-service direct database writes; schemas and migration ownership enforced by credentials and integration tests.
- [ ] Authenticated synchronous calls and asynchronous Cloud Tasks/Pub/Sub events are traced, idempotent, bounded, retried or dead-lettered as appropriate; no unbounded synchronous dependency chain.
- [ ] Student images upload securely, survive refresh, receive metadata/rights checks, and can inform *candidate* facts without silently becoming verified facts.
- [ ] Confirmed project facts, not model guesses, govern Mermaid diagrams and image captions.
- [ ] Mermaid generation returns validated SVG/PNG preview and export assets; hostile Mermaid labels, scripts and malformed diagrams cannot execute in the browser.
- [ ] Diffusion images are distinctly labeled illustrative, approved as required, and never impersonate real student results.
- [ ] Real charts are plotted only from genuine provided datasets; original dataset/version and units remain traceable.
- [ ] Visual failure cannot erase text, completed chapters, quota, or progress; critical missing required figures block final approval until resolved.
- [ ] All 36 roles, the university builder, Hobby/Pro/Premium rules, adaptive questioning, voice, preview, and DOCX/PDF/LaTeX outputs remain covered by tests.

## Decisions still open — do not imply they are locked

Specific OTP vendor; payment provider and subscription renewal policy; voice STT/TTS providers; paid Tiptap pagination/conversion license; exact Next.js/vinext/React/Tiptap/Mermaid patches; whether a Mermaid API provides value; FLUX provider/model and pricing/terms; vision model and privacy controls; permitted upload types/sizes/counts and retention period; external plagiarism dataset/provider; clinical-sensitive upload policy; Cloudflare-to-Cloud Run secure ingress; whether to introduce Cloud Tasks initially and Pub/Sub only for actual fan-out; and whether visual/document workers need separate Cloud Run Jobs immediately. These choices must be evaluated and recorded as ADRs before production use.

**Verified source references (November 2026):** [Google Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service), [Mermaid security configuration](https://mermaid.js.org/config/usage), [Cloudflare AI FLUX.2 model listing](https://developers.cloudflare.com/ai/models/black-forest-labs/flux-2-pro-preview/). References confirm capability and security characteristics, not a commitment to commercial terms.

---

## Preserved v2.1 baseline — unchanged text, retained for audit

> Read v2.2 decisions above first. The following complete text is preserved to ensure that no earlier requirement, library choice or caveat is lost. Its original version labels and deployment diagrams are historical where explicitly superseded by v2.2.

# Acadence — Technology Stack & Feature Coverage v2.1

**Date:** 2026-11-11  
**Owner:** Acadence project  
**Status:** Architectural baseline. All previously selected decisions retained. Exact dependency patches and the listed conditional integrations must be resolved with installation/compatibility tests; untested combinations must not be represented as production-validated.

## Decision rules
- **SELECTED**: an agreed product/platform decision. Do not silently change.
- **ADD**: a recommended v2.1 implementation or engineering capability needed by the requirements.
- **VERIFY**: a selected direction requiring compatibility proof or a paid-license decision.
- **CONDITIONAL**: only add when the feature/use case requires it; not silently included as a dependency.
- **VERSION RULE**: choose stable compatible versions, pin *exact patch versions and transitive dependencies* in `pnpm-lock.yaml` and Python lockfile after integration tests. Do not invent a full exact version matrix without running the project.

## 1. Product invariants (do not omit)
1. Sign up/in with Google OAuth/OIDC or mobile OTP; all nonpublic pages and all privileged APIs protected.
2. One account per verified email; one account per verified phone; attempt one account per physical device, with explicit recognition that web browsers cannot guarantee unique physical-device identity and that anti-abuse controls require careful privacy treatment. Do not silently relax the business rule.
3. New account: Hobby trial, exactly one preview-only report up to 10 pages, no download. After consumption, check paid entitlement and otherwise show pricing.
4. Pro: one project, maximum 100 pages, DOCX and PDF downloads. Premium: two projects, each maximum 100 pages, DOCX, PDF, and LaTeX downloads. Enforce on the server, including API endpoints, file URLs, and job creation. Quota renewal period and plan transition/refund rules have not yet been defined.
5. Flexible support for any education, specialization and discipline: diploma, engineering, law, psychology, medicine, etc. Never force every project into a software report schema.
6. Collect academic level, degree, specialization, project title/description, known technologies or methodology, and highly detailed formatting requirements.
7. **Before adaptive questions**, student can choose/create a report template in a dedicated Template Builder tab. Provide professionally designed default university/style templates and a maximum of **three saved personal initial-page templates per user**.
8. Editor has independent draggable/editable page blocks; add, reorder, move, duplicate, remove, customize; cover, certificate, declaration, acknowledgement, abstract, TOC, chapter pages, bibliography, appendix, arbitrary custom pages; margins, page size, logos, signatures, headers/footers, page numbering, fonts, spacing, alignment, tables/images, etc. Preview updates while editing.
9. Selected preliminary-page template is merged with final report after generation, while document layout rules guide preview/generation from the beginning. Maintain versioned snapshot so edits to a reusable template don't retroactively corrupt an in-progress report.
10. AI first analyzes initial context; plans discipline-specific outline; identifies facts required by every section; runs gap analysis; asks ONLY missing, relevant, adaptive questions; persists every typed/spoken answer; clarifies contradictions or unknowns.
11. No fabricated project-specific technology, hardware, architecture, methodology, implementation, study population, test data, metrics or results. General-purpose academic prose may be AI-generated; evidence/citations, when needed, must be verified, not hallucinated.
12. Long-form reports primarily authored by LLMs (Claude, Groq-hosted models, OpenAI alternatives), **not** assembled chiefly from research papers. External source/RAG lookup is conditional for citations, authoritative fact checking or user-uploaded materials.
13. Review every generated section for coverage, internal duplication/repetition, natural academic style, coherence, factual consistency, verified citations and originality/plagiarism risks; trigger bounded targeted revisions. External plagiarism checking requires comparison corpus/license; no guarantee of 0% plagiarism or undetectability.
14. Visual robot/AI agent types questions and speaks them, can capture typed or spoken answers, stores them, explains current stage, and shows real job progress.
15. Live preview of formatted sections *during* report generation, reflecting the chosen template, with review/draft indicators; distinguish preview from final paginated export and verify parity.
16. Graceful error paths for offline client, connection loss, cancellation, timeout, external API failures, quota exhaustion, worker restarts, invalid output, model rate limits, safe resume, retries, deduplication and honest user-facing states.
17. Export permissions: Hobby none; Pro DOCX/PDF; Premium DOCX/PDF/LaTeX. Enforce against backdoor direct file access.

## 2. Frontend and hosting
| Choice | Status | Version / package direction | Responsibility / note |
|---|---|---|---|
| Next.js App Router | SELECTED/VERIFY | Next.js 16.x target, stable patch after vinext tests | Pages/routes, server rendering, metadata, public SEO and protected UI |
| React | SELECTED | Compatible stable React 19.x line; verify peer dependencies | UI rendering |
| TypeScript | SELECTED | Stable TypeScript line compatible with Next/ESLint; exact patch lock | Compile-time types |
| Tailwind CSS | SELECTED | 4.x target; verify component/plugin support | Design system styling |
| shadcn/ui | SELECTED | CLI-generated components; version-lock underlying Radix/other packages | Accessible UI primitives |
| Redux Toolkit | SELECTED as-needed | `@reduxjs/toolkit` | Shared client state, questionnaire/preview state where appropriate |
| RTK Query | SELECTED as-needed | Included in Redux Toolkit | API caching, invalidation, polling |
| React Hook Form + Zod | ADD | `react-hook-form`, `zod`, `@hookform/resolvers` | Input forms and client validation; backend remains authority |
| Cloudflare Workers | SELECTED | Workers | **Frontend hosting**, not Cloudflare Pages |
| vinext | VERIFY | Current compatible beta, not safe to declare production-approved yet | Next.js-on-Workers adapter; run compatibility and streaming/auth tests |
| Cloudflare build tooling | ADD | `wrangler` or adapter-documented CLI, according to chosen vinext version | Local preview, deploy, environment configuration |
| Browser testing | ADD | Playwright | Login, editor, preview, billing and recovery end-to-end tests |
| Unit testing | ADD | Vitest, React Testing Library | UI and component tests |

Node development runtime: Node.js 24 LTS is a conservative candidate; Node.js 26 is Active LTS as of the date above. Confirm vinext/Next.js/other toolchain compatibility before pinning. Use pnpm with a frozen lockfile for reproducible frontend builds.

## 3. University template designer and document preview
| Choice | Status | Responsibility / limitation |
|---|---|---|
| Tiptap 3 + ProseMirror | ADD | Rich editable text, tables, content schema, placeholders, formatting |
| dnd-kit | ADD | Drag/drop/reorder page block cards; inspect new `@dnd-kit/react` vs legacy packages before install |
| Custom page-block model | ADD | Stable page ID, type, ordering, per-page layout, components, placeholders |
| Template versioning/snapshots | ADD | Store max 3 user-created preliminary-page templates plus selected immutable report snapshot |
| Template library | ADD | Professionally designed university/style defaults; verify claimed institution formats |
| Editable placeholder binding | ADD | Project title/student/department/college/supervisor/year data mapped into layout |
| Pagination and page-break calculation | ADD/VERIFY | True A4/Letter layout, margins, long tables, headers/footers, page numbering; test against exports |
| Tiptap Pages | CONDITIONAL/PAID | Official pagination extension is Team-plan beta; evaluate budget and parity before purchase |
| Tiptap Conversion | CONDITIONAL/PAID | Paid DOCX/PDF conversion beta; not required if using own exporters |
| Asset editing | ADD | R2-backed logos, stamps/signatures, image dimensions and validation |
| Live rendering | ADD | Preview of canonical document, with draft/approved states |
| Rich page data constraints | ADD | Custom nodes for certificates, declaration, TOC, citations, bibliography, tables/figures, appendix |

Do not equate drag/drop or a browser page preview with a complete Word/LaTeX layout engine. Define the canonical content/layout format before building multiple exporters. For flowable chapter pages, preview pagination is calculated rather than assuming fixed one-page blocks.

## 4. Backend API and infrastructure
| Choice | Status | Version / responsibility |
|---|---|---|
| Python | SELECTED | 3.13 baseline; only advance after all packages pass tests |
| FastAPI | SELECTED | Current compatible stable with Pydantic 2; HTTP APIs |
| Pydantic | SELECTED | v2; DTOs, agent structured output, data contracts |
| SQLAlchemy | SELECTED | v2; relational ORM/queries |
| Alembic | SELECTED | DB schema migrations |
| PostgreSQL driver | ADD | psycopg 3 for LangGraph Postgres; use `psycopg` consistent with SQLAlchemy setup |
| FastAPI server | ADD | Uvicorn/ASGI | Serving Cloud Run API |
| Google Cloud Run Service | SELECTED | API deployment, auth/entitlement, progress, job creation |
| Google Cloud Run Jobs | SELECTED | Isolated long-running report-generation worker container |
| Docker | SELECTED | Reproducible API/worker images |
| Google Cloud Tasks | CONDITIONAL | Dispatch throttling, deferred job initiation, independent retries |
| Celery + Redis | CONDITIONAL, not default | Use only if Cloud Run Jobs cannot meet workflow requirements |
| SSE | ADD | Live progress/approved-section events; reconnect via cursor; polling fallback |
| REST JSON API | SELECTED | First-class user/project/plan/template/job endpoints |
| Idempotency and deduplication | ADD | Duplicate job requests, retries, exports, plan reservations |
| Recovery/reconciliation | ADD | Detect stalled jobs, retry/restore from durable checkpoints |

Cloud Run Jobs task timeout is configurable; default 10 minutes and can be extended for CPU tasks. Configure meaningful retry and concurrency limits. Job state and paid quota are durable in PostgreSQL, not in Redis alone.

## 5. Database, cache, files and vector support
| Choice | Status | Responsibility |
|---|---|---|
| Neon PostgreSQL | SELECTED | Durable relational state: users, sessions, plan ledger, templates, projects, answers, sections, jobs, evaluations |
| pgvector | SELECTED | Embeddings/similarity; use only for a justified query/search/repetition task |
| PostgreSQL full-text | ADD | Hybrid retrieval/keyword match where needed |
| SQLAlchemy + Alembic | SELECTED | Relational DB access/migrations |
| Upstash Redis | SELECTED as-needed | Cache, OTP throttling, hot progress/rate-limit hints, not source of truth |
| Cloudflare R2 | SELECTED | Uploads, template assets, exports, intermediate artifact files |
| Signed R2 URLs | ADD | Time-limited authorized upload/download; short-lived private access |
| Object retention policy | ADD | Lifecycle/cleanup, temporary files, versions and user deletion |
| DB connection management | ADD | Pooling suited to serverless concurrency; validate Neon settings |

Key schema families: users, identities, mobile_verifications, sessions, devices/abuse_signals, plan_catalog, subscriptions, entitlements, quota_ledger, projects, report_specs, initial_templates, template_versions, selected_template_snapshots, page_blocks, formatting_rules, outline_versions, required_fact_fields, known_facts, provenance, question_sessions, questions, answers, agents/conversation_events, report_jobs, job_attempts, section_drafts, quality_checks, source_records, claim_source_links, exports, model_usage, audit_events.

## 6. AI models, orchestration, tools and monitoring
| Choice | Status | Responsibility |
|---|---|---|
| Claude via Anthropic API | SELECTED candidate | Primary quality-writing model, only after objective evaluation |
| Groq-hosted inference | SELECTED candidate | Fast tasks/low-cost candidate, mindful of rate limits |
| OpenAI API | SELECTED alternative | Other model choice, voice model candidates |
| LangGraph | SELECTED | Explicit planner/questioner/writer/validator workflow |
| LangChain | SELECTED selective | Integrations for model/tool/retrieval where useful |
| LangSmith | SELECTED | Traces, experiments, prompt/evaluation comparisons |
| `langgraph-checkpoint-postgres` | ADD | Durable graph checkpoints and resume; evaluate setup, security settings |
| Pydantic structured outputs | SELECTED | Facts/outline/question/draft/review schemas |
| Prompt versioning | ADD | Prompts/config/model versions tied to each output |
| Model routing | ADD | Task-based model selection and vendor fallbacks based on tests |
| Cost/token accounting | ADD | Provider usage, cost per report/section, budgeting and quotas |
| Concurrency and retries | ADD | 429 backoff, jitter, retries bounded by error class |
| Eval datasets and quality gates | ADD | Reproducible acceptance criteria instead of subjective assumptions |

Logical workflow stages, not necessarily separate autonomous agents: intake -> template selection -> discipline/context analysis -> outline planner -> information requirement/gap analysis -> adaptive questions -> confirmed fact store -> section writing -> continuity/repetition review -> facts/citations/originality check -> bounded correction -> canonical assembly -> export. Cross-section summaries and approved facts persist throughout. For sensitive clinical/legal content, mark unsupported claims and require appropriate checking rather than fictionalizing actual results.

## 7. Content QA, verification and originality
- Global report outline, section objectives, word/length budgets, cross-section summaries, previously-covered-topic memory.
- Fixed schemas for student-confirmed facts vs AI-generated general explanations; preserve provenance.
- Gap-driven question selection; do not re-ask known answers; ask clarification for inconsistent claims.
- Deterministic validation of chapter coverage, page budgeting, repeated n-grams and export integrity.
- Semantic repetition checks via Voyage AI embeddings and pgvector when justified (Voyage 4 family candidate).
- LLM review for clarity, consistency, discipline fit, voice and academic quality; bounded targeted rewrites.
- Originality screening: internal duplication + external licensed similarity service **only after selecting a provider and eligible corpus**. Similarity is not a guarantee of plagiarism-free content; do not optimize for AI-detector evasion.
- Real citations only when backed by sources. Metadata and evidence validation as separate steps; no fake references.
- Optional research/verification: OpenAlex, Crossref, Semantic Scholar, arXiv, PubMed as discipline demands; document parsing PyMuPDF/Docling/OCR fallback if ingesting source PDFs; hybrid search, reranker (Voyage), authorized RAG.
- Citation formatting: Citation Style Language-compatible processor for APA/IEEE/MLA and institution-specific requirements.
- Policy for ambiguous/unknown results: user clarification, explicit limitation, or truthful blank; never fabricate tests, participants or measurements.

## 8. AI agent UI, voice, progress, and offline
| Choice | Status | Responsibility |
|---|---|---|
| Animated robot/agent interface | ADD | Visual conversational assistant and task narration |
| Text chat and questionnaire UI | ADD | Typed answers, edits, review, explicit confirmation |
| Speech-to-text | ADD / provider VERIFY | Speech recognition to text; maintain transcript and user corrections |
| Text-to-speech | ADD / provider VERIFY | Read questions, optional status narration |
| OpenAI Realtime | CONDITIONAL | Low-latency conversational audio if architecture/cost justify |
| Web Speech API | CONDITIONAL | Browser-dependent fallback or prototype; support varies |
| Conversation persistence | ADD | Questions, answers, corrections, stage transitions, timestamps |
| SSE event stream | ADD | Show stage, current section, approved content, percentage derived from actual tasks |
| Reconnect/polling fallback | ADD | Recover after network disconnect, refresh or dropped stream |
| Failure taxonomy | ADD | Rate limit, validation, no answer, auth expired, payment, timeout, worker crashes, external APIs |
| User controls | ADD | Resume, retry within bounds, cancel, human review/confirm; backend authority |

## 9. Authentication, device policy and security
- Google OAuth/OIDC with authorization code and validated identity tokens; mobile OTP provider to be selected after price/delivery comparison. No phone or email duplication: DB-level unique normalized identifiers.
- Backend-managed device/session registry, short-lived JWT access tokens, rotating revocable refresh tokens, secure HTTP-only cookies where appropriate, CSRF defenses, protected API endpoints and consistent Cloudflare/FastAPI CORS behavior.
- Device fingerprinting alone cannot guarantee one account per physical device in browsers; consider privacy-conscious risk signals, device tokens, abuse throttling, manual review/appeal. Business rule stays in scope, technical limitation must be communicated.
- OTP expiry and attempt limits, bot/abuse controls, enumeration-safe errors, rate limits, account recovery and verified linking of email/phone identities.
- Plan checks are server-side at creation, run, progress access, preview, and file export endpoints. Sign URLs only after entitlement check.
- Permissions per owner/tenant; users cannot read other users' project, document, answer or template records.
- Files: validate type, sanitize uploaded content, scan if necessary, size limits and safe R2 access; protect against prompt injection through any user/retrieved documents.
- Google Secret Manager/environment separation, least-privilege GCP identities, log redaction, encryption, audit logs, data retention/deletion, privacy and applicable academic/health data rules.

## 10. Plans, billing and quota semantics
- Hobby: auto-enrolled; 1 report up to 10 pages; preview only; after used and no subscription show pricing.
- Pro: 1 complete project up to 100 pages; DOCX and PDF.
- Premium: 2 complete projects up to 100 pages each; DOCX, PDF, LaTeX.
- Subscription gateway **UNDECIDED**; compare Razorpay/Stripe and local payment/tax/subscription needs. Require verified webhook signature, idempotent payment events, entitlement ledger, refund/cancellation/expiry handling.
- Implement a quota reservation at job start; settle it upon successful completion and define refunds/failed jobs so retries don't double-consume. Distinguish project count, report revision and export count.
- Open policy choices to finalize later: subscription term, renewal reset, upgrade/downgrade, whether multiple regenerated revisions consume quota, refunds, failed trials and post-expiry access.

## 11. Document representation and exports
- Canonical report tree contains preliminary page blocks, generated chapters, paragraphs, lists, tables, images, equations, figures, references/TOC, page-break directives and formatting tokens. This is the source for live preview and export.
- `python-docx`: DOCX, preserving editable styles and headers/footers as far as possible.
- ReportLab **or** an approved DOCX/HTML-to-PDF renderer: PDF, chosen after fidelity tests; do not run redundant full exporters without benefit.
- Tectonic/LaTeX engine: Premium LaTeX output, especially for equations; build structured LaTeX output rather than merely renaming a file.
- CSL-compatible citation formatter: institutional style support as appropriate.
- R2: final document and export versions; access gated by paid entitlements.
- Final TOC, page numbers, referenced figures/tables, cross-references and bibliography computed once final composition is known.
- Validate sample files by opening them and checking page breaks, text overflow, fonts, images, tables, chapter headings, appendix and template parity.
- 100-page requirement is a maximum; never pad a report with fabricated or repetitive content to hit 100 pages.

## 12. Monitoring, QA, operations and team practices
- Cursor AI editor; Cursor project rules and version-controlled requirements documents.
- Git + GitHub; GitHub Actions for CI/CD; Docker for service and worker images.
- Tests: pytest (FastAPI, agent and job logic), Ruff (Python lint/format), Pyright or mypy (types); Vitest + React Testing Library (UI), Playwright (full browser journeys), and integration tests for provider APIs.
- Google Cloud Logging/Monitoring for infra; LangSmith for LLM traces and evals; Sentry for frontend/backend errors; OpenTelemetry for tracing across requests/jobs.
- Metrics: job success, retry count, time per section, quality score by rubric, repeated-content rate, verified citation rate, cost tokens/provider/report, subscriptions, payment webhooks, export fidelity.
- Alerts for budget anomalies, quota abuse, high 429s, failed jobs, expired credentials and failed payments.
- Configuration: separated dev/staging/prod, per-service IAM, secrets, migration testing, backup/restore drills, dependency license/security scans, build reproducibility, ADR decisions.

## 13. Compatibility test gate before coding complete product
1. Create basic Next.js 16 app with Tailwind/shadcn, build and deploy on Cloudflare Workers using vinext; run its compatibility check. Test middleware/route guards, cookies, protected API proxy, SSE streaming, upload URLs and output size.
2. Create Tiptap + dnd-kit editor proof of concept with editable custom blocks, three-template limit and page reordering; test print pagination and fidelity for DOCX/PDF/LaTeX. Determine paid Pages/Conversion licensing or custom alternative.
3. Deploy FastAPI Python 3.13 to Cloud Run Service; trigger Cloud Run Job; persist progress and one chapter to Neon/R2; confirm retry/resume and cost.
4. LangGraph + `langgraph-checkpoint-postgres`: verify resume across container restarts, safe serialization, no duplicate paid quota or section writes.
5. OAuth/OTP login and session checks between Cloudflare and FastAPI with domain/cookie settings; confirm security and account uniqueness behavior.
6. End-to-end 5-10 page prototype across at least two very different disciplines; quality rubric, no invented project-specific facts, live preview and exports.
7. Freeze exact package patches and model IDs in dependency locks/config only after the above tests pass.

## 14. Do not silently add these
- Another autonomous-agent framework (CrewAI/AutoGen), separate vector DB (Pinecone/etc), general-purpose fine-tuning, multiple task queues, a paid plagiarism platform, paid Tiptap Pages/Conversion, or OpenAI Realtime voice without measured need, license and budget.
- No vendor is selected yet for SMS OTP, payments, external plagiarism database, default university template catalog or model-specific quality routes.

## Official reference links (verified 2026-11-11)
- Next.js support policy: https://nextjs.org/support-policy
- Cloudflare Workers + vinext Next.js: https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/
- Node release schedule: https://github.com/nodejs/Release
- Tiptap Pages paid beta: https://tiptap.dev/docs/pages/getting-started/overview
- Tiptap Conversion paid beta: https://tiptap.dev/docs/conversion/getting-started/overview
- Tiptap react package: https://www.npmjs.com/package/@tiptap/react
- dnd-kit current docs: https://github.com/clauderic/dnd-kit
- Cloud Run Jobs timeout: https://docs.cloud.google.com/run/docs/configuring/task-timeout
- Cloud Run Jobs retry/checkpointing: https://docs.cloud.google.com/run/docs/jobs-retries
- LangGraph PostgreSQL checkpoint: https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/README.md
- Voyage embedding docs: https://docs.voyageai.com/docs/embeddings
- Voyage reranker docs: https://docs.voyageai.com/docs/reranker
- Neon pgvector FAQ: https://github.com/neondatabase/website/blob/main/content/faqs/enable-pgvector-extension.md

**Reminder:** This document is the complete design baseline, not evidence that exact runtime/library compatibility, costs or every feature have been implemented. Keep this file in your Cursor repo; only revise decisions deliberately and increment the version.
