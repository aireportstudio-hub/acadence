# P01 remaining execution checklist

**Status:** Execution checklist; all four work items remain blocked or open pending the evidence below.
**Prepared:** 2026-11-13
**Scope:** Documentation and read-only status only. No billing/API enablement, deployment, IAM change, key creation, or service-code change is authorized by this checklist.

## Source of truth and current evidence

Use the [P01 Auth deployment and rollback runbook](./P01_AUTH_SERVICE_DEV_DEPLOYMENT_ROLLBACK.md) for Auth preflight, identities, deployment, verification, rollback, and evidence details. Use the [P01 ingress decision](../adr/P01_DEV_INGRESS_DECISION.md) for the Worker authentication options and their required proof. Use the [Project fact-snapshot contract](../../packages/api-contracts/project-fact-snapshot.v1.md) for the proposed internal interaction, version pinning, actor authorization, and open contract decisions. This checklist tracks gates and evidence; it does not replace or approve those sources.

The recorded Auth preflight says billing is disabled and `run.googleapis.com` is disabled; the service inventory, region, URL, serving revision, and IAM policy could not be verified. The ingress ADR records no live Worker-to-Cloud Run proof and no approved ingress option. The fact-snapshot contract is a draft and is not implemented or deployed. These are recorded findings, not fresh cloud checks performed for this checklist. See also [P00 compatibility status](../adr/P00_COMPATIBILITY.md), which distinguishes local probes from the live proof required by P00.

## Execution order and summary

| # | Work item | Status | Blocker | Next action |
|---|---|---|---|---|
| 1 | Auth deployment and rollback rehearsal | **BLOCKED** | Recorded billing and Cloud Run API gates are not clear; deployment inputs and live service state are unverified. | An authorized operator resolves the separately approved prerequisites, performs the read-only preflight in the runbook, then schedules the Auth rehearsal. |
| 2 | Worker to private Cloud Run authentication | **BLOCKED — design open** | Direct WIF assertion source is unverified; broker ingress has no approved path that preserves the required IAM boundary. | Prove the candidate identity and ingress flow, then record an approved decision in the ingress ADR before any deployment. |
| 3 | Independent deploy, rollback, and permissions for nine services | **BLOCKED — depends on 1** | No passing Auth rehearsal or per-service live evidence is recorded. | Use the passing Auth rehearsal as the template; execute the repeated checks in §3 for all nine services. |
| 4 | Internal contracts and environment setup | **BLOCKED — decisions open** | Actor-context delegation and pinned-snapshot recovery are unresolved; environment and operations evidence is incomplete. | Approve the contract decisions and complete the environment/operations evidence checklist in §4. |

Do not treat an HTTP response, local test, draft contract, or proposed command as proof of a live gate. Record exact outcomes, timestamps, resource identities, and redacted evidence in the authorized change/rehearsal record. Do not record tokens, secrets, or other credentials.

## 1. Auth Service deployment and rollback

**Status:** **BLOCKED**
**Blocker:** The runbook's latest recorded preflight found billing disabled and Cloud Run API disabled. It could not verify the service, region, URL, serving revision/traffic, or IAM policy. The approved region, repository, runtime service account, deployer/IAM-admin/test-caller permissions, and Artifact Registry API state also require confirmation. No deployment or rollback evidence exists in the records reviewed.

**Next action:** After the relevant approvals and prerequisites have been resolved outside this documentation-only task, an authorized operator follows the runbook's read-only preflight and completes the Auth rehearsal. Stop on access/query errors; they do not prove a service is absent. Do not infer the serving revision from `latestReadyRevisionName`; confirm actual traffic assignments. Keep the Worker ingress decision separate and open until its own proof passes.

**Evidence needed to mark complete:**

- **Pre-deployment gate:** Redacted record of active operator/project identity, project state, billing and required API states, approved region, repository, runtime service account, service existence or approved create/update decision, stable service URL, current serving revision(s) and traffic, and service-level IAM policy. Confirm `allUsers` is absent and the intended caller is granted only service-level Invoker as approved. Record deployer, IAM administrator, and test-caller permission evidence. No credentials or token values.
- **Authorized health response:** From the authorized test caller and the same approved network path used for the negative test, `GET /healthz` returns HTTP `200` and JSON `{"status":"ok"}`. Record timestamp, URL/resource identity, response, request ID when available, and caller identity.
- **Unauthenticated IAM denial:** A direct request to that same URL/path without an Authorization header receives Cloud Run IAM denial (normally HTTP `401` or `403`) and does not return the application health response. Correlate request/time with Cloud Run evidence and prove the source reached the IAM check; DNS/TLS/transport failure, HTTP `000`, or an ingress-only rejection is inconclusive, not a pass.
- **Known-good rollback:** Before calling a revision known-good, prove its authorized health check. Record the exact revision and traffic state. On an authorized rollback rehearsal, record reason and before/after traffic, shift to the verified known-good revision, verify it receives `100%`, reread IAM to confirm public invocation remains disabled, and repeat both authorized and unauthenticated health checks. Include timestamps and change/incident reference. If this is the first deployment and no prior revision exists, record that no rollback target exists; do not guess a revision or call a corrected deployment a rollback.
- Record image source commit, unique tag and digest, deploy result/revision, traffic, and redacted logs/evidence as required by the runbook.

## 2. Cloudflare Worker to private Cloud Run authentication

**Status:** **BLOCKED — design open**
**Blocker:** The ingress ADR has no approved or tested option. Direct Workload Identity Federation (WIF) lacks a verified Worker-issued external OIDC assertion. The broker option remains conditional because Cloudflare Access authentication alone does not satisfy Cloud Run IAM, and a Cloud Run broker requiring IAM may reject the Worker before broker code runs. Billing and Cloud Run API blockers also prevent a live proof.

**Next action:** Compare and prove the required identity and ingress path for each viable option, keeping the Auth service private. Record the selected, approved design and its constraints in the ingress ADR before implementation or deployment. Do not grant `allUsers`, disable Cloud Run Invoker IAM checks, or claim Access JWT validation substitutes for Cloud Run IAM.

**Evidence needed to mark complete:**

- **Direct WIF candidate:** Evidence that the Worker can obtain a signed external OIDC assertion; verified issuer, audience, subject constraints and expiry; constrained Google STS exchange; successful IAM Credentials ID-token minting for the target Auth service audience; and least-privilege impersonation/Invoker permissions. Prove the full authorized call without a downloaded service-account key or token persistence/logging. If the assertion source cannot be verified, reject this path as unproven.
- **Broker candidate:** Document and test a broker ingress path that admits the intended Worker but does not create unauthenticated Cloud Run invocation or weaken the broker's IAM boundary. Prove the Worker service-token policy, broker validation of the Access JWT (signature, issuer, application audience and validity), fixed `GET /healthz` upstream, dedicated broker runtime identity, and audience-bound Google ID token to private Auth. Prove secrets are stored only in approved Worker secret bindings, can be rotated/revoked, and are neither returned nor logged. If a safe broker ingress path cannot be demonstrated, stop and leave this design blocked.
- **Authorized Worker call:** Call only the approved protected Worker test route. Pass only on HTTP `200` with `{"status":"ok"}` from Auth, correlated through Worker/broker/Auth request evidence. Confirm the Google token is not returned to the Worker or written to logs.
- **Direct unauthenticated call:** From outside the Worker and broker, call the same private Auth URL and path without authorization. Confirm the health body is not returned and Cloud Run IAM denied the request; an ingress/network rejection alone is not proof of the IAM boundary.
- **Unauthorized Worker callers:** Test both a request with no accepted Access identity and one with an identity not allowed by the route policy. Each must be denied before any broker/Auth upstream request. Verify the test route cannot change upstream host, path, or method. Preserve request IDs/statuses and redacted Worker, broker, and Cloud Run evidence.

The ADR's recommended broker is conditional, not a selected or approved implementation. Keep the decision open until its ingress prerequisite and the end-to-end evidence above pass.

## 3. Independent deployment and permissions for all nine services

**Status:** **BLOCKED — depends on the Auth rehearsal in §1**
**Blocker:** No passing Auth rehearsal or per-service deploy, rollback, or permission evidence is recorded. P01 calls for nine independently deployable skeleton services, not nine completed product implementations.

**Next action:** After the Auth rehearsal passes, use its approved process and evidence format as the first service gate. Then execute and record the following checks separately for every service. Do not combine deployment identities, traffic changes, service IAM grants, or rollback evidence across services.

**Repeat for each service:** (a) verify that its own build/deploy path changes only that service; (b) record image digest, service URL, revision and traffic; (c) verify its health/ready endpoint and service-specific configuration; (d) verify deployment and rollback leave the other eight services unchanged; (e) prove rollback to a health-verified known-good revision, or record that none exists on first deployment; (f) verify its dedicated runtime identity and least-privilege IAM; and (g) for each approved contract caller/receiver pair involving the service, prove the intended audience-bound authenticated call succeeds and missing, wrong-identity, wrong-audience, and ungranted calls are denied. Confirm service-level—not project-wide—Invoker scope, no public `allUsers` binding, application scope/tenant checks, and correlated redacted evidence.

| Service | Separate deployment/health/rollback evidence | Service-to-service permission evidence |
|---|---|---|
| Auth | Independent Auth image/revision/traffic; authorized health check; known-good rollback or documented first-deploy limitation. | Approved callers can invoke only their declared Auth operations; ungranted identity/token cases deny. Keep Worker ingress proof tracked separately in §2. |
| Billing | Independent Billing build, health/configuration, revision/traffic, and known-good rollback. | Only declared callers can reach quota/entitlement operations; prove intended identity, audience, operation scope, and denial cases. |
| Project | Independent Project build, health/configuration, revision/traffic, and known-good rollback. | AI Orchestration's approved fact-snapshot call is authorized; unauthorized service identity and actor/project access failures are denied. |
| Template | Independent Template build, health/configuration, revision/traffic, and known-good rollback. | Only declared callers can read or select template resources; prove service identity and resource/tenant authorization. |
| AI Orchestration | Independent control-service build, health/configuration, revision/traffic, and known-good rollback. Track its Cloud Run Job separately if/when in scope. | Only declared callers can invoke control operations; outbound calls use each target's audience and least-privilege identity. |
| Quality | Independent Quality build, health/configuration, revision/traffic, and known-good rollback. | Only declared callers can request quality operations; prove caller identity and draft/version scope checks. |
| Visual AI | Independent Visual AI build, health/configuration, revision/traffic, and known-good rollback. Track optional visual jobs separately if/when justified. | Only declared callers can request visual operations; prove service identity and project/asset scope checks. |
| Document | Independent Document build, health/configuration, revision/traffic, and known-good rollback. Track export jobs separately if/when in scope. | Only declared callers can request document/export operations; prove service identity and that export access remains entitlement-checked. |
| Notification | Independent Notification build, health/configuration, revision/traffic, and known-good rollback. | Only declared callers can request delivery operations; prove service identity and that Notification does not become authority for authentication or payment. |

For service-to-service checks, use the approved API/contract matrix rather than inventing new caller-target relationships. Record each tested caller identity, target audience, operation, expected allow/deny result, service-level grant, request ID and relevant policy/log evidence. Do not grant broad project roles to make a test pass.

**Evidence needed to mark complete:** A service-by-service record for all nine proving independent build/deploy/health/rollback and only declared service-to-service permissions; CI/path-filter or equivalent evidence that one service deployment does not alter another; and test results for intended and unauthorized callers. The gate is incomplete if any service lacks evidence or any unauthorized call succeeds.

## 4. Internal contracts and environment setup

**Status:** **BLOCKED — contract decisions and operational checks open**
**Blocker:** The fact-snapshot contract is a draft. It explicitly leaves delegated actor context and storage/retention/recovery of an accepted snapshot version unresolved. Environment, secrets, resource/concurrency, budget, and monitoring evidence is not established by the records reviewed.

**Next action:** Resolve the contract decisions below before implementing the internal call. Complete the environment and operations checklist using approved values and redacted read-only evidence. Keep values and policies unselected until authorized owners decide them; this checklist does not enable APIs, billing, or infrastructure.

**Open contract decisions:**

- **Delegated student access:** Select and document how Project Service verifies that the student actor may access the requested project when AI Orchestration calls it. Cloud Run IAM proves the calling service identity, not the student's project access. Do not trust a caller-supplied actor ID as proof. Define claims/context provenance, validation, scope/tenant enforcement, denial behavior, and contract tests; fail closed if access cannot be verified.
- **Pinned snapshot recovery:** Define how the accepted `fact_snapshot_version` is stored, retained, and recovered for every retry/resume. A job must use the exact accepted version. If that version cannot be recovered, stop and surface the failure; never silently substitute the latest snapshot. Bind a newer version only to an explicitly new job.
- **Contract approval:** Approve the exact versioned path and DTO, permission vocabulary, error-code/status mapping, request-ID behavior, timeout/rate limits, and snapshot-consistency semantics. Add consumer/provider contract tests for the Project-generated shared error schema and matching request IDs where applicable. Keep this internal Cloud Run interaction distinct from the unresolved Worker ingress.

**Outstanding environment and operations checks:**

- **Environment boundaries/configuration:** Confirm separate dev/staging/prod projects/configuration and per-service settings. Inventory only the variables each service needs, distinguish config from secret values, and prove a service does not load a shared all-services environment. Confirm approved region/resource identifiers and required API state through authorized read-only checks; the latest recorded Cloud Run API finding is disabled, while Artifact Registry API state and service inventory remain unverified.
- **Secrets and identities:** Confirm required secrets exist only in the approved secret store/bindings, each service has access only to its own required secrets, CI credentials are separate from runtime configuration, and rotation/revocation ownership is documented. Confirm no secrets are committed or exposed through browser-visible variables, logs, traces, or Worker responses. Use attached identities/short-lived credentials; do not create or use service-account key files.
- **Resource/concurrency limits:** Approve and record per-service CPU/memory, request/job deadlines, concurrency, connection-pool limits, retry ceilings, and job limits. Evidence must show configured values, their owner, and tests or measurements supporting them; do not invent limits or claim load capacity without measurements.
- **Budget:** Approve an environment budget and alert thresholds, document how actual spend and anomalies are observed, and verify alert configuration without enabling billing in this task. A configured application-side estimate/guard is not proof of a cloud billing alert or a provider spending cap. Never assert a price or threshold without approved evidence.
- **Monitoring and incident evidence:** Verify health/readiness status, structured logs, request/trace correlation, service/job failure and latency metrics, budget/quota alerts, and alert routing. Demonstrate redaction of tokens, secrets, and sensitive student data; retain enough request/policy evidence to distinguish IAM denial from ingress/transport failure. Record operational owner and response path.

**Evidence needed to mark complete:** Approved ADR/contract decisions and passing contract/authorization tests; redacted environment and IAM/secret-access evidence; resource and concurrency settings with supporting test/measurement records; approved budget and working alert evidence; and monitoring/logging/trace evidence with redaction and alert ownership. Record every still-open decision and owner rather than treating it as implicitly approved.

## Completion record

For each item, append the completion date, responsible operator/owner, change or rehearsal reference, exact evidence locations, test results, and remaining blockers. Keep tokens, secret values, and private student data out of the record. A work item is complete only when its listed evidence exists and its blocker is resolved; this checklist itself is not evidence that any cloud gate passed.
