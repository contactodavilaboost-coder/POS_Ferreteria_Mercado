# ==============================================================================
# SISTEMA DE RESPALDO BLINDADO EN LA NUBE - ERP FERRETERIA MERCADO
# Guarda copias en:
#   1. Carpeta Local (con historial de 14 respaldos)
#   2. Google Drive / OneDrive (si esta instalado en la PC)
#   3. GitHub Cloud (subida automatica al repositorio remoto)
# ==============================================================================

$ErrorActionPreference = "Continue"

$BaseDir = if ($PSScriptRoot) { $PSScriptRoot } else { "C:\Users\usuario\Desktop\Ferreteria Mercado" }
$BackupDir = Join-Path $BaseDir "backups"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$DumpFile = Join-Path $BackupDir "backup_ferreteria_mercado_$Timestamp.dump"
$LatestFile = Join-Path $BackupDir "PRODUCCION_REAL_FERRETERIA_MERCADO.dump"
$LogFile = Join-Path $BackupDir "backup_log.txt"

function Write-BackupLog($Message) {
    $Line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $Line
    Add-Content -Path $LogFile -Value $Line
}

Write-BackupLog "=== INICIANDO RESPALDO AUTOMATICO DE FERRETERIA MERCADO ==="

# 1. Detectar automaticamente el nombre del contenedor PostgreSQL
$DbContainer = (docker ps --filter "ancestor=postgres:15" --format "{{.Names}}" | Select-Object -First 1)
if (-not $DbContainer) {
    $DbContainer = "ferreteria-db-1"
}
Write-BackupLog "Contenedor de BD detectado: $DbContainer"

# 2. Generar pg_dump dentro del contenedor y copiar con docker cp (100% seguro en binario)
docker exec $DbContainer pg_dump -U odoo -d ferreteria_mercado -Fc -Z 9 -f /tmp/backup_ferreteria_mercado.dump
docker cp "${DbContainer}:/tmp/backup_ferreteria_mercado.dump" "$DumpFile"

# 3. Verificar integridad del archivo generado (> 500 KB)
if ((Test-Path $DumpFile) -and ((Get-Item $DumpFile).Length -gt 500000)) {
    $SizeMB = [math]::Round((Get-Item $DumpFile).Length / 1MB, 2)
    Write-BackupLog "[EXITO LOCAL] Respaldo generado: $DumpFile ($SizeMB MB)"

    # Actualizar el archivo maestro de produccion
    Copy-Item -Path $DumpFile -Destination $LatestFile -Force

    # --------------------------------------------------------------------------
    # CAPA NUBE 1: Copiar a Google Drive / OneDrive si existen en la PC
    # --------------------------------------------------------------------------
    $CloudCandidatePaths = @(
        "G:\Mi unidad",
        "G:\My Drive",
        "$env:USERPROFILE\Google Drive",
        "$env:OneDriveCommercial",
        "$env:OneDrive",
        "$env:USERPROFILE\OneDrive"
    )
    foreach ($CloudRoot in $CloudCandidatePaths) {
        if ($CloudRoot -and (Test-Path $CloudRoot)) {
            $CloudBackupDir = Join-Path $CloudRoot "Backups_POS_Ferreteria_Mercado"
            if (-not (Test-Path $CloudBackupDir)) {
                New-Item -ItemType Directory -Path $CloudBackupDir -Force | Out-Null
            }
            Copy-Item -Path $DumpFile -Destination (Join-Path $CloudBackupDir "backup_ferreteria_mercado_$Timestamp.dump") -Force
            Copy-Item -Path $DumpFile -Destination (Join-Path $CloudBackupDir "ULTIMO_RESPALDO_ZAIS_EXPRESS.dump") -Force
            Write-BackupLog "[EXITO DRIVE/ONEDRIVE] Copia guardada en nube: $CloudBackupDir"

            # Limpiar copias antiguas en Drive (conservar ultimas 20)
            Get-ChildItem -Path $CloudBackupDir -Filter "backup_ferreteria_mercado_*.dump" |
                Sort-Object LastWriteTime -Descending |
                Select-Object -Skip 20 |
                ForEach-Object { Remove-Item $_.FullName -Force }
        }
    }

    # --------------------------------------------------------------------------
    # CAPA NUBE 2: Subir automaticamente el respaldo maestro a GitHub
    # --------------------------------------------------------------------------
    try {
        Push-Location $BaseDir
        git add -f "backups/PRODUCCION_REAL_FERRETERIA_MERCADO.dump" 2>&1 | Out-Null
        git commit -m "backup(auto): respaldo automatico de produccion $Timestamp ($SizeMB MB)" 2>&1 | Out-Null
        git push origin main 2>&1 | Out-Null
        Write-BackupLog "[EXITO GITHUB CLOUD] Respaldo subido a GitHub satisfactoriamente."
        Pop-Location
    } catch {
        Write-BackupLog "[AVISO GITHUB] No se pudo subir a GitHub en este intento: $_"
        Pop-Location
    }

} else {
    Write-BackupLog "[ERROR] El respaldo fallo o pesa menos de 500 KB."
}

# 4. Rotacion local: Conservar los ultimos 14 respaldos con fecha y borrar los mas viejos
$OldBackups = Get-ChildItem -Path $BackupDir -Filter "backup_ferreteria_mercado_*.dump" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 14

foreach ($b in $OldBackups) {
    Remove-Item $b.FullName -Force
    Write-BackupLog "[ROTACION] Eliminado respaldo antiguo local: $($b.Name)"
}

Write-BackupLog "=== PROCESO DE RESPALDO FINALIZADO ==="
