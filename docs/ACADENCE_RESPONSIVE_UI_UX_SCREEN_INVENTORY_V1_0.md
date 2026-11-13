# Acadence — Responsive UI/UX Screen Inventory v1.0

**Status:** Proposed UI/UX design baseline; **inventory completed, individual full-resolution mockups and working frontend NOT yet completed**.  
**Date:** 2026-11-13  
**Current design sources:** `ACADENCE_TECH_STACK_V2_2.md`, `ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`, `ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`, `ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md`.  
**Design direction:** Preserve the existing Acadence lavender-gradient visual mockups, modern white/lavender cards, rounded edges, generous white space, and the friendly lavender/white **robot AI Mentor** with matching visible dialogue panel.

## 0. Scope and interpretation

This document inventories **95 screen and reusable interaction-state specifications**, not 95 separate Next.js routes. A modal, drawer, variation or error state may share one route with its parent screen. Each entry below requires desktop, tablet and mobile review; none may be silently omitted because its implementation lives inside another screen. This inventory is an **additive UX specification**, not a replacement for the technical architecture or established product rules.

**Locked behavior:** The AI Mentor becomes active when the student chooses **Create New Project**, starting with a spoken **and identically visible written** welcome if audio is enabled. Before any **project-specific adaptive questions**, the student chooses/creates a university report template. Mentor guides template selection, intake, project analysis, adaptive questions, report generation/status, quality review, visuals, recovery, preview and final completion. If audio is muted/unsupported/uncomfortable, the ENTIRE journey works via text. Audio never runs without user action and microphone permission where required; captions/transcript remain available regardless of audio mode. Mentor never invents a progress event.

**Core commercial rules:** Hobby: **one report up to 10 pages, preview only, no downloads**. After trial exhaustion, check paid entitlement and show pricing if absent. Pro: **one project up to 100 pages, DOCX/PDF**. Premium: **two projects, each up to 100 pages, DOCX/PDF/LaTeX**. These are maximums, not filler targets. Backend enforces all limits. The university Template Builder is a separate main tab, allows default templates and **at most three saved personal initial-page templates**; these are not capped at three pages. A template is selected before adaptive questioning and the saved snapshot is preserved for final assembly.

## 1. Lavender visual system — preserve prior mockups

| Token | Example target | Usage |
|---|---|---|
| Brand primary | `#7C3AED` | Primary CTA, active navigation, focused states |
| Brand deep | `#5B21B6` | High-contrast headings/accent gradients |
| Lavender medium | `#A78BFA` | Secondary accents, waves and speech visuals |
| Lavender soft | `#EDE9FE` | Background tint, soft panels |
| Canvas | `#F9F7FF` | Page background |
| White surface | `#FFFFFF` | Reading, editing and dense data areas |
| Main text | `#251B40` | Body and headings (test contrast) |
| Subdued text | `#5E5574` | Descriptions (test contrast) |
| Hero gradient | `linear-gradient(135deg,#F9F7FF 0%,#EDE9FE 50%,#D8C7FF 100%)` | Hero and decorative surfaces only |

Use lavender accents without sacrificing text contrast; no low-contrast pale purple text on pale lavender surfaces. Keep earlier white/purple glassmorphism, purple line icons, soft shadows, rounded cards and an inviting illustration/robot. The speaking robot is **one consistent mascot**, not a different character on every screen. Do not depend only on color for status (approved/warning/blocked).

## 2. Strict responsive baseline and interaction rules

| Device band | Layout target | Interaction guarantee |
|---|---|---|
| Compact phone `320–359px` | Single content column | Full functionality, scroll/zoom for documents, no body-level horizontal overflow |
| Phone `360–767px` | Single column with mobile navigation | Bottom navigation / drawer; sticky answer composer; robot and transcript readable |
| Tablet `768–1023px` | Flexible two-zone layout | Collapsible nav, canvas + controls in drawers or side sheets |
| Laptop `1024–1439px` | Sidebar + main area, optional contextual panel | 2–3 panels without clipped controls |
| Wide desktop `≥1440px` | Sidebar + robot/conversation/preview + contextual progress | As shown in prior wide lavender mockups; maintain readable text widths |

**Global gates:** usable at 320px, touch targets ~44×44 CSS pixels, keyboard focus visible, zoom to 200%, text/captions readable, reduced-motion animation option, no mandatory microphone, visual focus management when opening drawers, accessible drag alternatives, portrait/landscape, and browser safe-area padding. Full document pages may pan/zoom **inside their own canvas**; the overall website should never overflow horizontally. Test at 320, 360, 390, 430, 768, 820, 1024, 1280, 1440, 1920 widths and portrait/landscape; include low-bandwidth and iOS/Android keyboard behavior. Desktop sidebar collapses to drawer or bottom navigation on phone; three-pane AI Mentor becomes stacked robot + full transcript + collapsible progress. No hover-only actions.

### Mentor layout per form factor

- **Wide desktop:** robot avatar / speaking waveform on left, conversation and synchronized transcript at center, progress/next-step panel on right. The user always sees the latest spoken sentence in transcript beside the robot.
- **Laptop:** robot dock on left and chat center, progress as foldable right panel. If cramped, progress becomes a drawer.
- **Tablet:** robot heading top-left or top half, transcript below/beside as space permits, progress collapsible; controls sticky without covering answers.
- **Mobile:** a compact animated robot card at top, **spoken words displayed in a caption/chat panel directly below**, voice controls plus `Type your answer` editor pinned above safe area and keyboard; progress opens through a sheet. The user can mute speech or switch to text at any time, without losing the question/answer.
- **During template editing / generation:** full robot can collapse into an unobtrusive dock that still displays current narration and opens the conversation; it must never cover the editor, preview or crucial buttons.

### Robot communication and consent states

`idle → greeting → speaking → awaiting_answer → listening OR typing → transcript_review → answer_confirmed → processing → status_narration → next_question/quality_review → completion`. Also support `muted`, `voice_unavailable`, `mic_denied`, `offline`, `reconnecting`, `paused_for_user`, `retrying`, `cancelled`, `blocked_for_clarification`. Speech transcript is authoritative visible copy of spoken content and persisted as appropriate; model text is not automatically a confirmed student fact. Provide replay, subtitles, clear listening indicators, consent for recording/transcription, edit-before-confirm, translation/language options only where supported. Do not silently turn on microphone between steps.

## 3. Complete inventory — 95 screens and reusable states

Each row means an intentional design and responsive acceptance target. Stable IDs can be used for Figma screens, UI routes, tickets, screenshots, acceptance tests and Cursor prompts.

### A. Public website & discovery (7 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `PUB-01` | **Landing / Home** | Lavender hero, Acadence robot illustration, how it works, templates, quality, pricing CTAs | Hero becomes single-column; CTA and illustrated robot stay readable. |
| `PUB-02` | **Features** | Agentic writing, accuracy, template builder, visuals, preview, voice accessibility, export feature details | Feature grid becomes vertically stacked. |
| `PUB-03` | **How Acadence Works** | Transparent journey: template first, intake, adaptive Q&A, generate, verify, export | Vertical steps; no side-by-side text too small to read. |
| `PUB-04` | **Public Template Gallery** | Preview example university-style and generic layouts without claiming unverified official endorsement | Swipe or scroll gallery, tap preview. |
| `PUB-05` | **Public Pricing** | Correct Hobby/Pro/Premium quotas, limitations and FAQ; purchase redirects securely | Stack plan cards; compare entitlements via accessible rows. |
| `PUB-06` | **Public Help, FAQ & Contact** | Support articles, common questions, report limitations, contact form | Single-column searchable help. |
| `PUB-07` | **Legal & Trust** | Privacy, terms, academic integrity, data handling, rights to uploaded media and AI-use disclosure | Readable long form with sticky TOC only where room allows. |

### B. Authentication & first visit (8 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `AUTH-01` | **Sign in / Sign up** | Continue with Google or mobile OTP, existing account support, clear privacy notices | Large two-option stacked controls. |
| `AUTH-02` | **Google Authentication Return** | Loading, success, provider failure and existing-identity linking outcomes | Compact clear state; no secret/technical errors displayed. |
| `AUTH-03` | **Mobile Number Entry** | Phone country code, number, privacy note, send-code CTA | Numeric keyboard, accessible country selector. |
| `AUTH-04` | **OTP Verification** | Time-limited digits, resend timer, errors, attempts remaining where appropriate | Comfortable digit controls, no forced auto-submit. |
| `AUTH-05` | **Account Already Exists / Link Identity** | Explain verified existing identity; login or secure link, never create duplicate account | Plain call to action, avoid revealing other users. |
| `AUTH-06` | **Registration / Basic Profile** | Name and applicable academic profile basics; missing items may be collected in project intake | Single-column wizard with save progress. |
| `AUTH-07` | **Account Ready** | Welcome, Hobby entitlement, CTA to dashboard or Create Project | Clear single CTA; trial is exactly one <=10-page preview-only report. |
| `AUTH-08` | **Session Recovery / Reauthentication** | Expired/revoked session, secure retry/login without losing locally unsent text when feasible | Minimal modal/standalone page, data-loss warning if applicable. |

### C. App navigation & account (10 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `APP-01` | **Student Dashboard** | Quick actions: Create Project, Templates, In-progress, project quota/plan, recent projects | Summary cards stack; bottom nav or drawer replaces sidebar. |
| `APP-02` | **My Projects** | Project statuses, filters, search, resume, view, permitted actions | Cards replace dense tables; mobile sticky search. |
| `APP-03` | **Project Detail / History** | Project facts, linked template, progress, versions, reports, uploads, activity | Tabs accordion; no hidden ownership info. |
| `APP-04` | **My Reports Library** | Preview-ready or exported reports, statuses, allowed formats and restrictions | Card list, compact actions. |
| `APP-05` | **Template Hub / My 3 Templates** | Saved personal template slots (0/3 through 3/3), defaults, create/select/manage | Tile cards and accessible manage menu. |
| `APP-06` | **Notifications Inbox** | Payment, OTP safety alerts, quality hold, ready report, retry/resume states | Single-column grouped list. |
| `APP-07` | **Profile & Education Preferences** | Identity, institution, degree/specialization preferences, notification preferences | Grouped form panels. |
| `APP-08` | **Security & Devices** | Sessions, revoke, phone/email linking, one-device registration policy and support appeal | Device cards with revoke controls. |
| `APP-09` | **Accessibility & Voice Preferences** | Voice on/off, language, captions, reduced motion, text-only preference, microphone tests | Persistent accessible switches. |
| `APP-10` | **Help & Support** | Guides, tickets, contact, troubleshooting, academic integrity help | Simple support cards. |

### D. University Template Builder — separate tab (13 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `TPL-01` | **University & Style Templates Gallery** | Browse institution/style defaults; clearly distinguish sample vs verified official requirements | Cards in 1–2 columns; readable preview thumbnail. |
| `TPL-02` | **Template Details / Full Preview** | See pages, supported controls, usage notes, select or copy-to-edit | Full-screen scrollable pages on mobile. |
| `TPL-03` | **Create Personal Template** | Start blank or base on default; explain limit of 3 SAVED personal initial-page templates | Simple choosing cards with next CTA. |
| `TPL-04` | **Template Builder — Workspace** | Tiptap editor, dnd-kit page blocks, toolbar, canvas, property inspector, page list | Canvas in fit-width/zoom mode; toolbar in bottom drawer; no lost functions. |
| `TPL-05` | **Page Organizer** | Add, insert, reorder, move up/down, duplicate, delete, rename; independent page blocks | Drag handle + explicit move up/down accessible alternatives. |
| `TPL-06` | **Page Type Library** | Cover, certificate, declaration, acknowledgement, abstract, TOC, chapter, bibliography, appendix, custom | Searchable bottom sheet on mobile. |
| `TPL-07` | **Page Content & Element Editing** | Rich text, tables, images, logos, signature placeholders, borders and alignment | Full-screen editing sheet; touch selection and keyboard support. |
| `TPL-08` | **Typography & Page Settings** | Paper size, margins, fonts, size, headings, line/paragraph spacing, alignment, page breaks | Settings accordion; preview stays reachable. |
| `TPL-09` | **Headers, Footers & Page Numbers** | Running headers, page numbering style/start, chapter transitions, page regions | Tap to edit, mobile inspector sheet. |
| `TPL-10` | **Dynamic Placeholder Manager** | Student, supervisor, department, university, academic year, project title; required and unresolved status | List of chips with validation details. |
| `TPL-11` | **Template Preview / Layout Validation** | Page-accurate-ish preview, overflow errors, broken placeholders, zoom and print-oriented check | Full-screen preview; horizontal pan and zoom if necessary. |
| `TPL-12` | **Save / Version / Apply Template** | Save to <=3 personal slots, version history, selected immutable per-project snapshot | Simple compare and confirm flow. |
| `TPL-13` | **Three-Template Limit State** | 4th custom template blocked; manage/replace an existing slot without deleting in-use snapshots | Actionable message, never silent overwrite. |

### E. Create New Project — guided flow (13 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `PRJ-01` | **Create Project — Mentor Welcome** | AI robot ACTIVATE here, greeting spoken when enabled and identical visible caption; explain next template step | Robot visible above the dialogue, CTA and voice/text controls in safe area. |
| `PRJ-02` | **Select Existing / Default Template** | Choose or create a template BEFORE project-specific AI questions; snapshot selected version | Stack template cards; robot minimized but available. |
| `PRJ-03` | **New Template In-Flow** | Deep link to separate builder with state preservation; resume project flow after saving/selection | Mobile full-screen builder, clearly marked back-to-project. |
| `PRJ-04` | **Academic Details Intake** | Education, degree, specialization, institution, project title/description, known details | One question or logical group per screen; progress saved. |
| `PRJ-05` | **Project Type / Methodology Intake** | Discipline-adaptive fields for software, law, psychology, MBBS, diploma, etc. | Short groups, conditional fields; no fixed software-only forms. |
| `PRJ-06` | **Project Media Upload** | Screenshots, prototype photos, existing diagrams, research figures, template reference; rights/consent | Camera/file picker, multi-image preview, resumable upload states. |
| `PRJ-07` | **Image Observations Confirmation** | Show AI candidate observations, uncertainty, crop/thumbnail, confirm/reject/correct; no automatic fact promotion | Side-by-side becomes stacked annotated list. |
| `PRJ-08` | **Project Blueprint Summary** | Summarize known project facts, what is missing, and domain-specific intent | Compact editable cards; source provenance visible. |
| `PRJ-09` | **Outline Proposal & Page Budget** | Discipline-appropriate chapters, required facts and estimated length; review/adjust before Q&A | Collapsible sections; page budgets are estimates. |
| `PRJ-10` | **Adaptive Question Session** | Mentor voice/text prompts tailored only to missing facts, with full transcript and answer controls | Robot top/compact, dialogue below, sticky text/voice composer. |
| `PRJ-11` | **Clarification / Missing Result** | Ambiguous/conflicting/unknown details, skipped answers, requests for actual results not invented ones | Show previous answer and correction field. |
| `PRJ-12` | **Confirm Facts & Start Generation** | Confirmed facts, unresolved gaps, source files, selected template, plan and quota | Review cards; clear consent/confirm and Start action. |
| `PRJ-13` | **Waiting for Student Input / Resume** | Saved pending question, job paused, continue later; never hold billable Cloud Run Job idle | Persistent resume CTA, no loss of previous answers. |

### F. Speaking AI Mentor — reusable interactive states (9 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `BOT-01` | **Mentor Speaking + Captions** | Animated lavender/white robot, synchronized visible spoken text, waveform and repeat control | Robot compact but prominent; transcript fully readable. |
| `BOT-02` | **Mentor Listening** | Microphone active indicator, waveform, recording status, stop/pause and privacy signal | Sticky large controls accessible one-handed. |
| `BOT-03` | **Live Speech Transcript** | Live recognized user speech and correction before confirming important facts | Text occupies main column; edit transcript button always accessible. |
| `BOT-04` | **Text-Only Response Mode** | Everything possible without microphone: input, send, review, clarify, continue | Keyboard-friendly composer above virtual keyboard. |
| `BOT-05` | **Speech Paused / Muted** | Mute TTS, pause listening, disable auto narration; captions always remain | Clear toggles and persistent preference. |
| `BOT-06` | **Microphone Denied / Unsupported / Noisy** | Permission guidance, retry, fallback typing with no lost progress | Accessible non-modal fallback. |
| `BOT-07` | **Compact Mentor During Builder/Report** | Small docked robot, persistent activity caption and open conversation control; no editor obstruction | Bottom-sheet or edge dock respecting safe areas. |
| `BOT-08` | **Mentor Progress Narration** | Based on REAL status events (plan, writing chapter, QA, visuals, export); text always displayed, optional speech | Inline status strip expands to transcript without covering content. |
| `BOT-09` | **Mentor Completion / Next Step** | Accurate ready state, can preview/allowed export, warns on pending issues | Robot thanks/explains, clear next CTA. |

### G. Generation, quality, visuals, document & export (17 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `GEN-01` | **Generation Started / Job Queue** | Quota reserved, waiting/running, selected template, last saved state and cancel | Single timeline/card; no fake progress percentage. |
| `GEN-02` | **Live Report Generation** | Chapter-by-chapter preview, draft vs approved badges, progress tracker, Mentor updates | Preview as primary panel; progress drawer; robot compact. |
| `GEN-03` | **Chapter Status & Section Details** | Chapter list and content summary, retries, QA outcomes, missing facts | Collapsible list with resume/open controls. |
| `GEN-04` | **Quality Review Overview** | Distinct fact check, consistency, originality, citations, formatting, issues and next steps | Review cards stacked; never falsely guarantee plagiarism-free. |
| `GEN-05` | **Citation Review** | Actual source, claim-evidence relationship, DOI/reference metadata, unsupported-citation flags | Citation cards rather than tiny side-by-side columns. |
| `GEN-06` | **Originality / Similarity Review** | Internal duplication, possible external similarities, revision status, detection limitations | Readable issue list; no AI detector evasion claim. |
| `GEN-07` | **Fact Conflict / Needs Student Answer** | Blocked unsupported project-specific claims, ask student to confirm true data, resume affected sections | Mentor expands with exact disputed claim and answer box. |
| `GEN-08` | **Diagram & Flowchart Studio** | Mermaid diagrams/flowcharts/ER/sequence/architecture grounded in confirmed facts, edit code/render | Tabs and pinch/zoom canvas with accessible list of nodes. |
| `GEN-09` | **AI Illustration Studio** | Conceptual image generation with approval, style selections, AI-generated label and provider-cost status | Card-based gallery; full-screen inspect. |
| `GEN-10` | **Real Data Chart Studio** | Verified datasets, chart type, axes/units/source, accurate visualization | Table view alternative and responsive chart. |
| `GEN-11` | **Figure & Uploaded Asset Manager** | Uploaded/generated asset gallery, provenance, rights/consent, alt text, captions, section placement | Grid into one/two columns with inspection sheets. |
| `GEN-12` | **Live Report Editor / Document Preview** | Canonical document renderer, chapter navigation, selected preliminary pages, approved content, zoom and layout fidelity | Document fit-width, TOC in drawer, touch-safe editing. |
| `GEN-13` | **Document Layout Warnings** | Overflow, missing pages/placeholder, broken heading or TOC, actionable fixes | Error list and jump-to-page action. |
| `GEN-14` | **Generation Interrupted / Resumable** | Offline/retrying/paused/failed/cancelled state, last checkpoint and permitted retry | Resume status and accessible details always available. |
| `GEN-15` | **Report Ready** | Preview, quality summary, plan permissions, revisions and completion message | Hero + one primary CTA and clean action stack. |
| `GEN-16` | **Export Format Selection** | Hobby none, Pro Word/PDF, Premium Word/PDF/LaTeX; entitlement checked server-side | Simple stacked formats, disabled explanation. |
| `GEN-17` | **Export Processing / Downloads** | Conversion progress, status, saved versions, download errors and retry | Compact status cards, no fake ready state. |

### H. Billing, entitlements & account lifecycle (8 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `BILL-01` | **Plan Comparison In-App** | Hobby 1x10 preview-only; Pro 1x100 DOCX/PDF; Premium 2x100 DOCX/PDF/LaTeX | Single column cards, accessible side-by-side comparison optional. |
| `BILL-02` | **Upgrade / Checkout** | Selected plan, merchant/currency, coupon if supported, secure provider checkout | Mobile-safe provider redirect/webview with clear return path. |
| `BILL-03` | **Payment Pending / Confirmation** | Processing and verified provider result, never activate based on UI alone | Readable pending state with retry-safe refresh. |
| `BILL-04` | **Payment Success** | Verified entitlement, receipt if available, next CTA | Single clean confirmation. |
| `BILL-05` | **Payment Failed / Cancelled** | Transaction failure, retry or change method, no false entitlement | Return-to-pricing CTA; prior work retained. |
| `BILL-06` | **Trial Exhausted / Pricing Gate** | Hobby already used, pricing call-to-action, clear preview-only limits | Helpful explanation and easy plan comparison. |
| `BILL-07` | **Quota Exceeded / Format Not Allowed** | Blocked second Pro/third Premium/new Hobby project or forbidden export; show allowed alternatives | Informative action, not generic error. |
| `BILL-08` | **Subscription / Billing Management** | Active status, project usage, expiration, invoices/receipts where supported, renewal/cancellation | Simple cards; business policies not invented. |

### I. Failure states, privacy & platform utilities (10 entries)

| ID | Screen / state | Required behavior | Strict responsive rule |
|---|---|---|---|
| `SYS-01` | **No Internet / Reconnect** | Explain that running backend job may continue; recover progress on reconnect | Persistent nonblocking banner, retry action. |
| `SYS-02` | **LLM Rate Limit / Retry Delay** | Temporary slowdown, reason and eventual resume status with bounded retry | Clear status; no fake countdown. |
| `SYS-03` | **Worker Crash / Recovery** | Last saved checkpoint, resume/cancel controls and precise uncertainty | Robust resume panel; no duplicate project consumption. |
| `SYS-04` | **Service Unavailable** | Image, voice, quality, export or billing degradation mapped to meaningful alternatives | Feature-specific banner, preserve unaffected work. |
| `SYS-05` | **Upload Rejected / Privacy Warning** | Invalid/malicious/large/sensitive file, rights/consent controls, replace/remove | Inline upload errors near affected assets. |
| `SYS-06` | **Permission / Session / Account Restriction** | Unauthorized resource, session revoked, device restriction appeal/support path | Nonrevealing state, login/support CTA. |
| `SYS-07` | **Cancel Job / Confirm Intent** | Stop in-progress request where possible, describe retained draft and quota treatment according to policy | Accessible confirmation sheet. |
| `SYS-08` | **Empty / Loading / Skeleton** | No project, no templates, no reports, service loading and failed loads | No blank screens, legible skeleton and next action. |
| `SYS-09` | **Notifications / Support Errors** | Unread/read notices, help ticket or contact flows and delivery errors | Keyboard and screen-reader accessible. |
| `SYS-10` | **Responsive Landscape / Zoom / Reduced Motion** | Device rotation, 200% zoom, no horizontal page chrome overflow, non-animated robot option | Fallback layout without missing controls. |

## 4. Core new-project interaction choreography (must not regress)

1. Student clicks **Create New Project** from dashboard or public conversion flow (requires authenticated/eligible account). Display AI Mentor and text simultaneously; user-enabled TTS may greet audibly after the initiating click. Never auto-start microphone without consent.
2. Mentor explains university template selection **before** asking project-specific questions. Student selects existing/default template or enters dedicated Builder to create one. Maintain Mentor availability as a small dock in builder.
3. Once snapshot is selected, Mentor asks/collects academic education, specialization, project title/description and known technology/methodology; typed and spoken paths are equal. LangGraph orchestrates AI reasoning and pause/resume while the Project Service persists confirmed facts.
4. Student can upload real screenshots, photos, charts or diagram references at intake or during questions. Vision findings stay *candidate observations* until explicitly confirmed.
5. AI creates discipline-aware blueprint and outline, identifies required facts per chapter and asks only unanswered gap-driven questions. If missing methodology/results, ask rather than invent. If answer is ambiguous, show editable transcript and clarification prompt.
6. Before writing, show confirmed facts, unknowns, selected template, plan/page cap and generation CTA. Persist answer and fact provenance, including edits.
7. Start durable background job. Mentor narrates **real** stage transitions (outline, chapter draft, factual/consistency/originality/citation checks, diagrams/charts/optional illustrations, document layout, exports) with identical visible captions; user can mute or switch to text instantly. Show draft vs approved content distinctly in the live formatted preview.
8. On internet loss, tell the user the browser disconnected while backend may continue, then reconnect to authoritative job status; if human input is needed, pause graph, save checkpoint, stop idle job, let student answer and resume in a new execution.
9. Final assembly merges selected initial pages with generated chapters, TOC, references and visuals; compute true page count; validate formatting; show completion only when results truly exist.
10. Hobby gets full permitted preview but **no file download**; Pro Word/PDF; Premium Word/PDF/LaTeX. Require server authorization on all export URLs and actions. After Hobby exhausted with no active plan, show pricing.

### Speech/text parity table

| Robot action | Must appear visually | User can act with voice | User can act with text |
|---|---|---|---|
| Greeting and template guidance | Caption/chat bubble | Listen if enabled | Read, continue, select template |
| Adaptive fact question | Exact question in transcript | Answer via mic | Type answer |
| Answer correction | Transcript editor and confirm | Re-record | Edit text |
| Missing fact clarification | Missing-field explanation | Speak missing details | Type missing details |
| Writing/QA/progress | Real stage status + timestamp | Hear status if opted in | Read text status |
| Failure/reconnect | Error + recovery option | Optional spoken notice | Always readable and actionable |
| Complete/export | Exact report readiness + authorized formats | Hear completion notice | Preview or use allowed export |

## 5. End-to-end responsive acceptance gates

- [ ] **Visual continuity:** all earlier 18 mockup groups map to inventory (see map below); consistent robot style and lavender theme.
- [ ] **Create-project trigger:** robot becomes available on Create New Project, not a mandatory global floating microphone on unrelated pages.
- [ ] **Template-first:** default/personal template selected before project-specific adaptive questions; max 3 saved personal initial-page templates enforced; page reordering fully usable on phone without drag-only dependency.
- [ ] **Caption equality:** each spoken Mentor prompt/status has the same on-screen words; replay and text-only available throughout.
- [ ] **Voice choice:** microphone off until consent; denied/unsupported/muted voice never blocks task; speech transcript editable before critical fact confirmation.
- [ ] **Responsive widths:** 320/360/390/430/768/820/1024/1280/1440/1920 plus landscape, safe-area, virtual keyboard, 200% zoom; no cropped actions or unreadable chat.
- [ ] **Report preview:** during generation, draft vs approved sections, real progress, document page zoom and section navigation remain accessible on mobile.
- [ ] **Visual provenance:** student media distinguished from illustrative AI art; chart numbers originate in confirmed data; diagrams never assert unknown project facts.
- [ ] **Plan truth:** Hobby exactly one max-10-page preview and no exports; Pro one <=100 DOCX/PDF; Premium two <=100 each DOCX/PDF/LaTeX. Ignore erroneous placeholder labels in earlier collage images.
- [ ] **Failure states:** auth expiry, payment decline, quota exhausted, rate limit, offline, job recovery, invalid upload, quality hold, missing data, export error all have usable responsive screens.
- [ ] **Accessibility:** screen reader announces live status without overwhelming, keyboard shortcuts and focus, captions, reduced motion, min touch targets, appropriate contrast.
- [ ] **Screen audit:** every screen/state ID above has desktop/tablet/mobile screenshot or documented shared-layout test and owner before signoff.

## 6. Continuity map — retain our previous illustrated screens

| Earlier 18-screen collage label | New inventory IDs / destination |
|---|---|
| 01 Welcome & Onboarding | `PUB-01`, `PUB-03`, `AUTH-06` |
| 02 Onboarding Profile | `AUTH-06`, `APP-07` |
| 03 Sign In (Google) | `AUTH-01`, `AUTH-02` |
| 04 Mobile OTP Verification | `AUTH-03`, `AUTH-04` |
| 05 Plan Selection & Billing | `PUB-05`, `BILL-01`–`BILL-08` |
| 06 Main Dashboard | `APP-01` |
| 07 University Template Builder | `TPL-01`–`TPL-13` |
| 08 Project Details & Inputs | `PRJ-04`–`PRJ-07` |
| 09 AI Planning & Adaptive Questioning | `PRJ-08`–`PRJ-12`, `BOT-01`–`BOT-09` |
| 10 Live Report Generation (with Recovery) | `GEN-01`–`GEN-03`, `GEN-14`, `SYS-01`–`SYS-03` |
| 11 Plagiarism, Citations & Quality Review | `GEN-04`–`GEN-07` |
| 12 Diagrams, Flowcharts & Charts | `GEN-08`–`GEN-11` |
| 13 Live Document Preview & Editing | `GEN-12`, `GEN-13` |
| 14 Export Options (Word, PDF, LaTeX) | `GEN-15`–`GEN-17` |
| 15 Notifications | `APP-06`, `SYS-09` |
| 16 Settings | `APP-07`–`APP-09`, `BILL-08` |
| 17 Help & Support | `PUB-06`, `APP-10` |
| 18 AI Speaking & Listening (Voice Robot) | `BOT-01`–`BOT-09`, `PRJ-01`, `PRJ-10` |

Prior collage generated copy contains inconsistent sample plan counts and UI controls. **Our architecture and entitlement rules supersede any illustrative mockup text.** Preserve layout direction and subject identity, not wrong plan details.

## 7. Recommended individual high-fidelity mockup production order

The inventory is complete; **screens are not yet finalized individually**. Produce each of these prioritized screen families at minimum at desktop `1440×900`, tablet `820×1180`, and mobile `390×844`, with 320px proof. Keep each family linked to inventory IDs and detailed state variants.

1. Design system and robot component (voice, speaking caption, listening waveform, typed answer, error states).
2. Public landing, authentication, OTP, dashboard and exact pricing/entitlements.
3. New project Mentor welcome, template selection and **separate template-builder full editor**.
4. Intake, image upload/confirmation, project outline, adaptive voice/text dialogue, fact review.
5. Live generation, robot status, progress, interruptions/resume and chapter preview.
6. Quality gates, Mermaid diagrams, conceptual images, real-data charts and asset placement.
7. Final document edit, export states, project history, billing/settings/help, privacy and error states.

Each family must ship a **responsive specification**, not one wide screenshot that is simply shrunk for mobile. Record open decisions (voice vendor, exact pagination/rendering technology, merchant, plagiarism provider) without inventing functionality.

## 8. Traceability and ownership

| Area | UX owner / backend owner | Existing tech & roles |
|---|---|---|
| Public/auth/account | Frontend + Auth Service | Session Guard #2, Notification #5, Safety #31 |
| Entitlements and billing | Frontend + Billing Service | Subscription #3, Payment #4, Job/Quota #30 |
| Template Builder | Frontend + Template/Document Services | Template Architect #6, Layout Validation #29, Tiptap/dnd-kit |
| Project intake, uploads and confirmed facts | Frontend + Project/Visual AI Services | Fact & Provenance #24, Image Understanding #34, Asset Manager #36 |
| Voice Mentor, outline and gap questions | Frontend + AI Orchestration/Project Services | Mentor #1, Analysis #7, Outline #8, Gap #9, Answer Interpreter #25 |
| Long generation and progress | AI Orchestration/Quality/Document Services | Writer #12, Memory #28, Orchestrator #23, Recovery #20, Retry #21, Progress #22 |
| Quality, citations and plagiarism | Quality Service | Citation #13, Consistency #14, Plagiarism #15, Fact #16, Style #17, Source Verify #26, Gate #27 |
| Mermaid and image generation | Visual AI Service | Diagrams #32, Renderer #33, Image Generator #35, Visual Assets #36 |
| Editor, export and R2 files | Document Service | Formatter #18, Export #19, Layout #29 |

**Change-control rule:** Preserve all 48 existing roadmap requirements R01–R48 and 36 responsibilities. The UX inventory adds detail; it doesn't delete or downgrade other requirements. Screens stay as `DESIGNED` only after individual variants are reviewed. Before Cursor coding, use this inventory and four current project references together. No feature is deemed implemented simply because its mockup exists.
