# Tên file: validate-outline.ps1
# Last update: 05/06/2026 11:30 (GMT+7)
# Vai trò: Kiểm định chất lượng và tính hợp lệ của Outline (Dàn ý) bài viết cho Phase 4.
# Sử dụng khi nào: Được gọi ở Phase 4 bởi detect-bypass.ps1 để kiểm tra file 04-outline.md.
# Output: Exit 0 nếu hợp lệ (PASS), exit > 0 nếu vi phạm điều kiện kiểm định (FAIL).
# Tóm tắt logic hoạt động:
#   1. Đọc tệp cấu hình formats/active.json để lấy số từ mục tiêu min/max.
#   2. Đọc file 04-outline.md và phân tích các thẻ BLOCK theo hợp đồng dữ liệu trong SKILL.md.
#   3. Tính toán tổng số lượng từ phân bổ cho các phần trong dàn ý và so sánh với cấu hình.
#   4. Kiểm tra rotation của phần kết bài (Closing Rotation E/S combo) dựa trên lịch sử trong production-log.md.
#   5. Xác minh sự tồn tại của từ cấm "Framework" và khai báo Atom trong các phần Story và Deep Dive.

param(
    [Parameter(Mandatory=$true)][string]$OutlinePath,
    [string]$LogPath = "vault/.content-pipeline/logs/production-log.md"
)

$ErrorActionPreference = "Stop"

# --- Load Format Config ---
$formatPath = "formats/active.json"
if (-not (Test-Path $formatPath)) {
    $formatPath = "formats/default.json"
}
if (-not (Test-Path $formatPath)) {
    Write-Host "WARNING: No format config found. Using hardcoded defaults."
    $format = $null
} else {
    $format = Get-Content $formatPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
$cfgWordCountMin = if ($format) { $format.word_count_total.min } else { 1500 }
$cfgWordCountMax = if ($format) { $format.word_count_total.max } else { 1800 }

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
                if ($outline -match $rx) {
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
