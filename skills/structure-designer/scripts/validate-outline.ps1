# Last Update: 02/05/2026 16:50 (GMT+7)
<#
.SYNOPSIS
    Validate Outline - Objective checks for Phase 4 (Structure Designer)
.DESCRIPTION
    Check: section count (5), word allocation total (configurable), closing rotation.
.PARAMETER OutlinePath
    Path to outline-brief.md
.PARAMETER LogPath
    Path to production-log.md
.NOTES
    Last Update: 18/05/2026
#>

param(
    [Parameter(Mandatory=$true)][string]$OutlinePath,
    [string]$LogPath = "output/logs/production-log.md"
)

$ErrorActionPreference = "Stop"

# --- Load Format Profile ---
$profilePath = "profiles/active.json"
if (-not (Test-Path $profilePath)) {
    $profilePath = "profiles/default.json"
}
if (-not (Test-Path $profilePath)) {
    Write-Host "WARNING: No format profile found. Using hardcoded defaults."
    $profile = $null
} else {
    $profile = Get-Content $profilePath -Raw -Encoding UTF8 | ConvertFrom-Json
}
$cfgWordCountMin = if ($profile) { $profile.word_count_total.min } else { 1500 }
$cfgWordCountMax = if ($profile) { $profile.word_count_total.max } else { 1800 }

$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

if (-not (Test-Path $OutlinePath)) {
    Write-Host "ERROR: Outline not found at $OutlinePath"; exit 1
}
$outline = Get-Content $OutlinePath -Raw -Encoding UTF8

# ============================================================
# CHECK 1: Word Count Allocation (total in configured range)
# ============================================================
$wordNumbers = [regex]::Matches($outline, '(\d+)\s*(?:tu|t\S+|words?)')
$totalAllocated = 0
foreach ($m in $wordNumbers) {
    $totalAllocated += [int]$m.Groups[1].Value
}
if ($totalAllocated -gt 0) {
    if ($totalAllocated -ge $cfgWordCountMin -and $totalAllocated -le $cfgWordCountMax) {
        Add-Result "Word Allocation" "PASS" "Total: $totalAllocated words ($cfgWordCountMin-$cfgWordCountMax)"
    }
    else {
        Add-Result "Word Allocation" "FAIL" "Total: $totalAllocated words (range: $cfgWordCountMin-$cfgWordCountMax)"
    }
}
else {
    Add-Result "Word Allocation" "WARN" "Could not extract word allocations from outline"
}

# ============================================================
# CHECK 2: Closing Rotation (E-tone + S-technique not repeating)
# ============================================================
if (Test-Path $LogPath) {
    $log = Get-Content $LogPath -Raw -Encoding UTF8

    # Find closing combo in outline (E1-E6, S1-S6)
    $currentE = ""
    $currentS = ""
    if ($outline -match '\b(E[1-6])\b') { $currentE = $Matches[1] }
    if ($outline -match '\b(S[1-6])\b') { $currentS = $Matches[1] }

    # Find recent combos in log
    $recentE = [regex]::Matches($log, '\b(E[1-6])\b') | Select-Object -Last 2
    $recentS = [regex]::Matches($log, '\b(S[1-6])\b') | Select-Object -Last 2

    $eDuplicate = $false
    $sDuplicate = $false
    foreach ($m in $recentE) {
        if ($m.Value -eq $currentE) { $eDuplicate = $true }
    }
    foreach ($m in $recentS) {
        if ($m.Value -eq $currentS) { $sDuplicate = $true }
    }

    if ($currentE -and $currentS) {
        if (-not $eDuplicate -and -not $sDuplicate) {
            Add-Result "Closing Rotation" "PASS" "$currentE + $currentS (no repeat)"
        }
        else {
            $detail = ""
            if ($eDuplicate) { $detail += "$currentE repeats; " }
            if ($sDuplicate) { $detail += "$currentS repeats" }
            Add-Result "Closing Rotation" "FAIL" $detail.Trim('; ')
        }
    }
    else {
        Add-Result "Closing Rotation" "WARN" "Could not find E/S combo in outline"
    }
}
else {
    Add-Result "Closing Rotation" "PASS" "No production log yet (first post)"
}

# ============================================================
# CHECK 3: Nomenclature Compliance (No Framework)
# ============================================================
if ($outline -match '(?i)framework') {
    Add-Result "Nomenclature" "FAIL" "Found forbidden term 'Framework'"
}
elseif ($outline -match '(?i)(solution|concept)') {
    Add-Result "Nomenclature" "PASS" "Found valid terms 'Solution' or 'Concept'"
}
else {
    Add-Result "Nomenclature" "WARN" "No Solution/Concept mentioned"
}

# ============================================================
# CHECK 4: Atoms Declaration
# Story and Deep Dive must declare Atoms
# Use section extraction to avoid cross-section matching
# ============================================================
$storyHasAtoms = $false
$diveHasAtoms = $false

if ($outline -match '(?is)##\s*Story\b(.*?)(?=##\s|\z)') {
    if ($Matches[1] -match "(?i)Atoms\s*[:$([char]0xFF1A)]\s*\S") {
        $storyHasAtoms = $true
    }
}
if ($outline -match '(?is)##\s*Deep\s*Dive\b(.*?)(?=##\s|\z)') {
    if ($Matches[1] -match "(?i)Atoms\s*[:$([char]0xFF1A)]\s*\S") {
        $diveHasAtoms = $true
    }
}

if ($storyHasAtoms -and $diveHasAtoms) {
    Add-Result "Atoms Declaration" "PASS" "Story and Deep Dive both declare Atoms"
}
else {
    $detail = ""
    if (-not $storyHasAtoms) { $detail += "Story missing Atoms; " }
    if (-not $diveHasAtoms) { $detail += "Deep Dive missing Atoms" }
    Add-Result "Atoms Declaration" "FAIL" $detail.Trim('; ')
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  OUTLINE VALIDATION REPORT (Phase 4)"
Write-Host "========================================="
foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
