# ------------------------------------------------------------------
# run-migrations.ps1
# Last update: 23/06/2026 15:12 (GMT+7)
# Role: Read FACTORY_VERSION, scan migrations/ folder, backup
#       user data (vault/, personas/) via robocopy, then execute
#       pending migration scripts in sequential order.
# When: Called automatically by /update-agents workflow after
#       replacing .agents/ folder.
# Output: Console messages indicating migration status.
#         Exit 0 = success, Exit 1 = failure.
# Logic: Read version -> find pending -> if none: exit 0 ->
#        backup vault/ + personas/ (check robocopy exit code) ->
#        run each migration -> update version.
#        Backup is NEVER auto-deleted.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot,

    [Parameter(Mandatory = $false)]
    [string]$BackupDir = ""
)

# --- Path setup ---
$versionFile = Join-Path $FactoryRoot "FACTORY_VERSION"
$migrationsDir = Join-Path $FactoryRoot ".agents\migrations"

# --- Read current version (default 0 if file missing) ---
if (Test-Path $versionFile) {
    $currentVersion = [int](Get-Content $versionFile -Raw).Trim()
} else {
    $currentVersion = 0
    Set-Content -Path $versionFile -Value "0" -NoNewline
    Write-Host "FACTORY_VERSION not found. Created with value 0."
}

# --- Scan migration scripts ---
$migrationFiles = @()
if (Test-Path $migrationsDir) {
    $migrationFiles = @(
        Get-ChildItem -Path $migrationsDir -Filter "*.ps1" |
        Where-Object {
            $_.Name -match '^\d+_'
        } |
        ForEach-Object {
            $num = [int]($_.Name -replace '^(\d+)_.*', '$1')
            [PSCustomObject]@{ Number = $num; FullPath = $_.FullName; Name = $_.Name }
        } |
        Where-Object { $_.Number -gt $currentVersion } |
        Sort-Object Number
    )
}

# --- No pending migrations ---
if ($migrationFiles.Count -eq 0) {
    Write-Host "Already up to date. Current version: $currentVersion"
    exit 0
}

# --- Backup user data before running migrations ---
# BackupDir is passed by /update-agents workflow.
# If not provided (standalone run), create a timestamped folder.
if (-not $BackupDir) {
    $timestamp = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId(
        (Get-Date), 'SE Asia Standard Time'
    ).ToString('yyyy-MM-dd_HHmmss')
    $BackupDir = Join-Path $FactoryRoot ".update_backups\backup_$timestamp"
}

New-Item -Path $BackupDir -ItemType Directory -Force | Out-Null

$vaultPath = Join-Path $FactoryRoot "vault"
$personasPath = Join-Path $FactoryRoot "personas"

if (Test-Path $vaultPath) {
    Write-Host "Backing up vault/ ..."
    robocopy $vaultPath (Join-Path $BackupDir "vault") /E /NJH /NJS /NDL /NFL /NC /NS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) {
        Write-Host "ERROR: Failed to backup vault/. Robocopy exit code: $LASTEXITCODE"
        Write-Host "Migrations NOT executed. No data was changed."
        exit 1
    }
}

if (Test-Path $personasPath) {
    Write-Host "Backing up personas/ ..."
    robocopy $personasPath (Join-Path $BackupDir "personas") /E /NJH /NJS /NDL /NFL /NC /NS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) {
        Write-Host "ERROR: Failed to backup personas/. Robocopy exit code: $LASTEXITCODE"
        Write-Host "Migrations NOT executed. No data was changed."
        exit 1
    }
}

Write-Host "Data backup saved to: $BackupDir"

# --- Execute pending migrations sequentially ---
Write-Host "Found $($migrationFiles.Count) pending migration(s). Current version: $currentVersion"

foreach ($mig in $migrationFiles) {
    Write-Host "Running migration $($mig.Name) ..."
    powershell -ExecutionPolicy Bypass -File $mig.FullPath -FactoryRoot $FactoryRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Migration $($mig.Name) failed with exit code $LASTEXITCODE"
        Write-Host "Stopping. Version stays at $currentVersion"
        Write-Host "Your original data is safe at: $BackupDir"
        exit 1
    }
    # Update version after each successful migration
    $currentVersion = $mig.Number
    Set-Content -Path $versionFile -Value "$currentVersion" -NoNewline
    Write-Host "OK. Version updated to $currentVersion"
}

Write-Host "All migrations completed successfully. Final version: $currentVersion"
Write-Host "DATA BACKUP is kept at: $BackupDir"
Write-Host "You may delete old backups after confirming everything works."
exit 0
