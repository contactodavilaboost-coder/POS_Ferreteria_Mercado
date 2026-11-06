# ==============================================================================
# CONECTAR FERRETERIA MERCADO CON CLOUDFLARE TUNNEL
# ==============================================================================

$ErrorActionPreference = "Continue"
$ProjectDir = $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   CONECTAR FERRETERIA MERCADO CON CLOUDFLARE TUNNEL     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Solicitar o configurar token de Cloudflare
$TokenFile = Join-Path $ProjectDir "config\cloudflare_token.txt"
$Token = ""
if (Test-Path $TokenFile) {
    $Token = (Get-Content $TokenFile -Raw).Trim()
}

if (-not $Token -or $Token -eq "PEGA_AQUI_EL_TOKEN_NUEVO") {
    $Token = Read-Host "Pegue aqui el Token del tunel de Cloudflare (eyJh...)"
    if ($Token) {
        [System.IO.File]::WriteAllText($TokenFile, $Token, (New-Object System.Text.UTF8Encoding($false)))
    } else {
        Write-Host "[AVISO] No se proporciono token. Omitiendo conexion remota." -ForegroundColor Yellow
        exit 0
    }
}

# 2. Levantar contenedores Docker
Write-Host "`n[1/3] Levantando contenedores Docker (web + db)..." -ForegroundColor Yellow
Set-Location $ProjectDir
docker compose up -d

# 3. Localizar o descargar cloudflared.exe
Write-Host "`n[2/3] Verificando ejecutable de Cloudflare (cloudflared.exe)..." -ForegroundColor Yellow
$SafeDir = "C:\Users\usuario\AppData\Local\CloudflaredFerreteria"
if (-not (Test-Path $SafeDir)) {
    New-Item -ItemType Directory -Path $SafeDir -Force | Out-Null
}
$SafeExe = Join-Path $SafeDir "cloudflared.exe"

if (-not (Test-Path $SafeExe)) {
    Write-Host "Descargando cloudflared.exe oficial..." -ForegroundColor Yellow
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $SafeExe -UseBasicParsing
}

Write-Host "[OK] Usando conector: $SafeExe" -ForegroundColor Green

# 4. Iniciar conector en Windows con protocolo HTTP2
Write-Host "`n[3/3] Iniciando conector..." -ForegroundColor Yellow
Start-Process -FilePath $SafeExe -ArgumentList "tunnel --no-autoupdate --protocol http2 run --token $Token" -WindowStyle Hidden
Start-Sleep -Seconds 3

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [EXITO] TUNEL INICIADO PARA FERRETERIA MERCADO" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
