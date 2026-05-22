# File       : create-checkpoint.ps1
# Last update: 21/05/2026 11:22 (GMT+7)
# Vai tro    : Tao checkpoint.yaml trong run folder.
#              Tu suy ra completed_phases va current_phase tu file ton tai.
# Dung khi   : Duoc goi TU DONG boi detect-bypass.ps1 khi Phase 4 PASS.
# Output     : Exit 0 = OK (checkpoint.yaml da ghi)
#              Exit 1 = FAIL (error message)
# Logic      : Quet file trong RunFolder -> map sang phase -> ghi YAML

param(
    [Parameter(Mandatory = $true)][string]$RunFolder
)

$ErrorActionPreference = "Stop"

# --- Ordered mapping: filename -> phase number ---
# Thu tu PHAI dung thu tu pipeline (0 -> 1 -> 2 -> 3 -> 4 -> 45 -> 5 -> 6 -> 7)
$phaseOrder = @(
    @{ Phase = 0; File = "00-blackboard.yaml" }
    @{ Phase = 1; File = "01-idea-brief.md" }
    @{ Phase = 2; File = "02-research-brief.md" }
    @{ Phase = 3; File = "03-hook.md" }
    @{ Phase = 4; File = "04-outline.md" }
    @{ Phase = 45; File = "04.5-persona-pack.md" }
    @{ Phase = 5; File = "05-draft.md" }
    @{ Phase = 6; File = "06-qa-result.md" }
    @{ Phase = 7; File = "07-final.md" }
)

# --- Quet file ton tai -> xay completed_phases va current_phase ---
$completed = @()
$currentPhase = $null

foreach ($entry in $phaseOrder) {
    $filePath = Join-Path $RunFolder $entry.File
    if (Test-Path $filePath) {
        $completed += $entry.Phase
    }
    elseif ($null -eq $currentPhase) {
        # Phase dau tien khong co file = phase tiep theo can chay
        $currentPhase = $entry.Phase
    }
}

# --- Kiem tra: khong co file nao -> state khong hop le ---
if ($completed.Count -eq 0) {
    Write-Host "[FAIL] Khong tim thay file nao trong $RunFolder."
    exit 1
}

# --- Fallback: neu tat ca file ton tai (hoan thanh), current = completed ---
if ($null -eq $currentPhase) { $currentPhase = "completed" }

# --- Ghi checkpoint.yaml (ghi de neu da ton tai) ---
$timestamp = (Get-Date).ToUniversalTime().AddHours(7).ToString("yyyy-MM-ddTHH:mm:ss+07:00")
$statusValue = if ($currentPhase -eq "completed") { "completed" } else { "in_progress" }
$yaml = @"
status: $statusValue
current_phase: $currentPhase
completed_phases: [$($completed -join ', ')]
last_updated: "$timestamp"
"@

$cpPath = Join-Path $RunFolder "checkpoint.yaml"
Set-Content -Path $cpPath -Value $yaml -Encoding UTF8 -Force

# --- Thong bao ket qua ---
Write-Host "[CHECKPOINT] Da luu checkpoint.yaml thanh cong."
exit 0
