import { forwardAuthRequest } from "../proxy.js";

export function GET(request) {
  return forwardAuthRequest(request, "/v1/auth/session");
}
