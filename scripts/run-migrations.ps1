# ------------------------------------------------------------------
# run-migrations.ps1
# Last update: 22/06/2026 23:56 (GMT+7)
# Role: Read FACTORY_VERSION, scan migrations/ folder, execute
#       pending migration scripts in sequential order.
# When: Called automatically by /update-agents workflow after
#       replacing .agents/ folder.
# Output: Console messages indicating migration status.
# Logic: Read version -> find pending scripts -> run each ->
#        update version. If no FACTORY_VERSION file exists,
#        create it with value 0 and run all migrations.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot
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

# --- Execute pending migrations sequentially ---
Write-Host "Found $($migrationFiles.Count) pending migration(s). Current version: $currentVersion"

foreach ($mig in $migrationFiles) {
    Write-Host "Running migration $($mig.Name) ..."
    powershell -ExecutionPolicy Bypass -File $mig.FullPath -FactoryRoot $FactoryRoot
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Migration $($mig.Name) failed with exit code $LASTEXITCODE"
        Write-Host "Stopping. Version stays at $currentVersion"
        exit 1
    }
    # Update version after each successful migration
    $currentVersion = $mig.Number
    Set-Content -Path $versionFile -Value "$currentVersion" -NoNewline
    Write-Host "OK. Version updated to $currentVersion"
}

Write-Host "All migrations completed successfully. Final version: $currentVersion"
exit 0
