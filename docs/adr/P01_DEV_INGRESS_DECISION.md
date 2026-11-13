# P01 Dev Ingress Decision: Worker to private Auth Service

**Status:** Draft — proposed dev proof only; not approved or deployed  
**Prepared:** 2026-11-13  
**Scope:** Cloudflare Worker test route → Google-hosted ingress → private Auth Service `GET /healthz`  
**Roadmap:** P01, minimal authenticated frontend-to-service proof

## Context and verified state

The approved architecture keeps the Cloudflare Worker as the frontend/BFF, keeps
Cloud Run services independently deployed with per-service identities, and
requires audience-bound Google ID tokens and least-privilege
`roles/run.invoker` for private Cloud Run calls. It explicitly leaves
Cloudflare-to-Google authentication open and does not assume Workers can obtain
a Google metadata-server token. See
[`ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`](../ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md)
§§4–5 and [`ACADENCE_TECH_STACK_V2_2.md`](../ACADENCE_TECH_STACK_V2_2.md)
§§BFF caveat / open decisions. P01 calls for one authenticated Worker endpoint
and cross-service permission tests; it does not authorize public Auth access.

Read-only preflight for `acadence-dev-shubh` found:

- The project is ACTIVE and readable by the configured `gcloud` account.
- Billing is disabled and no billing account is linked.
- `run.googleapis.com` is disabled. Listing Cloud Run services failed, so
  service existence, region, URL, ingress mode, and IAM policy could not be
  verified. Reuse of an existing service is unknown.
- Local Auth and Project FastAPI code each defines `/healthz` returning
  `{"status":"ok"}`. Auth is selected for this proof.
- The existing P00 Worker spike has no Cloud Run request or ingress credential
  implementation; `EDGE_TO_API_AUTH_MODE` remains `PENDING_DESIGN`.

No billing, API, IAM, or deployment changes were made. The Git worktree was
clean at preflight.

## Authentication options

| Question | Direct Workload Identity Federation (WIF) | Google-hosted broker proxy |
|---|---|---|
| How the Worker authenticates | Worker obtains a signed external OIDC assertion and exchanges it with Google STS under a narrowly constrained WIF provider. The assertion issuer, audience, and Worker’s ability to obtain the assertion must be proven first. | Worker sends a dedicated Cloudflare Access service-token client ID and client secret to a Cloudflare Access-protected broker URL. Access validates the token and forwards a signed `Cf-Access-Jwt-Assertion`. |
| Credentials held by the Worker | Short-lived external assertion, STS credential, and Google ID token in request-time memory; no downloaded Google service-account key. Do not persist or log tokens. | Cloudflare Access client ID and secret in Worker secret bindings; no Google credential or Google ID token. The Access pair is a static secret and needs rotation/revocation; this is keyless for Google, not credential-free. |
| Where the Google ID token is obtained | Worker exchanges the external assertion at STS, then calls IAM Credentials `generateIdToken` for the target service account, with the Auth service URL as audience. | Broker obtains the ID token at runtime using its attached Cloud Run service identity (metadata server or Google auth library), with the Auth service URL as audience. The token remains server-side and is sent only to Auth. |
| Principal granted Cloud Run Invoker on Auth | A dedicated service account impersonated by the federated Worker identity. Grant the federated principal only the required service-account impersonation permission (`roles/iam.workloadIdentityUser`); grant the service account `roles/run.invoker` on Auth. | The broker’s dedicated runtime service account only. Grant that service account `roles/run.invoker` on Auth. The Worker and Cloudflare Access identity receive no Auth invoker role. |
| Main unresolved point | **Open prerequisite:** no verified Cloudflare Worker OIDC assertion source or supported direct Worker-to-Google WIF flow was established in the preflight. Google supports WIF for external OIDC assertions, but the Worker’s assertion source is not verified. | The broker needs an ingress path. Cloudflare Access service-token/JWT authentication is not a Google-signed ID token and does not satisfy Cloud Run IAM by itself. A Cloud Run broker configured to require IAM authentication would reject the Access request before broker code runs. Do not solve this by granting `allUsers` or disabling the broker’s Invoker IAM check without a separately approved design. |

### Broker proxy constraints

The broker, if selected, is a fixed proxy for **only**
`GET /healthz` on the configured Auth service:

- Accept only the intended test route and GET method. Fix the upstream host and
  path in broker configuration; do not accept caller-controlled URLs, paths,
  methods, headers, or bodies.
- Protect the Worker test route with a Cloudflare Access policy limited to the
  authorized dev tester(s). The Worker must fail closed when Access identity
  is absent or not allowed, before making an upstream request.
- Use a separate Access Service Auth policy for the broker application, limited
  to a dedicated Worker service token. Keep its client ID and secret in Worker
  secret bindings.
- At the broker, require `Cf-Access-Jwt-Assertion`; validate its signature
  using the Cloudflare Access public JWKS, and check the expected issuer,
  application audience, and token validity. A missing, invalid, expired, or
  wrong-audience token must be rejected before the proxy is called. Do not
  trust an unvalidated client-supplied header.
- Give the broker a dedicated user-managed Cloud Run service identity. Obtain
  a Google ID token for the Auth service audience using Cloud Run credentials,
  attach it to the fixed Auth request, and never return or log it.
- Keep Auth IAM-private, with only the broker runtime service account granted
  `roles/run.invoker`. The broker’s own ingress must be resolved separately:
  Cloudflare Access does not cause Google Cloud Run IAM to accept a request.
  If the broker cannot be reached without making it publicly invokable, or
  without adding a separately approved gateway/private network path, the
  broker proof is blocked. App-level Access JWT validation is not a substitute
  for Cloud Run IAM at the broker.

## Recommendation

Do **not** approve direct WIF yet: it has the fewest moving parts, but its
required Worker identity assertion is unverified.

For the first dev proof, prefer evaluating the narrow Google-hosted broker
proxy because it keeps the Google ID token and Auth invoker identity on Google
Cloud, and limits the exposed operation to a health check. Treat it as a
conditional recommendation, not an implementation decision: first establish
an ingress path for the broker that authenticates the Worker without granting
unauthenticated Cloud Run invocation or exposing the private Auth service. If
that cannot be done within the dev constraints, stop and resolve the ingress
design rather than weakening IAM. No option is currently ready to deploy.

## Required proof checks

Run these checks only after the broker ingress, Auth URL, service identity,
and Access policies have been approved and configured.

1. **Authorized Worker call succeeds.** Invoke the protected Worker test route.
   The Worker authenticates to the broker through the designated Cloudflare
   Access policy. The broker validates the Access JWT, fetches a Google ID
   token for the Auth service URL, and calls Auth `GET /healthz`. Pass only if
   the Worker receives HTTP `200` with `{"status":"ok"}` from Auth. Confirm the
   ID token is not returned to the Worker or written to logs.
2. **Direct unauthenticated Auth call is denied by Cloud Run IAM.** From
   outside the Worker and broker, call the same Auth URL and path with no
   authorization token, for example
   `curl -i --max-time 10 "{AUTH_SERVICE_URL}/healthz"`. Pass only if Cloud Run
   IAM rejects it (normally `401`; an ingress-layer denial may differ) and the
   health response is not returned. To claim IAM proof, ensure the request
   reaches Cloud Run’s IAM check rather than being stopped only by network
   ingress.
3. **Unauthorized callers cannot use the Worker route.** Call the Worker test
   route without an accepted Cloudflare Access identity, and separately with
   an identity not allowed by the route policy. Pass only if Access or the
   Worker denies each request and the broker/Auth receive no corresponding
   upstream request. Confirm the route cannot select another host, path, or
   method.

Record the service and policy identifiers (not credentials), request IDs,
response status/body, Cloud Run IAM denial evidence, and broker/Worker logs
with secrets and tokens redacted. These are acceptance criteria, not completed
test results.

## Open prerequisites and blockers

- Billing is disabled; the preflight did not enable billing.
- Cloud Run Admin API is disabled; no services or IAM policies could be listed.
- Whether a reusable Auth service exists and its URL, region, network ingress,
  and current IAM policy are unknown.
- Direct WIF needs a verified Worker-issued external assertion and tested
  STS → IAM Credentials ID-token flow.
- Broker ingress must be designed so Cloud Run IAM at the broker does not
  require a Google credential that the Worker cannot supply, and so an
  unauthenticated route to the broker is not introduced. Do not grant
  `allUsers`, disable Invoker IAM checks, or deploy until this is resolved.
- No live test has been performed. Billing, APIs, IAM, and deployments remain
  untouched.

## Current official references

Checked 2026-11-13:

- Google Cloud, [Authenticating service-to-service](https://docs.cloud.google.com/run/docs/authenticating/service-to-service):
  audience-bound Google ID tokens, `roles/run.invoker`, metadata-server token
  acquisition, and WIF from outside Google Cloud.
- Google Cloud, [Workload Identity Federation with other providers](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-other-providers):
  external OIDC issuer/assertion requirements and short-lived credential
  exchange.
- Google Cloud, [Cloud Run service identity](https://docs.cloud.google.com/run/docs/securing/service-identity):
  attached runtime service-account identity and ADC.
- Google Cloud, [Access control with IAM](https://docs.cloud.google.com/run/docs/securing/managing-access):
  per-service IAM and the `allUsers` public-invocation binding.
- Cloudflare, [Workers and external services](https://developers.cloudflare.com/workers/configuration/integrations/external-services/):
  Worker secret bindings for external-service credentials.
- Cloudflare, [Access service tokens](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/):
  client ID/secret request headers, service-token policies, and rotation.
- Cloudflare, [Validate Access JWTs](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/):
  `Cf-Access-Jwt-Assertion`, account signing keys, issuer, and application
  audience validation.
