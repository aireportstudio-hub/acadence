# Acadence — Environment Variables & Secrets Specification v1.0

**Reference date:** 2026-11-12  
**Status:** Ready-to-fill template and proposed naming conventions; not tested runtime configuration.

## Scope and source documents

Companion to `ACADENCE_TECH_STACK_V2_2.md`, `ACADENCE_MULTI_AGENT_ARCHITECTURE_V1_1.md`, `ACADENCE_SYSTEM_ARCHITECTURE_V1_1.md`, and `ACADENCE_DEVELOPMENT_ROADMAP_V1_0.md`. No earlier decisions are replaced.

All nine independent Cloud Run microservices, the Cloudflare Workers frontend, two selected Cloud Run Jobs and one optional visual worker have dedicated templates.

## Critical security and operational rules

1. **One configuration per deployed service.** Do not load a single giant root `.env` into every process. Provision secrets only to the service that needs them.
2. **Secrets vs nonsecrets.** Use Google Secret Manager for Cloud Run secrets and encrypted Cloudflare Workers secrets for Workers; use `.env`/`.dev.vars` only in local development.
3. **Frontend exposure.** Anything prefixed `NEXT_PUBLIC_` can be readable in the browser bundle. Never put model API keys, database URLs, R2 credentials, SMS secrets, payment secrets, service tokens, or signing keys there.
4. **Cloudflare local config.** Use `.dev.vars` for the frontend Worker; do not maintain competing `.env` and `.dev.vars` simultaneously. Set production secrets with Workers secret bindings.
5. **Cloud Run IAM.** Use service identities/ADC and Google-signed audience-bound ID tokens to call private Cloud Run services; do not deploy service-account JSON files to production or set `GOOGLE_APPLICATION_CREDENTIALS` in Cloud Run.
6. **Worker to Cloud Run security is still a design proof task (P00).** `EDGE_TO_API_AUTH_MODE=PENDING_DESIGN` must not be treated as a deployed authentication mechanism.
7. **Dedicated DB users.** `DATABASE_URL` is the same variable name in multiple services, but its VALUE is distinct: grant only the owning service schema/table permissions; use a separate checkpoint role.
8. **Provider decisions.** SMS, payment provider, real plagiarism corpus, vision, diffusion model, and PDF renderer are not finalized. Do not obtain every competing key or use `NONE/UNSELECTED` in production for an enabled feature.
9. **Plan caps live in billing data and enforced server-side**: Hobby 1×10 pages preview-only, Pro 1×100 DOCX/PDF, Premium 2×100 DOCX/PDF/LaTeX. Do not use client env flags to authorize subscriptions.
10. **Never check secrets into source control.** Commit only `.env.example` and `.dev.vars.example`, plus a suitable `.gitignore`; consider secret-scanning CI.
11. **Rotate leaked keys** and use different credentials for development, staging and production. Do not send keys via AI chat, tickets or logs.
12. **Required fields depend on phase.** A skeleton service may boot with local DB config while billing/voice/AI credentials remain blank until implementing their feature.

## Directory layout

```text
acadence/
apps/frontend/.dev.vars.example
services/auth-service/.env.example
services/billing-service/.env.example
services/project-service/.env.example
services/template-service/.env.example
services/ai-orchestration-service/.env.example
services/quality-service/.env.example
services/visual-ai-service/.env.example
services/document-service/.env.example
services/notification-service/.env.example
infrastructure/ci/.env.example
workers/report-generation/.env.example
workers/document-export/.env.example
workers/visual-generation/.env.example
```

## Register/configure external providers

| Provider | Variables or identity | Notes |
|---|---|---|
| Neon PostgreSQL | `DATABASE_URL`, `CHECKPOINT_DATABASE_URL` | Provision roles scoped by service and schema; TLS |
| Cloudflare Workers | `.dev.vars`, Cloudflare secrets, deployment credentials in CI | Worker-to-private-Cloud-Run mechanism requires P00 test |
| Cloudflare R2 | `R2_ACCOUNT_ID`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` | Limit token to intended bucket |
| Google Cloud Run | `GCP_PROJECT_ID`, `GCP_REGION`, `REPORT_GENERATION_JOB_NAME`, `DOCUMENT_EXPORT_JOB_NAME` | Use attached IAM service accounts; most authorization via IAM, not static env tokens |
| Google OAuth | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI` | Redirect URI must match the Google Cloud Console config |
| OTP/SMS | `OTP_PROVIDER` and selected vendor credentials | One provider only, not all candidate keys |
| Billing | `PAYMENT_PROVIDER`, Stripe OR Razorpay keys, webhook secret | Provider undecided; verify webhooks before updating entitlements |
| Anthropic / Groq / OpenAI | `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY` | Only model-using services get relevant keys |
| LangSmith | `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` | Trace/redact safely; avoid exposing sensitive student details |
| Voyage AI | `VOYAGE_API_KEY` | Embeddings and semantic repetition; conditional until enabled |
| Upstash | `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | REST client token; no browser exposure |
| Image/diagram providers | `CLOUDFLARE_AI_API_TOKEN` or `FAL_KEY` or `BFL_API_KEY`, `MERMAID_API_KEY` | Mermaid local library needs no API key; paid API optional |
| Quality/plagiarism | `EXTERNAL_PLAGIARISM_API_KEY`, source APIs | Only with licensed and permitted provider |
| Sentry + OpenTelemetry | `SENTRY_DSN`, `OTEL_EXPORTER_OTLP_ENDPOINT` | Optional early, recommended for production |
| Voice | `VOICE_PROVIDER`, `STT_PROVIDER`, `TTS_PROVIDER`, model/voice IDs | Provider not selected; audio requires consent, safe handling and ephemeral frontend sessions |
| GitHub Actions deployment | `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `CLOUDFLARE_API_TOKEN` | CI secrets only; not runtime application variables |

## All environment variable names and purpose

The following is a comprehensive inventory across the **provided templates**, not a requirement that every microservice receive every variable. `CORE` refers to implementation-phase usage; blank optional credentials should not be required to start unrelated services.

| Variable | Kind | Stage | Purpose |
|---|---|---|---|
| `ACCESS_TOKEN_TTL_SECONDS` | config | core | Short-lived access token lifetime |
| `AI_ORCHESTRATION_SERVICE_URL` | config | core | Project workflow submission |
| `ALLOWED_IMAGE_MIME_TYPES` | config | core | Do not trust MIME only; inspect file signatures |
| `ANTHROPIC_API_KEY` | secret | core | Claude API key |
| `API_GATEWAY_ORIGIN` | config | core | Private server-side URL for selected BFF/API ingress design |
| `API_VERSION` | config | core | HTTP API version |
| `APP_ENV` | config | core | Environment: development, staging, production |
| `AUTH_SERVICE_URL` | config | core | Auth service URL |
| `BFL_API_KEY` | secret | conditional | Only if direct Black Forest Labs API selected |
| `BILLING_CURRENCY` | config | core | Billing currency to validate with selected gateway |
| `BILLING_SERVICE_URL` | config | core | Entitlement and quota checks |
| `CHECKPOINT_DATABASE_URL` | secret | core | Postgres checkpoint DSN for LangGraph; service-owned credential |
| `CLOUDFLARE_ACCOUNT_ID` | config | conditional | Cloudflare account ID for Workers AI REST API |
| `CLOUDFLARE_AI_API_TOKEN` | secret | conditional | For Cloud Run calling Cloudflare Workers AI REST API; not needed for Workers AI binding |
| `CLOUDFLARE_API_TOKEN` | secret | core | CI deployment token for Workers/R2; least-privilege GitHub Actions secret |
| `CLOUD_TASKS_QUEUE_PATH` | config | conditional | Optional Cloud Tasks queue name/ID, only after dispatch provider enabled |
| `COOKIE_DOMAIN` | config | core | Optional cookie domain; blank for localhost/host-only cookie |
| `COOKIE_SECURE` | config | core | True for HTTPS production |
| `CORS_ALLOWED_ORIGINS` | config | core | Origins explicitly permitted by the service, not wildcard with credentials |
| `CROSSREF_MAILTO` | config | conditional | Contact email for Crossref polite pool where relevant; not a secret |
| `DATABASE_URL` | secret | core | Neon PostgreSQL DSN for service-owned auth schema and role; use TLS |
| `DB_MAX_OVERFLOW` | config | core | Limit concurrent PostgreSQL connections |
| `DB_POOL_SIZE` | config | core | Connection pool size, subject to Cloud Run concurrency and Neon limits |
| `DB_SCHEMA` | config | core | Schema owned by this service; do not write to others |
| `DEFAULT_TEMPLATE_CATALOG_VERSION` | config | core | Default template catalog revision |
| `DOCUMENT_EXPORT_JOB_NAME` | config | core | Cloud Run Job for heavy exports |
| `DOCUMENT_SERVICE_URL` | config | core | Render/preview export integration |
| `DOCX_RENDERER` | config | core | Word generation library |
| `EDGE_TO_API_AUTH_MODE` | config | conditional | Security decision pending: Worker-to-GCP authentication/ingress; do not deploy public unprotected backend |
| `EMAIL_FROM` | config | conditional | Verified sender address |
| `EMAIL_PROVIDER` | config | conditional | Choose mail delivery service before email notifications |
| `EMBEDDING_MODEL_ID` | config | when-feature-enabled | Exact tested embedding model |
| `ENABLE_AI_IMAGES` | config | conditional | Enable after provider selection and provenance controls |
| `ENABLE_DEVICE_RISK_CHECKS` | config | core | Privacy-conscious risk checks; physical-device identity cannot be guaranteed |
| `ENABLE_GENERATED_ILLUSTRATIONS` | config | conditional | Must label as AI-generated, never invent results |
| `ENABLE_IMAGE_INPUTS` | config | core | Student project screenshot/photo upload support |
| `ENABLE_LATEX_EXPORT` | config | core | Backend must still enforce Premium entitlement |
| `ENABLE_OCR_FALLBACK` | config | conditional | Turn on OCR for scanned images/documents when needed |
| `ENABLE_SOURCE_RETRIEVAL` | config | conditional | Turn on when sourced citations are required |
| `ENABLE_TIPTAP_CONVERSION` | config | conditional | Paid conversion only if purchased/validated |
| `ENABLE_TIPTAP_PAGES` | config | conditional | Paid pagination package only if purchased/validated |
| `EXPORT_RUN_ID` | config | core | Injected per job execution; do not set in deployed static config |
| `EXTERNAL_PLAGIARISM_API_KEY` | secret | conditional | Licensed provider credential only |
| `EXTERNAL_PLAGIARISM_PROVIDER` | config | conditional | Only if a licensed provider is selected |
| `FAL_KEY` | secret | conditional | Only if fal.ai selected |
| `FAST_MODEL_ID` | config | when-feature-enabled | Fast model for extraction/auxiliary tasks |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | config | core | CI deployment service account to impersonate via WIF |
| `GCP_PROJECT_ID` | config | core | Google Cloud project ID |
| `GCP_REGION` | config | core | Region where Cloud Run jobs are deployed |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | config | core | Prefer WIF GitHub OIDC; avoid downloaded service-account key |
| `GOOGLE_OAUTH_CLIENT_ID` | config | core | Google OAuth application client ID; not equivalent to API secret |
| `GOOGLE_OAUTH_CLIENT_SECRET` | secret | core | Google OAuth web-app client secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | config | core | Exact allowed redirect URI registered in Google console |
| `GROQ_API_KEY` | secret | when-feature-enabled | Groq inference API key |
| `IMAGE_GENERATION_PROVIDER` | config | conditional | Choose a model provider: Cloudflare AI, BFL, fal.ai etc |
| `IMAGE_MODEL_ID` | config | conditional | Actual image model ID after provider selection |
| `JOB_DISPATCH_MODE` | config | core | Dispatcher choice, Cloud Tasks optional |
| `JWT_ALGORITHM` | config | core | Chosen signing algorithm; no algorithm downgrade |
| `JWT_AUDIENCE` | config | core | Intended API audience |
| `JWT_ISSUER` | config | core | JWT issuer |
| `JWT_SIGNING_KEY_ID` | config | core | Key rotation identifier (kid) |
| `JWT_SIGNING_PRIVATE_KEY` | secret | core | Asymmetric private signing key from Secret Manager; PEM format |
| `LANGSMITH_API_KEY` | secret | core | LangSmith tracing credential |
| `LANGSMITH_ENDPOINT` | config | core | LangSmith endpoint; regional endpoint varies |
| `LANGSMITH_PROJECT` | config | core | Trace project for environment |
| `LANGSMITH_TRACING` | config | core | Enable LangSmith traces after appropriate data redaction |
| `LANGSMITH_WORKSPACE_ID` | config | conditional | Needed for certain organization-scoped keys |
| `LATEX_ENGINE` | config | core | LaTeX compiler after sandbox and package tests |
| `LLM_DAILY_BUDGET_USD` | config | core | Illustrative cost guard, not a provider spending limit |
| `LLM_MAX_RETRIES` | config | core | Bounded transient retries |
| `LLM_REQUEST_TIMEOUT_SECONDS` | config | core | Per-request deadline |
| `LOG_LEVEL` | config | core | Log verbosity; never log credentials or raw sensitive student content |
| `MAX_CONCURRENT_LLM_CALLS` | config | core | Initial cap to avoid provider 429 and budget spikes |
| `MAX_EXPORT_TIME_SECONDS` | config | core | Budget for document exporter |
| `MAX_UPLOAD_BYTES` | config | core | Illustrative 15 MiB maximum per upload; tune for requirements |
| `MERMAID_API_KEY` | secret | conditional | Only for optional hosted Mermaid API plan |
| `MERMAID_RENDER_MODE` | config | core | Local Mermaid library/CLI by default |
| `NEXT_PUBLIC_API_BASE_PATH` | public | core | Browser-facing API path on same origin |
| `NEXT_PUBLIC_APP_URL` | public | core | Public URL for the web app; okay to expose |
| `NEXT_PUBLIC_ENABLE_AI_IMAGES` | public | when-feature-enabled | Public feature visibility only |
| `NEXT_PUBLIC_ENABLE_VOICE` | public | when-feature-enabled | Public feature visibility flag, NOT authorization |
| `NEXT_PUBLIC_SENTRY_DSN` | public | when-feature-enabled | Public DSN only if Sentry browser SDK is enabled; not a secret |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | public | conditional | Cloudflare Turnstile public site key, if anti-bot protection enabled |
| `NOTIFICATION_RETRY_LIMIT` | config | core | Bounded retries for delivery attempts |
| `NOTIFICATION_SERVICE_URL` | config | core | Used if SMS send/verify is delegated to notification service |
| `OCR_ENGINE` | config | conditional | Selected safe OCR method if fallback is enabled |
| `OIDC_ISSUER` | config | core | Validate issuer, audience, state, nonce and PKCE |
| `OPENAI_API_KEY` | secret | when-feature-enabled | OpenAI model API key |
| `OPENALEX_API_KEY` | secret | conditional | Only if account/API plan requires it |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | config | when-feature-enabled | OpenTelemetry collector endpoint; authentication configured separately |
| `OTEL_SERVICE_NAME` | config | when-feature-enabled | Service identity for distributed traces |
| `OTP_MAX_ATTEMPTS` | config | core | Verification attempt limit |
| `OTP_PROVIDER` | config | conditional | Choose one SMS provider before enabling mobile auth |
| `OTP_RATE_LIMIT_PER_HOUR` | config | core | Illustrative rate limit, tune via abuse tests |
| `OTP_TTL_SECONDS` | config | core | OTP expiry |
| `PAYMENT_PROVIDER` | config | conditional | Choose stripe OR razorpay after business/payment evaluation |
| `PDF_RENDERER` | config | core | ReportLab or validated conversion pipeline |
| `PLANNER_MODEL_ID` | config | core | Versioned tested planner model name |
| `PROJECT_SERVICE_URL` | config | core | Project quota collaboration endpoint |
| `PROMPT_VERSION` | config | core | Prompt version recorded with outputs |
| `PUBSUB_TOPIC_REPORT_EVENTS` | config | conditional | Optional Pub/Sub fan-out topic; no Pub/Sub required for basic dispatch |
| `QUALITY_JUDGE_MODEL_ID` | config | when-feature-enabled | Evaluated LLM quality reviewer model ID |
| `QUALITY_MAX_REVISIONS` | config | core | Upper bound for per-section targeted revisions |
| `QUALITY_SERVICE_URL` | config | core | Quality checks |
| `R2_ACCESS_KEY_ID` | secret | core | R2 S3-compatible access key |
| `R2_ACCOUNT_ID` | config | core | Cloudflare account ID for constructing S3 endpoint |
| `R2_BUCKET_NAME` | config | core | Private bucket; isolate production |
| `R2_ENDPOINT` | config | core | https://ACCOUNT_ID.r2.cloudflarestorage.com |
| `R2_SECRET_ACCESS_KEY` | secret | core | R2 S3-compatible secret access key |
| `R2_SIGNED_URL_TTL_SECONDS` | config | core | Short-lived private download/upload URL validity |
| `RAZORPAY_KEY_ID` | config | conditional | If Razorpay selected; server-side config |
| `RAZORPAY_KEY_SECRET` | secret | conditional | Razorpay API secret |
| `RAZORPAY_WEBHOOK_SECRET` | secret | conditional | Webhook signature verification |
| `REFRESH_TOKEN_TTL_DAYS` | config | core | Session refresh lifetime, enforce rotation and revocation |
| `REPORT_GENERATION_JOB_NAME` | config | core | Cloud Run Job resource name |
| `REPORT_RUN_ID` | config | core | Injected per execution by Cloud Run Job override; do not store permanently |
| `RERANK_MODEL_ID` | config | conditional | Only when retrieval reranking is used |
| `RESEND_API_KEY` | secret | conditional | Only if Resend selected |
| `S2S_AUTH_MODE` | config | core | IAM-based service-to-service authentication, not an LLM/tool API key |
| `S2S_REQUEST_TIMEOUT_SECONDS` | config | core | Bound outbound service HTTP calls |
| `SEMANTIC_SCHOLAR_API_KEY` | secret | conditional | Only if Semantic Scholar API with key used |
| `SENDGRID_API_KEY` | secret | conditional | Only if SendGrid selected |
| `SENTRY_AUTH_TOKEN` | secret | conditional | Optional release/source-map upload token |
| `SENTRY_DSN` | config | when-feature-enabled | Server-side tracing/error monitoring |
| `SERVICE_NAME` | config | core | Set separately to the service name |
| `SMS_PROVIDER` | config | conditional | Choose SMS delivery/verification provider |
| `SMS_PROVIDER_API_KEY` | secret | conditional | Generic slot for another approved OTP provider |
| `SSE_HEARTBEAT_SECONDS` | config | core | Heartbeat interval for progress SSE stream |
| `STRIPE_PREMIUM_PRICE_ID` | config | conditional | Stripe price identifier if used |
| `STRIPE_PRO_PRICE_ID` | config | conditional | Stripe price identifier if used |
| `STRIPE_SECRET_KEY` | secret | conditional | If Stripe selected |
| `STRIPE_WEBHOOK_SECRET` | secret | conditional | Stripe signed webhook verification |
| `STT_MODEL_ID` | config | conditional | Tested transcription model ID |
| `STT_PROVIDER` | config | conditional | Speech-to-text provider used after user permission |
| `TEMPLATE_RENDER_ENGINE` | config | core | Canonical structured document model |
| `TEMPLATE_SERVICE_URL` | config | core | Template snapshot reference |
| `TTS_MODEL_ID` | config | conditional | Tested speech generation model ID |
| `TTS_PROVIDER` | config | conditional | Text-to-speech provider |
| `TTS_VOICE_ID` | config | conditional | Selected speaking voice ID |
| `TURNSTILE_SECRET_KEY` | secret | conditional | Server-side verification secret for Cloudflare Turnstile, if enabled |
| `TWILIO_ACCOUNT_SID` | config | conditional | Only if Twilio chosen for OTP |
| `TWILIO_AUTH_TOKEN` | secret | conditional | Only if Twilio chosen |
| `TWILIO_VERIFY_SERVICE_SID` | config | conditional | Only if Twilio Verify chosen |
| `UPLOAD_RETENTION_DAYS` | config | core | Illustrative retention, finalize privacy policy |
| `UPSTASH_REDIS_REST_TOKEN` | secret | when-feature-enabled | Upstash Redis REST token; never browser-visible |
| `UPSTASH_REDIS_REST_URL` | config | when-feature-enabled | Upstash HTTPS REST endpoint |
| `VISION_MODEL_ID` | config | conditional | Tested multimodal model ID |
| `VISION_PROVIDER` | config | conditional | Multimodal image-understanding provider |
| `VISUAL_AI_SERVICE_URL` | config | core | Visual agents |
| `VOICE_DEFAULT_LANGUAGE` | config | conditional | Default speech language, allow user preference |
| `VOICE_PROVIDER` | config | conditional | Voice backend provider, e.g. OpenAI Realtime or TTS/STT combination |
| `VOICE_SESSION_TTL_SECONDS` | config | conditional | Short-lived voice session credential lifetime; mint backend-side |
| `VOYAGE_API_KEY` | secret | when-feature-enabled | Voyage embeddings/reranking |
| `WRITER_MODEL_ID` | config | core | Versioned tested model name; decide after evaluation |

## Environment file routing

| Path | Key count |
|---|---:|
| `apps/frontend/.dev.vars.example` | 9 |
| `services/auth-service/.env.example` | 40 |
| `services/billing-service/.env.example` | 26 |
| `services/project-service/.env.example` | 28 |
| `services/template-service/.env.example` | 26 |
| `services/ai-orchestration-service/.env.example` | 55 |
| `services/quality-service/.env.example` | 27 |
| `services/visual-ai-service/.env.example` | 37 |
| `services/document-service/.env.example` | 31 |
| `services/notification-service/.env.example` | 23 |
| `infrastructure/ci/.env.example` | 7 |
| `workers/report-generation/.env.example` | 27 |
| `workers/document-export/.env.example` | 28 |
| `workers/visual-generation/.env.example` | 21 |

## Three use cases

### Local development
Copy a service `.env.example` to the adjacent `.env` and fill only keys used by the feature currently being tested. Copy `apps/frontend/.dev.vars.example` to `apps/frontend/.dev.vars` for Cloudflare local development. Use distinct development-only API credentials.

### Cloud Run production
Set nonsecret settings on the appropriate Cloud Run service or job; attach individual Secret Manager secrets (by IAM) for passwords and API keys. Configure service-to-service authenticated requests and distinct database roles. Cloud Run injects `PORT` for services; do **not** hardcode or set it in these templates.

### Cloudflare Workers production
Public variables can be configured as Workers vars; sensitive edge-only settings as Workers secrets. **Never** use `NEXT_PUBLIC_` for secret values. Deployment tokens such as `CLOUDFLARE_API_TOKEN` belong in CI secrets and are not needed at runtime.

## Decisions unresolved before production

- Worker-to-Cloud Run authentication and ingress topology (design + proof of concept).
- OTP vendor, sender policies and regional regulations.
- Payment gateway, webhooks, subscription renewal/refund logic.
- Voice provider/multimodal model, only when voice feature is implemented.
- Licensed external plagiarism comparison provider.
- PDF rendering/pagination fidelity and Tiptap licensing.
- Diffusion image-generation provider/model, quotas and rights.
- Exact model IDs and per-task routing based on evaluations.
- Country/region, trace redaction, log retention and sensitive clinical/academic data policy.

## Official documentation

- Cloudflare Workers local env/secrets: https://developers.cloudflare.com/workers/local-development/environment-variables/
- Cloudflare Workers secrets: https://developers.cloudflare.com/workers/configuration/secrets/
- Cloudflare R2 S3: https://developers.cloudflare.com/r2/get-started/s3/
- Google Cloud Run env: https://docs.cloud.google.com/run/docs/configuring/services/environment-variables
- Google Cloud Run job secrets: https://docs.cloud.google.com/run/docs/configuring/jobs/secrets
- Google Cloud Run service-to-service: https://docs.cloud.google.com/run/docs/authenticating/service-to-service
- Upstash Redis Python SDK: https://upstash.com/docs/redis/sdks/py/gettingstarted
- LangSmith tracing: https://reference.langchain.com/python/langsmith
