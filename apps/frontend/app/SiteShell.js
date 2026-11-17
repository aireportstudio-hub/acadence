function BrandMark() {
  return (
    <svg
      aria-hidden="true"
      className="brand-mark"
      viewBox="0 0 40 40"
      fill="none"
    >
      <rect x="1" y="1" width="38" height="38" rx="12" fill="currentColor" />
      <path
        d="M11 27.5 19.9 10l9.1 17.5M14.2 21.5h11.5"
        stroke="white"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function PublicHeader() {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a className="brand-link" href="/" aria-label="Acadence home">
          <BrandMark />
          <span>Acadence</span>
        </a>
        <nav className="site-nav" aria-label="Main navigation">
          <a href="/#templates">Templates</a>
          <a href="/#workflow">How it works</a>
          <a className="nav-cta" href="/sign-in">
            Sign in
          </a>
        </nav>
      </div>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <a className="footer-brand" href="/">
          Acadence
        </a>
        <p>Start with your structure. Build from your own ideas.</p>
        <a href="#main-content">Back to top</a>
      </div>
    </footer>
  );
}
