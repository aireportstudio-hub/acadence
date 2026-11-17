import WorkspaceBrand from "../WorkspaceBrand";

export default function ProjectShell({ children }) {
  return (
    <div className="min-h-screen bg-[var(--ac-canvas)] text-[var(--ac-text)]">
      <header className="border-b border-[var(--ac-border)] bg-white px-4 py-3">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
          <WorkspaceBrand />
          <nav aria-label="Workspace navigation" className="flex flex-wrap gap-2">
            <a className="inline-flex min-h-11 items-center rounded-xl px-3 font-semibold" href="/dashboard">Dashboard</a>
            <a className="inline-flex min-h-11 items-center rounded-xl px-3 font-semibold" href="/projects">My projects</a>
          </nav>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-5xl px-4 py-8 sm:py-12">
        {children}
      </main>
    </div>
  );
}
