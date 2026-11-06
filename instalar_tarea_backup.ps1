# ==============================================================================
# INSTALADOR DE TAREA PROGRAMADA DE RESPALDO AUTOMATICO (2:00 PM y 10:00 PM)
# ==============================================================================

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$BackupScript = Join-Path $ScriptDir "backup_automatico.ps1"
$TaskName = "Respaldo_Automatico_Ferreteria_Mercado"

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO RESPALDO AUTOMATICO EN LA NUBE" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Crear disparadores: Todos los dias a las 2:00 PM (14:00) y 10:00 PM (22:00)
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "14:00"
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "22:00"

# 2. Accion: Ejecutar PowerShell oculto corriendo backup_automatico.ps1
$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$BackupScript`"" `
    -WorkingDirectory $ScriptDir

# 3. Configuracion: Ejecutar aunque este con bateria, reintentar si falla y correr apenas prenda
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# 4. Registrar tarea programada en Windows
Register-ScheduledTask -TaskName $TaskName `
    -Trigger @($Trigger1, $Trigger2) `
    -Action $Action `
    -Settings $Settings `
    -Description "Respaldo automatico diario de ERP Ferreteria Mercado hacia Local, Google Drive/OneDrive y GitHub Cloud" `
    -Force | Out-Null

Write-Host "[OK] Tarea programada '$TaskName' instalada con exito (2:00 PM y 10:00 PM)." -ForegroundColor Green
Write-Host "Ejecutando primer respaldo de prueba hacia la nube ahora mismo..." -ForegroundColor Yellow
Write-Host ""

# 5. Ejecutar un respaldo inmediato de prueba
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$BackupScript"
