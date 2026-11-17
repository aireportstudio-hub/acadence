import ProjectShell from "../ProjectShell";
import { requireSession } from "../project-data";

export const dynamic = "force-dynamic";
export const metadata = { title: "New project — Acadence" };

export default async function NewProjectPage() {
  await requireSession();
  return (
    <ProjectShell>
      <section className="grid gap-6 rounded-2xl border border-[var(--ac-border)] bg-white p-6 md:grid-cols-[180px_1fr]" aria-labelledby="welcome-title">
        <figure className="m-0">
          <img className="h-auto w-36 max-w-full" src="/illustrations/ai-mentor/robo-girl-dashboard-hero.svg" alt="Acadence AI Mentor robot illustration" />
          <figcaption className="text-sm text-[var(--ac-text-muted)]">AI illustration</figcaption>
        </figure>
        <div>
          <p className="font-semibold text-[var(--ac-primary)]">AI Mentor · text mode</p>
          <h1 id="welcome-title" className="text-3xl font-bold">Create New Project</h1>
          <p className="rounded-xl bg-[var(--ac-lavender-100)] p-4">Welcome! I’ll guide you through creating your report. First, choose a university template.</p>
          <p>Template selection and eligibility checks are not available yet. Project creation will be available once both are ready.</p>
          <a className="inline-flex min-h-11 items-center font-semibold underline" href="/projects">Return to my projects</a>
        </div>
      </section>
    </ProjectShell>
  );
}
