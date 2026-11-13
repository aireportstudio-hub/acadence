function MentorIllustration() {
  return (
    <svg
      aria-label="A friendly Acadence robot beside a sample report layout"
      className="mentor-illustration"
      role="img"
      viewBox="0 0 520 440"
    >
      <defs>
        <linearGradient id="robot-shell" x1="120" y1="110" x2="320" y2="340">
          <stop stopColor="#FFFFFF" />
          <stop offset="1" stopColor="#EDE9FE" />
        </linearGradient>
        <linearGradient id="robot-screen" x1="170" y1="175" x2="305" y2="270">
          <stop stopColor="#7C3AED" />
          <stop offset="1" stopColor="#5B21B6" />
        </linearGradient>
      </defs>
      <ellipse cx="273" cy="385" rx="174" ry="24" fill="#6D28D9" opacity=".1" />
      <rect x="334" y="86" width="146" height="222" rx="18" fill="#FFFFFF" stroke="#DED6F2" strokeWidth="2" />
      <rect x="356" y="111" width="84" height="8" rx="4" fill="#6D28D9" />
      <rect x="356" y="137" width="102" height="5" rx="2.5" fill="#DED6F2" />
      <rect x="356" y="151" width="88" height="5" rx="2.5" fill="#DED6F2" />
      <rect x="356" y="180" width="100" height="45" rx="8" fill="#F4F0FF" />
      <path d="M367 212h17l10-17 11 17 10-10 12 10" stroke="#7C3AED" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="356" y="243" width="96" height="5" rx="2.5" fill="#DED6F2" />
      <rect x="356" y="258" width="76" height="5" rx="2.5" fill="#DED6F2" />
      <rect x="76" y="178" width="310" height="190" rx="76" fill="url(#robot-shell)" stroke="#DED6F2" strokeWidth="3" />
      <path d="M230 178v-28c0-16 13-29 29-29h14" fill="none" stroke="#6D28D9" strokeWidth="8" strokeLinecap="round" />
      <circle cx="286" cy="119" r="13" fill="#A78BFA" />
      <rect x="133" y="218" width="196" height="98" rx="35" fill="url(#robot-screen)" />
      <circle cx="189" cy="265" r="8" fill="white" />
      <circle cx="273" cy="265" r="8" fill="white" />
      <path d="M208 286c10 9 27 9 37 0" fill="none" stroke="white" strokeWidth="5" strokeLinecap="round" />
      <path d="M103 249h-21c-16 0-29 13-29 29v15" fill="none" stroke="#A78BFA" strokeWidth="8" strokeLinecap="round" />
      <circle cx="53" cy="302" r="12" fill="#A78BFA" />
      <path d="M178 368v15m106-15v15" stroke="#6D28D9" strokeWidth="12" strokeLinecap="round" />
      <rect x="140" y="379" width="62" height="15" rx="7.5" fill="#5B21B6" />
      <rect x="263" y="379" width="62" height="15" rx="7.5" fill="#5B21B6" />
      <path d="M115 153c-15-13-15-36 0-49" fill="none" stroke="#A78BFA" strokeWidth="5" strokeLinecap="round" />
      <path d="M348 56c10-9 24-9 34 0m-17-17v34" stroke="#6D28D9" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}

const workflowSteps = [
  {
    number: "01",
    title: "Choose a report template",
    description:
      "Begin with a university-style structure that suits your report. Check your institution's own requirements as you choose.",
  },
  {
    number: "02",
    title: "Work through your project",
    description:
      "The AI Mentor guides you through project questions. Share what you know in text, with voice as an optional way to respond.",
  },
  {
    number: "03",
    title: "Review as you build",
    description:
      "Keep your own project details at the center and review report content and supporting information before you use it.",
  },
];

export default function HomePage() {
  return (
    <main id="main-content" className="public-main" tabIndex={-1}>
      <section className="acadence-hero" aria-labelledby="hero-title">
        <div className="hero-inner page-width">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="eyebrow-dot" aria-hidden="true" />
              A clearer way to shape your report
            </p>
            <h1 id="hero-title">
              Your project,
              <br />
              <span>with a plan.</span>
            </h1>
            <p className="hero-description">
              Start with a university-style report template, then work through
              your project with a text-first AI Mentor—one thoughtful step at a
              time.
            </p>
            <div className="hero-actions">
              <a className="acadence-button-primary hero-primary" href="#templates">
                Explore templates
                <span aria-hidden="true">→</span>
              </a>
              <a className="hero-secondary" href="#workflow">
                See how it works
              </a>
            </div>
            <p className="hero-note">
              Your project details stay yours to confirm and refine.
            </p>
          </div>
          <div className="hero-art">
            <div className="art-orbit art-orbit-one" aria-hidden="true" />
            <div className="art-orbit art-orbit-two" aria-hidden="true" />
            <div className="art-label">
              <span className="art-label-dot" aria-hidden="true" />
              Your ideas, in focus
            </div>
            <MentorIllustration />
            <div className="art-caption">
              <span className="caption-sparkle" aria-hidden="true">✦</span>
              <span>Guidance that keeps you in control</span>
            </div>
          </div>
        </div>
        <div className="hero-bottom-rule" aria-hidden="true" />
      </section>

      <section
        id="templates"
        className="templates-section page-width"
        aria-labelledby="templates-title"
      >
        <div className="section-heading">
          <p className="section-kicker">A strong start</p>
          <h2 id="templates-title">Begin with the format in mind</h2>
          <p>
            Set up your report structure before you dive into project-specific
            questions. Look for clear labels that distinguish sample layouts
            from institution-verified templates.
          </p>
        </div>
        <div className="template-feature acadence-card">
          <div className="template-preview" aria-hidden="true">
            <div className="preview-page">
              <div className="preview-seal">A</div>
              <span className="preview-rule preview-rule-long" />
              <span className="preview-rule preview-rule-short" />
              <span className="preview-rule preview-rule-mid" />
              <span className="preview-rule preview-rule-long" />
              <span className="preview-rule preview-rule-short" />
              <div className="preview-footer" />
            </div>
            <div className="preview-tag">Sample layout</div>
          </div>
          <div className="template-copy">
            <span className="content-label">Template-first workflow</span>
            <h3>A structure you can make your own</h3>
            <p>
              Explore university-style report structures and choose a starting
              point that fits your needs. A sample is a starting point—not a
              claim of official university approval.
            </p>
            <a className="text-link" href="#workflow">
              See the steps
              <span aria-hidden="true">→</span>
            </a>
          </div>
        </div>
      </section>

      <section
        id="workflow"
        className="workflow-section"
        aria-labelledby="workflow-title"
      >
        <div className="page-width workflow-inner">
          <div className="section-heading workflow-heading">
            <p className="section-kicker">A guided workflow</p>
            <h2 id="workflow-title">From template to a report you can review</h2>
            <p>
              The AI Mentor helps organize your process while you stay in
              charge of the facts and choices in your project.
            </p>
          </div>
          <ol className="workflow-grid">
            {workflowSteps.map((step) => (
              <li className="workflow-card acadence-card" key={step.number}>
                <span className="step-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </li>
            ))}
          </ol>
          <p className="workflow-footnote">
            Voice is optional. The Mentor's guidance is available as text.
          </p>
        </div>
      </section>
    </main>
  );
}