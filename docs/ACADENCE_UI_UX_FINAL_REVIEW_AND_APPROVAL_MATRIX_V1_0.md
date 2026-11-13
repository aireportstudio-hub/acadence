# Acadence — Final UI/UX Review & Approval Matrix v1.0

**Created:** 2026-11-13  
**Status:** **Review initiated; NOT fully approved**. Prior image-generation collages are concept art. This file is an acceptance checklist and corrective UX specification; it is not proof that 95 responsive screens were built or manually QA-tested.

## Source-of-truth documents
- `ACADENCE_TECH_STACK_V2_2.md`
- `ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`
- `ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`
- `ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md`
- `ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md` (95 IDs)
- `ACADENCE_UI_UX_DESIGN_SYSTEM_V1_0.md` (approved UX rules)
- `ACADENCE_CURSOR_UI_HANDOFF_V1_0.md`

## 1 — Immutable UX decisions

1. **Brand:** premium lavender theme, readable white content canvases; focus and disabled states visible, never text hidden in low-contrast gradients.
2. **Auth:** Google OAuth or mobile OTP **only**. The application does not support email/password, password reset, or speculative biometric identity login. Existing verified identities are resolved without creating duplicates; device-registration policy is explained with an appeal route.
3. **Plans:** Hobby = 1 report up to 10 pages, preview only, no file download; Pro = 1 project up to 100 pages, DOCX/PDF; Premium = 2 projects up to 100 pages **each**, DOCX/PDF/LaTeX. Do not invent prices, renewal cycles, plan names or access allowances.
4. **Project creation sequence:** Dashboard → user selects **Create New Project** → AI Mentor **welcomes and shows exact caption** → **select/create institution-style template** → project/education details and uploads → discipline-aware outline, gaps and adaptive questions → confirm student facts → generation → QA → preview → plan-authorized export. No project-specific question before template selection.
5. **Mentor:** sole visible robot, maintains the project journey until completion, explains actual backend milestones, speaks only after opt-in, every spoken sentence has exactly matching visible text, typing works for the complete journey; mic denied/noisy/offline does not block answering.
6. **Templates:** user can save at most **three personal initial-page template definitions**, *not* a maximum of three pages. Separate Template Builder supports reorder, edit, duplicate, delete, insert, margins, logos, signatures, placeholders, headers, footers, TOC, and page numbering. Selected version is snapshotted for the project.
7. **Truthfulness:** no fabricated university endorsements, student numbers, scores, similarity/plagiarism outcomes, DOI, reference or user-project implementation/results. Unsupported project-specific claims ask for confirmation. AI images are labeled conceptual; uploaded real project images maintain provenance.
8. **Status:** distinguish draft vs approved sections, queued/running/blocked/retrying/completed; never present generated guesses as job progress. Browser offline does not itself mean Cloud Run Job is paused. Resume from server checkpoint; don't double-charge quotas.
9. **Exports:** actual authorization comes from backend. Hobby preview only; Pro Word/PDF; Premium Word/PDF/LaTeX. A rendered >100 page report is an error to correct, not an approved delivery.

## 2 — Fixed primary screen journeys

### A. Google/mobile OTP only (AUTH-01—AUTH-08)
- Primary auth choice cards: **Continue with Google** and **Continue with mobile OTP**.
- Mobile branch: enter number → send code → enter OTP → verify → account ready or existing-identity flow.
- No password inputs, password-reset links, email/password CTA or made-up sign-in methods.
- Accessible resend/expiry/error state; privacy-preserving existing-account warning; session renewal retains unsent text when feasible.

### B. Template-first speaking Mentor (PRJ-01—PRJ-13, BOT-01—BOT-09)
- The first Mentor on-screen message is: **“Welcome! I’ll guide you through creating your report. First, choose a university template.”**
- Robot can animate silently; audio playback is **off until user enables it**. The full sentence is always on-screen regardless of audio.
- Template list: defaults clearly marked as sample/unverified unless validated; saved user templates show **0/3–3/3 slots**; builder opens without losing in-progress project state.
- After template selected, speech and captions: **“Your template is selected. Now tell me about your course and project.”**
- Intake and adaptive question flow may use text input, voice transcript review, or quick selection. Confirmed answers are shown for edit. No automated speech recognition result becomes immutable fact before student confirmation.
- During generation, robot may collapse into a small dock with an expandable real-status transcript; must not cover document or send controls. On completion only permitted download formats appear.

### C. Pricing/export (PUB-05, BILL-01—BILL-08, GEN-16—GEN-17)
- Three plan cards exactly **Hobby / Pro / Premium**; use pricing placeholder **“Pricing available at checkout”** until actual catalog exists.
- Hobby: **One trial report • up to 10 pages • preview only • no downloads**.
- Pro: **One complete project • up to 100 pages • DOCX and PDF**.
- Premium: **Two complete projects • up to 100 pages each • DOCX, PDF and LaTeX**.
- Avoid pricing cadence toggle and paid-plan renewal language before rules finalized.
- Backend verifies paid access before checkout success or every download; front-end locked states are explanatory only.

### D. Template editor and responsive controls (TPL-01—TPL-13)
- Desktop: page list / document canvas / properties inspector; tablet: collapsible page list and inspector; phone: one active pane at a time with bottom-sheet settings and full-screen canvas.
- Every page has accessible **Move up**, **Move down**, **Duplicate**, **Delete** and **Edit** menus, not drag-only controls.
- Live preview includes overflow warnings and unresolved placeholders; institution claims are labeled appropriately.
- Save and apply keep version history and frozen selected snapshot. Fourth saved personal template explains the limit and offers to manage existing slots.

### E. Generation, review, visuals and recovery (GEN-01—GEN-17; SYS-01—SYS-10)
- Display **verified** section stages and draft/approved status; preview not misrepresented as final export.
- Citation review: verified evidence, source metadata and unsupported claim actions. Originality: show results only if checking service actually ran, with coverage caveat.
- Mermaid diagrams are derived from confirmed architecture/process. Scientific charts require actual data. Conceptual AI images differ from student-uploaded evidence.
- Offline UI: **“Connection lost. Your saved progress is available. Checking job status when reconnected.”** Do **not** claim job stopped.
- Worker failure: show last saved checkpoint and safe retry; provider 429: indicate backed-off retry or waiting state; payment and authorization errors never autocorrected by an AI agent.

## 3 — Responsive acceptance checklist (must pass per screen)

- [ ] 320px, 360px, 390px, 430px mobile snapshots; 768/820px tablet; 1024/1280px laptop; 1440/1920px desktop. Document/diagram internal canvas may scroll, page chrome must not overflow horizontally.
- [ ] Full keyboard navigation including dialogs, Tiptap controls, page reorder and export selection; visible focus ring and skip navigation.
- [ ] 44×44px touch targets minimum and virtual keyboard does not obscure submit/send/record-stop or save controls.
- [ ] Body text remains readable at 200% zoom; no caption truncation, reduced motion alternative and captions visible when audio is muted.
- [ ] Role/control accessibility names, field errors, semantic labels; test with axe and manual keyboard/screen reader where applicable.
- [ ] Correct loading, empty, offline, retry, permission denied and blocked states.
- [ ] No fake metrics, university approvals, final citations, pricing, similarity rates, page counts or AI-generated experimental results.
- [ ] Preview/document formatting and entitlement labels correspond to current backend truth or clearly labeled development fixtures.
- [ ] Confirm on iOS/Android touch navigation and at landscape orientation; desktop navigation never hides essential tasks.

## 4 — Visual discrepancy log: older concepts and required correction

| Severity | Found in concept artworks | Must be corrected in approved art or working UI |
|---|---|---|
| Critical | Email/password login, forgot-password link | AUTH only Google + mobile OTP |
| Critical | Plan names “Student/Academic/Free”, incorrect project counts, prices | Exactly Hobby/Pro/Premium, quotas as above, unpriced placeholder |
| Critical | New-project robot asks title before choosing template | Mentor greeting and template choice FIRST, then intake/questions |
| Critical | Robot suggests mic mandatory or mic activated automatically | Consent-based voice, fully functional typing, captions always |
| Critical | “Plagiarism 0%”, “100% unique”, unverifiable references/DOIs | Verified review status or ‘not checked’, with source evidence |
| High | Specific “official” university badge and seal without authorization | “Sample university-style layout” unless independently verified |
| High | Fake “10K+ users”, reviews, testimonials | Replace with truthful feature summary, no fabricated metrics |
| High | 112 pages or “exactly 100 pages” | Upper bound, accurate page count after rendering |
| High | Mobile screenshot drops chapter editor, template controls or preview | Responsive full-featured mobile pane with accessible alternate controls |
| High | Browser disconnect portrayed as always stopping backend job | Show connection status separate from backend job state |
| High | Generated project screenshots presented as real hardware/results | AI conceptual provenance label, real upload confirmation |
| Medium | Inaccurate estimated completion time or unverified progress bars | Actual server event state, or no ETA until reliable |
| Medium | Download button always present/active in Hobby | Disabled explanatory UI with backend enforcement |

## 5 — Four reviewed screen gates (work to perform before sign-off)

| Key screen | Inventory IDs | Current contract review | Visual evidence / manual QA | Required correction |
|---|---|---|---|---|
| Sign-in + OTP | AUTH-01/03/04/05 | **Rules checked** | **Pending** | No email/password, clear OTP/error states |
| New-project Mentor + Template-first | PRJ-01/02/03, BOT-01/04 | **Rules checked** | **Pending** | Welcome and template ahead of project questions; type/voice parity |
| Plan comparison + export gating | PUB-05, BILL-01/06/07, GEN-16 | **Rules checked** | **Pending** | Correct 1×10/1×100/2×100 entitlements, no price guess |
| Editor + mobile template controls | TPL-04/05/07, GEN-12 | **Rules checked** | **Pending** | No drag-only control, mobile edit/preview access |

## 6 — Complete screen/state sign-off matrix

**Status legend:** `Requirements mapped` = screen intent exists in master inventory; **NOT** proof the screen has a finished responsive visual or passed tests. Every row begins `Visual QA pending` until a real screenshot/prototype is reviewed on supported widths.

| ID | Screen / state | Requirements mapped | Visual QA | Interaction QA | Responsive QA |
|---|---|---|---|---|---|
| `PUB-01` | Landing / Home | Yes | Pending | Pending | Pending |
| `PUB-02` | Features | Yes | Pending | Pending | Pending |
| `PUB-03` | How Acadence Works | Yes | Pending | Pending | Pending |
| `PUB-04` | Public Template Gallery | Yes | Pending | Pending | Pending |
| `PUB-05` | Public Pricing | Yes | Pending | Pending | Pending |
| `PUB-06` | Public Help, FAQ & Contact | Yes | Pending | Pending | Pending |
| `PUB-07` | Legal & Trust | Yes | Pending | Pending | Pending |
| `AUTH-01` | Sign in / Sign up | Yes | Pending | Pending | Pending |
| `AUTH-02` | Google Authentication Return | Yes | Pending | Pending | Pending |
| `AUTH-03` | Mobile Number Entry | Yes | Pending | Pending | Pending |
| `AUTH-04` | OTP Verification | Yes | Pending | Pending | Pending |
| `AUTH-05` | Account Already Exists / Link Identity | Yes | Pending | Pending | Pending |
| `AUTH-06` | Registration / Basic Profile | Yes | Pending | Pending | Pending |
| `AUTH-07` | Account Ready | Yes | Pending | Pending | Pending |
| `AUTH-08` | Session Recovery / Reauthentication | Yes | Pending | Pending | Pending |
| `APP-01` | Student Dashboard | Yes | Pending | Pending | Pending |
| `APP-02` | My Projects | Yes | Pending | Pending | Pending |
| `APP-03` | Project Detail / History | Yes | Pending | Pending | Pending |
| `APP-04` | My Reports Library | Yes | Pending | Pending | Pending |
| `APP-05` | Template Hub / My 3 Templates | Yes | Pending | Pending | Pending |
| `APP-06` | Notifications Inbox | Yes | Pending | Pending | Pending |
| `APP-07` | Profile & Education Preferences | Yes | Pending | Pending | Pending |
| `APP-08` | Security & Devices | Yes | Pending | Pending | Pending |
| `APP-09` | Accessibility & Voice Preferences | Yes | Pending | Pending | Pending |
| `APP-10` | Help & Support | Yes | Pending | Pending | Pending |
| `TPL-01` | University & Style Templates Gallery | Yes | Pending | Pending | Pending |
| `TPL-02` | Template Details / Full Preview | Yes | Pending | Pending | Pending |
| `TPL-03` | Create Personal Template | Yes | Pending | Pending | Pending |
| `TPL-04` | Template Builder — Workspace | Yes | Pending | Pending | Pending |
| `TPL-05` | Page Organizer | Yes | Pending | Pending | Pending |
| `TPL-06` | Page Type Library | Yes | Pending | Pending | Pending |
| `TPL-07` | Page Content & Element Editing | Yes | Pending | Pending | Pending |
| `TPL-08` | Typography & Page Settings | Yes | Pending | Pending | Pending |
| `TPL-09` | Headers, Footers & Page Numbers | Yes | Pending | Pending | Pending |
| `TPL-10` | Dynamic Placeholder Manager | Yes | Pending | Pending | Pending |
| `TPL-11` | Template Preview / Layout Validation | Yes | Pending | Pending | Pending |
| `TPL-12` | Save / Version / Apply Template | Yes | Pending | Pending | Pending |
| `TPL-13` | Three-Template Limit State | Yes | Pending | Pending | Pending |
| `PRJ-01` | Create Project — Mentor Welcome | Yes | Pending | Pending | Pending |
| `PRJ-02` | Select Existing / Default Template | Yes | Pending | Pending | Pending |
| `PRJ-03` | New Template In-Flow | Yes | Pending | Pending | Pending |
| `PRJ-04` | Academic Details Intake | Yes | Pending | Pending | Pending |
| `PRJ-05` | Project Type / Methodology Intake | Yes | Pending | Pending | Pending |
| `PRJ-06` | Project Media Upload | Yes | Pending | Pending | Pending |
| `PRJ-07` | Image Observations Confirmation | Yes | Pending | Pending | Pending |
| `PRJ-08` | Project Blueprint Summary | Yes | Pending | Pending | Pending |
| `PRJ-09` | Outline Proposal & Page Budget | Yes | Pending | Pending | Pending |
| `PRJ-10` | Adaptive Question Session | Yes | Pending | Pending | Pending |
| `PRJ-11` | Clarification / Missing Result | Yes | Pending | Pending | Pending |
| `PRJ-12` | Confirm Facts & Start Generation | Yes | Pending | Pending | Pending |
| `PRJ-13` | Waiting for Student Input / Resume | Yes | Pending | Pending | Pending |
| `BOT-01` | Mentor Speaking + Captions | Yes | Pending | Pending | Pending |
| `BOT-02` | Mentor Listening | Yes | Pending | Pending | Pending |
| `BOT-03` | Live Speech Transcript | Yes | Pending | Pending | Pending |
| `BOT-04` | Text-Only Response Mode | Yes | Pending | Pending | Pending |
| `BOT-05` | Speech Paused / Muted | Yes | Pending | Pending | Pending |
| `BOT-06` | Microphone Denied / Unsupported / Noisy | Yes | Pending | Pending | Pending |
| `BOT-07` | Compact Mentor During Builder/Report | Yes | Pending | Pending | Pending |
| `BOT-08` | Mentor Progress Narration | Yes | Pending | Pending | Pending |
| `BOT-09` | Mentor Completion / Next Step | Yes | Pending | Pending | Pending |
| `GEN-01` | Generation Started / Job Queue | Yes | Pending | Pending | Pending |
| `GEN-02` | Live Report Generation | Yes | Pending | Pending | Pending |
| `GEN-03` | Chapter Status & Section Details | Yes | Pending | Pending | Pending |
| `GEN-04` | Quality Review Overview | Yes | Pending | Pending | Pending |
| `GEN-05` | Citation Review | Yes | Pending | Pending | Pending |
| `GEN-06` | Originality / Similarity Review | Yes | Pending | Pending | Pending |
| `GEN-07` | Fact Conflict / Needs Student Answer | Yes | Pending | Pending | Pending |
| `GEN-08` | Diagram & Flowchart Studio | Yes | Pending | Pending | Pending |
| `GEN-09` | AI Illustration Studio | Yes | Pending | Pending | Pending |
| `GEN-10` | Real Data Chart Studio | Yes | Pending | Pending | Pending |
| `GEN-11` | Figure & Uploaded Asset Manager | Yes | Pending | Pending | Pending |
| `GEN-12` | Live Report Editor / Document Preview | Yes | Pending | Pending | Pending |
| `GEN-13` | Document Layout Warnings | Yes | Pending | Pending | Pending |
| `GEN-14` | Generation Interrupted / Resumable | Yes | Pending | Pending | Pending |
| `GEN-15` | Report Ready | Yes | Pending | Pending | Pending |
| `GEN-16` | Export Format Selection | Yes | Pending | Pending | Pending |
| `GEN-17` | Export Processing / Downloads | Yes | Pending | Pending | Pending |
| `BILL-01` | Plan Comparison In-App | Yes | Pending | Pending | Pending |
| `BILL-02` | Upgrade / Checkout | Yes | Pending | Pending | Pending |
| `BILL-03` | Payment Pending / Confirmation | Yes | Pending | Pending | Pending |
| `BILL-04` | Payment Success | Yes | Pending | Pending | Pending |
| `BILL-05` | Payment Failed / Cancelled | Yes | Pending | Pending | Pending |
| `BILL-06` | Trial Exhausted / Pricing Gate | Yes | Pending | Pending | Pending |
| `BILL-07` | Quota Exceeded / Format Not Allowed | Yes | Pending | Pending | Pending |
| `BILL-08` | Subscription / Billing Management | Yes | Pending | Pending | Pending |
| `SYS-01` | No Internet / Reconnect | Yes | Pending | Pending | Pending |
| `SYS-02` | LLM Rate Limit / Retry Delay | Yes | Pending | Pending | Pending |
| `SYS-03` | Worker Crash / Recovery | Yes | Pending | Pending | Pending |
| `SYS-04` | Service Unavailable | Yes | Pending | Pending | Pending |
| `SYS-05` | Upload Rejected / Privacy Warning | Yes | Pending | Pending | Pending |
| `SYS-06` | Permission / Session / Account Restriction | Yes | Pending | Pending | Pending |
| `SYS-07` | Cancel Job / Confirm Intent | Yes | Pending | Pending | Pending |
| `SYS-08` | Empty / Loading / Skeleton | Yes | Pending | Pending | Pending |
| `SYS-09` | Notifications / Support Errors | Yes | Pending | Pending | Pending |
| `SYS-10` | Responsive Landscape / Zoom / Reduced Motion | Yes | Pending | Pending | Pending |

## 7 — Review closure and operational next steps

1. Produce **individual, readable full-size mockups** for AUTH, template-first PRJ/BOT, correct BILL, and responsive TPL (desktop/tablet/phone). Avoid one unreadable 95-screen collage.
2. Check those visuals against sections 1–5; document defects and rework until corrected. Then advance remaining grouped screen IDs in dependency order.
3. Prototype the interaction transitions (mic allowed/denied, text-only, transcript correction, template selection, real progress, blocked fact, reconnect, trial exhausted, export authorization).
4. Only mark a screen approved once its visual, interaction and responsive QA have evidence with the viewport/device and reviewer.
5. Update the Cursor handoff document with final approved frames and tests. **Do not claim all 95 screens are approved yet.**

**Acceptance goal:** all 95 IDs accounted for; all critical workflows independently reviewed at desktop/tablet/mobile; no violations of architecture/plan/template/mentor rules; keyboard and text-only paths complete. Cursor UI code and production service tests are later implementation tasks.
