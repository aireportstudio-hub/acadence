# Acadence — Cursor UI Implementation Handoff v1.0

**Status:** Instructions for *future implementation* in Cursor. No claim that frontend code is already working or tested.  
**References:**
- `ACADENCE_TECH_STACK_V2_2.md`
- `ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`
- `ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`
- `ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md`
- `ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md`
- `ACADENCE_UI_UX_DESIGN_SYSTEM_V1_0.md`
- `styles/acadence-design-tokens.css`

## Implementation contract

1. Use **Next.js App Router + TypeScript + Tailwind + shadcn/ui**; target Cloudflare Workers. Do not silently swap to Pages or change the approved stack. Validate vinext/Next.js compatibility before production deployment.
2. Build responsive **mobile-first** functional components, with design breakpoints 320+, 360–767, 768–1023, 1024–1439, ≥1440. Document page/diagram areas can scroll internally; app chrome cannot overflow horizontally.
3. **Design hierarchy:** existing lavender mockups = visual inspiration; design system + 95-screen inventory + architecture = functional contract. No copying mockup inaccuracies.
4. **Auth:** Google or mobile OTP only; no email/password fields or password reset pages.
5. **Plans:** Hobby preview-only 1×10; Pro 1×100 DOCX/PDF; Premium 2×100 DOCX/PDF/LaTeX. Prices, terms and renewal policies must come from a verified backend catalog and should remain placeholders until defined.
6. **New Project:** AI Mentor appears at Create New Project and greets with text; ask template selection FIRST, then student/project questions and adaptive follow-ups. Captions must match spoken text byte-for-byte (or exactly per chosen language), and users can fully complete with typing. Mic permission is explicit; voice never mandatory.
7. **Templates:** up to three personal saved initial-page designs, default templates, reusable page blocks, move/duplicate/delete/insert, editable cover/certificate/declaration/acknowledgement/abstract/TOC/chapter/reference/appendix/custom blocks; versioned selection.
8. **Progress/Quality:** show only server-confirmed statuses, draft vs approved, actual retry/blocked states. Cite evidence only after verification. Uploaded project photos are separate from AI illustrations.
9. **Export:** never issue client-side download bypass. Authorize every export through backend; render page count according to selected template and limits.
10. **Tests:** responsive screenshot tests, keyboard/mic-denial/text-only, project quota and export locked UI, template reorder without dragging, reconnect and resume, trace status parity, actual source records.

## Recommended directory outline

```text
apps/frontend/
  app/
    (public)/
    (auth)/
    (protected)/
      dashboard/
      projects/
      templates/
      reports/
      billing/
      settings/
  components/
    acadence-ui/             # accessible reusable primitives
    navigation/
    mentor/                  # robot, captions, voice/text composer
    templates/               # selector, page organizer, editor, inspector
    projects/                # intake, facts, questions, progress
    reports/                 # preview, quality, citations, visuals, export
  features/
    auth/ billing/ project/ template/ mentor/ report/ visual/
  styles/
    acadence-design-tokens.css
  tests/
```

## Screen-by-screen task template for Cursor

```text
Implement ONLY screen ID: <e.g. PRJ-02> from
ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md.
Read ACADENCE_UI_UX_DESIGN_SYSTEM_V1_0.md, all current architectural
reference files and the specific screen acceptance rule before coding.
Preserve Cloudflare Workers + Next.js + TypeScript + Tailwind + shadcn/ui.
Deliver desktop, tablet and 320px mobile layouts; keyboard and touch
alternatives; error/loading/empty states; and source-aligned test cases.
For API-dependent data, use clearly named mock fixtures during UI development,
never invented claims or a fake purchase-success flow. Do not modify unrelated
routes or implement other screen IDs. Report what was actually tested.
```

## Source-of-truth rules

- No hard-coded report progress percentages; use persisted event status.
- No hard-coded fake project score, plagiarism percentage, citations or reference URLs.
- No fake university authorization/logo; mark sample examples.
- No audio-only robot interface or silent mandatory voice mode.
- When user facts are incomplete, display a clarification state rather than invented implementation/results.
- No payment approval or plan access based on static frontend state.
- No cross-service database shortcuts; service contracts govern data.

## Acceptance gate per screen

- [ ] Correct inventory ID and content/workflow sequence.
- [ ] 320, 390, 768, 1024, 1440 desktop/tablet/mobile screenshots captured.
- [ ] No horizontal document-external overflow; keyboard controls/touch targets ≥44px.
- [ ] Screen reader labels, focus, reduced motion, visible caption alternatives.
- [ ] Empty/loading/error/retry states tested.
- [ ] Correct plan/permission/template/robot behavior.
- [ ] Accurate API models, source IDs, state tracking; no fabricated progress.
- [ ] Lint, unit/component tests and relevant Playwright tests pass or blockers recorded.

## Suggested first UX implementation slices

1. Design tokens, buttons, inputs, navigation, responsive shell, and auth choice screen.
2. Dashboard + Create New Project + Mentor welcome + template-first selector (typed-only functional prototype first).
3. Dedicated template builder and saved template snapshots; mobile reorder/accessibility.
4. Typed adaptive Q&A and answer-confirmation UI with mock structured job state.
5. Live narration/caption persistence, voice opt-in and robust mic fallback.
6. Generation progress + draft/approved preview + recovery states.
7. Visuals and quality review + plan-gated export UI.
8. All remaining 95 inventory screens/states in dependency order, with QA evidence.

**Do not implement all 95 screen IDs in a single giant Cursor prompt.** Work in small increments and verify each slice.
