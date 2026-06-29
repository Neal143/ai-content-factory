# ------------------------------------------------------------------
# init_vault.ps1
# Last update: 30/06/2026 00:55 (GMT+7)
# Role: Khoi tao toan bo he sinh thai cho user moi: persona folder
#       (tu .agents/assets/persona-template) va cau truc he thong
#       (tu .agents/assets/factory-scaffold via sync script).
# When: Goi boi persona-interviewer SKILL.md khi user bat dau onboarding.
# Output: Console messages. Exit 0 = success, Exit 1 = failure.
# Logic: Validate template -> create persona dir (neu chua co) ->
#        copy persona templates -> call sync-factory-scaffold ->
#        cleanup stale .gitkeep.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$UserName
)

$ErrorActionPreference = "Stop"

# --- Xac dinh workspace root (4 cap: scripts -> persona-interviewer -> skills -> .agents -> root) ---
$workspaceRoot = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

Write-Host ">>> Bat dau khoi tao he sinh thai Persona va Vault cho: $UserName"

# === KHOI 1: Khoi tao Persona ===
$templateDir = Join-Path $workspaceRoot ".agents\assets\persona-template"
$personaDir = Join-Path $workspaceRoot "personas\$UserName"

# Validate template ton tai (LUON kiem tra, bat ke persona da co hay chua)
if (-not (Test-Path $templateDir)) {
    Write-Host "[FATAL] Persona template not found at: $templateDir" -ForegroundColor Red
    exit 1
}

# Chi tao + copy khi persona dir CHUA TON TAI (bao ve du lieu user da onboard)
if (-not (Test-Path $personaDir)) {
    New-Item -ItemType Directory -Path $personaDir -Force | Out-Null
    Copy-Item -Path "$templateDir\*" -Destination $personaDir -Recurse -Force
    Write-Host "[OK] Da tao persona folder: personas/$UserName (7 YAML templates)"
} else {
    Write-Host "[INFO] Persona folder da ton tai: personas/$UserName (giu nguyen du lieu)"
}

# === KHOI 2: Dong bo cau truc he thong (folders + foundation files) ===
$syncScript = Join-Path $workspaceRoot ".agents\scripts\sync-factory-scaffold.ps1"
if (-not (Test-Path $syncScript)) {
    Write-Host "[FATAL] Sync script not found at: $syncScript" -ForegroundColor Red
    exit 1
}
powershell -ExecutionPolicy Bypass -File $syncScript -FactoryRoot $workspaceRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FATAL] Factory scaffold sync failed." -ForegroundColor Red
    exit 1
}

# === KHOI 3: Don dep .gitkeep thua (backward compat voi version cu) ===
$gitkeep = Join-Path $workspaceRoot "vault\00-Inbox\.gitkeep"
if (Test-Path $gitkeep) { Remove-Item $gitkeep -Force }

Write-Host ">>> HOAN TAT TAO LAP HE THONG!" -ForegroundColor Green