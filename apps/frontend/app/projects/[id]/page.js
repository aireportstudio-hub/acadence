import { notFound } from "next/navigation";
import ProjectShell from "../ProjectShell";
import { getProjects } from "../project-data";

export const dynamic = "force-dynamic";
export const metadata = { title: "Project — Acadence" };

export default async function ProjectPage({ params }) {
  const { id } = await params;
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) notFound();
  const project = await getProjects(`/v1/projects/${id}`);
  if (!project) notFound();
  return (
    <ProjectShell>
      <a className="inline-flex min-h-11 items-center font-semibold underline" href="/projects">Back to my projects</a>
      <article className="mt-4 rounded-2xl border border-[var(--ac-border)] bg-white p-6">
        <p className="font-semibold text-[var(--ac-primary)]">Project</p>
        <h1 className="text-3xl font-bold">{project.title}</h1>
        <h2 className="mt-6 text-xl font-semibold">Description</h2>
        <p className="whitespace-pre-wrap text-[var(--ac-text-muted)]">{project.description || "No description provided."}</p>
        <p className="mt-6">Template selection and report workflows are not yet available.</p>
      </article>
    </ProjectShell>
  );
}
