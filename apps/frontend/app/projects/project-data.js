import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { env } from "cloudflare:workers";

async function sessionCookie() {
  const token = (await cookies()).get("acadence_session")?.value;
  return token ? `acadence_session=${token}` : "";
}

export async function requireSession() {
  if (!env.AUTH_SERVICE_URL) throw new Error("AUTH_SERVICE_URL is not configured.");
  const cookie = await sessionCookie();
  if (!cookie) redirect("/sign-in");
  const response = await fetch(new URL("/v1/auth/session", env.AUTH_SERVICE_URL), {
    headers: { Cookie: cookie },
    cache: "no-store",
  });
  if (response.status === 401) redirect("/sign-in");
  if (!response.ok) throw new Error(`Session validation failed: ${response.status}`);
}

export async function getProjects(path) {
  if (!env.PROJECT_SERVICE_URL) throw new Error("PROJECT_SERVICE_URL is not configured.");
  const cookie = await sessionCookie();
  if (!cookie) redirect("/sign-in");
  const response = await fetch(new URL(path, env.PROJECT_SERVICE_URL), {
    headers: { Cookie: cookie },
    cache: "no-store",
  });
  if (response.status === 401) redirect("/sign-in");
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Project access failed: ${response.status}`);
  return response.json();
}
