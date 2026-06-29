# ------------------------------------------------------------------
# sync-factory-scaffold.ps1
# Last update: 30/06/2026 00:55 (GMT+7)
# Role: Scan .agents/assets/factory-scaffold/ template va mirror
#       toan bo cau truc thu muc + foundation files sang FactoryRoot.
# When: Goi boi run-migrations.ps1 (truoc numbered migrations)
#       va boi init_vault.ps1 (khi onboarding user moi).
# Output: Console messages. Exit 0 = success, Exit 1 = failure.
# Logic: Scan template dir recursive -> tao folder neu thieu ->
#        copy file neu thieu (bo qua .gitkeep) -> bao cao.
#        TUYET DOI KHONG BAO GIO ghi de file da ton tai.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot
)

$ErrorActionPreference = "Stop"

# --- Xac dinh duong dan template ---
$templateDir = Join-Path $FactoryRoot ".agents\assets\factory-scaffold"
if (-not (Test-Path $templateDir)) {
    Write-Host "[FATAL] factory-scaffold template not found at: $templateDir" -ForegroundColor Red
    exit 1
}

Write-Host "Syncing factory scaffold from template..."
$createdCount = 0

# --- Scan de quy va mirror ---
$items = Get-ChildItem -Path $templateDir -Recurse

foreach ($item in $items) {
    # Tinh relative path: cat phan templateDir ra khoi FullName
    $relativePath = $item.FullName.Substring($templateDir.Length).TrimStart('\', '/')
    $destPath = Join-Path $FactoryRoot $relativePath

    if ($item.PSIsContainer) {
        # --- FOLDER: tao neu chua co ---
        if (-not (Test-Path $destPath)) {
            New-Item -ItemType Directory -Path $destPath -Force | Out-Null
            Write-Host "  + Created folder: $relativePath"
            $createdCount++
        }
    }
    else {
        # --- FILE: bo qua .gitkeep, copy neu chua co ---
        if ($item.Name -eq ".gitkeep") { continue }
        if (-not (Test-Path $destPath)) {
            # Dam bao parent folder ton tai
            $parentDir = Split-Path $destPath -Parent
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }
            Copy-Item -Path $item.FullName -Destination $destPath -Force
            Write-Host "  + Created file: $relativePath"
            $createdCount++
        }
    }
}

# --- Bao cao ---
if ($createdCount -eq 0) {
    Write-Host "[OK] Factory scaffold is up to date."
} else {
    Write-Host "[OK] Created $createdCount new item(s)."
}
exit 0
