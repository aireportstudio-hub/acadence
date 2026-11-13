# Project Service

P01 startup validation reads only the process environment. `APP_ENV` defaults
to `development` and accepts `development`, `staging`, or `production`.
`LOG_LEVEL` defaults to `INFO` and accepts `DEBUG`, `INFO`, `WARNING`, `ERROR`,
or `CRITICAL`, case-insensitively. Empty or invalid values stop startup.
Validation does not configure logging, load an env file, or require credentials.

## P01 test evidence

From the repository root, the following passed on 13 November 2026:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\services\project-service -p "test_*.py" -v
.\scripts\test-services.ps1 -Service project-service
```

The unit tests cover defaults, valid overrides, invalid values and both health
responses. The container smoke test builds the image and checks both endpoints.
This is only the Project Service configuration slice of P01, not the P01 gate.
Cloudflare-to-Cloud Run ingress remains an open P00/P01 decision.
