import { env } from "cloudflare:workers";

export async function forwardAuthRequest(request, authPath) {
  const serviceOrigin = env.AUTH_SERVICE_URL;
  if (!serviceOrigin) {
    return Response.json(
      { code: "SERVICE_UNAVAILABLE", message: "Sign-in is temporarily unavailable." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }

  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  const origin = request.headers.get("origin");
  if (cookie) headers.set("Cookie", cookie);
  if (origin) headers.set("Origin", origin);

  const response = await fetch(new URL(authPath, serviceOrigin), {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  });
  const responseHeaders = new Headers(response.headers);
  responseHeaders.set("Cache-Control", "no-store");
  responseHeaders.delete("Content-Length");
  responseHeaders.delete("Content-Encoding");
  return new Response(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}
