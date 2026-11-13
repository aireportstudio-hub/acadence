# Acadence Copilot Instructions

## Architecture and development sequence

Read docs/ACADENCE_TECH_STACK_V2_2.md, docs/ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md,
docs/ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md, and docs/ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md
before implementing a task. Use the latest sections over the archived sections embedded
in those files. See docs/adr/P00_COMPATIBILITY.md for compatibility evidence and open items.

Keep Cloudflare Workers, the nine Cloud Run service boundaries and service-owned data,
the single LangGraph coordinator, and the approved product and plan rules.
Use verified student inputs for project-specific claims and verified evidence for citations.
Load only the environment variables a component needs. Keep credentials out of Git.
Record the test evidence and any open decision for the requested roadmap task.

## UI and functional requirements

For any Acadence UI changes, read `docs/ACADENCE_UI_UX_DESIGN_SYSTEM_V1_0.md`
and `docs/ACADENCE_RESPONSIVE_UI_UX_SCREEN_INVENTORY_V1_0.md`, plus latest
tech, multi-agent, system architecture, and roadmap references.

The implementation must be fully responsive at 320px+, support keyboard,
Touch/44px targets, 200% zoom, reduced motion, and text-only AI Mentor.
Every spoken Mentor message must have matching visible caption text.
Create New Project activates Mentor. Before asking project-specific questions,
the student must select or create a report template; the separate Builder
supports no more than three saved personal initial-page templates.

Authentication is GOOGLE OIDC OR MOBILE OTP ONLY. No email/password UI.
Plans: Hobby exactly one preview-only report <=10 pages and NO downloads;
Pro one project <=100 pages, DOCX/PDF; Premium two projects <=100 pages,
DOCX/PDF/LaTeX. Never invent prices, renewal policies, adoption metrics,
quality scores, university endorsements or references. Always use actual
backend plan/transaction/quality/status data before claiming success.

Student project facts must be confirmed; image understanding observations
are candidate facts; AI illustrations must be labeled. No fabricated research,
implemented tech, measurements, tests, source URLs, plagiarism assurances or
human-detector evasion.

Treat old generated mockup screenshots as visual inspiration ONLY. The
current design system and product specs override mockup copy/behavior.
Do not modify unrelated screens; cite relevant inventory IDs and test outcomes.
