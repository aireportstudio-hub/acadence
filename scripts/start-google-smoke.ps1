$ErrorActionPreference = 'Stop'
if (-not $env:GOOGLE_OAUTH_CLIENT_ID -or -not $env:GOOGLE_OAUTH_CLIENT_SECRET) {
    throw 'Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET first.'
}

$repo = Split-Path -Parent $PSScriptRoot
$pg = 'C:\Program Files\PostgreSQL\17\bin'
$python = Join-Path $repo '.venv\Scripts\python.exe'
$service = Join-Path $repo 'services\auth-service'
if (-not (Test-Path $python) -or -not (Test-Path "$service\database\bootstrap.sql")) {
    throw 'The repository .venv and Auth bootstrap are required.'
}

$names = @('SMOKE_ADMIN_PASSWORD', 'SMOKE_MIGRATOR_PASSWORD',
    'SMOKE_RUNTIME_PASSWORD', 'SMOKE_PORT', 'SMOKE_BOOTSTRAP',
    'MIGRATION_DATABASE_URL', 'DATABASE_URL', 'GOOGLE_OAUTH_REDIRECT_URI',
    'OIDC_ISSUER', 'APP_ENV')
$saved = @{}
foreach ($name in $names) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

$root = Join-Path $env:LOCALAPPDATA ('AcadenceAuthSmoke-' + [guid]::NewGuid().ToString('N'))
$data = Join-Path $root 'data'
$pwfile = Join-Path $root 'admin-password'
$started = $false
try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = $listener.LocalEndpoint.Port
    $listener.Stop()

    $adminPassword = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $env:SMOKE_ADMIN_PASSWORD = $adminPassword
    $env:SMOKE_MIGRATOR_PASSWORD = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $env:SMOKE_RUNTIME_PASSWORD = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    $env:SMOKE_PORT = "$port"
    $env:SMOKE_BOOTSTRAP = Join-Path $service 'database\bootstrap.sql'

    New-Item -ItemType Directory -Path $root | Out-Null
    [System.IO.File]::WriteAllText($pwfile, $adminPassword, [System.Text.Encoding]::ASCII)
    & "$pg\initdb.exe" -D $data -U postgres --auth=scram-sha-256 --pwfile=$pwfile | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL initialization failed.' }
    Remove-Item -LiteralPath $pwfile

    $arguments = '-D "{0}" -l "{1}" -o "-h 127.0.0.1 -p {2}" -w start' -f $data, "$root\postgres.log", $port
    $ctl = Start-Process -FilePath "$pg\pg_ctl.exe" -ArgumentList $arguments `
        -RedirectStandardOutput "$root\pgctl.out" `
        -RedirectStandardError "$root\pgctl.err" -PassThru
    $ctlHandle = $ctl.Handle
    $ctl.WaitForExit()
    if ($ctl.ExitCode -ne 0) {
        throw "PostgreSQL startup failed; check $root\pgctl.err and postgres.log."
    }
    $started = $true

    @'
import os
from pathlib import Path
import psycopg
from psycopg import sql

try:
    options = dict(host="127.0.0.1", port=os.environ["SMOKE_PORT"],
                   user="postgres", password=os.environ["SMOKE_ADMIN_PASSWORD"])
    with psycopg.connect(dbname="postgres", autocommit=True, **options) as conn:
        conn.execute("CREATE DATABASE acadence_auth_smoke")
    with psycopg.connect(dbname="acadence_auth_smoke", autocommit=True, **options) as conn:
        conn.execute(Path(os.environ["SMOKE_BOOTSTRAP"]).read_text(encoding="utf-8"), prepare=False)
        for role, name in (("acadence_auth_migrator", "SMOKE_MIGRATOR_PASSWORD"),
                           ("acadence_auth_runtime", "SMOKE_RUNTIME_PASSWORD")):
            conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                sql.Identifier(role), sql.Literal(os.environ[name])))
except Exception as exc:
    print("Auth database bootstrap failed: " + type(exc).__name__)
    raise SystemExit(1)
'@ | & $python -
    if ($LASTEXITCODE -ne 0) { throw 'Auth database bootstrap failed.' }

    $env:MIGRATION_DATABASE_URL = "postgresql+psycopg://acadence_auth_migrator:$($env:SMOKE_MIGRATOR_PASSWORD)@127.0.0.1:${port}/acadence_auth_smoke"
    $env:DATABASE_URL = "postgresql://acadence_auth_runtime:$($env:SMOKE_RUNTIME_PASSWORD)@127.0.0.1:${port}/acadence_auth_smoke"
    Push-Location $service
    try {
        & $python -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Auth migration failed.' }
        foreach ($name in @('MIGRATION_DATABASE_URL', 'SMOKE_ADMIN_PASSWORD',
                'SMOKE_MIGRATOR_PASSWORD', 'SMOKE_RUNTIME_PASSWORD',
                'SMOKE_PORT', 'SMOKE_BOOTSTRAP')) {
            [Environment]::SetEnvironmentVariable($name, $null, 'Process')
        }

        $env:GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8001/v1/auth/google/callback'
        $env:OIDC_ISSUER = 'https://accounts.google.com'
        $env:APP_ENV = 'development'
        Write-Host 'Open http://localhost:8001/v1/auth/google/start; Ctrl+C stops Auth.'
        & $python -m uvicorn main:app --host 127.0.0.1 --port 8001 --no-access-log
        if ($LASTEXITCODE -ne 0) { throw 'Auth service exited with an error.' }
    } finally {
        Pop-Location
    }
} finally {
    if (Test-Path -LiteralPath $pwfile) {
        Remove-Item -LiteralPath $pwfile -Force
    }
    if ($started) {
        & "$pg\pg_ctl.exe" -D $data -m fast -w stop | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Remove-Item -LiteralPath $root -Recurse -Force
        } else {
            Write-Warning "PostgreSQL did not stop; inspect $root."
        }
    } elseif (Test-Path -LiteralPath $root) {
        Write-Warning "Setup failed; inspect and remove the disposable directory: $root"
    }
    foreach ($name in $names) {
        [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process')
    }
}
