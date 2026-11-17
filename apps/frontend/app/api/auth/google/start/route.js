import { env } from "cloudflare:workers";

export async function GET() {
  const serviceOrigin = env.AUTH_SERVICE_URL;
  if (!serviceOrigin) {
    return Response.json(
      { code: "SERVICE_UNAVAILABLE", message: "Sign-in is temporarily unavailable." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  const upstream = await fetch(new URL("/v1/auth/google/start", serviceOrigin), {
    cache: "no-store",
    redirect: "manual",
  });
  if (!upstream.ok) {
    return new Response(null, {
      status: upstream.status,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const result = await upstream.json();
  let authorizationUrl;
  try {
    authorizationUrl = new URL(result.authorization_url);
  } catch {
    return Response.json(
      { code: "UPSTREAM_ERROR", message: "Sign-in could not be started." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
  if (
    authorizationUrl.protocol !== "https:" ||
    authorizationUrl.hostname !== "accounts.google.com"
  ) {
    return Response.json(
      { code: "UPSTREAM_ERROR", message: "Sign-in could not be started." },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }

  const headers = new Headers(upstream.headers);
  headers.set("Location", authorizationUrl.href);
  headers.set("Cache-Control", "no-store");
  headers.delete("Content-Length");
  headers.delete("Content-Encoding");
  return new Response(null, { status: 303, headers });
}
