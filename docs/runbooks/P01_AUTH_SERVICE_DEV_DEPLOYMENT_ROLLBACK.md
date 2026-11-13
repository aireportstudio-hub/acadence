# P01 Auth Service dev deployment and rollback runbook

**Status:** Proposed operator procedure; no deployment or IAM change has been performed
**Project:** `acadence-dev-shubh`
**Service:** `auth-service`
**Probe:** `GET /healthz`
**Scope:** Auth Service only; this procedure does not deploy or configure the other services.

## Gate and current known state

The latest recorded preflight found project billing disabled and
`run.googleapis.com` disabled. Cloud Run services, their locations, URLs,
current revisions, and IAM policies could not be verified while the API was
disabled. Do not proceed to image push or deployment until an authorized
operator separately resolves billing and API enablement and re-runs the
read-only preflight. This runbook does not enable billing or APIs, create a
repository or service account, or change IAM.

The P01 ingress decision remains unresolved for Cloudflare Worker-to-Google
authentication. These steps test an operator's direct authenticated call to
Cloud Run; they do **not** prove or approve the Worker ingress design. Keep the
open decision in [P01_DEV_INGRESS_DECISION.md](../adr/P01_DEV_INGRESS_DECISION.md)
open until that separate proof is completed.

The Auth container uses Python 3.13, listens on port 8080, runs as UID/GID
10001:10001, and needs no environment variables for this health probe.
`GET /healthz` returns `{"status":"ok"}`. Do not add credentials or unrelated
service configuration to this deployment.

## 1. Read-only PowerShell preflight

Run these commands from PowerShell with the Google Cloud CLI installed and
authenticated. Replace `<REGION>` with an approved candidate region; region,
repository, runtime service account, caller, and service URL are not verified
values. Each command is read-only. Do not treat an API/query error as evidence
that a service does not exist.

```powershell
$Project = 'acadence-dev-shubh'
$Service = 'auth-service'
$Region = '<REGION>'

# Confirm which gcloud identity is active, then confirm project access/state.
gcloud auth list --filter='status:ACTIVE' --format='value(account)'
gcloud projects describe $Project --format='yaml(projectId,lifecycleState)'

# Confirm billing state. Expected current finding: billingEnabled is false.
gcloud billing projects describe $Project --format='yaml(projectId,billingEnabled,billingAccountName)'

# Show whether the deployment and image registry APIs are enabled.
gcloud services list --enabled --project=$Project --format='value(config.name)' |
    Where-Object { $_ -in @('run.googleapis.com', 'artifactregistry.googleapis.com') }

# List services in the approved region; check for an existing Auth service
# before choosing create/update behavior.
gcloud run services list --project=$Project --region=$Region `
    --format='table(metadata.name,status.url,status.latestReadyRevisionName)'

# For an existing Auth service, inspect URL, latest-ready revision, and actual
# traffic assignments. status.traffic identifies revisions currently serving.
gcloud run services describe $Service --project=$Project --region=$Region `
    --format='yaml(status.url,status.latestReadyRevisionName,status.traffic)'

# Read the service-level IAM policy; look for allUsers and the intended caller.
gcloud run services get-iam-policy $Service --project=$Project --region=$Region `
    --format=yaml
```

If `run.googleapis.com` is absent, service listing/description fails, or the
project/billing/API query fails for lack of access, stop and record the exact
error. The most recent recorded state is a disabled Cloud Run API and disabled
billing; do not retry deployment or infer that no service exists. If
`auth-service` is not found in the candidate region, check only approved
regions and resolve any existing service/name before creating one.

Before continuing, verify the current serving revision from `status.traffic`;
do not assume `status.latestReadyRevisionName` is serving. If traffic is split,
record every revision and percentage and confirm the intended baseline with
the service owner. If an existing `allUsers` Invoker binding is present, stop
until an authorized IAM administrator removes it and verifies the service
policy. Do not weaken IAM to work around an ingress or permission error.

## 2. Identities and least-privilege permissions

Use separate identities where practical:

| Identity | Required permission |
| --- | --- |
| **Deployer** | `roles/run.developer` to create/update the Cloud Run service; `roles/iam.serviceAccountUser` scoped to the selected runtime service account so it can attach it; and `roles/artifactregistry.writer` scoped to the selected image repository to push the image. A separate IAM administrator must apply service IAM changes; `roles/run.developer` does not grant policy-setting access. |
| **IAM administrator** | Permission to set IAM policy for this service (for example, Cloud Run Admin permissions, assigned as narrowly as supported). This identity grants only the intended test caller `roles/run.invoker` on `auth-service`, never project-wide. |
| **Runtime service account** | A user-managed service account attached to this service only. The current health endpoint needs no application-level Google Cloud permissions. Do not create or download a key. |
| **Authorized test caller** | `roles/run.invoker` on this Auth Service only, plus an authenticated `gcloud` user session for the authorized verification command. Do not grant the caller Invoker at project scope. |

The service must require Cloud Run IAM authentication. `--ingress=all` below
allows the direct negative test to reach Cloud Run's IAM check; it does not
allow unauthenticated invocation. `--no-allow-unauthenticated` and
`--invoker-iam-check` keep invocation protected. If organization policy does
not permit this ingress setting, stop and use an approved, reachable test path;
do not claim an IAM denial based only on an ingress rejection.

## 3. Proposed image build, push, deployment, and service IAM

These are proposed live-run commands, **not commands executed for this
documentation task**. Proceed only after the preflight gate passes and the
image repository and service accounts are already provisioned through their
approved processes. Use a unique source revision tag and replace every
placeholder with a verified value.

```powershell
$Project = 'acadence-dev-shubh'
$Service = 'auth-service'
$Region = '<REGION>'
$Repo = '<ARTIFACT_REGISTRY_REPOSITORY>'
$RuntimeServiceAccount = '<AUTH_RUNTIME_SERVICE_ACCOUNT_EMAIL>'
$TestCaller = '<TEST_CALLER_EMAIL>'
$ArtifactHost = "${Region}-docker.pkg.dev"
$GitSha = (git rev-parse --short=12 HEAD).Trim()
$Image = "${ArtifactHost}/${Project}/${Repo}/auth-service:${GitSha}"

# Configure the local Docker credential helper (no service-account key).
gcloud auth configure-docker $ArtifactHost

# Build only the Auth Service Dockerfile and push its uniquely tagged image.
docker build --platform linux/amd64 --tag $Image .\services\auth-service
docker push $Image

# Create/update only auth-service. Ingress permits testing the IAM boundary;
# the explicit flags require IAM-authenticated invocation.
gcloud run deploy $Service --project=$Project --region=$Region `
    --image=$Image --service-account=$RuntimeServiceAccount --port=8080 `
    --ingress=all --no-allow-unauthenticated --invoker-iam-check
```

Do not grant `allUsers` or `allAuthenticatedUsers`. An authorized IAM
administrator grants the named test principal at the service resource only
(substitute the actual caller email):

```powershell
gcloud run services add-iam-policy-binding $Service --project=$Project --region=$Region `
    --member="user:$TestCaller" --role='roles/run.invoker'
```

If the service policy currently contains an `allUsers` binding, do not proceed
until the IAM administrator removes it from this service and verifies the
result. Do not replace it with a project-level binding. Re-read the service
policy after any authorized IAM change.

## 4. Verify the same health URL with and without authentication

Set `$ServiceUrl` to the stable service URL returned by the service
description. Run both commands from the same authorized network path. The
authorized caller must receive HTTP 200 and JSON with `status` equal to `ok`.
The direct request without an Authorization header must be denied by Cloud Run
IAM and must not reach the application health response.

**Authorized caller — expect 200 and `{"status":"ok"}`:**

```powershell
$ServiceUrl = 'https://<AUTH_SERVICE_URL>'
$IdToken = (gcloud auth print-identity-token).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($IdToken)) {
    throw 'Could not obtain the test caller identity token.'
}
try {
    $Response = Invoke-WebRequest -UseBasicParsing -Method Get `
        -Uri "$ServiceUrl/healthz" `
        -Headers @{ Authorization = "Bearer $IdToken" }
    $Body = $Response.Content | ConvertFrom-Json
    if ($Response.StatusCode -ne 200 -or $Body.status -ne 'ok') {
        throw "Health check failed: HTTP $($Response.StatusCode), body did not match."
    }
    'PASS: authorized GET /healthz returned HTTP 200 and status=ok.'
}
finally {
    Remove-Variable IdToken -ErrorAction SilentlyContinue
}
```

**Direct unauthenticated caller — expect Cloud Run IAM 401 or 403:**

```powershell
$UnauthResponse = & curl.exe --silent --show-error --max-time 15 `
    --dump-header - --output NUL --write-out "`nHTTP_STATUS=%{http_code}`n" `
    "$ServiceUrl/healthz"
$CurlExit = $LASTEXITCODE
$UnauthResponse
if ($CurlExit -ne 0) {
    throw "No reliable HTTP response (curl exit $CurlExit); investigate DNS, TLS, proxy, routing, or timeout. This is not an IAM pass."
}
if (($UnauthResponse -join "`n") -notmatch 'HTTP_STATUS=(401|403)') {
    throw 'Expected an HTTP 401/403 denial without credentials; investigate before accepting.'
}
'PASS candidate: unauthenticated request received HTTP 401/403; confirm the denial is from Cloud Run IAM, not ingress.'
```

A curl transport error or HTTP status `000` means no usable HTTP response
(for example DNS, TLS, proxy, routing, or timeout) and is **not** evidence of
an IAM denial. An HTTP response proves the request reached an HTTP endpoint,
but a `403` alone does not distinguish Cloud Run IAM from an ingress or other
policy rejection. Confirm the test source is allowed by the service ingress;
correlate the response timestamp/request with Cloud Run evidence and confirm
that the authorized request from the same path succeeds. If the response is an
ingress rejection or the source cannot reach the IAM check, mark the IAM test
inconclusive rather than passed.

## 5. Record known-good revision and roll back

After an authorized health check succeeds, record the exact revision receiving
100% of traffic from:

```powershell
gcloud run services describe $Service --project=$Project --region=$Region `
    --format='yaml(status.url,status.latestReadyRevisionName,status.traffic)'
```

Write the serving revision name (`revisionName`) and its traffic percentage
into the live-run record as the known-good revision. Only call a revision
known-good after its authorized health check has passed. If traffic is split,
record every serving revision and percentage; obtain owner agreement on the
rollback target before changing traffic.

To shift all traffic to the verified known-good revision (replace the
placeholder; this changes service traffic):

```powershell
$KnownGoodRevision = '<KNOWN_GOOD_REVISION>'
gcloud run services update-traffic $Service --project=$Project --region=$Region `
    --to-revisions="${KnownGoodRevision}=100"
```

After the traffic update:

1. Re-run the service description and confirm the known-good revision receives
   100% of traffic.
2. Re-read `gcloud run services get-iam-policy` for `auth-service`. Confirm
   `allUsers` is absent and only the approved caller/service principals have
   the intended service-level Invoker binding.
3. Re-run **both** verification commands above against the same
   `$ServiceUrl`: authorized call must return 200 and `{"status":"ok"}`;
   unauthenticated direct call must be denied by Cloud Run IAM, not blocked by
   a network/ingress failure.
4. Record the rollback revision, traffic before/after, verification results,
   timestamps, and any incident/change reference.

**First deployment:** There is no prior known-good revision to roll back to.
Do not run `update-traffic` with an empty or guessed revision. If the first
revision fails verification, record that no rollback target exists, stop
promoting changes, investigate, and use the approved deployment/change process
to deploy and verify a corrected revision. Do not describe a first-deployment
failure as a rollback.

## 6. Live-run evidence and secret handling

Record, without credentials or tokens:

- UTC start/end time, operator identity, project, approved region, service
  name, stable service URL, and whether the preflight gate passed.
- Billing/API state and any preflight errors; service existence, current
  serving revision/traffic, and the service-level IAM principals/roles.
- Source commit SHA, image tag **and digest**, deploy result, new revision
  name, and traffic percentages before and after deployment/rollback.
- Authorized `/healthz` HTTP status and JSON result; unauthenticated HTTP
  status and evidence that Cloud Run IAM (not transport or ingress) denied it.
- Response request ID when available, UTC timestamps, relevant Cloud Run
  request/audit evidence, rollback reason, and post-rollback health/IAM result.
- Any open blocker, inconclusive check, approver, and follow-up owner.

Never record, paste, or log the identity token, Authorization header, service
account key, or other credentials. Do not create service-account keys for this
run. Redact tokens from terminal captures and logs before attaching evidence.

## 7. Checks still requiring an authorized live run

- Reconfirm billing and the Cloud Run and Artifact Registry API states; resolve
  the known disabled billing and Cloud Run API blockers through their separate
  approval process.
- Verify the approved region, repository, runtime service account, existing
  service/revision, image push permission, and service-level IAM policy.
- Build and push the Auth image, deploy with IAM authentication, and record
  the actual revision and serving traffic.
- Prove authorized `GET /healthz` returns 200 with `{"status":"ok"}` and the
  same-URL unauthenticated request is denied specifically by Cloud Run IAM.
- Rehearse traffic rollback to a verified prior revision and repeat health/IAM
  checks; if this is a first deployment, document that no prior revision
  exists instead.
- Resolve and separately prove the Cloudflare Worker-to-Cloud Run ingress
  design in the P01 decision; this runbook does not close that gate.

## Official command references

Syntax checked against current Google Cloud documentation on 2026-11-13:

- [Deploy a container image with `gcloud run deploy`](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)
- [Adjust Cloud Run revision traffic](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update-traffic)
- [Authenticate developers to private Cloud Run services](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [Manage Cloud Run service IAM access](https://docs.cloud.google.com/run/docs/securing/managing-access)
- [Push images to Artifact Registry](https://docs.cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling)
- [Read project and billing state](https://docs.cloud.google.com/sdk/gcloud/reference/projects/describe) and [`gcloud billing projects describe`](https://docs.cloud.google.com/sdk/gcloud/reference/billing/projects/describe)
- [List enabled APIs](https://docs.cloud.google.com/sdk/gcloud/reference/services/list)
