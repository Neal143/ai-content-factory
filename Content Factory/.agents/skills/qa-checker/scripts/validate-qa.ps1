<#
.SYNOPSIS
    Tên file: validate-qa.ps1
    Vai trò: Làm "người gác cổng" (Quality Gate) cho Phase 6 (QA Checker).
    Được sử dụng khi nào: Chạy tự động ngay sau khi QA Checker tạo xong file 06-qa-result.md.
    Input: Đường dẫn file 06-qa-result.md. PersonaPath auto-detect từ 00-blackboard.yaml.
    Output: Trả về PASS/FAIL cho 4 tiêu chí (Điểm chuẩn, Tính nhất quán, Đối chiếu Atom, FILE_KEY Persona). Nếu có lỗi, exit code > 0.
.DESCRIPTION
    Tóm tắt logic hoạt động:
    1. Kiểm tra tổng điểm QA có lớn hơn hoặc bằng điểm sàn (pass_threshold) trong rules không.
    2. Kiểm tra chữ VERDICT (PASS/REVISE/FAIL) có khớp với điểm số thực tế không.
    3. Kiểm tra Poka-Yoke: Đếm số lượng Atom trong Phase 2 phải khớp với số lượng block "Vault Fact" đã check trong Phase 6.
.PARAMETER QAResultPath
    Đường dẫn tới 06-qa-result.md
.PARAMETER ScoringRulesPath
    Đường dẫn tới scoring-rules.yaml
.NOTES
    Last Update: 05/05/2026 18:11 (GMT+7)
#>

param(
    [Parameter(Mandatory = $true)][string]$QAResultPath,
    [string]$PersonaPath = ""
)

$ErrorActionPreference = "Stop"

# Auto-detect PersonaPath tu blackboard neu chua truyen
if (-not $PersonaPath) {
    $bbPath = Join-Path (Split-Path $QAResultPath -Parent) "00-blackboard.yaml"
    if (Test-Path $bbPath) {
        $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
        if ($bbContent -match 'Persona_Path:\s*"?([^"\r\n]+)"?') {
            $PersonaPath = $Matches[1]
        }
    }
}

if (-not $PersonaPath) {
    throw "Persona_Path khong duoc cung cap va khong the auto-detect tu blackboard."
}

# Derive ScoringRulesPath tu PersonaPath
$ScoringRulesPath = Join-Path $PersonaPath "scoring-rules.yaml"
$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } elseif ($status -eq "FAIL") { $script:failCount++ }
}

# Kiểm tra vật lý: Nếu file 06-qa-result.md không tồn tại thì dừng toàn bộ (exit 1)
if (-not (Test-Path $QAResultPath)) {
    Write-Host "ERROR: QA result not found at $QAResultPath"; exit 1
}
# Đọc toàn bộ nội dung file QA vào biến $qaContent
$qaContent = Get-Content $QAResultPath -Raw -Encoding UTF8

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
                if ($qaContent -match $rx) {
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
# CHECK 1: KIỂM TRA ĐIỂM SÀN (Score Threshold Compliance)
# - Mục đích: Đảm bảo điểm số QA Agent chấm đạt tiêu chuẩn tối thiểu (pass_threshold).
# - Logic: Đọc file rule lấy điểm sàn. Sau đó quét file QA lấy tổng điểm. So sánh 2 số.
# ============================================================
$threshold = -1
# Nếu tìm thấy file luật chấm điểm (scoring-rules.yaml)
if (Test-Path $ScoringRulesPath) {
    # Đọc file luật vào biến
    $scoringContent = Get-Content $ScoringRulesPath -Raw -Encoding UTF8
    # Thực thi quét Regex: Tìm dòng có chữ "pass_threshold: [số]"
    if ($scoringContent -match 'pass_threshold:\s*(\d+)') {
        # Ép kiểu chữ số vừa quét được thành số nguyên (int)
        $threshold = [int]$Matches[1]
    }
}

$scoreExtracted = -1
# Thực thi quét Regex: Tìm tất cả cụm dạng "[Điểm số] / [Điểm tối đa]" trong file QA (VD: 110 / 130)
if ($qaContent -match '(\d+)\s*/\s*(\d+)') {
    $allScoreMatches = [regex]::Matches($qaContent, '(\d+)\s*/\s*(\d+)')
    # Chỉ lấy cụm cuối cùng (Vì tổng điểm thường nằm ở cuối bài, tránh nhầm với điểm thành phần)
    $lastMatch = $allScoreMatches[$allScoreMatches.Count - 1]
    # Ép kiểu điểm số thực đạt thành số nguyên
    $scoreExtracted = [int]$lastMatch.Groups[1].Value
}

# Kiểm tra: Nếu điểm thực tế (scoreExtracted) lớn hơn hoặc bằng điểm sàn (threshold) thì PASS
if ($threshold -gt 0 -and $scoreExtracted -ge 0) {
    if ($scoreExtracted -ge $threshold) {
        Add-Result "Score Threshold" "PASS" "$scoreExtracted >= $threshold (from scoring-rules.yaml)"
    }
    else {
        Add-Result "Score Threshold" "FAIL" "$scoreExtracted < $threshold (from scoring-rules.yaml)"
    }
}
elseif ($threshold -le 0) {
    Add-Result "Score Threshold" "WARN" "Could not read pass_threshold from $ScoringRulesPath"
}
else {
    Add-Result "Score Threshold" "WARN" "Could not extract score from $QAResultPath"
}

# ============================================================
# CHECK 2: KIỂM TRA TÍNH NHẤT QUÁN CỦA PHÁN QUYẾT (Verdict Consistency)
# - Mục đích: Ép chữ VERDICT phải khớp đúng với dải điểm, chống việc AI chấm điểm cao nhưng báo FAIL (hoặc ngược lại).
# ============================================================
$verdict = ""
# Thực thi quét Regex: Tìm cụm "VERDICT: [PASS|REVISE|FAIL]" (không phân biệt hoa thường)
if ($qaContent -match '(?i)VERDICT:\s*(PASS|REVISE|FAIL)') {
    $verdict = $Matches[1].ToUpper()
}

# Nếu có đủ dữ liệu (chữ verdict, điểm số, điểm sàn) để so sánh
if ($verdict -and $scoreExtracted -ge 0 -and $threshold -gt 0) {
    # Tự động tính toán Phán quyết kỳ vọng (expectedVerdict) dựa trên công thức toán học
    # Nếu Điểm >= Điểm sàn -> Kỳ vọng là PASS
    # Nếu Điểm rớt xuống vùng cảnh báo (Điểm sàn - 10) -> Kỳ vọng là REVISE
    # Còn lại (thấp hơn nữa) -> Kỳ vọng là FAIL
    $expectedVerdict = if ($scoreExtracted -ge $threshold) { "PASS" }
    elseif ($scoreExtracted -ge ($threshold - 10)) { "REVISE" }
    else { "FAIL" }
    
    # Kiểm tra: Phán quyết AI ghi ra phải giống y hệt Phán quyết kỳ vọng
    if ($verdict -eq $expectedVerdict) {
        Add-Result "Verdict Consistency" "PASS" "Verdict '$verdict' matches score $scoreExtracted (threshold: $threshold)"
    }
    else {
        Add-Result "Verdict Consistency" "FAIL" "Verdict '$verdict' but score $scoreExtracted expects '$expectedVerdict' (threshold: $threshold)"
    }
}
elseif (-not $verdict) {
    Add-Result "Verdict Consistency" "FAIL" "No VERDICT found in QA result"
}
else {
    Add-Result "Verdict Consistency" "WARN" "Cannot verify (missing score or threshold)"
}

# ============================================================
# CHECK 3: KIỂM TRA ĐỐI CHIẾU ATOM (Atom Attribution Poka-Yoke)
# - Mục đích: Ép QA Agent (Phase 6) phải thực sự check lại từng Atom đã tạo ở Insight Agent (Phase 2).
# - Logic: Đếm số lượng Atom có trong file research (P2) so với số lượng Vault Fact có trong file QA (P6). Bắt buộc phải bằng nhau.
# ============================================================
# Suy luận đường dẫn tới file 02-research-brief.md nằm cùng thư mục
$runFolder = Split-Path $QAResultPath -Parent
$researchPath = Join-Path $runFolder "02-research-brief.md"

if (Test-Path $researchPath) {
    $researchContent = Get-Content $researchPath -Raw -Encoding UTF8
    
    # Bước 1: Quét tất cả thẻ [Atom: ...] (bao gồm cả none)
    $allAtomMatches = [regex]::Matches($researchContent, '\[Atom:\s*[^\]]+\]')
    # Bước 2: Lọc bỏ [Atom: none] (case-insensitive, bắt mọi khoảng trắng thừa)
    $atomMatches = $allAtomMatches | Where-Object { $_.Value -notmatch '(?i)\[Atom:\s*none\s*\]' }
    # Fix A: Normalize path (bỏ "[Atom:" prefix và "]" suffix, trim dấu cách) rồi đếm UNIQUE
    # Cùng atom xuất hiện ở Evidence body lẫn Số liệu citation → chỉ đếm 1 lần
    $atomCount = ($atomMatches | ForEach-Object {
        ($_.Value -replace '^\[Atom:\s*', '' -replace '\]$', '').Trim()
    } | Sort-Object -Unique).Count

    # Thực thi quét Regex: Đếm số lượng cụm "Vault Fact:" xuất hiện trong bài test của QA Agent
    $vaultFactCount = ([regex]::Matches($qaContent, '(?i)Vault Fact\s*:')).Count

    # Kiểm tra: Bắt buộc số lượng Atom gốc (atomCount) phải BẰNG số lượng đã đối chiếu (vaultFactCount)
    if ($atomCount -eq 0) {
        Add-Result "Atom Attribution" "WARN" "Khong tim thay [Atom: ...] trong research brief (khong co atom hoac file trong)"
    }
    elseif ($vaultFactCount -eq $atomCount) {
        Add-Result "Atom Attribution" "PASS" "$vaultFactCount Vault Fact blocks = $atomCount Atom tags"
    }
    else {
        $diff = $atomCount - $vaultFactCount
        Add-Result "Atom Attribution" "FAIL" "Vault Fact blocks: $vaultFactCount / Atom tags: $atomCount - POKA-YOKE VIOLATION (thieu $diff block)"
    }
}
else {
    Add-Result "Atom Attribution" "WARN" "02-research-brief.md not found at $researchPath"
}

# ============================================================
# CHECK 4: KIEM TRA FILE_KEY PERSONA (Proof-of-Read)
# - Muc dich: Ep QA Agent PHAI doc file vat ly voice-dna.yaml va scoring-rules.yaml.
# - Logic: So khop FILE_KEY trong file goc voi key Agent ghi trong 06-qa-result.md.
#   Guard: Key = "PENDING" (chua inject) → FAIL ngay, chong false positive.
# ============================================================
if ($PersonaPath) {
    $voiceDnaPath = Join-Path $PersonaPath "voice-dna.yaml"
    $personaKeyPattern = '(?i)<!--\s*persona_keys:\s*voice-dna=(\w+),\s*scoring-rules=(\w+)\s*-->'

    $qaPersonaMatch = [regex]::Match($qaContent, $personaKeyPattern)

    if (-not $qaPersonaMatch.Success) {
        Add-Result "Persona FILE_KEY" "FAIL" "Khong tim thay <!-- persona_keys: ... --> trong QA result"
    }
    else {
        $qaVoiceKey = $qaPersonaMatch.Groups[1].Value
        $qaScoringKey = $qaPersonaMatch.Groups[2].Value
        $keyErrors = @()

        # So khop voice-dna key
        if (Test-Path $voiceDnaPath) {
            $vdContent = Get-Content $voiceDnaPath -Raw -Encoding UTF8
            if ($vdContent -match '# FILE_KEY:\s*(\w+)') {
                $srcKey = $Matches[1]
                if ($srcKey -eq "PENDING") {
                    $keyErrors += "voice-dna.yaml FILE_KEY chua inject (PENDING)"
                }
                elseif ($srcKey -ne $qaVoiceKey) {
                    $keyErrors += "voice-dna: expected=$srcKey, got=$qaVoiceKey"
                }
            } else { $keyErrors += "voice-dna.yaml missing FILE_KEY" }
        } else { $keyErrors += "voice-dna.yaml not found at $voiceDnaPath" }

        # So khop scoring-rules key
        if (Test-Path $ScoringRulesPath) {
            $srContent = Get-Content $ScoringRulesPath -Raw -Encoding UTF8
            if ($srContent -match '# FILE_KEY:\s*(\w+)') {
                $srcKey = $Matches[1]
                if ($srcKey -eq "PENDING") {
                    $keyErrors += "scoring-rules.yaml FILE_KEY chua inject (PENDING)"
                }
                elseif ($srcKey -ne $qaScoringKey) {
                    $keyErrors += "scoring-rules: expected=$srcKey, got=$qaScoringKey"
                }
            } else { $keyErrors += "scoring-rules.yaml missing FILE_KEY" }
        } else { $keyErrors += "scoring-rules.yaml not found at $ScoringRulesPath" }

        if ($keyErrors.Count -eq 0) {
            Add-Result "Persona FILE_KEY" "PASS" "voice-dna=$qaVoiceKey, scoring-rules=$qaScoringKey"
        }
        else {
            Add-Result "Persona FILE_KEY" "FAIL" ($keyErrors -join "; ")
        }
    }
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  QA VALIDATION REPORT (Phase 6)"
Write-Host "========================================="
# Duyệt qua từng kết quả lưu trong mảng $results để in ra màn hình
foreach ($r in $results) {
    # Gán icon hiển thị dựa trên trạng thái (PASS/WARN/FAIL)
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
