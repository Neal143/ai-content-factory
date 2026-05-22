# Last Update: 04/05/2026 16:15 (GMT+7)
<#
.SYNOPSIS
    Validate Format - Objective checks for Phase 7 (Format Agent)
.DESCRIPTION
    Check 5 criteria for Phase 7:
    production log, hook history, YAML frontmatter, pillar rotation, content integrity.
    Paragraph/heading checked in Phase 5 validate-draft.ps1.
.PARAMETER DraftPath
    Path to the final post file
.PARAMETER SourceDraftPath
    Path to 05-draft.md (used for Content Integrity check)
.PARAMETER LogPath
    Path to production-log.md
.PARAMETER HookHistoryPath
    Path to hook-history.md
.NOTES
    Last Update: 04/05/2026 16:15 (GMT+7)
#>

param(
    [Parameter(Mandatory=$true)][string]$DraftPath,
    [string]$SourceDraftPath = "",
    [string]$LogPath = "output/logs/production-log.md",
    [string]$HookHistoryPath = "output/logs/hook-history.md"
)

$ErrorActionPreference = "Stop"
$results = @()
$passCount = 0
$failCount = 0

# --- Helper: Record results ---
function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

# --- Read draft file ---
if (-not (Test-Path $DraftPath)) {
    Write-Host "ERROR: Draft not found at $DraftPath"; exit 1
}
$draft = Get-Content $DraftPath -Raw -Encoding UTF8

# ============================================================
# CHECK 2: Production Log Updated
# ============================================================
if (Test-Path $LogPath) {
    $logContent = Get-Content $LogPath -Raw -Encoding UTF8
    $today = Get-Date -Format "yyyy-MM-dd"
    if ($logContent -match $today) {
        Add-Result "Production Log" "PASS" "Log updated for $today"
    }
    else {
        Add-Result "Production Log" "FAIL" "No entry for today ($today)"
    }
}
else {
    Add-Result "Production Log" "FAIL" "File not found: $LogPath"
}

# ============================================================
# CHECK 3: Hook History Updated
# ============================================================
if (Test-Path $HookHistoryPath) {
    $hookContent = Get-Content $HookHistoryPath -Raw -Encoding UTF8
    if ($hookContent.Length -gt 20) {
        Add-Result "Hook History" "PASS" "Hook history has content"
    }
    else {
        Add-Result "Hook History" "FAIL" "Hook history is empty/minimal"
    }
}
else {
    Add-Result "Hook History" "FAIL" "File not found: $HookHistoryPath"
}

# ============================================================
# CHECK 4: YAML Frontmatter (metadata at top of file)
# ============================================================
$hasFrontmatter = $false
$requiredKeys = @('title', 'date', 'pillar', 'topic', 'hook_formula', 'word_count', 'qa_score', 'status')
$missingKeys = @()

if ($draft -match '(?s)^---\r?\n(.+?)\r?\n---') {
    $hasFrontmatter = $true
    $frontmatterBlock = $Matches[1]
    foreach ($key in $requiredKeys) {
        if ($frontmatterBlock -notmatch "(?i)${key}\s*:") {
            $missingKeys += $key
        }
    }
}

if ($hasFrontmatter -and $missingKeys.Count -eq 0) {
    Add-Result "YAML Frontmatter" "PASS" "All $($requiredKeys.Count) required keys present"
}
elseif ($hasFrontmatter) {
    Add-Result "YAML Frontmatter" "FAIL" "Missing keys: $($missingKeys -join ', ')"
}
else {
    Add-Result "YAML Frontmatter" "FAIL" "No YAML frontmatter block (---) found at top of file"
}

# ============================================================
# CHECK 4.1: YAML Frontmatter Spacing
# ============================================================
if ($hasFrontmatter) {
    if ($draft -match '(?s)^---.*?---\r?\n\r?\n') {
        Add-Result "YAML Spacing" "PASS" "Blank line found after Frontmatter"
    }
    else {
        Add-Result "YAML Spacing" "FAIL" "MISSING blank line after --- ending Frontmatter. (Markdown parser will fail)"
    }
}

# ============================================================
# CHECK 5: Pillar Rotation (no duplicates in 2 consecutive posts)
# Reason: AI ignores pillar diversity when appending production log.
# Script reads production-log.md and compares with current frontmatter.
# ============================================================
$currentPillar = ""
if ($hasFrontmatter -and $frontmatterBlock -match 'pillar:\s*"([^"]+)"') {
    $currentPillar = $Matches[1]
}

if ($currentPillar -and (Test-Path $LogPath)) {
    $logRaw = Get-Content $LogPath -Raw -Encoding UTF8
    $pillarMatches = [regex]::Matches($logRaw, '\*\*Pillar\*\*:\s*(.+)')
    if ($pillarMatches.Count -ge 2) {
        # Current post was appended to log BEFORE running this script
        # So "previous" post is the second to last match
        $previousPillar = $pillarMatches[$pillarMatches.Count - 2].Groups[1].Value.Trim()
        if ($currentPillar -eq $previousPillar) {
            Add-Result "Pillar Rotation" "FAIL" "Pillar '$currentPillar' matches previous post"
        }
        else {
            Add-Result "Pillar Rotation" "PASS" "Current: '$currentPillar' vs Previous: '$previousPillar'"
        }
    }
    else {
        Add-Result "Pillar Rotation" "PASS" "Only 1 post in log (no rotation needed)"
    }
}
elseif (-not $currentPillar) {
    Add-Result "Pillar Rotation" "WARN" "Could not extract pillar from frontmatter"
}
else {
    Add-Result "Pillar Rotation" "PASS" "No production log yet (first post)"
}

# ============================================================
# CHECK 6: Content Integrity (word count delta <= 2%)
# Ly do: Phase 7 Agent rewrites content -> loses words.
# Compare word count between 05-draft.md and 07-final.md body.
# Note: both files contain execution_key line so delta cancels out.
# ============================================================
if ($SourceDraftPath -and (Test-Path $SourceDraftPath)) {
    $sourceContent = Get-Content $SourceDraftPath -Raw -Encoding UTF8
    # Strip ALL structural markers before counting
    $sourceClean = $sourceContent -replace '\u2042', '' -replace '<!--[^>]*-->', ''
    $sourceWords = ($sourceClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

    $finalBody = $draft -replace '(?s)^---.*?---\s*', ''
    $finalClean = $finalBody -replace '<!--[^>]*-->', ''
    $finalWords = ($finalClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

    if ($sourceWords -gt 0) {
        $delta = [math]::Abs($sourceWords - $finalWords)
        $deltaPercent = [math]::Round(($delta / $sourceWords) * 100, 1)
        if ($deltaPercent -le 2) {
            Add-Result "Content Integrity" "PASS" "Delta: $delta words ($deltaPercent%)"
        }
        else {
            Add-Result "Content Integrity" "FAIL" "Delta: $delta words ($deltaPercent%) exceeds 2%. Source: $sourceWords, Final: $finalWords"
        }
    }
    else {
        Add-Result "Content Integrity" "WARN" "Source draft is empty"
    }
}
elseif ($SourceDraftPath) {
    Add-Result "Content Integrity" "FAIL" "Source draft not found: $SourceDraftPath"
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  FORMAT VALIDATION REPORT (Phase 7)"
Write-Host "========================================="
foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
