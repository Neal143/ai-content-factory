<#
.SYNOPSIS
    Validate Hook — Objective checks cho Phase 3 (Hook Engineer)
.DESCRIPTION
    Kiểm tra: core hook word count (≤ 15 từ), hook formula rotation.
.PARAMETER HookPath
    Đường dẫn tới file hook-brief.md
.PARAMETER HistoryPath
    Đường dẫn tới file hook-history.md
.NOTES
    Last Update: 28/04/2026 15:24 (GMT+7)
#>

param(
    [Parameter(Mandatory = $true)][string]$HookPath,
    [string]$HistoryPath = "output/logs/hook-history.md"
)

$ErrorActionPreference = "Stop"
$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

if (-not (Test-Path $HookPath)) {
    Write-Host "ERROR: Hook brief not found at $HookPath"; exit 1
}
$hook = Get-Content $HookPath -Raw -Encoding UTF8

# ============================================================
# CHECK BLOCK: Data Contract Validation (Dynamic from SKILL.md)
# ============================================================
$skillMdPath = Join-Path $PSScriptRoot "../SKILL.md"
if (Test-Path $skillMdPath) {
    $skillRaw = Get-Content $skillMdPath -Raw -Encoding UTF8
    if ($skillRaw -match "(?s)^---\r?\n(.*?)\r?\n---") {
        $fm = $Matches[1]
        if ($fm -match "(?s)provided_outputs:\r?\n(.*?)(?:\r?\n\S|\Z)") {
            $poBlock = $Matches[1]
            $outputs = [regex]::Matches($poBlock, '-\s*(\S+)') | ForEach-Object { $_.Groups[1].Value }
            foreach ($blk in $outputs) {
                $rx = "(?s)\[BLOCK:\s*$blk\s*\](.*?)\[/BLOCK:\s*$blk\s*\]"
                if ($hook -match $rx) {
                    if ($Matches[1].Trim().Length -gt 0) {
                        Add-Result "Block [$blk]" "PASS" "OK ($($Matches[1].Trim().Length) chars)"
                    } else {
                        Add-Result "Block [$blk]" "FAIL" "Block rong"
                    }
                } else {
                    Add-Result "Block [$blk]" "FAIL" "Thieu [BLOCK: $blk]...[/BLOCK: $blk]"
                }
            }
        }
    }
} else {
    Add-Result "Block Check" "WARN" "SKILL.md khong tim thay tai $skillMdPath"
}


# ============================================================
# CHECK 1: Core Hook ≤ 15 words
# ============================================================
# Try to find the core hook line (after "Core Hook:" or first non-header line)
$coreHookLine = ""
$hookLines = Get-Content $HookPath -Encoding UTF8
foreach ($line in $hookLines) {
    if ($line -match '(?i)core\s*hook\s*[:：]\s*(.+)') {
        $coreHookLine = $Matches[1].Trim()
        break
    }
}
if ($coreHookLine) {
    $hookWordCount = ($coreHookLine -split '\s+' | Where-Object { $_ -ne '' }).Count
    if ($hookWordCount -le 15) {
        Add-Result "Core Hook Length" "PASS" "$hookWordCount tu (<= 15)"
    }
    else {
        Add-Result "Core Hook Length" "FAIL" "$hookWordCount tu (max 15)"
    }
}
else {
    Add-Result "Core Hook Length" "WARN" "Could not find 'Core Hook:' line in brief"
}

# ============================================================
# CHECK 2: Hook Formula Rotation
# ============================================================
if (Test-Path $HistoryPath) {
    $history = Get-Content $HistoryPath -Raw -Encoding UTF8
    # Extract current formula from hook brief
    $currentFormula = ""
    foreach ($line in $hookLines) {
        if ($line -match '(?i)(formula|cong\s*thuc|F\d+)\s*[:：]\s*(.+)') {
            $currentFormula = $Matches[2].Trim()
            break
        }
        if ($line -match '\b(F\d{1,2})\b') {
            $currentFormula = $Matches[1]
            break
        }
    }

    if ($currentFormula) {
        # Extract last 2 formulas from history
        $historyFormulas = [regex]::Matches($history, '(?i)(?:formula|hook\s*formula)\s*[:：]\s*(\S+)')
        $recentFormulas = @()
        if ($historyFormulas.Count -gt 0) {
            $startIdx = [Math]::Max(0, $historyFormulas.Count - 2)
            for ($i = $startIdx; $i -lt $historyFormulas.Count; $i++) {
                $recentFormulas += $historyFormulas[$i].Groups[1].Value
            }
        }

        if ($currentFormula -in $recentFormulas) {
            Add-Result "Hook Rotation" "FAIL" "'$currentFormula' trung voi 2 bai gan nhat: $($recentFormulas -join ', ')"
        }
        else {
            Add-Result "Hook Rotation" "PASS" "'$currentFormula' khong trung (recent: $($recentFormulas -join ', '))"
        }
    }
    else {
        Add-Result "Hook Rotation" "WARN" "Could not extract formula from hook brief"
    }
}
else {
    Add-Result "Hook Rotation" "PASS" "No hook history yet (first post)"
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  HOOK VALIDATION REPORT (Phase 3)"
Write-Host "========================================="
foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
if ($failCount -eq 0) {
    Write-Host "  Verdict: ALL OBJECTIVE CHECKS PASSED"
}
else {
    Write-Host "  Verdict: $failCount ISSUE(S) NEED FIXING"
}
Write-Host "========================================="

exit $failCount
