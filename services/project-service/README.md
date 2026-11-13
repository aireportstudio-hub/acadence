# Project Service

P01 startup validation reads only the process environment. `APP_ENV` defaults
to `development` and accepts `development`, `staging`, or `production`.
`LOG_LEVEL` defaults to `INFO` and accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`,
or `CRITICAL`, case-insensitively. Empty or invalid values stop startup.
Validation does not configure logging, load an env file, or require credentials.

Every HTTP response includes `X-Request-ID`. A single incoming ID is reused if
it contains 1–64 ASCII letters, digits, hyphens, or underscores; otherwise a
new ID is generated. HTTP, validation, and unexpected errors return `code`,
`message`, `request_id`, and `details`, with the same ID in the header and
body. Messages are generic and `details` is currently empty; exception text
and submitted values are not returned. HTTP error headers such as `Allow` and
`WWW-Authenticate` are preserved.

## P01 test evidence

From the repository root, the following passed on 13 November 2026:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\services\project-service -p "test_*.py" -v
.\scripts\test-services.ps1 -Service project-service
```

The unit tests cover configuration validation, health responses, request IDs,
router errors, protocol headers, request validation, and sanitized 500 errors.
The container smoke test builds the image and checks both health endpoints.
This is only the Project Service configuration and error-handling slice of P01,
not the P01 gate. Distributed tracing and rollout to other services remain
future work; Cloudflare-to-Cloud Run ingress remains an open P00/P01 decision.
