param(
    [ValidateSet(
        "project-service", "auth-service", "billing-service",
        "template-service", "ai-orchestration-service", "quality-service",
        "visual-ai-service", "document-service", "notification-service"
    )]
    [string[]]$Service
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $Service) {
    $Service = @(
        "project-service", "auth-service", "billing-service",
        "template-service", "ai-orchestration-service", "quality-service",
        "visual-ai-service", "document-service", "notification-service"
    )
}

foreach ($name in $Service) {
    $context = Join-Path $repoRoot "services/$name"
    $image = "acadence-${name}:local"

    Write-Host "`nBuilding $name"
    docker build -t $image $context
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed for $name" }

    $containerId = docker run -d -p "127.0.0.1::8080" $image
    if ($LASTEXITCODE -ne 0) { throw "Docker startup failed for $name" }

    try {
        $binding = docker port $containerId 8080/tcp
        if ($LASTEXITCODE -ne 0 -or $binding -notmatch '^127\.0\.0\.1:\d+$') {
            throw "Could not find the local port for $name"
        }
        $baseUrl = "http://$binding"

        $health = $null
        for ($attempt = 0; $attempt -lt 20; $attempt++) {
            try {
                $health = Invoke-RestMethod "$baseUrl/healthz" -TimeoutSec 2
                break
            } catch {
                if ($attempt -eq 19) { throw }
                Start-Sleep -Milliseconds 500
            }
        }
        if ($health.status -ne "ok") { throw "$name returned unexpected /healthz status" }

        $ready = Invoke-RestMethod "$baseUrl/readyz" -TimeoutSec 2
        if ($ready.status -ne "ready") { throw "$name returned unexpected /readyz status" }

        Write-Host "PASS: $name /healthz and /readyz"
    } catch {
        docker logs $containerId
        throw
    } finally {
        docker rm -f $containerId | Out-Null
    }
}

Write-Host "`nPASS: All $($Service.Count) selected service containers passed."