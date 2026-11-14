# Acadence — Development Roadmap v1.0

**Status:** Proposed execution baseline — planning complete, development not yet started.  
**Prepared:** 2026-11-12  
**Project:** Acadence (formerly AI Report Studio / AI Project Report)  
**Target environment:** Cursor AI editor, Git/GitHub monorepo, Next.js on Cloudflare Workers, Python/FastAPI services on Cloud Run.

> **Source-of-truth and change-control rule:** Read the three files below **before changing this roadmap or implementing a task**:
> - `docs/ACADENCE_TECH_STACK_V2_2.md`
> - `docs/ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`
> - `docs/ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`
>
> These architecture references take precedence over this execution plan on product behavior and technical boundaries. **No selected requirement, service, or agent responsibility may be silently removed.** Open provider, licensing, business-policy and exact-version choices remain OPEN until explicitly decided, tested, and recorded in an Architecture Decision Record (ADR). Historic material embedded inside the newer docs is retained for audit; **the new-version section at the top of each file takes precedence** over superseded older diagrams or counts.

## 1. Project definition and non-negotiable behavior

Acadence is a multi-disciplinary, voice-enabled, agentic academic report platform. AI primarily **writes original academic prose from confirmed student project details**; optional retrieval is for supporting references, factual verification and authorized inputs. AI must never manufacture the student's implementation, algorithms, methods, actual observations, participants, experimental measurements, clinical data or results. A central LangGraph workflow orchestrates 36 logical responsibilities, not 36 independently running LLMs. Nine independently deployable backend microservices share infrastructure with strict service-owned data boundaries.

**Must deliver and test:** Google login and mobile OTP; unique email/phone identities and the one-device account restriction objective with the unavoidable limits of browser identification; server-protected pages/APIs; Hobby **one** preview-only report of at most **10 pages** (no downloads), pricing after exhausted trial unless paid; Pro **one** project up to **100 pages**, DOCX/PDF; Premium **two** projects each up to **100 pages**, DOCX/PDF/LaTeX; independent university Template Builder tab with **three** saved personal initial-page templates maximum, defaults, drag/drop full page editing, snapshot and final assembly; institution-specific layouts; initial academic input; gap-driven adaptive voice/text questions; confirmed and versioned fact ledger; generated chapter writing with global memory; citation, similarity, factual, style and document quality gates; student image uploads/vision confirmation; Mermaid flowcharts/diagrams; clearly marked conceptual AI images; genuine-data charts; live formatted preview and progress; durable retries, interruptions and recovery; authorized private exports.

**Honesty guarantees:** Browser fingerprints cannot guarantee uniqueness of physical devices. A similarity score cannot prove zero plagiarism. LLM reviews cannot prove all claims correct. Independent services do not remove shared Neon/R2/network failure domains. Preview and DOCX/PDF/LaTeX cannot be assumed pixel-identical without rendering tests. Unknown or unavailable provider features must be marked pending, not described as implemented.

## 2. Architectural boundaries that will not change silently

| Deployable / component | Selected owner and runtime | Scope of data / responsibility |
|---|---|---|
| Frontend / BFF | Next.js App Router + TypeScript + Tailwind 4 + shadcn/ui + React, **Cloudflare Workers**, vinext compatibility gate | UI, public/authenticated routes, template editor, voice Mentor, SSE and preview; never direct DB/LLM admin credentials |
| 1. Auth Service | Python 3.13 + FastAPI on **Cloud Run Service**, schema `auth` | Verified identities, Google OIDC, mobile OTP verification, session/device policies, account recovery |
| 2. Billing Service | FastAPI, Cloud Run, schema `billing` | Provider-verified payments, subscriptions, Hobby/Pro/Premium entitlements, **authoritative quota reservation/settlement** |
| 3. Project Service | FastAPI, Cloud Run, schema `project` | Intake, projects, answers, confirmed facts/provenance, image-upload references and student confirmation |
| 4. Template Service | FastAPI, Cloud Run, schema `template` | Default templates, maximum 3 saved initial-page templates, page-block versions, immutable selected template snapshots |
| 5. AI Orchestration Service | FastAPI control plane, Cloud Run; **Cloud Run Job** for generation, schema `orchestration` | LangGraph, chapter planning/writing, questions, Mentor reasoning, checkpoint orchestration, job state, progress, retries |
| 6. Quality Service | FastAPI, Cloud Run, schema `quality` | Citation/source checks, consistency/repetition, originality screening, fact verification and quality verdicts |
| 7. Visual AI Service | FastAPI, Cloud Run; optional heavy-job worker, schema `visual` | Vision observations, validated Mermaid render, conceptual image provider, charts, visual asset provenance |
| 8. Document Service | FastAPI, Cloud Run; **Cloud Run Job** for heavy exports, schema `document` | Canonical report tree, preview, pagination and export quality, DOCX/PDF/LaTeX, private R2 output |
| 9. Notification Service | FastAPI, Cloud Run, schema `notification` | OTP dispatch, payment/report/recovery notices and delivery events; not authority on authentication/payment |
| Shared infrastructure | Neon Postgres, Cloudflare R2, Upstash Redis as needed, LangSmith, Google logging/monitoring, Sentry, OpenTelemetry | Independent database roles/schemas, narrow R2/IAM policies, trace IDs and secure secrets |

**Internal communication:** bounded authenticated REST for immediate reads/commands; Cloud Tasks **only if** needed for one-recipient asynchronous dispatch, Pub/Sub **only if** multi-subscriber fanout is justified; durable outbox/event inbox when cross-service state needs atomic delivery semantics. No other service writes another owner's schema. Cross-service requests use typed API contracts, identity, scope, trace and idempotency keys. Only Billing owns quota ledger; only Project confirms student facts; only Template owns approved template snapshots; only Quality approves section quality; only Document signs final export grants after checking Billing.

## 3. Completion rules for every work item

- [ ] Requirements and acceptance tests linked to a numbered roadmap task; no feature is marked done because the UI merely exists.
- [ ] One explicit owning service and one versioned request/response or event contract.
- [ ] Validated Pydantic request/response models and generated client contracts (where applicable).
- [ ] Authentication, authorization, tenant isolation, limits, idempotency and error handling implemented at trust boundaries.
- [ ] Unit, integration, service contract, cross-service, failure/retry and applicable end-to-end tests pass in CI.
- [ ] Migrations, logs/traces/metrics, local setup, health checks and rollback path documented.
- [ ] Sensitive project or uploaded media not leaked into logs, evaluation traces or external model APIs.
- [ ] Actual demos and traces prove the feature, not model promises or mocks alone.
- [ ] Any deviation from selected architecture recorded as an ADR and approved before implementation.

**Status vocabulary for tracking:** `BACKLOG`, `IN_PROGRESS`, `BLOCKED`, `READY_FOR_TEST`, `VERIFIED`, `DEFERRED_BY_APPROVED_DECISION`. A deferred feature still appears in requirement coverage; it is not silently deleted. The phases below are dependencies, **not time estimates**, and parallel work is allowed where contracts and facts are stable.

## 4. Dependency-ordered milestones and acceptance gates

### Phase P00 — Architecture guardrails and high-risk feasibility spikes

**Purpose:** Confirm fragile technology combinations before expensive implementation. **Depends on:** three architecture docs only.

- [ ] Copy all three latest files into `/docs` and establish explicit version precedence; set Cursor project rules to read them first.
- [ ] ADR-001: verify Next.js 16 + current compatible vinext + Cloudflare Workers in a real deployment; evaluate React/Tailwind/shadcn/RTK Query, streaming, auth cookies and image/static features; pin exact working versions afterward.
- [ ] ADR-002: prove Cloudflare-to-Cloud Run ingress authentication without shipping private GCP keys to browser/Worker; verify service-to-service IAM for private Cloud Run calls.
- [ ] ADR-003: prototype Tiptap 3 + ProseMirror + dnd-kit: one moveable initial page, headers/footers, automatic chapter pagination; determine custom layout engine versus Tiptap Pages paid license.
- [ ] ADR-004: render the **same canonical sample** into browser preview, DOCX, PDF and LaTeX; identify unsupported styles/page differences before implementing the full editor.
- [ ] ADR-005: test a LangGraph Postgres checkpoint and Cloud Run Job handoff that exits at a human-input pause, then resumes in a **new execution** after an answer (no idle billable job waiting).
- [ ] ADR-006: verify Neon separate schema permissions, per-service credentials/migrations, serverless pooling and R2 private signed upload/download grants.
- [ ] ADR-007: Mermaid strict renderer and SVG sanitization spike; image-provider/vision-provider technical and privacy feasibility, with FLUX.2 **candidate**, not hard-coded.
- [ ] Create decision backlog for OTP provider, payment gateway, renewals/refunds, plagiarism licensed provider/corpus, clinical-sensitive uploads, speech STT/TTS, PDF conversion, exact model selection and retention.

**Gate P00:** Demonstrable proof-of-concept deployments and documented ADRs for blocking risks; unresolved choices marked as blockers for **their dependent feature**, not invented defaults.

### Phase P01 — Cursor monorepo, microservice skeleton and CI foundations

**Depends on:** P00 compatible toolchains. **Owner:** infrastructure and all nine service maintainers.

- [ ] Initialize `apps/frontend`, all nine `services/*`, `workers/report-generation`, `workers/document-export`, optional `workers/visual-processing`, `packages/api-contracts`, `packages/event-contracts`, `infrastructure`, `tests`, `docs/adr`.
- [ ] Add pnpm frozen lockfile and Python pinned lock(s), Docker multi-stage images, Ruff/Pyright/pytest/Vitest/RTL/Playwright standards.
- [ ] Independently build, start, health-check, stop, deploy and roll back every service without changing the deployment of another; service-specific GitHub Actions path filters.
- [ ] Add `healthz`, `readyz`, structured errors, request correlation/trace IDs, OpenAPI schema checks and per-service configuration validation.
- [ ] Create dev/staging/prod boundaries, IAM service accounts, secrets handling, R2 buckets/prefixes, database roles, resource/concurrency limits, budget alerts and observability foundation.
- [ ] Design exact synchronous interservice contracts, auth headers/scopes, idempotency key semantics and versioning; contract tests fail on breaking changes.
- [ ] Add a minimal Cloudflare Workers frontend that successfully calls the authorized Auth or Project API through the verified ingress method.

**Gate P01:** Nine independently deployable **empty/skeleton services**, not nine fully built products; only the test frontend endpoint reaches a properly authenticated backend; cross-service permission tests pass.

The remaining P01 execution gates and required evidence are consolidated in the [P01 remaining execution checklist](./runbooks/P01_REMAINING_EXECUTION_CHECKLIST.md). The Auth runbook, ingress ADR, and Project fact-snapshot contract remain their respective sources of truth.

### Phase P02 — Service-owned persistence, audit and event patterns

**Depends on:** P01. **Owners:** each service; platform/infrastructure.

- [ ] Build nine service-owned PostgreSQL schemas (`auth`, `billing`, `project`, `template`, `orchestration`, `quality`, `visual`, `document`, `notification`), service-specific Alembic migrations and least-privilege DB users.
- [ ] Create stable user/project/report identifiers without allowing cross-service ORM ownership; resolve reference lookup through APIs or verified event projections.
- [ ] Add versioned API/event schemas, access/audit logs, outbox/inbox and deduplication only where asynchronous cross-service guarantees are required.
- [ ] Add document/R2 metadata versioning, checksum, signed URLs, immutable version references, cleanup/deletion and access logging.
- [ ] Add durable job ledger, attempt history, progress event sequence, section version and checkpoint reference entities in orchestration schema.
- [ ] Define ownership, retention and backup/restore drills; prove service A cannot insert/update service B's table.

**Gate P02:** Migrations work from an empty database, can be rolled forward independently, owner roles cannot cross-write, secrets are not stored in code, backups/restores are exercised.

Local schema/role/baseline verification and remaining P02 work are recorded in the [P02 database foundation runbook](./runbooks/P02_DATABASE_FOUNDATION.md); this evidence does not complete the P02 gate.

### Phase P03 — Authentication, route protection and notification foundation

**Depends on:** P01–P02. **Owners:** Auth (#2), Notification (#5), Safety guard (#31), frontend.

- [ ] Google OIDC signup/login and secure verified identity linking; verified phone OTP request, expiry, attempt limits, resend limits, verification, account recovery and notification dispatch.
- [ ] Normalize and uniquely constrain verified email and phone; prevent duplicate signup across devices and handle existing-account login and Google/phone linking without bypass.
- [ ] Implement one-account-per-device risk signals, revocable device/session registration, privacy limits and support appeal; document why a browser cannot guarantee permanent physical device identity.
- [ ] JWT short-lived access, rotating revocable refresh tokens, protected pages/server APIs, CORS/CSRF design, device/session revoke and logout.
- [ ] Apply resource ownership validation to every service and never trust frontend plan/user flags.
- [ ] Deliver fully tested public vs protected routes (signup/login/pricing public as explicitly designated; project/template/report private).

**Gate P03:** Google and OTP pass signup/login/recovery tests, duplicate email/phone is blocked at DB boundary, expired/revoked sessions rejected, one user cannot fetch another user's data.

### Phase P04 — Pricing, payment, quotas and entitlement lifecycle

**Depends on:** P03 and payment-provider ADR. **Owners:** Billing (#3, #4, #30 quota half), Notification, frontend.

- [ ] Build plans with immutable entitlements: Hobby `1 report, max_pages=10, downloads=[]`; Pro `1 project, max_pages=100, exports=[docx,pdf]`; Premium `2 projects, max_pages=100 each, exports=[docx,pdf,latex]`.
- [ ] Define billing term and reset/upgrade/downgrade/refund/cancellation/failed-job/revision policies in approved ADR **before implementing real commercial charges**.
- [ ] Implement payment checkout, verified webhook signature and replay protection; payment event ledger, subscription status, expiration and refunds.
- [ ] Implement transactional quota reservation/settlement and idempotent authorization; never charge/deduct twice when the user double-clicks or a job retries.
- [ ] After consumed Hobby and no active paid plan, route to pricing; server rejects new paid generation and direct file download bypass.
- [ ] Implement pricing pages and plan status UI, including failed payment/retry states and no accidental paid access on gateway downtime.

**Gate P04:** Concurrent-generation race tests, repeated webhook events, payment outage and direct-download bypass tests prove correct entitlements; Hobby cannot download anything.

### Phase P05 — Canonical document model, university template builder and preview proof

**Depends on:** P00 rendering ADR, P02–P04. **Owners:** Template (#6), Document (#18, #29), frontend.

- [ ] Define a versioned canonical document tree: page/document blocks, text, lists, tables, figures, formula/equation, TOC, references, appendix, page-break directives, layout tokens and placeholders.
- [ ] Implement default university/report-style templates with attribution and verification of any institution-specific claims; build the **separate Template Builder tab** before adaptive AI questions.
- [ ] Build Tiptap/ProseMirror content editing plus dnd-kit independent initial-page cards: add/insert anywhere, drag/reorder, duplicate, delete, edit and reset.
- [ ] Support cover, certificate, declaration, acknowledgement, abstract, TOC, chapter layout, bibliography, appendix and arbitrary custom page blocks.
- [ ] Support fonts, typography, alignment, page size/margins, spacing, page numbers, headers/footers, university logos, signatures, borders, assets, dynamic student/college/supervisor/project placeholders.
- [ ] Enforce max **three saved personal initial-page templates** per user, not three pages; allow selecting one default/personal version and saving immutable per-project snapshot.
- [ ] Build instant visual preview and first pagination engine, including flowable chapter pages and TOC placeholder; retain export parity test suite for DOCX/PDF/LaTeX.
- [ ] Make formatting rules available as immutable references to later AI planning and report export, without allowing AI to modify an approved template silently.

**Gate P05:** Two students create distinct, correctly isolated templates; user creates exactly 3 personal templates, fourth rejected; drag/drop and snapshot survive reload; preliminary page + sample generated chapter export visually compared to preview.

### Phase P06 — Project intake, student files and confirmed fact ledger

**Depends on:** P03 and P05. **Owners:** Project (#24), Visual (#34, #36 ingestion), Safety (#31), frontend.

- [ ] Build discipline-neutral intake for education/degree/specialization, project title/description, known technologies, methodology, constraints, formatting and initial user goals.
- [ ] Associate selected template snapshot with project before adaptive AI questions begin; require server-side ownership/plan checks.
- [ ] Define `known_fact`, `provenance`, `candidate_fact`, `fact_conflict`, `confirmation_state`, versions and correction/invalidation semantics.
- [ ] Implement secured student upload at intake and during questions: actual screenshots, prototype photos, diagram samples, layout references, verified data charts, optional report figures.
- [ ] Sign constrained private R2 upload intents, verify actual MIME/signature/size/dimensions/pixel count, scan or reject risky content, remove sensitive EXIF/GPS as appropriate, restrict SVG/active content; track consent/rights/retention/withdrawal.
- [ ] Vision analyzes uploaded image as **candidate observation** only, records source image/region/uncertainty; ask student to confirm before promoting project-specific facts in Project Service.
- [ ] Require additional privacy/legal rules before clinical/patient/participant material reaches external model providers; provide a non-upload path.
- [ ] Add project changes that mark dependent questions, chapters and diagrams stale when confirmed facts change.

**Gate P06:** User can create and revisit project, upload approved formats privately, correct image interpretations and see provenance; unconfirmed vision findings never become writer facts; malicious/oversized cross-tenant uploads fail safely.

### Phase P07 — Discipline-aware planning, adaptive questioning and AI Mentor text

**Depends on:** P06; model-provider/prompt evaluation baseline. **Owners:** AI #1, #7, #8, #9, #25, #23; Project #24.

- [ ] Implement Pydantic-typed `ProjectBlueprint`, `Outline`, `SectionObjectives`, `RequiredFact`, `GapResult`, `QuestionIntent`, `AnswerCandidate`, `ConfirmedFactSnapshot` schemas.
- [ ] LangGraph Project Analysis consumes education/title/details + confirmed facts and creates context; Outline Planner chooses chapters dynamically for diploma, software, law, psychology, MBBS and other disciplines.
- [ ] Allocate realistic topic/length budgets; pages are upper bounds verified in renderer, never justification for padded/repeated text.
- [ ] Gap Analyzer compares fact requirements with confirmed values, suppresses already-answered questions and asks only meaningful missing information.
- [ ] AI Mentor renders student-friendly typed questions; Answer Interpreter extracts candidate values, handles unknown/skipped/conflicting answers and requests clarification.
- [ ] All question, answer, edits and confirmations persist in Project; no AI node gets permission to silently overwrite canonical facts.
- [ ] Pause LangGraph for human input, checkpoint, **exit Cloud Run Job if any job was started**, resume in a new execution only after authorized answer submission.
- [ ] Create eval cases for software, law, psychology, medicine, diploma, multi-disciplinary projects, ambiguous inputs and explicitly missing methodologies/results.

**Gate P07:** Same facts never trigger duplicate questions; wrong-discipline template questions are absent; missing algorithm/results remain unknown, not invented; sessions survive refresh and graph pause/resume tests.

### Phase P08 — Durable generation worker and first complete text report slice

**Depends on:** P07; job architecture and SSE proof from P00–P02. **Owners:** AI Orchestration (#12, #20–23, #28, job half of #30), Project, Billing, Document.

- [ ] Define job state machine (created/reserved/planning/waiting_user/queued/running/reviewing/assembling/completed/failed/cancelled) and allowed transitions.
- [ ] Start Cloud Run Jobs from authorized orchestration control plane; persist job IDs, checkpoint IDs, input/template/fact versions, model versions, token usage, deadlines and idempotency keys.
- [ ] Build structured chapter drafting from confirmed facts and approved outline, plus cross-section memory of topic coverage and chapter summaries; model routing among Claude/Groq/OpenAI after measured quality/cost tests.
- [ ] Save each draft and approved section separately; prevent stale output overwriting newer project facts; limit concurrency and rate, handle provider 429 and transient errors with bounds.
- [ ] Implement real progress event log, SSE IDs, reconnection, polling fallback, accurate statuses and partial formatted preview with `draft` vs `approved` markers.
- [ ] Implement checkpoint, cancellation, timeout handling, worker-restart recovery, orphan job reconciliation and quota settlement rules; do not keep a job idle while waiting for student answers.
- [ ] Produce the **first end-to-end report slice**: login → plan → template → intake → questions → two well-grounded chapters → checkpoint → preview → safe completion (exports handled in P11).

**Gate P08:** Worker crash mid-report resumes without losing or duplicating approved chapters, repeated clicks don't create multiple quota reservations, student can reconnect to same progress, no unsupported project-specific assertions in sample.

### Phase P09 — Full content-quality, originality and citation pipeline

**Depends on:** P08. **Owners:** Quality (#10, #11, #13–16, #26–27), AI (#17, #28), LangSmith.

- [ ] Add deterministic coverage/schema/repetition checks, n-gram overlap, internal cross-section comparison and optional Voyage embeddings/pgvector semantic similarity.
- [ ] Fact Validation compares every project-specific claim to confirmed fact IDs and flags contradictions, invented algorithms/hardware/results and unsupported statistics.
- [ ] Optional research lookup uses OpenAlex/Crossref/Semantic Scholar/arXiv/PubMed as appropriate, authorized hybrid retrieval/rerank, verified metadata + claim-evidence links; no invented DOI or bibliography.
- [ ] Keep Citation Agent separate from originality/plagiarism review. Choose a licensed plagiarism provider/corpus when external similarity coverage is a contract requirement; never claim a perfect or 0% plagiarism guarantee.
- [ ] Consistency Reviewer checks terminology, duplicated explanations, chapter overlap and missing section responsibilities.
- [ ] Style editor improves natural academic readability, **not AI-detector evasion**, preserving facts/citations; run the factual validator again **after** style edits.
- [ ] Quality Gate returns typed `approved`, `revise`, `needs_student_input`, `blocked` with explicit reasons. Bound revisions, escalate unresolved contradictions to student, version the approval against fact/section snapshots.
- [ ] Build LangSmith evaluation dataset with real anonymized examples across disciplines and release gates for regression in factual accuracy, repetition, citations, coverage and cost.

**Gate P09:** Deliberately introduced fake database/DOI/measurement is caught; post-style factual drift caught; bounded revision doesn't loop indefinitely; mandatory failed plagiarism/citation review cannot be reported as passed.

### Phase P10 — Diagram generation, image understanding, AI illustrations and charts

**Depends on:** P06, P08–P09; Mermaid and model/provider ADRs. **Owners:** #32–#36 Visual/AI, Quality, Project, Document.

- [ ] #32 generates typed `DiagramSpec` from confirmed fact IDs for flowcharts, ER, architecture, sequence, state, class and other supported structured figures; missing topology triggers a student question.
- [ ] #33 validates factual references/diagram schema, compiles pinned Mermaid with strict security, sanitizes SVG, generates tested preview SVG and export-compatible SVG/PNG, rejects malicious labels and links.
- [ ] #34 vision observations stay candidate facts until confirmed through Project; include figure relevance, student correction and privacy safeguards.
- [ ] #35 conceptual illustration uses a provider-neutral adapter (evaluate FLUX.2 Cloudflare AI, BFL/fal/Stability or alternatives), stores model/prompt/cost and always labels output as AI-generated illustrative—not actual evidence.
- [ ] Real-data graphs are produced with Matplotlib/Plotly from student-supplied verified datasets including units and provenance, not invented numbers.
- [ ] #36 registers source rights, approval, asset origin/type, content hash, captions, alt text, intended section, version, private R2 reference, figure numbering and replacement history.
- [ ] Quality + Document verify that asset caption matches real confirmed project details, that unlicensed/missing visuals are rejected, and mandatory diagrams can block completion while optional art failure doesn't erase the report.

**Gate P10:** Mermaid hostile code fails safely, diagrams do not invent components, actual screenshot vs AI illustration never confused, image provider outage doesn't corrupt written chapters, figures survive final exports.

### Phase P11 — Full live preview, document assembly and plan-based exports

**Depends on:** P05, P08–P10. **Owners:** Document (#18, #19, #29), Template, Billing, Quality.

- [ ] Assemble one canonical report tree from immutable selected preliminary template, approved sections, citations, verified figures, TOC, bibliography, appendix and page layout tokens.
- [ ] Render progressively updated, formatted preview while report is being generated; highlight unapproved drafts separately and update on true section/version events.
- [ ] Implement page numbering, header/footer variants, images/figure tables, captions, TOC/reference updates, equations and supported academic layout settings.
- [ ] Export DOCX with python-docx; PDF through ReportLab **or** tested document conversion; Premium LaTeX via Tectonic and a real LaTeX source file. No fake `.tex` export, no mismatched proprietary only-in-preview document model.
- [ ] Version completed exports in R2; validate page counts **after rendering** and enforce 10/100-page maximum without filler. Flag overflow and request controlled revision or layout adjustments with user approval as appropriate.
- [ ] Verify preview/export page parity on representative college templates and real uploaded figures, clearly document remaining platform differences.
- [ ] Download endpoint verifies owner/active entitlement/format **at request time** and returns short-lived grant only for permitted formats. Hobby never exports; Pro DOCX/PDF; Premium DOCX/PDF/LaTeX.

**Gate P11:** Institution sample templates compare acceptably, no missing preliminary pages/figure/citations, final page count meets limits, Hobby direct R2 and API bypass blocked, outputs open correctly in target tools.

### Phase P12 — Voice-enabled robot and accessible conversational experience

**Depends on:** P07–P08; STT/TTS ADR. **Owners:** frontend, AI Mentor (#1), notification, orchestrator.

- [ ] Implement animated robot avatar, current verified stage narration, typed message stream, clear thinking/waiting/retrying/error states, user controls.
- [ ] Integrate speech-to-text and text-to-speech, allowing student voice or text input; user reviews/corrects transcript before important facts become confirmed.
- [ ] Select STT/TTS provider based on quality, India language support as applicable, privacy, mobile-browser permissions, latency and cost; OpenAI Realtime/Web Speech are **conditional**, not locked.
- [ ] On microphone denial, TTS failure, network disconnect or poor transcription, fall back to typed Q&A without losing question state.
- [ ] Narrate only real persisted progress events and never claim the system verified a citation/payment until the relevant service returns a confirmed result.
- [ ] Add keyboard accessibility, screen reader labels, reduced-motion option and responsive mobile interface.

**Gate P12:** Real voice round-trip creates an answer in project state after confirmation; fallback text succeeds when voice unavailable; no phantom progress announcements; mobile tests pass.

### Phase P13 — Integration, security, isolation, resilience and observability

**Depends on:** P01–P12. **Owners:** all services; infrastructure and security.

- [ ] Verify nine independent deploy/rollback paths, schema isolation, Cloud Run IAM internal identity, verified Cloudflare ingress, tenant isolation, session revocation and signed R2 URLs.
- [ ] End-to-end tests for cross-service workflows, contract breaking changes, duplicate webhooks, double generation clicks, stale facts, broken images, retry storms, cancellation and export entitlements.
- [ ] Fault-injection: deliberately break Auth, Billing, Quality, Visual, Document, Notification, DB, R2, Cloud Run Job and model providers; ensure fail-closed on access/payment and graceful degradation on optional features.
- [ ] Introduce Cloud Tasks only for required one-to-one async dispatch and Pub/Sub only if fan-out is proven; ensure transactional outbox/inbox/dedup, dead letters and reconciliation.
- [ ] Apply security headers, CSRF/CORS, file malware handling, SVG/XSS sanitization, LLM prompt-injection defenses, PII redaction, access/audit and retention/deletion controls including clinical/sensitive data rules.
- [ ] Trace frontend request → BFF → service → LangGraph → worker → Quality/Visual/Document using OpenTelemetry, Sentry, Cloud Logging/Monitoring and LangSmith without exposing private student media/answers.
- [ ] Test load, runaway model spend safeguards, concurrency, serverless connection exhaustion, 429 throttling, job timeout/cost tracking, backup/restore and production alarms.

**Gate P13:** Passing security/isolation/resilience test suite with recorded evidence and remedied high-risk issues; measured spending and performance within approved budget thresholds.

### Phase P14 — Staged release and operations handover

**Depends on:** P13. **Owners:** product and all services.

- [ ] Finalize commercial/provider/privacy/retention and support/appeal policies; publish clear AI-assisted authoring and academic-integrity disclosures.
- [ ] Set rollout stages (internal test → limited cohort → production), rollback procedure, incident playbooks and on-call ownership.
- [ ] Run complete real-project acceptance across software, law, psychology, clinical/medical with privacy guardrails, diploma and other disciplines; validate source-grounding, template fidelity, adaptive questions, diagrams and figures.
- [ ] Confirm Hobby/Pro/Premium end-to-end with real provider sandbox payments, quotas, allowed exports, finished report notifications and safe retries.
- [ ] Verify cost/quality metrics, actual document page counts, user-visible progress and recovery behavior; no unresolved critical safety/privacy bugs.
- [ ] Mark the entire roadmap `VERIFIED` **only after** acceptance evidence and review; otherwise record remaining gates honestly.

**Gate P14:** Release candidate signed off on requirements traceability, quality, security, finances, operational recovery and architecture compatibility.

## 5. Responsibility coverage: all 36 IDs (none omitted)

| Role ID | Responsibility | Owning service | First phase / completion focus |
|---:|---|---|---|
| 1 | AI Mentor (visible voice/text agent) | AI Orchestration + frontend | P07 text, P12 voice |
| 2 | Session Guard | Auth | P03 |
| 3 | Subscription Service | Billing | P04 |
| 4 | Payment Service | Billing | P04 |
| 5 | Notification Service | Notification | P03 OTP, P04 billing, P14 completion |
| 6 | Template Architect | Template | P05 |
| 7 | Project Analysis | AI Orchestration | P07 |
| 8 | Outline Planner | AI Orchestration | P07 |
| 9 | Gap Analysis | AI Orchestration | P07 |
| 10 | Hybrid Retrieval (conditional) | Quality | P09 |
| 11 | Reranker (conditional) | Quality | P09 |
| 12 | Chapter Writer | AI Orchestration | P08 |
| 13 | Citation Agent | Quality | P09 |
| 14 | Consistency Reviewer | Quality | P09 |
| 15 | Plagiarism Review | Quality | P09 |
| 16 | Fact Validation | Quality | P09, post-edit |
| 17 | AI Content Humanizer / Style Editor | AI Orchestration | P09 |
| 18 | Document Formatter | Document | P05 model, P11 exports |
| 19 | Export Manager | Document | P11 |
| 20 | Recovery Service | AI Orchestration | P08, P13 failure tests |
| 21 | Retry Service | AI Orchestration | P08, P13 |
| 22 | Progress Service | AI Orchestration | P08 SSE and polling |
| 23 | Workflow Orchestrator | AI Orchestration | P07–P08 |
| 24 | Project Fact & Provenance Manager | Project | P06 |
| 25 | Answer Interpreter & Clarifier | AI Orchestration | P07 |
| 26 | Research Source Verifier (conditional) | Quality | P09 |
| 27 | Section Quality Gate | Quality | P09 |
| 28 | Global Report Memory Manager | AI Orchestration | P08–P09 |
| 29 | Layout Validation Engine | Document | P05 preview, P11 export |
| 30 | Job & Quota Coordinator — split ownership | Billing quota + AI job orchestration | P04, P08 |
| 31 | Safety & Policy Guard (cross-cutting) | All services and gateway | P01 onward |
| 32 | Diagram Generation Agent | AI Orchestration with Visual | P10 |
| 33 | Diagram Validation & Rendering Service | Visual AI | P10 |
| 34 | Image Understanding Agent | Visual AI; Project confirms | P06 ingestion, P10 expanded |
| 35 | AI Image Generation Agent | Visual AI | P10 |
| 36 | Visual Asset & Figure Manager | Visual AI; Document placement | P06 upload, P10–P11 assets |

**Audit invariant:** role IDs are exactly **1–36**; 10 AI roles, 9 hybrid roles, 17 deterministic services. Some are conditional at runtime, but **all are accounted for** in design, contracts, tests and responsible ownership.

## 6. Complete requirement-to-phase traceability

| ID | Required behavior / policy | Phase(s) | Must-pass acceptance |
|---|---|---|---|
| R01 | Google OIDC signup/login | P03 | Verified login, link, logout and recovery |
| R02 | Mobile OTP signup/login | P03 | Secure OTP expiry, delivery, attempt and resend limits |
| R03 | One account per verified email/number; device goal with caveat | P03 | DB uniqueness; abuse controls, appeal, no false guarantee |
| R04 | Protect private pages and every privileged API | P03, P13 | Unauthorized and cross-tenant requests rejected |
| R05 | Hobby one report ≤10 pages, preview only | P04, P11 | Quota and every download route blocked |
| R06 | After Hobby used and no subscription show pricing | P04 | Redirect and server rejection |
| R07 | Pro one ≤100-page project, DOCX/PDF | P04, P11 | Quota, formats, page count enforced |
| R08 | Premium two ≤100-page projects, DOCX/PDF/LaTeX | P04, P11 | Both project quotas/exports enforced |
| R09 | Verified payments, renewals, cancellation, refunds | P04 | Replay/double-spend tests; policies documented |
| R10 | Project intake: education, specialization, title, description, tech/methods | P06 | Discipline-neutral typed intake and persistence |
| R11 | Support software, engineering, diploma, LLB, Psychology, MBBS and others | P07, P14 | Diverse real-case evaluations |
| R12 | Dedicated university Template Builder tab | P05 | Separate tab before adaptive questions |
| R13 | Professionally designed default institution/style templates | P05 | Default library and accurate claims |
| R14 | Max 3 personal saved **initial-page templates**, not max pages | P05 | Fourth custom template rejected, many pages allowed |
| R15 | Custom initial page blocks add/reorder/duplicate/delete/insert anywhere | P05 | Editor persistence and drag tests |
| R16 | Cover, certificate, declaration, acknowledgements, abstract, TOC, chapters, references, appendix, custom | P05, P11 | All supported structures render/export |
| R17 | Margins, fonts, headers/footers, page numbers, logo, signatures, spacing, tables/figures | P05, P11 | Style/layout parity visual tests |
| R18 | Choose template before adaptive Qs, immutable snapshot | P05–P07 | Selected version never silently changes |
| R19 | Merge preliminary pages with generated report after generation | P11 | Final assembly retains order and dynamic TOC |
| R20 | AI project analysis, discipline-aware outline and per-section requirements | P07 | Typed blueprint and objectives with no fixed universal outline |
| R21 | Gap-driven relevant adaptive questions, no re-asking known facts | P07 | Questions bound to missing fact IDs |
| R22 | Text and spoken answers saved, clarifications and corrections | P07, P12 | Confirmed structured answers persist and resume |
| R23 | No fabricated project-specific technologies/methods/participants/results | P06–P10 | Negative tests detect unsupported statements |
| R24 | Primarily LLM-authored prose; selective RAG for factual evidence | P08–P09 | Evidence-backed when necessary, no blind paper copying |
| R25 | Global report memory avoids repeated content | P08–P09 | Repetition regression tests |
| R26 | Citation checking separate from originality | P09 | Invalid DOI/unsupported source fails quality gate |
| R27 | Plagiarism/originality review + targeted rewrite, truthful limitations | P09 | Internal/external-as-licensed checks with explicit outcomes |
| R28 | Natural, coherent academic writing with post-style fact recheck | P09 | Style drift caught |
| R29 | LangGraph agents shared state, Pydantic contracts, checkpoints | P07–P09 | Pause/resume, stale version and unauthorized write tests |
| R30 | Live formatted preview **during** generation | P05, P08, P11 | Draft/approved sections appear incrementally |
| R31 | Visible robot types/speaks and listens; accessible text fallback | P07, P12 | Full turn and fallback test |
| R32 | Honest real progress and explanations, SSE/polling reconnect | P08, P12 | Sequence/replay/refresh tests |
| R33 | Internet disconnect, interruption, API error, 429, retries, auto resume, cancellation | P08, P13 | Failure-injection and no duplicate work |
| R34 | Student image upload with project details and questions | P06 | Private, verified, persistently associated uploads |
| R35 | Image understanding observations require student fact confirmation | P06, P10 | Candidates never silently verified |
| R36 | Mermaid diagrams, flowcharts/architecture/ER/sequence from confirmed facts | P10 | Safe SVG/PNG, semantic checks, supported diagram types |
| R37 | Diffusion-based conceptual illustrations, explicitly labeled | P10 | No fake real screenshots/experiments |
| R38 | Chart generation only from genuine verified numeric data | P10 | Provenance and units checked |
| R39 | Versioned figure manager captions, rights, alt text and placement | P10–P11 | Export matches approved figure records |
| R40 | Canonical document model and correct DOCX/PDF/LaTeX per plan | P05, P11 | All formats, rendering tests and entitlement guards |
| R41 | Nine independently deployable microservices | P01, P13 | Independent health, rollbacks and isolation |
| R42 | Service-owned Neon schemas, typed APIs/events, secure auth | P01–P02, P13 | No cross-service writes, contract tests |
| R43 | Cloudflare Workers frontend, Cloud Run Services/Jobs workers | P00–P01, P08 | Actual integration proofs |
| R44 | R2 assets/exports, Neon durable state, Redis optional | P02, P06, P11 | Signed access, proper ownership and persistence |
| R45 | Security/PII/clinical consent, injection/XSS/media protections | P03, P06, P10, P13 | Adversarial tests and documented privacy rules |
| R46 | CI/CD, independent service deployment, monitoring, LangSmith/evals | P01, P09, P13 | Automated checks, traces and rollback |
| R47 | Budget, tokens, rate limits and usage accounting | P08–P09, P13 | Verified cost controls and 429 handling |
| R48 | Conditional tools remain conditional; unknown providers explicitly unresolved | P00, P04, P10, P12 | ADR register and no fake implementation claims |

**Traceability rule:** Every R01–R48 has at least one phase, implementation owner and reproducible test; no checklist item may be removed from the roadmap without written approval and version bump.

## 7. Cross-service workflow test cases (minimum end-to-end suite)

1. **Free student:** Google/OTP → verified account → choose default/preliminary template → discipline-neutral intake → adaptive Q → 10-page preview → retry attempt to download (must fail) → second report without subscription (must route to pricing).
2. **Paid Pro:** verified payment sandbox → one project → <=100 pages → approved report → DOCX/PDF downloads only, attempted LaTeX or second paid project rejected.
3. **Paid Premium:** two projects with individually correct templates → each <=100 pages → DOCX/PDF/LaTeX authorized → third project denied unless independently entitled.
4. **Duplicate identity/device:** same verified phone/email across browser/device cannot create another account; device-risk enforcement explained and appeal supported.
5. **Adaptive cross-discipline:** software, psychology, LLB and MBBS provide different outlines/questions; no generic 'which database?' for irrelevant disciplines.
6. **Unconfirmed fact:** AI guesses model or algorithm; validator blocks, Mentor asks; student confirms/corrects before inclusion.
7. **Uploaded screenshot:** visual finding remains candidate; student corrects it; chapters and diagrams reflect only corrected confirmed fact; no private R2 exposure.
8. **Mermaid diagram:** source facts provide nodes/edges; unknown component causes question, malicious label is rejected; SVG/PNG and caption survive export.
9. **AI image:** conceptual artwork includes visible/metadata indication that it is illustrative; provider outage doesn't erase chapter; not mistaken for student project photo.
10. **Research/chart:** verified source-based citation works; invented DOI fails; numeric chart without actual data blocked; plagiarism provider outage not misreported as passed.
11. **Quality editing:** style rewrite changes number/result; post-style factual validation flags regression; bounded repair; student approval escalation if needed.
12. **Browser offline:** Cloud Run job continues, SSE reconnect or polling recovers true progress, no duplicate quota charge or new job.
13. **Worker kill mid-section:** checkpoint resumes, approved chapters remain identical, no stale overwrite, generation eventually completes or reports an honest blocker.
14. **Service failure:** Visual/Document/Notification independent outages degrade only affected feature, Billing/Auth failure never grants unauthorized access, Quality outage never fakes approval.
15. **Template fidelity:** 3 personal initial-page templates allowed; snapshot unaffected by edits; TOC/page numbers/figures correctly assembled; DOCX/PDF/LaTeX actual layouts checked.
16. **Security:** cross-tenant document/figure/export/answer attempts fail; webhook spoofing and retry replay fail; prompt injection in uploaded documents/diagrams cannot change workflow permissions.

## 8. Cursor-first implementation working agreement

### One vertical slice at a time

For each implementation session, provide Cursor exactly: (1) latest three architecture references; (2) this roadmap; (3) **one** selected task ID/phase; (4) permitted files/services; (5) explicit API/DB contract; (6) tests and exit gate; (7) requirement IDs and agent IDs. Generate code only after inspecting the relevant existing files; don't bulk-create unrelated features or switch providers. Keep each PR small, review migrations carefully and run tests before merging.

### Reusable Cursor instruction (copy to your Cursor chat)

> Read `docs/ACADENCE_TECH_STACK_V2_2.md`, `docs/ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`, `docs/ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`, and `docs/ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md`. Treat the latest-version sections as authoritative and older embedded documents as historical. We are implementing **Phase P00, starting with repository documentation and ADR/compatibility proofs**. Preserve all 48 requirements and 36 responsibilities. Do not implement unrelated modules or silently choose open providers. Before changing code, show the files you would change, required test cases, and the exact risk addressed. Use TypeScript/Next.js on Cloudflare Workers for frontend and Python/FastAPI for independently deployed Cloud Run services. Keep ownership boundaries, least privilege and validated contracts. Provide working commands and evidence of tests; do not claim deployment compatibility without a successful test.

### Milestone tracking template

```text
Task ID: Pxx-yy
Requirement IDs: Rxx, Ryy
Agent/service IDs: #xx, #yy
Owning service: ...
Status: BACKLOG | IN_PROGRESS | BLOCKED | READY_FOR_TEST | VERIFIED
Dependencies: ...
Files / migrations / API contracts changed: ...
Acceptance tests and evidence: ...
Open decisions / ADRs: ...
Rollback / remediation: ...
```

## 9. Open decisions register and blockers (do not invent answers)

| Decision | First needed | Rule |
|---|---|---|
| Next.js/vinext/React/Tiptap/Mermaid exact compatible versions | P00/P01 | Prove in real build and pin lockfile |
| Secure Cloudflare → Cloud Run ingress | P00/P01 | No private service account keys in browser/Worker |
| Paid Tiptap Pages / conversion or owned pagination engine | P00/P05 | Validate cost and DOCX/PDF/LaTeX fidelity before builder investment |
| OTP provider and phone coverage | P03 | Verify deliverability, pricing and privacy compliance |
| Payment provider, subscription term, renewal/expiry, refunds, upgrades, failed jobs | P04 | Approved product policy/ADR before charging |
| User-device restriction anti-abuse implementation and account appeals | P03 | Browser limitation and privacy policy explicit |
| AI model IDs, routing, evaluation thresholds and budget | P07–P09 | Benchmark reproducible outputs, costs, rate limits |
| Originality corpus/provider and permitted marketing claims | P09 | No guarantee of zero plagiarism |
| Citation source availability and clinical/legal fact review | P09/P14 | No fabricated sources, results or advice |
| Vision API, image generation API (FLUX.2 candidate), asset rights | P06/P10 | Student images private; illustrative art labeled |
| Image formats/size, consent and retention/deletion periods | P06 | Security/privacy controls before production upload |
| Speech-to-text/TTS provider and accessibility languages | P12 | Browser fallback and user correction required |
| Cloud Tasks vs Pub/Sub vs direct calls, visual job separation | P08/P10/P13 | Add only on clear delivery/fanout/load need |
| PDF exporter approach, LaTeX parity and layout acceptance thresholds | P00/P11 | Tested against canonical university-style templates |

## 10. Progress scoreboard (as of document creation)

| Planning deliverable | Status |
|---|---|
| Tech Stack v2.2 | **DESIGN BASELINE COMPLETED**; exact versions/provider integration testing pending |
| Multi-Agent Architecture v1.1 | **DESIGN BASELINE COMPLETED**, all 36 responsibilities accounted for |
| System Architecture v1.1 | **DESIGN BASELINE COMPLETED**, nine-service microservice design documented |
| Development Roadmap v1.0 | **THIS DOCUMENT CREATED**, all phases, owners and exit gates drafted |
| Actual implementation | **NOT STARTED** |
| Production compatibility & security tests | **NOT STARTED** |
| Production launch | **NOT STARTED** |

---

**Final rule:** The road to a reliable 100-page report starts with a correct small, fully grounded report and export. No feature is 'done' until its user-visible behavior, authorization, source provenance, tests, fault recovery and relevant quality checks are proven against the requirements above.
