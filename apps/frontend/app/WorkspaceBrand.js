export default function WorkspaceBrand({ className = "" }) {
  return (
    <a
      className={`workspace-brand ${className}`.trim()}
      href="/"
      aria-label="Acadence home"
    >
      <svg
        aria-hidden="true"
        className="workspace-brand-mark"
        viewBox="0 0 40 40"
        fill="none"
      >
        <path
          d="M5 10.5c5.8-2.4 10.6-1.6 15 1.7v21c-4.4-3.3-9.2-4.1-15-1.7v-21Zm30 0c-5.8-2.4-10.6-1.6-15 1.7v21c4.4-3.3 9.2-4.1 15-1.7v-21Z"
          fill="currentColor"
          opacity=".16"
        />
        <path
          d="M5 10.5c5.8-2.4 10.6-1.6 15 1.7v21c-4.4-3.3-9.2-4.1-15-1.7v-21Zm30 0c-5.8-2.4-10.6-1.6-15 1.7v21c4.4-3.3 9.2-4.1 15-1.7v-21ZM20 12.2v21"
          stroke="currentColor"
          strokeWidth="2.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="workspace-brand-copy">
        <span className="workspace-brand-name">Acadence</span>
        <span className="workspace-brand-tagline">Your AI research partner</span>
      </span>
    </a>
  );
}
