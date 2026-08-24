<#
Ten file: Update-PersonalAtomsQueue.ps1
Last update: 24/08/2026 14:45 (GMT+7)
Vai tro: Thin Wrapper duy tri backward compatibility cho cac skills cu va kich hoat Live-Sync refresh.
Su dung khi nao:
  - append: Goi boi story-architect/inbox-processor/persona-interviewer sau khi tao atom moi co source_type=User.
            Ghi file tam pending_curation_atoms.txt de VaultCuratorAgent xu ly.
  - remove: Goi boi validate-format.ps1 sau khi ghi production-log. Trigger refresh dashboard.
  - init: Goi boi migration 001 hoac khi can rebuild toan bo. Trigger refresh dashboard.
Output:
  - Ghi file tam vault/.tmp/pending_curation_atoms.txt (khi append).
  - Kich hoat generate_coverage_preview.py de refresh vault-health-report.md (co Khoi 7: Personal Queue).
Tom tat logic hoat dong:
  1. Neu Action=append va co AtomPathsRaw: Ghi tung duong dan atom vao file tam pending_curation_atoms.txt.
  2. Goi python generate_coverage_preview.py de refresh toan bo dashboards (bao gom Khoi 7 Personal Queue).
#>

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "append", "remove")]
    [string]$Action,

    # Comma-separated atom paths (giu nguyen interface cu cho backward compat)
    [Parameter(Mandatory = $false)]
    [string]$AtomPathsRaw = "",

    # Giu nguyen tham so cu de migration 001 va callers cu khong bi loi
    [Parameter(Mandatory = $false)]
    [string]$QueueFile = "vault/03-Content/Content Plan/personal-atoms-queue.md",

    [Parameter(Mandatory = $false)]
    [string]$ProductionLog = "vault/.content-pipeline/logs/production-log.md"
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# ==========================================
# NHOM 1: GHI FILE TAM PENDING CURATION ATOMS (Chi khi append)
# ==========================================
if ($Action -eq "append" -and $AtomPathsRaw -ne "") {
    $atomPaths = $AtomPathsRaw -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    if ($atomPaths.Count -gt 0) {
        $tmpDir = "vault/.tmp"
        if (-not (Test-Path $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null }
        $handoffPath = "$tmpDir/pending_curation_atoms.txt"
        foreach ($p in $atomPaths) {
            $cleanPath = $p -replace '\\', '/'
            [System.IO.File]::AppendAllText($handoffPath, "$cleanPath`r`n", $utf8NoBom)
        }
        Write-Host "[OK] Ghi $($atomPaths.Count) atom(s) vao pending_curation_atoms.txt" -ForegroundColor Green
    }
}

# ==========================================
# NHOM 2: KICH HOAT LIVE-SYNC REFRESH DASHBOARDS
# ==========================================
$previewScript = ".agents/scripts/generate_coverage_preview.py"
if (-not (Test-Path $previewScript)) {
    # Ho tro neu dang dung o workspace root thay vi Content Factory
    $previewScript = "Content Factory/.agents/scripts/generate_coverage_preview.py"
}

if (Test-Path $previewScript) {
    python $previewScript
    Write-Host "[OK] Dashboard refreshed (vault-health-report.md + coverage-preview.md)" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Khong tim thay script generate_coverage_preview.py" -ForegroundColor Yellow
}
