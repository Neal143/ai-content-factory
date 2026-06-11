# Tên file: validate-format.ps1
# Last update: 05/06/2026 11:30 (GMT+7)
# Vai trò: Định dạng tự động bài viết cuối cùng, chèn YAML frontmatter và kiểm định chất lượng tệp 07-final.md.
# Sử dụng khi nào: Được gọi ở Phase 7 bởi format-agent để hoàn tất và lưu trữ bài viết.
# Output: Tạo file 07-final.md, lưu trữ bài đăng vào vault/03-Content/Posted/, ghi nhật ký vào production-log.md và hook-history.md.
# Tóm tắt logic hoạt động:
#   1. Ở chế độ định dạng: Đọc bản thảo thô đạt QA -> Chèn YAML Frontmatter -> Làm sạch các thẻ AI marker -> Xuất bản 07-final.md.
#   2. Lưu bài viết hoàn chỉnh sang vault/03-Content/Posted/ dưới dạng tệp có tiền tố timestamp và slug hóa tiêu đề.
#   3. Ghi chép thông tin bài viết vào production-log.md và lịch sử mở bài vào hook-history.md (sử dụng đường dẫn tương đối đúng).
#   4. Ở chế độ kiểm định: Xác minh cấu trúc tệp 07-final.md, kiểm tra sự chênh lệch từ (Content Integrity < 2%) và các trường YAML bắt buộc.

param(
    [Parameter(Mandatory = $true)][string]$DraftPath,
    [string]$SourceDraftPath = "",
    [string]$RunFolder = "",
    [string]$LogPath = "vault/.content-pipeline/logs/production-log.md",
    [string]$HookHistoryPath = "vault/.content-pipeline/logs/hook-history.md"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrEmpty($RunFolder)) {
    $RunFolder = Split-Path -Parent $DraftPath
}
$RunFolderAbs = [System.IO.Path]::GetFullPath($RunFolder)

$isValidationMode = -not [string]::IsNullOrEmpty($SourceDraftPath)

$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

function Get-Slug($str) {
    if ([string]::IsNullOrWhiteSpace($str)) { return "" }
    $s = $str.ToLower()
    $s = $s.Normalize([System.Text.NormalizationForm]::FormD)
    $sb = New-Object System.Text.StringBuilder
    foreach ($char in $s.ToCharArray()) {
        $uc = [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($char)
        if ($uc -ne [System.Globalization.UnicodeCategory]::NonSpacingMark) {
            $sb.Append($char) | Out-Null
        }
    }
    $s = $sb.ToString().Normalize([System.Text.NormalizationForm]::FormC)
    $d = [char]0x0111
    $s = $s.Replace($d, 'd')
    $s = $s -replace '[^a-z0-9-]', '-'
    $s = $s -replace '-+', '-'
    return $s.Trim('-')
}

# ----------------------------------------------------------------------
# PHAN 1: CHE DO FORMAT
# ----------------------------------------------------------------------
if (-not $isValidationMode) {
    
    $formatPath = "formats/active.json"
    if (-not (Test-Path $formatPath)) { $formatPath = "formats/default.json" }
    $format = Get-Content $formatPath -Raw -Encoding UTF8 | ConvertFrom-Json

    $blackboardPath = Join-Path $RunFolderAbs "00-blackboard.yaml"
    $pillar = "Unknown"; $topic = "Unknown"; $targetAudience = "Unknown"
    if (Test-Path $blackboardPath) {
        $bb = Get-Content $blackboardPath -Raw -Encoding UTF8
        if ($bb -match 'Target_Pillar:\s*(.+)') { $pillar = $Matches[1].Trim().Trim('"').Trim("'") }
        if ($bb -match 'topic:\s*(.+)') { $topic = $Matches[1].Trim().Trim('"').Trim("'") }
        if ($bb -match 'Target_Audience:\s*(.+)') { $targetAudience = $Matches[1].Trim().Trim('"').Trim("'") }
    }
    if ([string]::IsNullOrEmpty($targetAudience)) { $targetAudience = "Unknown" }

    $draftPathAbs = [System.IO.Path]::GetFullPath($DraftPath)
    if (-not (Test-Path $draftPathAbs)) {
        Write-Host "ERROR: Draft file not found at $draftPathAbs"; exit 1
    }
    $draftContent = Get-Content $draftPathAbs -Raw -Encoding UTF8
    
    $title = "Untitled"
    if ($draftContent -match '<!--\s*TITLE:\s*(.*?)\s*-->') { $title = $Matches[1].Trim() }
    
    $asterism = [char]0x2042
    $cleanDraft = $draftContent -replace '<!--[^>]*-->', '' -replace "$asterism", ''
    $wordCount = ($cleanDraft -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

    $qaPath = Join-Path $RunFolderAbs "06-qa-result.md"
    $qaScore = "100/100"
    if (Test-Path $qaPath) {
        $qa = Get-Content $qaPath -Raw -Encoding UTF8
        if ($qa -match '(?i)(?:t.*?ng.*?i.*?m|verdict|total score).*?(\d+\s*/\s*\d+)') {
            $qaScore = $Matches[1] -replace '\s+', ''
        }
        elseif ($qa -match '(?i)score.*?(\d+\s*/\s*\d+)') {
            $qaScore = $Matches[1] -replace '\s+', ''
        }
    }

    $hookPath = Join-Path $RunFolderAbs "03-hook.md"
    $hookFormula = "N/A"
    if (Test-Path $hookPath) {
        $hookContent = Get-Content $hookPath -Raw -Encoding UTF8
        if ($hookContent -match 'F\d+') { $hookFormula = $Matches[0] }
    }

    $skillMdPath = Join-Path $PSScriptRoot "../SKILL.md"
    $execKey = "UNKNOWN"
    if (Test-Path $skillMdPath) {
        $skillRaw = Get-Content $skillMdPath -Raw -Encoding UTF8
        if ($skillRaw -match '(?m)^>\s*EXECUTION_KEY:\s*([a-fA-F0-9]+)') {
            $execKey = $Matches[1].Trim()
        }
    }

    $revisions = (Get-ChildItem -Path $RunFolderAbs -Filter "gate6-issues*" -File -ErrorAction SilentlyContinue).Count

    $global:outputLines = @()
    $global:pendingBlankLines = 0

    function Add-Text($text) {
        if ($null -eq $text -or $text.Trim() -eq "") { return }
        if ($global:outputLines.Count -gt 0) {
            for ($i = 0; $i -lt $global:pendingBlankLines; $i++) {
                $global:outputLines += ""
            }
        }
        $global:outputLines += $text
        $global:pendingBlankLines = 0
    }

    function Add-BlankLines($count) {
        $global:pendingBlankLines += $count
    }

    $lines = $draftContent -split "`r?`n"
    $isFirstSection = $true
    $isFirstParagraph = $true
    # Cờ theo dõi để xác định có 2 khối text (chain) liền kề hay không
    $lastLineWasText = $false

    $runFolderUriFrontmatter = "file:///" + ($RunFolderAbs -replace '\\', '/').Replace(" ", "%20")
    
    $runFolderNameForTime = Split-Path $RunFolderAbs -Leaf
    if ($runFolderNameForTime -match '^(\d{4}-\d{2}-\d{2}_\d{6})') {
        $timestamp = $Matches[1]
        $today = $timestamp.Substring(0, 10)
    } else {
        $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
        $today = Get-Date -Format "yyyy-MM-dd"
    }
    
    Add-Text "---"
    Add-Text "title: ""$title"""
    Add-Text "date: $today"
    Add-Text "pillar: ""$pillar"""
    Add-Text "topic: ""$topic"""
    Add-Text "target_audience: ""$targetAudience"""
    Add-Text "hook_formula: ""$hookFormula"""
    Add-Text "word_count: $wordCount"
    Add-Text "qa_score: $qaScore"
    Add-Text "run_folder: ""$runFolderUriFrontmatter"""
    Add-Text "status: published"
    Add-Text "---"
    Add-BlankLines 1
    Add-Text "[BLOCK: FINAL_POST]"
    Add-BlankLines 1

    if ($null -ne $format.output_elements -and $format.output_elements.title -eq $true) {
        Add-Text "# $title"
        Add-BlankLines 1
    }

    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].TrimEnd()
        
        if ($line -match '^\s*<!--\s*\[BLOCK: DRAFT_SECTIONS\]\s*-->\s*$') { continue }
        if ($line -match '^\s*<!--\s*\[/BLOCK: DRAFT_SECTIONS\]\s*-->\s*$') { continue }
        if ($line -match '^\s*<!--\s*TITLE:') { continue }
        if ($line -match '^\s*<!--\s*ref_keys:') { continue }
        if ($line -match '^\s*<!--\s*bundle_key:') { continue }
        if ($line -match '^\s*<!--\s*execution_key:') { continue }
        if ($line -match "^\s*$asterism\s*$") { continue }

        if ($line -match '^\s*<!--\s*SECTION:\s*(.*?)\s*-->\s*$') {
            if (-not $isFirstSection) {
                if ($null -ne $format.section_separator) {
                    $global:pendingBlankLines = 0
                    Add-BlankLines $format.section_separator.blank_lines_above
                    if ($format.section_separator.marker) { Add-Text $format.section_separator.marker }
                    Add-BlankLines $format.section_separator.blank_lines_below
                }
            }
            $isFirstSection = $false
            $isFirstParagraph = $true
            # Chặn chain_separator can thiệp vào dòng chữ đầu tiên của phần mới
            $lastLineWasText = $false
            continue
        }

        if ($line -match '^\s*<!--\s*SECTION_HEADING:\s*(.*?)\s*-->\s*$') {
            $secHead = $Matches[1]
            if ($null -ne $format.output_elements -and $format.output_elements.section_heading -eq $true) {
                if ($null -ne $format.section_heading_spacing) { Add-BlankLines $format.section_heading_spacing.blank_lines_above }
                Add-Text $secHead
                if ($null -ne $format.section_heading_spacing) { Add-BlankLines $format.section_heading_spacing.blank_lines_below }
            }
            # Chặn chain_separator can thiệp vào dòng chữ kế tiếp của heading
            $lastLineWasText = $false
            continue
        }

        if ($line -match '^\s*<!--\s*PARAGRAPH:\s*(.*?)\s*-->\s*$') {
            if (-not $isFirstParagraph) {
                if ($null -ne $format.paragraph_separator) {
                    $global:pendingBlankLines = 0
                    Add-BlankLines $format.paragraph_separator.blank_lines_above
                    if ($format.paragraph_separator.marker) { Add-Text $format.paragraph_separator.marker }
                    Add-BlankLines $format.paragraph_separator.blank_lines_below
                }
            }
            $isFirstParagraph = $false
            # Chặn chain_separator can thiệp vào dòng chữ đầu tiên của đoạn mới
            $lastLineWasText = $false
            continue
        }

        if ($line -match '^\s*<!--\s*PARAGRAPH_HEADING:\s*(.*?)\s*-->\s*$') {
            $parHead = $Matches[1]
            if ($null -ne $format.output_elements -and $format.output_elements.paragraph_heading -eq $true) {
                if ($null -ne $format.paragraph_heading_spacing) { Add-BlankLines $format.paragraph_heading_spacing.blank_lines_above }
                Add-Text $parHead
                if ($null -ne $format.paragraph_heading_spacing) { Add-BlankLines $format.paragraph_heading_spacing.blank_lines_below }
            }
            # Chặn chain_separator can thiệp vào dòng chữ kế tiếp của heading đoạn
            $lastLineWasText = $false
            continue
        }

        # Nhóm code 1: Xử lý khoảng trắng nguyên bản từ bản nháp
        # Giữ lại khoảng trắng gốc và đóng khóa chặn chain_separator
        if ($line -eq "") { 
            Add-BlankLines 1
            $lastLineWasText = $false
            continue
        }

        # Nhóm code 2: Áp dụng chain_separator khi có 2 khối text liền kề
        if ($lastLineWasText) {
            $cSep = $format.chain_separator
            # Dọn sạch hàng chờ để chuẩn bị nạp thông số chính xác từ cấu hình
            $global:pendingBlankLines = 0
            if ($null -ne $cSep) {
                if ($null -ne $cSep.blank_lines_above -and $cSep.blank_lines_above -gt 0) { Add-BlankLines $cSep.blank_lines_above }
                if ([string]::IsNullOrEmpty($cSep.marker) -eq $false) { Add-Text $cSep.marker }
                if ($null -ne $cSep.blank_lines_below -and $cSep.blank_lines_below -gt 0) { Add-BlankLines $cSep.blank_lines_below }
            } else {
                # Fallback an toàn nếu cấu hình bị lỗi/thiếu
                Add-BlankLines 1
            }
        }

        # Nhóm code 3: In nội dung văn bản ra tệp và mở khóa theo dõi
        $line = $line -replace '\s*<!--\s*PUNCHLINE\s*-->', ''
        Add-Text $line
        $lastLineWasText = $true
    }

    Add-BlankLines 1
    Add-Text "[/BLOCK: FINAL_POST]"
    Add-BlankLines 1
    Add-Text "<!-- execution_key: $execKey -->"

    $finalContent = $global:outputLines -join "`r`n"
    $finalPath = Join-Path $RunFolderAbs "07-final.md"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($finalPath, $finalContent, $utf8NoBom)

    $postsDir = [System.IO.Path]::GetFullPath("vault/03-Content/Posted")
    if (-not (Test-Path $postsDir)) {
        New-Item -ItemType Directory -Path $postsDir -Force | Out-Null
    }

    # Đã lấy $today và $timestamp đồng bộ từ RunFolder ở trên
    $titleSlug = Get-Slug $title
    $postPath = Join-Path $postsDir "${timestamp}-${titleSlug}.md"
    
    $postContent = $finalContent -replace '(?m)^\[BLOCK: FINAL_POST\]\r?\n?', '' `
        -replace '(?m)^\[/BLOCK: FINAL_POST\]\r?\n?', '' `
        -replace '(?m)^<!-- execution_key:.*?-->\r?\n?', ''
    
    $postContent = $postContent.Trim() + "`r`n"
    [System.IO.File]::WriteAllText($postPath, $postContent, $utf8NoBom)

    Write-Host " [i] Cap nhat production-log.md..." -ForegroundColor Cyan
    $logPathAbs = [System.IO.Path]::GetFullPath($LogPath)
    
    $usedAtomsStr = "none"
    $comboPath = Join-Path $RunFolderAbs "00.5-dikw-combo.md"
    if (Test-Path $comboPath) {
        $comboContent = Get-Content $comboPath -Raw -Encoding UTF8
        $atomMatches = [regex]::Matches($comboContent, '(?m)^### ATOM:\s*(vault/[\w\-\/\s]+\.md)')
        $atomsList = @()
        foreach ($m in $atomMatches) {
            $atomsList += $m.Groups[1].Value.Trim()
        }
        if ($atomsList.Count -gt 0) {
            $atomsList = $atomsList | Select-Object -Unique
            $usedAtomsStr = $atomsList -join ", "
        }
    }

    $logEntry = @"

## [$timestamp] - $title
- **Pillar**: $pillar
- **Topic**: "$topic"
- **Target_Audience**: $targetAudience
- **Hook Formula**: $hookFormula
- **QA Score**: $qaScore
- **Atoms Used**: $usedAtomsStr
- **Revisions**: $revisions
- **Status**: published
"@

    $logHeaderCheck = "## [$timestamp] - $title"
    if (Test-Path $logPathAbs) {
        $existingLog = Get-Content $logPathAbs -Raw -Encoding UTF8
        if ($existingLog -match [regex]::Escape($logHeaderCheck)) {
            Write-Host " [i] Ban ghi nhat ky cho bai viet nay da ton tai trong phien nay. Bo qua ghi trung lap." -ForegroundColor Yellow
        }
        else {
            [System.IO.File]::AppendAllText($logPathAbs, $logEntry, $utf8NoBom)
        }
    }
    else {
        $dir = Split-Path $logPathAbs
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        [System.IO.File]::WriteAllText($logPathAbs, "# Production Log`r`n$logEntry", $utf8NoBom)
    }

    Write-Host " [i] Cap nhat hook-history.md..." -ForegroundColor Cyan
    $hookHistoryPathAbs = [System.IO.Path]::GetFullPath($HookHistoryPath)
    $hookScore = "N/A"
    if ($qa -match '(?m)CT-01.*?\b(\d+)/10') {
        $hookScore = $Matches[1]
    }
    elseif ($qaScore -match '(\d+)/') {
        $num = [math]::Round([int]$Matches[1] / 13, 0)
        if ($num -gt 10) { $num = 10 }
        $hookScore = "$num"
    }
    $hookScoreStr = if ($hookScore -eq "N/A") { "N/A" } else { "${hookScore}/10" }
    
    $postFilename = "${timestamp}-${titleSlug}.md"
    $hookEntry = "`r`n| $timestamp | $topic | [$postFilename](../../03-Content/Posted/$postFilename) | $hookFormula | $hookScoreStr |"
    
    $hookLineCheck = "| $timestamp | $topic |"
    if (Test-Path $hookHistoryPathAbs) {
        $existingHook = Get-Content $hookHistoryPathAbs -Raw -Encoding UTF8
        if ($existingHook -match [regex]::Escape($hookLineCheck)) {
            Write-Host " [i] Lich su hook cho chu de nay da ton tai trong phien. Bo qua ghi trung lap." -ForegroundColor Yellow
        }
        else {
            [System.IO.File]::AppendAllText($hookHistoryPathAbs, $hookEntry, $utf8NoBom)
        }
    }
    else {
        $dir = Split-Path $hookHistoryPathAbs
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $header = @"
# Lich Su Hieu Suat Hook (Gate 3)

| Ngay Xuat Ban | Topic / Chu De | Post Filename | Hook Formula | Diem so Gate 6 |
|---|---|---|---|---|
"@
        [System.IO.File]::WriteAllText($hookHistoryPathAbs, "$header$hookEntry", $utf8NoBom)
    }

    # Ghi log Idea History (Idea Curator sẽ đọc)
    Write-Host " [i] Cap nhat idea-history.md..." -ForegroundColor Cyan
    $ideaHistoryPathAbs = [System.IO.Path]::GetFullPath("vault/.content-pipeline/logs/idea-history.md")
    $ideaBriefPath = Join-Path $RunFolderAbs "01-idea-brief.md"
    
    if (Test-Path $ideaBriefPath) {
        $ideaBriefContent = Get-Content $ideaBriefPath -Raw -Encoding UTF8
        
        $extAngle = if ($ideaBriefContent -match '(?s)\[BLOCK:\s*CONTRARIAN_ANGLE\s*\](.*?)\[/BLOCK:\s*CONTRARIAN_ANGLE\s*\]') { $Matches[1].Trim() -replace '\s+', ' ' } else { "N/A" }
        $extTension = if ($ideaBriefContent -match '(?s)\[BLOCK:\s*CORE_TENSION\s*\](.*?)\[/BLOCK:\s*CORE_TENSION\s*\]') { $Matches[1].Trim() -replace '\s+', ' ' } else { "N/A" }
        $extBelief = if ($ideaBriefContent -match '(?s)\[BLOCK:\s*HIDDEN_BELIEF\s*\](.*?)\[/BLOCK:\s*HIDDEN_BELIEF\s*\]') { $Matches[1].Trim() -replace '\s+', ' ' } else { "N/A" }
        $extPromise = if ($ideaBriefContent -match '(?s)\[BLOCK:\s*TRANSFORMATION_PROMISE\s*\](.*?)\[/BLOCK:\s*TRANSFORMATION_PROMISE\s*\]') { $Matches[1].Trim() -replace '\s+', ' ' } else { "N/A" }

        # Tạo đường dẫn tương đối phục vụ truy xuất link
        $runFolderName = Split-Path $RunFolderAbs -Leaf
        $ideaBriefLink = "../runs/$runFolderName/01-idea-brief.md"
        $postLink = "../../../$postFilename"

        $ideaEntry = @"

## [$timestamp] - [$title]($postLink)
- **Idea Brief**: [01-idea-brief.md]($ideaBriefLink)
- **Pillar**: $pillar
- **Topic**: "$topic"
- **Contrarian Angle**: $extAngle
- **Core Tension**: $extTension
- **Hidden Belief**: $extBelief
- **Transformation Promise**: $extPromise
"@
        
        $ideaHeaderCheck = "## [$timestamp] - \["
        if (Test-Path $ideaHistoryPathAbs) {
            $existingIdeaLog = Get-Content $ideaHistoryPathAbs -Raw -Encoding UTF8
            if ($existingIdeaLog -notmatch [regex]::Escape("[$timestamp]")) {
                [System.IO.File]::AppendAllText($ideaHistoryPathAbs, $ideaEntry, $utf8NoBom)
            }
        } else {
            $dir = Split-Path $ideaHistoryPathAbs
            if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            [System.IO.File]::WriteAllText($ideaHistoryPathAbs, "# Idea History Log`r`n$ideaEntry", $utf8NoBom)
        }
    }
}

# ----------------------------------------------------------------------
# PHAN 2: CHE DO KIEM DINH (VALIDATION)
# ----------------------------------------------------------------------
if ($isValidationMode) {
    $fileToValidate = $DraftPath
    $sourceFileToCompare = $SourceDraftPath
}
else {
    $fileToValidate = Join-Path $RunFolderAbs "07-final.md"
    $sourceFileToCompare = $DraftPath
}

$fileToValidateAbs = [System.IO.Path]::GetFullPath($fileToValidate)
if (-not (Test-Path $fileToValidateAbs)) {
    Write-Host "ERROR: File to validate not found at $fileToValidateAbs"; exit 1
}
$draft = Get-Content $fileToValidateAbs -Raw -Encoding UTF8

$skillMdPath = Join-Path $PSScriptRoot "../SKILL.md"
if (Test-Path $skillMdPath) {
    $skillRaw = Get-Content $skillMdPath -Raw -Encoding UTF8
    if ($skillRaw -match "(?s)^---`r?`n(.*?)`r?`n---") {
        $fm = $Matches[1]
        if ($fm -match "(?s)provided_outputs:`r?`n(.*?)(?:`r?`n\S|\Z)") {
            $poBlock = $Matches[1]
            $outputs = [regex]::Matches($poBlock, '-\s*(\S+)') | ForEach-Object { $_.Groups[1].Value }
            foreach ($blk in $outputs) {
                $rx = "(?s)\[BLOCK:\s*$blk\s*\](.*?)\[/BLOCK:\s*$blk\s*\]"
                if ($draft -match $rx) {
                    if ($Matches[1].Trim().Length -gt 0) {
                        Add-Result "Block [$blk]" "PASS" "OK"
                    }
                    else {
                        Add-Result "Block [$blk]" "FAIL" "Empty"
                    }
                }
                else {
                    Add-Result "Block [$blk]" "FAIL" "Missing tag"
                }
            }
        }
    }
}
else {
    Add-Result "Block Check" "WARN" "SKILL.md not found"
}

$logPathAbs = [System.IO.Path]::GetFullPath($LogPath)
if (Test-Path $logPathAbs) {
    $logContent = Get-Content $logPathAbs -Raw -Encoding UTF8
    $today = Get-Date -Format "yyyy-MM-dd"
    if ($logContent -match $today) {
        Add-Result "Production Log" "PASS" "Updated for today"
    }
    else {
        Add-Result "Production Log" "FAIL" "Missing today's entry"
    }
}
else {
    Add-Result "Production Log" "FAIL" "File not found"
}

$hookHistoryPathAbs = [System.IO.Path]::GetFullPath($HookHistoryPath)
if (Test-Path $hookHistoryPathAbs) {
    $hookContent = Get-Content $hookHistoryPathAbs -Raw -Encoding UTF8
    $today = Get-Date -Format "yyyy-MM-dd"
    if ($hookContent.Length -gt 20 -and $hookContent -match $today) {
        Add-Result "Hook History" "PASS" "Updated for today"
    }
    else {
        Add-Result "Hook History" "FAIL" "Missing today's entry"
    }
}
else {
    Add-Result "Hook History" "FAIL" "File not found"
}

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
    Add-Result "YAML Frontmatter" "PASS" "All required fields present"
}
elseif ($hasFrontmatter) {
    Add-Result "YAML Frontmatter" "FAIL" "Missing fields: $($missingKeys -join ', ')"
}
else {
    Add-Result "YAML Frontmatter" "FAIL" "Missing YAML block"
}

if ($hasFrontmatter) {
    if ($draft -match '(?s)^---.*?---\r?\n\r?\n') {
        Add-Result "YAML Spacing" "PASS" "Valid blank line after frontmatter"
    }
    else {
        Add-Result "YAML Spacing" "FAIL" "Missing blank line after frontmatter"
    }
}

$asterism = [char]0x2042
$sourceFileToCompareAbs = [System.IO.Path]::GetFullPath($sourceFileToCompare)
if ($sourceFileToCompareAbs -and (Test-Path $sourceFileToCompareAbs)) {
    $sourceContent = Get-Content $sourceFileToCompareAbs -Raw -Encoding UTF8
    $sourceClean = $sourceContent -replace '<!--[^>]*-->', '' -replace "$asterism", ''
    $sourceWords = ($sourceClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

    $finalBody = $draft -replace '(?s)^---.*?---\s*', ''
    $finalClean = $finalBody -replace '<!--[^>]*-->', ''
    $finalWords = ($finalClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

    if ($sourceWords -gt 0) {
        $delta = [math]::Abs($sourceWords - $finalWords)
        $deltaPercent = [math]::Round(($delta / $sourceWords) * 100, 1)
        if ($deltaPercent -le 2) {
            Add-Result "Content Integrity" "PASS" "Deviation $deltaPercent% - Within safe threshold"
        }
        else {
            Add-Result "Content Integrity" "FAIL" "Deviation $deltaPercent% - Exceeds 2% threshold"
        }
    }
    else {
        Add-Result "Content Integrity" "WARN" "Source file empty"
    }
}
elseif ($sourceFileToCompareAbs) {
    Add-Result "Content Integrity" "FAIL" "Source file not found"
}

Write-Host ""
Write-Host "========================================="
Write-Host "  VALIDATION REPORT (Phase 7)"
Write-Host "========================================="
foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Result: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
