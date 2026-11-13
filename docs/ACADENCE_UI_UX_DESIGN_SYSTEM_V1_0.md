# Acadence — Responsive UI/UX Design System v1.0

**Design authority:** Acadence Tech Stack v2.2 + Multi-Agent Architecture v1.1 + System Architecture v1.1 + Development Roadmap v1.0 + Responsive Screen Inventory v1.0.  
**Design direction:** Premium lavender gradient; elegant, friendly, accessible, readable academic work surfaces.  
**Date:** 2026-11-13  
**Status:** **Cursor handoff design baseline** — specification and early concept mockups; neither a production implementation nor approval of every previously generated picture. All **95 inventory IDs** require responsive screen-by-screen QA and approval before UI/UX can be called finished.

> **Precedence rule:** Product/business and accessibility rules in this document and the current architecture **override incidental copy, numbers, metrics, names, screenshots, interactions, and layout sequencing in earlier AI-generated visual mockups**. Preserve their lavender visual direction and robot mascot, not their invented labels or claims.

## 1. The non-negotiable product rules

| Area | Approved behavior |
|---|---|
| Authentication | **Only Google sign-in/sign-up and mobile number OTP**. No email/password sign-in, forgot password or invented sign-up methods. The same verified email/phone resolves to an existing account; enforce device/abuse policy with clear support/appeal and acknowledge physical-device identification limits in browsers. |
| Hobby | Every new account receives **one preview-only report, up to 10 pages**. **No downloads**, including hidden links or file URLs. After consumed, check active paid plan and otherwise show pricing. |
| Pro | **One complete project up to 100 pages**. DOCX and PDF permitted. |
| Premium | **Two complete projects, each up to 100 pages**. DOCX, PDF, LaTeX permitted. |
| Pricing | **No price, billing interval, renewal/reset promise, discount, deadline, or purchase-success state invented**. Use “Price announced at checkout” / blank placeholders until commerce rules are finalized. Server is the authority for all entitlements. |
| Template Builder | Dedicated tab with university-style default templates + **maximum three personal saved templates for initial pages**. Independent page blocks: insert, move up/down, drag, duplicate, delete; full editor with cover/certificate/declaration/acknowledgement/abstract/TOC/chapter/reference/appendix/custom page structures and margins, logos, signatures, fonts, page numbers, headers/footers. Three templates != three pages. |
| Template first | New Project starts the Mentor, but **student selects/creates the template before any project-specific question**. Template selection creates immutable report-linked snapshot. The preliminary pages are assembled with final content, while formatting rules guide preview throughout. |
| Mentor | One visible robot: **starts guiding from Create New Project**, through template selection, intake, adaptive Q&A, generation, quality, errors, preview and completion. Spoken Mentor words appear identically as on-screen captions/transcript. All functionality works using text only; speech is opt-in and microphone never auto-activates. |
| Accuracy | Questions follow education-specific outline and gap analysis. Only confirmed student-supplied implementation details/results can be asserted as student facts. Image analysis observations remain proposed until user confirms. |
| AI visuals | Mermaid diagrams grounded in confirmed facts, data charts from real supplied data, AI image illustrations labeled as such, real uploaded images with asset provenance. No fabricated screenshots or results. |
| Quality | Distinguish factual consistency, real citation verification, originality similarity findings, and content review. Never promise “plagiarism-free”, fake citations, unverifiable scores, or “human-undetectable” text. |
| Live updates | Chapter status, true draft/approved distinctions, current section, retries, user input needed, accurate progress and saved state. Offline browser does NOT automatically mean stopped backend job. |
| Export | DOCX/PDF/LaTeX only as permitted by plan. Actual page count validated after rendering, max not target; no invented 112-page reports for 100-page plans. |

## 2. Design pillars and visual identity

1. **Calm premium academic workspace:** White document canvas, lavender surroundings, dark readable body text.
2. **Human-feeling assistant without inventing human expertise:** Consistent lavender/white friendly robot. Never present artificial verification as fact.
3. **Voice/text parity:** Voice is a convenience; the entire workflow is accessible through the transcript and keyboard.
4. **Institution-first formatting:** Template before interview; document integrity before decorative UI.
5. **Visible truth:** Every status, citation, grade and quota from authoritative services, not illustrations or guessed percentages.
6. **Mobile-first usability:** All content and actions accessible at 320 CSS pixels; document canvas may scroll/zoom within its own boundary.

### Core palette — light mode v1.0

| Token | Value | Usage |
|---|---|---|
| `--ac-primary` | `#6D28D9` | Primary buttons and selected states; 7.1:1 against white |
| `--ac-primary-strong` | `#5B21B6` | Dark violet highlights, contrast |
| `--ac-primary-hover` | `#5B21B6` | Hover/active button surfaces |
| `--ac-accent` | `#A78BFA` | Decorative waveform, gradient accents only |
| `--ac-lavender-100` | `#EDE9FE` | Gentle raised or selected panels |
| `--ac-lavender-200` | `#DDD6FE` | Dividers/decorative accents |
| `--ac-canvas` | `#F9F7FF` | App background |
| `--ac-surface` | `#FFFFFF` | Editor, forms, cards |
| `--ac-surface-muted` | `#F4F0FF` | Secondary panel |
| `--ac-text` | `#251B40` | Main reading color |
| `--ac-text-muted` | `#5E5574` | Secondary labels, contrast-tested |
| `--ac-border` | `#DED6F2` | Borders |
| `--ac-success` | `#137C4A` | Verified success with text/icon |
| `--ac-error` | `#B42318` | Failures with text/icon |
| `--ac-warning` | `#915400` | Warning text on suitable light surface |
| `--ac-focus` | `#6D28D9` | 3px visible keyboard ring |
| `--ac-hero-gradient` | `linear-gradient(135deg, #F9F7FF 0%, #EDE9FE 54%, #D8C7FF 100%)` | Hero/headers only |
| `--ac-action-gradient` | `linear-gradient(110deg, #7C3AED 0%, #5B21B6 100%)` | Primary CTA (white text) |

Use solid high-contrast buttons for critical primary actions, with the gradient reserved for clearly legible surfaces. Never use purple-on-purple low contrast for important text. Background visual gradients **cannot** reduce readability of reports or controls. Keep colored badges meaningful (not decorative for every label).

### Typography

- **Primary UI font:** Inter or compatible system sans-serif; validate `next/font` with Cloudflare Workers deployment. Fallback `ui-sans-serif, system-ui, sans-serif`.
- **Academic document editor font:** The user's **template-selected font** (not forced to Inter). Display typeface choices with realistic previews; exported font availability/embedding requires verification.
- Body: **16px / 1.5** default; secondary **14px / 1.45**. Do not rely on 10–12px UI text from collages.
- Type scale: 12 (small metadata only), 14 (caption), 16 (body), 18 (section), 22 (card header), 28 (page heading), 36–48 (hero responsive); using sensible weight 400/500/600/700.
- Allow 200% browser zoom and text resizing; no truncation of essential form instructions or spoken captions.

### Shape, elevation, density and spacing

- 4px spacing base, 8px-grid major rhythm; standard card padding **16/20/24px** by device.
- Borders 1px, subtle lavender; 12px control radius, 16px card radius, 20–24px hero/panel radius.
- Shadows soft and limited; do not put glass-blur behind the document reading area.
- Minimum touch target **44×44 CSS px**; generous separation between destructive and submit actions.
- Inputs 44–48px minimum height, focus ring 3px with offset; visible error text linked to field.
- Animations 120–240ms for UI transitions; decorative robot gestures may be longer; respect `prefers-reduced-motion: reduce` and provide still avatar.
- No fabricated testimonials, adoption statistics, university endorsements or AI-check percentages in promotional copy.

## 3. Responsive grid, navigation and workspace behavior

| Width | Layout | Navigation | Robot/Chat | Builder/Editor |
|---|---|---|---|---|
| 320–359px | One column; 12–16px outer gutter | Hamburger/drawer or compact bottom bar | Small robot top, **caption beneath**, sticky reply above keyboard/safe-area | Full-screen section editors, explicit Move Up/Down + canvas pan/zoom inside frame |
| 360–767px | One column; 16px gutter | Bottom navigation + drawer for less common items | Robot top, transcript scrollable, typed/voice composer always available | Page list/builder tabs, settings bottom sheet, preview full-screen |
| 768–1023px | One or two columns | Collapsible rail | Avatar and transcript side-by-side if room; progress drawer | Canvas + collapsible list, properties sheet |
| 1024–1439px | Sidebar + content, optional right rail | Compact sidebar | Robot left or dock; conversation main; progress collapsible | Canvas and pages beside inspector if room |
| ≥1440px | 12-column shell with max readable content width | Sidebar | **Robot left + transcript/conversation center + progress right** | Page list left + document center + inspector right |

Test widths **320, 360, 390, 430, 768, 820, 1024, 1280, 1440, 1920**, at 200% zoom, mobile landscape and desktop text resizing. The whole page must not scroll horizontally; **only document and diagram canvases** may be scrollable in a contained viewport. Mobile virtual keyboard cannot obscure `Send`, `Stop listening`, `Confirm`, and template Save. Respect safe-area insets.

### Visual layout rules by area

- Public landing: hero headline + 2 CTAs, robot illustration as non-interactive preview; no automatic speaking on mere landing page.
- Auth: centered clean choice Google / Mobile OTP; no email/password UI; OTP error, resend, back and accessible labels.
- Dashboard: greeting, actual plan usage (or clear placeholder), Create New Project CTA, current projects, saved templates, last known job status.
- Template Selector: default institution-style galleries (verified vs sample badges), 0–3 saved personal designs, `Create Template` and `Use Selected` actions; Mentor greeting is available as caption/dock.
- Template Builder: explicit independent page list with drag + move/duplicate/delete controls; Tiptap content canvas; inspectors for style, headers/footers, placeholder binding; precise saved template version; live preview; native fallback for touch.
- Mentor: exact words are rendered in transcript before/during playback. User can mute, replay, switch to text, edit interpreted answer, and correct project facts. No automatic microphone without explicit start.
- Generation: center report preview with `Draft` / `Approved` and real statuses; Mentor can dock while narrating actual events; side progress becomes drawer on mobile.
- Reports: white paper preview, outline navigation, zoom/scroll, citations/figure tabs, warnings, plan-based download gating.
- Quality: distinguish `Checking`, `Needs evidence`, `Blocked`, `Reviewed`, `Passed with scope` instead of one magical percentage.
- Visual tools: Mermaid code/diagram preview and syntax errors; illustrations explicitly `AI-generated`; real uploads explicitly `Student-provided`; chart editor includes source data/units/accessible table.
- Billing: exact Hobby/Pro/Premium card comparison; price and term only from verified runtime catalog; no hardcoded monthly data.

## 4. UI component contract inventory

These are **logical React component families**, not necessarily one file each. Use shadcn/ui primitives, Tailwind, React Hook Form/Zod, RTK Query according to existing stack.

| Component family | Design contract | Essential states |
|---|---|---|
| `AppShell` / `TopNav` / `MobileNav` | Access-aware app shell, skip-to-main and responsive navigation | expanded/collapsed/mobile/unauthenticated |
| `PageHeader` / `GradientHero` | Section context and one primary action | compact/large/breadcrumb/disabled |
| `PrimaryButton` / `ActionButton` | Brand CTA with focus, disabled and loading | default/hover/focus/loading/disabled/danger |
| `Field` / `Select` / `OtpCodeInput` | Inline validation, keyboard and labels | empty/error/success/expired/rate-limited |
| `PlanCard` / `EntitlementBanner` | Exact quotas, formats, unknown price placeholder | current/trial-used/upgrade/pending |
| `ProjectCard` / `ProjectStatus` | Real job progress and last known state | draft/queued/running/blocked/ready/failed |
| `TemplateCard` / `TemplateSlotMeter` | Personal vs sample templates with 3 slot cap | empty/selected/at-limit/versioned |
| `PageBlockItem` / `PageOrganizer` | Reorder/insert/duplicate/delete initial pages | dragging/keyboard reorder/focus/locked |
| `RichPageCanvas` / `LayoutInspector` | Tiptap body, margin and header/footer controls | edit/preview/overflow/conflict |
| `MentorAvatar` / `MentorDock` | One consistent robot identity; non-blocking dock | idle/speaking/listening/thinking/muted/error/completed |
| `MentorCaption` / `TranscriptList` | **Exact displayed spoken words**, safe scrolling, replay | streaming/final/edited/copied |
| `AnswerComposer` / `VoiceControls` | Equal voice/text input access; mic status | typing/listening/denied/unsupported/offline |
| `FactConfirmationCard` | Verified vs candidate observations, source and edit | proposed/confirmed/conflicted/unknown |
| `OutlineTree` / `QuestionProgress` | Required facts + discipline-aware sections | planning/waiting/revising/approved |
| `GenerationTimeline` / `ProgressAnnouncer` | Backend-truth progress, section state and retry | queued/running/checking/blocked/resuming |
| `DocumentPreview` / `ReportEditor` | Canonical preview, chapter navigator, pagination warning | draft/approved/render-error/saved |
| `CitationIssue` / `SimilarityFinding` | Source support and concrete highlighted passages | supported/unsupported/not-checked/review |
| `MermaidEditor` / `DiagramCanvas` | Source + rendered diagram + error recovery | empty/rendering/invalid/approved |
| `IllustrationCard` / `UploadedAssetCard` | Provenance visible, rights/caption/alt text | uploaded/AI-generated/needs-confirmation/rejected |
| `ExportFormatCard` | Authenticated plan-gated DOCX/PDF/LaTeX | permitted/locked/processing/ready/error |
| `InlineError` / `RecoveryPanel` | Clear cause + saved-state/allowed action | offline/stale/retry/blocked/cancelled |

### Core interaction patterns

- Dialogs and sheets must trap focus as appropriate, return focus to trigger, and provide explicit close; text can be read by screen readers.
- Status updates use `aria-live="polite"`; critical irreversible errors use assertive where justified; avoid announcing every token of a streaming response.
- Captions and transcript use a stable event/message ID; TTS reads the same exact message string after localizing it, and its read state is tracked. Do not synthesize a separate paraphrase that disagrees with transcript.
- Voice settings: `Voice enabled`, `Auto-read mentor responses`, `Microphone permission`, `Language (supported only)`, `Speech rate`, `Show captions` (always on or non-disableable in required mentor workflow).
- Connection recovery: when browser offline, say **“Connection lost. Your saved work is preserved; the report may continue on the server. Reconnecting to check status.”** Never claim worker has definitely paused or resumed until backend confirms.
- Errors expose `Retry`, `Edit answer`, `Contact support`, `Resume later` only where applicable. Do not show fake countdown/ETA.
- Pricing / exports query authoritative entitlements on every privileged action; disabled UI is informative, not the security boundary.

## 5. Speaking Mentor — exact interaction storyboard

1. Student clicks **Create New Project**. Mentor UI opens, renders written greeting; with prior voice opt-in and browser permission, speaks that exact content. No microphone is enabled automatically.
2. Mentor says **“First, select or create the university report template you want to use.”** Student navigates default/sample or three personal saved templates; builder is separate tab. Robot can be minimized to a dock.
3. Selecting a template creates immutable selected snapshot. Mentor can now ask for academic field, education, specialization, project title, project description, actual methodology and known implementation details.
4. Gap planner proposes only missing/meaningful questions based on approved outline. For speech: microphone → transcription → **student review/edit** → confirm → canonical facts. Typing follows same confirmation route.
5. User images/screenshots may be attached. Vision observations are clearly tagged **“AI observation — please confirm”** and never automatically become asserted implementation facts.
6. Robot summarizes current facts, unresolved unknowns, outline and plan limit, requests user confirmation, then starts background report generation.
7. During generation, robot can narrate only real backend events like **“Chapter 2 draft saved; checking accuracy next.”** Display identical text in transcript and a progress timeline. It does not speak invented percentages or fabricated results.
8. If additional fact needed, Mentor asks and records it, while LangGraph saves interrupt state; Cloud Run Job exits during waiting and resumes in a new execution after response.
9. For offline/resume, show last persisted checkpoint and status; offer text-only mode if voice provider fails; never erase previous answers.
10. On completion, report is available for preview and plan-authorized export only. Mentor clearly explains Hobby download lock or Pro/Premium formats.

**Student-friendly default microcopy** (illustrative only, may be copy-reviewed):

| Stage | Visible Mentor caption / spoken sentence |
|---|---|
| Start | “Welcome! I’ll guide you through creating your report. First, choose a university template.” |
| Template done | “Your template is selected. Now tell me about your course and project.” |
| Missing fact | “I still need one detail to describe your actual implementation accurately.” |
| Transcript review | “I heard: ‘I used FastAPI and PostgreSQL.’ Is that correct?” |
| Outline | “I’ve prepared a draft chapter plan based on your field. Please review it.” |
| Writing | “Chapter 2 has been saved as a draft. I’m checking it before approval.” |
| Fact blocked | “The results section needs your actual findings. I won’t invent them.” |
| Connection lost | “Your connection dropped. I’m checking the last saved progress when you reconnect.” |
| Completed | “Your report is ready to preview. Your plan determines which files you can download.” |

## 6. Feature-specific responsive acceptance matrix

| UX feature | Desktop | Tablet | Phone | Mandatory gate |
|---|---|---|---|---|
| Public + auth | Two-column hero/centered auth | Narrow hero/cards | Stack, keyboard aware | Google/OTP only |
| Dashboard | Sidebar/cards/table | Sidebar drawer/cards | Bottom nav/cards/stacked projects | Actual plan status |
| Template selector | Gallery + preview side-by-side | Gallery with overlay preview | Single-column cards, full preview | Template first; 3 slots |
| Template builder | Page list + canvas + inspector | Canvas + drawers | Tabs and full-screen canvas, Move Up/Down | No drag-only actions |
| AI Mentor | Robot + transcript + progress | 2 panels + drawer | Robot/captions + sticky answer input | Voice optional + exact captions |
| Chapter generation | Preview + progress timeline | Preview + collapsible progress | One-pane preview + status sheet | Actual event data |
| QA | Issue list + sources | Stacked cards | Drill-in issue details | Never invented pass/fail |
| Mermaid | Editor and canvas | Tabs | Tabbed code/canvas scroll/zoom | Diagram based on confirmed facts |
| Images/upload | Asset grid + preview | 2-column grid | 1–2-column cards | AI/generated provenance distinct |
| Report editor | TOC + page canvas + properties | TOC drawer + canvas | Full-screen editing with page zoom | Format snapshot maintained |
| Billing/export | Comparison or format cards | Stack | Single-column actions | Exact quotas; verified prices only |
| Failures | Contextual alerts & details | Drawer | Inline bottom sheet | No lost saved progress |

## 7. Accessibility, privacy and content integrity

**Target:** WCAG 2.2 AA as design/testing goal. Validate with automated checks (axe-core in Playwright) and manual keyboard/screen-reader/mobile tests; automated pass alone is not a guarantee. Contrast test every text-on-gradient/background combination. Focus order follows visual reading order. All icons have a label/tooltip where meaning isn't adjacent. No color-only feedback.

- Use proper landmarks, a `Skip to main content` link, consistent heading hierarchy and native input semantics.
- Mentor subtitles are always text; voice never required. `prefers-reduced-motion` disables non-essential avatar/wave animations. Avoid continuous flashing/pulsing.
- Support keyboard page reordering and explicit move controls for template pages; do not require drag gesture.
- File uploads ask for permission/rights; caution on clinical patient/participant material and avoid displaying private data unnecessarily.
- Student uploads and AI illustrations use separate badge text, with provenance/confirmation and actual source/rights metadata.
- Citation UI never substitutes a fake DOI/source URL; if claim verification fails, show `Unsupported—needs evidence`.
- Plagiarism similarity results appear only if an eligible comparison source actually ran; no global plagiarism-free guarantee.
- Public pages do not contain made-up adoption counts, official university endorsement or fabricated customer ratings.
- User sessions, project contents and financial data are loaded from authenticated services; user interface is not a source of truth.

## 8. Reconciliation of earlier mockup problems — fixed contract

| Earlier illustrative artifact problem | Approved replacement |
|---|---|
| Email/password and forgot password on login screenshots | Google OAuth or Mobile OTP exclusively |
| Hobby 25–30 pages, downloads on free plan, extra plans named Student/Academic | Hobby **1×10 preview only**, Pro **1×100 DOCX/PDF**, Premium **2×100 DOCX/PDF/LaTeX** |
| Random ₹499/₹999 monthly, yearly toggle or fabricated renewal | Price and renewal term are **TBD** and only shown when configured by billing provider/catalog |
| Robot asks project topic before template selection | Mentor **greets**, directs user to template, then project-specific Q&A begins **after template selection** |
| Fake university official template logos or unsupported institution claims | Label `Sample university-style layout` until verified and institution rules reviewed |
| Invented 10k+ students, 25k+ reports, 4.8/5, plagiarism 0–4%, 96/100 | Omit fake marketing and QA metrics; show real measured/verified only |
| More than 100 pages, “100 pages always” | **Up to 100 pages** for paid projects, actual limit checked after rendering |
| Fake screenshot/model accuracy or diagram described as actual result | Require confirmed implementation/data; AI visuals labeled conceptual |
| Universal “download report” button active for Hobby | Disabled with explanation/upgrade, server rejects downloads |
| Offline banner saying generation definitely paused | Backend job status queried; browser disconnect != backend stop |
| Ambiguous pause/resume semantics | Frontend control requests server action; show status only after confirmation; idempotent resume |

## 9. Design source and screen coverage

The full **95-ID inventory** is in `ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md` and forms part of this handoff. It includes:

- Public website `PUB-01..07` (7)
- Google/mobile OTP & onboarding `AUTH-01..08` (8)
- App shell and account `APP-01..10` (10)
- University Template Builder `TPL-01..13` (13)
- Create New Project `PRJ-01..13` (13)
- Voice/text Mentor modes `BOT-01..09` (9)
- Generation, quality, visuals, export `GEN-01..17` (17)
- Billing `BILL-01..08` (8)
- Recovery/system `SYS-01..10` (10)

**Total = 95.** Each ticket, screenshot and implementation test should reference one or more IDs. Work does not close because a single collage visually implies support. Treat ALL older visual images as **concept inspiration**, not final pixel/interaction/requirements authority.

## 10. Completion and approval criteria

To mark **Acadence UI/UX complete** (not yet reached), require all of the following:

- [ ] Every one of the 95 IDs has individually reviewed desktop, tablet and phone layouts or a documented reusable state with responsive screenshots.
- [ ] Every major interactive behavior has a prototype/wireflow, including template-first Mentor, text-only path, stop speech, mic permission, confirmation and saved-progress recovery.
- [ ] No mockup shows invented plans, quota terms, university endorsement, plagiarism verification, adoption figures or scientific claims.
- [ ] All critical screens meet 320px readability, 200% zoom, keyboard, reduced-motion, and mobile touch requirements.
- [ ] Template builder has at least 3 initial pages, custom layouts, 3 personal template slots, reorder via accessible controls, header/footer and preview states.
- [ ] Report-generation experience distinguishes draft/approved, real progress, missing facts, source verification and export entitlements.
- [ ] Export styling/renderer fidelity tested later in implementation; no claim of perfect parity without evidence.
- [ ] Component documentation and Cursor constraints are used and reviewed for each implementation PR.

## 11. Hand-off linkage to technical architecture

| Frontend concern | Implementation boundary |
|---|---|
| Auth/sign-up | Next.js UI → Auth Service; Google/mobile OTP only; backend policy authoritative |
| Plans/pricing | Billing Service and Plan Catalog; UI shows only verified runtime plans |
| Templates | Template Service canonical page blocks + versioned snapshot; Tiptap 3/ProseMirror and dnd-kit |
| Intake/answers | Project Service persists answer sources; AI Mentor receives approved question/state via AI Orchestration |
| Voice | Opt-in STT/TTS adapter, answer transcript correction, no mic without consent |
| Generation | AI Orchestration + Cloud Run Jobs; SSE last-event cursor/polling fallback; persistent section state |
| Quality | Quality Service separate originality/citation/fact/consistency, evidence-backed statuses |
| Visuals | Visual AI Service separate uploads, Mermaid, AI illustrations, verified charts and asset provenance |
| Editor/exports | Document Service uses canonical document representation, template layout, gated exports to R2 |
| Messages | Notification Service provides actual events, avoids invented completion |

**Change protocol:** UI updates affecting a previously locked product rule require updating this file, the 95-screen inventory if necessary, and current architecture references using versioned changes; no silent changes to the stack or subscription rules.
