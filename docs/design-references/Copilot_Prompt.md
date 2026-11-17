# Acadence P03 Task 3 visual update

Finish the existing sign-in and protected dashboard UI. Use the two attached
original mockup sheets and the supplied vector character assets:

- `authentication-ui-showcase.png`: use its Desktop, Tablet, and Mobile
  sign-in panels, focusing on the lavender composition, illustration placement,
  header, card, typography, spacing, and Google button.
- `dashboard-workflow.png`: use the dashboard panels on desktop, tablet, and
  mobile for the sidebar or compact navigation, welcome area, hero banner, and
  placement of the project section. If I provide a different dashboard panel
  as the chosen reference, follow that panel instead.
- Use `robo-girl-auth-hero.svg` on sign-in and
  `robo-girl-dashboard-hero.svg` in the dashboard hero. The other supplied
  variants are for the mentor and report workflow.

Read `.github/copilot-instructions.md`, `.cursor/rules/acadence-ui.mdc`,
`docs/ACADENCE_UI_UX_DESIGN_SYSTEM_V1_0.md`,
`docs/ACADENCE_CURSOR_UI_HANDOFF_V1_0.md`,
`docs/ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md`,
`docs/ACADENCE_UI_UX_FINAL_REVIEW_AND_APPROVAL_MATRIX_V1_0.md`, and
`styles/acadence-design-tokens.css`. Inspect the sign-in and dashboard
pages, buttons, layout, and styles before editing.

Use the real SVG files as static assets. If the repository has no convention
for serving these, place just the two SVGs used by Task 3 in
`apps/frontend/public/illustrations/ai-mentor/`. Keep their intrinsic SVG
aspect ratios and use responsive sizing and positioning. Build the UI as
accessible HTML and CSS, with the reference images used for comparison.
Keep headings, buttons, and navigation as live elements. If the references
aren't accessible or you need a choice between conflicting panels, ask me
before styling the affected screen.

Preserve working Google sign-in, server-side session protection, and sign-out.
The mockups also depict future or sample states. Apply the visual layout to the
current functional scope. Keep mobile OTP unavailable, omit password and
create-account forms, avoid sample project counts or subscription data, and
leave project creation and project endpoints for Task 4. Keep the rest of the
worktree intact.

Run the frontend check and Workers build. Compare screenshots side by side
against the reference panels at desktop (1440 px), tablet (820 px), and mobile
(390 px), and check 320 px for overflow. Verify signed-out redirect, valid
session access, and sign-out. Report whether the full live Google-to-dashboard
flow was exercised. Report any remaining visual differences or blocked check.
