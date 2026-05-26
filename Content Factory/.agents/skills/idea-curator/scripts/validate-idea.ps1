# Tên file: validate-idea.ps1
# Last Update: 15/05/2026 00:20 (GMT+7)
# Vai trò: Poka-Yoke gate khách quan cho Phase 1 Idea Curator.
# Được sử dụng khi nào?: Chạy ở bước tự kiểm tra (Self-Check Gate) cuối cùng của Phase 1.
# Output là gì: Exit code (0 = PASS, >0 = FAIL) và log báo cáo chi tiết.
# Tóm tắt logic hoạt động: Đọc file Idea Brief, quét 5 Regex checks độc lập đa hình để chặn lỗi format, thiếu section bắt buộc và thiếu nguyên liệu gốc.

<#
.SYNOPSIS
    Validate Idea — Objective checks cho Phase 1 (Idea Curator)
.DESCRIPTION
    Poka-Yoke gate: Kiểm tra cấu trúc Idea Brief. 
    5 checks: Blackboard Integrity, Audience Routing, Viral Score Gate, Structural Completeness, DIKW Reference Integrity.
.PARAMETER IdeaPath
    Đường dẫn tới idea-brief.md
#>

param(
    [Parameter(Mandatory=$true)][string]$IdeaPath
)

$ErrorActionPreference = "Stop"
$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

if (-not (Test-Path $IdeaPath)) {
    Write-Host "ERROR: Idea brief not found at $IdeaPath"; exit 1
}
$idea = Get-Content $IdeaPath -Raw -Encoding UTF8

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
                if ($idea -match $rx) {
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
# CHECK 1: Blackboard Integrity
# Ý nghĩa: Đảm bảo LLM giữ lại các biến cốt lõi từ Blackboard. Trích xuất Is_Novel_Angle để định tuyến các check kế.
# ============================================================
$hasTopics = ($idea -match '(?im)^\s*(?:-\s*)?topics\s*[:：]\s*(.+)')
$hasPillar = ($idea -match '(?im)^\s*(?:-\s*)?Target_Pillar\s*[:：]\s*(.+)')
$hasNovel  = ($idea -match '(?im)^\s*(?:-\s*)?Is_Novel_Angle\s*[:：]\s*(.+)')

$isNovelValue = $false
if ($hasNovel) {
    # Parse string thành boolean an toàn để dùng làm toán tử
    $val = $Matches[1].Trim() -replace '["'']', ''
    if ($val -match '(?i)^true$') { $isNovelValue = $true }
}

if ($hasTopics -and $hasPillar -and $hasNovel) {
    Add-Result "Blackboard Integrity" "PASS" "Found all core variables"
} else {
    Add-Result "Blackboard Integrity" "FAIL" "Missing topics, Target_Pillar, or Is_Novel_Angle"
}

# ============================================================
# CHECK 2: Audience Routing
# Ý nghĩa: Kịch bản 1 (Thuần Vault) bắt buộc phải có đối tượng độc giả mục tiêu.
# ============================================================
if (-not $isNovelValue) {
    $hasAudience = ($idea -match '(?im)^\s*(?:-\s*)?Target_Audience\s*[:：]\s*(.+)')
    if ($hasAudience) {
        Add-Result "Audience Routing" "PASS" "Target_Audience found for Standard mode"
    } else {
        Add-Result "Audience Routing" "FAIL" "Standard mode requires Target_Audience"
    }
}

# ============================================================
# CHECK 3: Viral Score Threshold
# Ý nghĩa: Đảm bảo Viral Score được sinh ra đúng cấu trúc số và vượt ngưỡng >= 7.
# ============================================================
if ($idea -match '(?i)Viral.*?(?:Score|Điểm).*?([0-9]+(?:\.[0-9]+)?)\s*/\s*10') {
    $score = [double]$Matches[1]
    if ($score -ge 7) {
        Add-Result "Viral Score" "PASS" "Score is $score/10 (>= 7)"
    } else {
        Add-Result "Viral Score" "FAIL" "Score is $score/10 (Below 7 threshold)"
    }
} else {
    Add-Result "Viral Score" "FAIL" "Score not found or invalid format"
}

# ============================================================
# CHECK 4: Structural Completeness
# Ý nghĩa: Chống việc LLM bỏ sót các section yêu cầu trong Dàn bài.
# ============================================================
$req1 = ($idea -match '(?i)Contrarian')
$req2 = ($idea -match '(?i)Core Tension')
$req3 = ($idea -match '(?i)Hidden Belief')
$req4 = ($idea -match '(?i)Transformation Promise')

if ($req1 -and $req2 -and $req3 -and $req4) {
    Add-Result "Structural Completeness" "PASS" "All 4 core sections are present"
} else {
    Add-Result "Structural Completeness" "FAIL" "Missing one or more core sections"
}

# ============================================================
# CHECK 5: DIKW Reference Integrity
# Ý nghĩa: Kịch bản 1 bắt buộc phải sử dụng Insight và Solution từ thư viện để đảm bảo chuyên môn.
# ============================================================
if (-not $isNovelValue) {
    $hasInsight = ($idea -match '(?i)insight')
    $hasSolution = ($idea -match '(?i)(solution|concept)')
    
    if ($hasInsight -and $hasSolution) {
        Add-Result "DIKW Reference" "PASS" "Standard mode references Vault assets"
    } else {
        Add-Result "DIKW Reference" "FAIL" "Missing Insight or Solution/Concept in Standard mode"
    }
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  IDEA VALIDATION REPORT (Phase 1)"
Write-Host "========================================="
foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
