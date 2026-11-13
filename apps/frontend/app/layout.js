import "./public-shell.css";

export const metadata = {
  title: "Acadence — Start with the right report structure",
  description:
    "Explore a template-first approach to academic reports, with a guided AI Mentor workflow.",
};

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

function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a className="brand-link" href="/" aria-label="Acadence home">
          <BrandMark />
          <span>Acadence</span>
        </a>
        <nav className="site-nav" aria-label="Main navigation">
          <a href="#templates">Templates</a>
          <a href="#workflow">How it works</a>
          <a className="nav-cta" href="#workflow">
            Explore Acadence
          </a>
        </nav>
      </div>
    </header>
  );
}

function SiteFooter() {
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

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="acadence-app">
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}