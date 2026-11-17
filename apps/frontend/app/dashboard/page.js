import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { env } from "cloudflare:workers";
import SignOutButton from "./SignOutButton";
import WorkspaceBrand from "../WorkspaceBrand";

export const metadata = {
  title: "Workspace — Acadence",
  description: "Your protected Acadence workspace.",
};

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const authServiceUrl = env.AUTH_SERVICE_URL;
  if (!authServiceUrl) {
    throw new Error("AUTH_SERVICE_URL must be configured to protect the dashboard.");
  }

  const cookieHeader = (await cookies()).toString();
  const response = await fetch(new URL("/v1/auth/session", authServiceUrl), {
    headers: { Cookie: cookieHeader },
    cache: "no-store",
  });
  if (response.status === 401) {
    redirect("/sign-in");
  }
  if (!response.ok) {
    throw new Error(`Session validation failed with status ${response.status}.`);
  }

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar" aria-label="Workspace">
        <WorkspaceBrand />
        <nav className="dashboard-sidebar-nav" aria-label="Workspace navigation">
          <a href="#overview" aria-current="page">
            <span aria-hidden="true">⌂</span>
            Dashboard
          </a>
          <a href="/projects">
            <span aria-hidden="true">▤</span>
            My projects
          </a>
          <a href="#templates">
            <span aria-hidden="true">▱</span>
            Templates
          </a>
        </nav>
      </aside>

      <div className="dashboard-main-column">
        <header className="dashboard-topbar">
          <WorkspaceBrand className="dashboard-mobile-brand" />
          <p className="dashboard-topbar-label">Your workspace</p>
          <SignOutButton />
        </header>

        <nav className="dashboard-mobile-nav" aria-label="Workspace navigation">
          <a href="#overview" aria-current="page">Dashboard</a>
          <a href="/projects">My projects</a>
          <a href="#templates">Templates</a>
        </nav>

        <main id="main-content" className="dashboard-page" tabIndex={-1}>
          <div className="dashboard-content">
            <section
              id="overview"
              className="dashboard-hero acadence-card"
              aria-labelledby="dashboard-title"
            >
              <div className="dashboard-hero-copy">
                <p className="dashboard-card-kicker">Your workspace</p>
                <h1 id="dashboard-title">Welcome to Acadence</h1>
                <p className="dashboard-description">
                  Reopen your projects or start the guided setup.
                </p>
                <a
                  className="dashboard-create-button acadence-button-primary"
                  href="/projects/new"
                >
                  Create New Project
                </a>
                <p className="dashboard-action-note" id="project-unavailable-note">
                  Template selection and eligibility are not available yet.
                </p>
              </div>
              <figure className="dashboard-hero-art">
                <img
                  src="/illustrations/ai-mentor/robo-girl-dashboard-hero.svg"
                  alt="Acadence AI Mentor robot illustration"
                />
                <figcaption className="illustration-label">
                  AI illustration
                </figcaption>
              </figure>
            </section>

            <section className="dashboard-overview" aria-labelledby="overview-title">
              <div className="dashboard-section-heading">
                <div>
                  <p className="section-kicker">Workspace overview</p>
                  <h2 id="overview-title">A clear place to begin</h2>
                </div>
                <p>
                  Access saved projects and see what is coming next.
                </p>
              </div>

              <div className="dashboard-info-grid">
                <article
                  className="dashboard-info-card acadence-card"
                  id="projects"
                  aria-labelledby="projects-title"
                >
                  <p className="dashboard-card-kicker">My projects</p>
                  <h3 id="projects-title">Project workspace</h3>
                  <p>View and reopen your saved projects.</p>
                  <a href="/projects">View my projects</a>
                </article>
                <article
                  className="dashboard-info-card acadence-card"
                  id="templates"
                  aria-labelledby="templates-title"
                >
                  <p className="dashboard-card-kicker">Templates</p>
                  <h3 id="templates-title">Report structure</h3>
                  <p>The template workspace is not available in this release.</p>
                </article>
                <article className="dashboard-info-card acadence-card">
                  <p className="dashboard-card-kicker">Recent activity</p>
                  <h3>Report status</h3>
                  <p>Activity will appear when the report workflow is connected.</p>
                </article>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
