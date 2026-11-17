import ProjectShell from "./ProjectShell";
import { getProjects } from "./project-data";

export const dynamic = "force-dynamic";
export const metadata = { title: "My projects — Acadence" };

export default async function ProjectsPage() {
  const projects = await getProjects("/v1/projects");
  if (!Array.isArray(projects)) throw new Error("Invalid project list response.");
  return (
    <ProjectShell>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="font-semibold text-[var(--ac-primary)]">Your workspace</p>
          <h1 className="text-3xl font-bold">My projects</h1>
        </div>
        <a className="acadence-button-primary inline-flex items-center" href="/projects/new">Create New Project</a>
      </div>
      {projects.length === 0 ? (
        <p className="mt-8 rounded-2xl border border-[var(--ac-border)] bg-white p-6">You have no saved projects yet.</p>
      ) : (
        <ul className="mt-8 grid list-none gap-4 p-0 md:grid-cols-2">
          {projects.map((project) => (
            <li key={project.id} className="rounded-2xl border border-[var(--ac-border)] bg-white p-6">
              <h2 className="text-xl font-semibold">{project.title}</h2>
              {project.description && <p className="whitespace-pre-wrap text-[var(--ac-text-muted)]">{project.description}</p>}
              <a className="inline-flex min-h-11 items-center font-semibold underline" href={`/projects/${encodeURIComponent(project.id)}`}>Open project</a>
            </li>
          ))}
        </ul>
      )}
    </ProjectShell>
  );
}
