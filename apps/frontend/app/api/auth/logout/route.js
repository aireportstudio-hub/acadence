import { forwardAuthRequest } from "../proxy.js";

export function POST(request) {
  return forwardAuthRequest(request, "/v1/auth/logout").then((response) => {
    if (response.status !== 204) return response;

    const headers = new Headers(response.headers);
    headers.set("Location", new URL("/sign-in", request.url).href);
    return new Response(null, { status: 303, headers });
  });
}
