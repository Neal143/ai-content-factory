# Tên file: detect-bypass.ps1
# Last update: 05/06/2026 11:30 (GMT+7)
# Vai trò: Phát hiện hành vi bypass của LLM trong pipeline content-post.
# Sử dụng khi nào: Được gọi bởi content-post.md sau khi mỗi Phase ghi xong output.
# Output: Exit 0 = PASS | Exit 1 = HALT | Exit 2 = RETRY, cập nhật sentinel-checklist.md và sentinel-data.json.
# Tóm tắt logic hoạt động:
#   1. Check 0 (Prerequisite Chain): Kiểm tra sự hiện diện và tính hợp lệ của output từ các Phase trước để chặn nhảy cóc.
#   2. Check 1 (Script Scanner): Kiểm tra file cấm tạo lén trong thư mục output/ và thư mục gốc.
#   3. Check 2 (Vault Guard): Phát hiện file rác ghi trực tiếp vào root của vault/.content-pipeline/ (chỉ cho phép ghi vào thư mục con).
#   4. Check 3 (QA Forgery): Chặn việc điền khống điểm QA mà chưa thực hiện Phase 6.
#   5. Check 4 (Execution Key): Đối chiếu mã khóa execution_key giữa SKILL.md và output để đảm bảo Agent thực sự đọc SKILL.md.
#   6. Check 4BC (DIKW Poka-yoke): Kiểm tra bundle_key khớp với combo atom đã chọn.
#   7. Check 5 (Quality Validate): Chạy lại script kiểm định chất lượng nội dung tương ứng của Phase vừa hoàn tất.
<#
.SYNOPSIS
    Anti-Bypass Sentinel
.PARAMETER RunFolder
    Duong dan run folder hien tai (vd: vault/.content-pipeline/runs/2026-04-28_topic-slug/)
.PARAMETER Phase
    Phase vua hoan thanh (0-7, 45)
#>

param(
    [Parameter(Mandatory = $true)][string]$RunFolder,
    [Parameter(Mandatory = $true)][int]$Phase
)

$bypassFailed = $false
$qualityFailed = $false
$checkResults = @{}

# [Nhóm code: Khởi tạo lưu trữ lỗi]
# Sử dụng $script scope để giới hạn rủi ro tràn RAM hoặc xung đột nếu chạy đa luồng.
$script:errorLogs = @()

# [Nhóm code: Hàm ghi nhận lỗi]
function Log-Error([string]$CheckCode, [string]$Msg) {
    Write-Host "[FAIL] BYPASS DETECTED [$CheckCode]: $Msg"
    $script:errorLogs += @{
        timestamp = (Get-Date).ToUniversalTime().AddHours(7).ToString("HH:mm:ss")
        phase     = $Phase
        check     = $CheckCode
        message   = $Msg
    }
}

# ============================================================
# CHECK 0 - Prerequisite Chain Validation
# Ly do: Agent nhay coc Phase -> cac Phase sau khong phat hien.
# Kiem tra: Tat ca output file cua cac Phase truoc phai ton tai VA khong rong.
# ============================================================
$phaseOrder = @(0, 1, 2, 3, 4, 45, 5, 6, 7)
$phaseOutputMap = @{
    0  = "00-blackboard.yaml"
    1  = "01-idea-brief.md"
    2  = "02-research-brief.md"
    3  = "03-hook.md"
    4  = "04-outline.md"
    45 = "04.5-persona-pack.md"
    5  = "05-draft.md"
    6  = "06-qa-result.md"
    7  = "07-final.md"
}

if ($Phase -ne 0) {
    $currentIndex = [array]::IndexOf($phaseOrder, $Phase)
    $missingPrereqs = @()

    for ($i = 0; $i -lt $currentIndex; $i++) {
        $prereqPhase = $phaseOrder[$i]
        $prereqFile = Join-Path $RunFolder $phaseOutputMap[$prereqPhase]

        if (-not (Test-Path $prereqFile)) {
            $missingPrereqs += "Phase $prereqPhase ($($phaseOutputMap[$prereqPhase]) - KHONG TON TAI)"
        }
        elseif ((Get-Item $prereqFile).Length -eq 0) {
            $missingPrereqs += "Phase $prereqPhase ($($phaseOutputMap[$prereqPhase]) - FILE RONG)"
        }
    }

    if ($missingPrereqs.Count -gt 0) {
        $checkResults["C0"] = "FAIL"
        $errDetail = $missingPrereqs -join "; "
        Log-Error "C0" "Agent nhay coc - thieu output cua cac Phase truoc: $errDetail"
        foreach ($m in $missingPrereqs) { Write-Host "  - $m" }
        $bypassFailed = $true
    }
    else {
        $checkResults["C0"] = "PASS"
        Write-Host "[PASS] CHECK 0: Prerequisite chain verified."
    }
}
else {
    $checkResults["C0"] = "SKIP"
}

# ============================================================
# CHECK 1 - Script rac trong output/ root VA workspace root
# ============================================================
$forbiddenExtensions = @("*.py", "*.js", "*.sh")
$scanPaths = @("output", ".")
$forbidden = @()
foreach ($scanPath in $scanPaths) {
    if (Test-Path $scanPath) {
        $forbidden += Get-ChildItem -Path "$scanPath\*" -Include $forbiddenExtensions -File -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -eq (Resolve-Path $scanPath).Path }
    }
}
if ($forbidden.Count -gt 0) {
    Log-Error "C1" "Script bi cam: $($forbidden.FullName -join ', ')"
    $bypassFailed = $true
    $checkResults["C1"] = "FAIL"
}
else {
    $checkResults["C1"] = "PASS"
}

# ============================================================
# CHECK 2 - File rac ghi truc tiep vao vault/.content-pipeline/ root (chi cho phep sub-folder)
# ============================================================
$pipelineRoot = "vault/.content-pipeline"
$rootFiles = @()
if (Test-Path $pipelineRoot) {
    $rootFiles = Get-ChildItem -Path "$pipelineRoot\*" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.DirectoryName -eq (Resolve-Path $pipelineRoot).Path }
}
if ($rootFiles.Count -gt 0) {
    Log-Error "C2" "File bi ghi vao root vault/.content-pipeline/: $($rootFiles.Name -join ', ')"
    $bypassFailed = $true
    $checkResults["C2"] = "FAIL"
}
else {
    $checkResults["C2"] = "PASS"
}

# ============================================================
# CHECK 3 - qa_score hardcode ma 06-qa-result.md chua ton tai
# ============================================================
if ($Phase -ge 6) {
    $draftPath = Join-Path $RunFolder "05-draft.md"
    if (Test-Path $draftPath) {
        $content = Get-Content $draftPath -Raw -Encoding UTF8
        $hasScore = $content -match 'qa_score:\s*\d+'
        $hasQAFile = Test-Path (Join-Path $RunFolder "06-qa-result.md")
        if ($hasScore -and -not $hasQAFile) {
            Log-Error "C3" "qa_score hardcode trong 05-draft.md nhung 06-qa-result.md chua ton tai."
            $bypassFailed = $true
            $checkResults["C3"] = "FAIL"
        }
        else {
            $checkResults["C3"] = "PASS"
        }
    }
    else {
        $checkResults["C3"] = "SKIP"
    }
}
else {
    $checkResults["C3"] = "SKIP"
}

# ============================================================
# CHECK 4 - Execution Key Verification
# ============================================================
$skillPaths = @{
    0  = ".agents/skills/semantic-router/SKILL.md"
    1  = ".agents/skills/idea-curator/SKILL.md"
    2  = ".agents/skills/insight-agent/SKILL.md"
    3  = ".agents/skills/hook-engineer/SKILL.md"
    4  = ".agents/skills/structure-designer/SKILL.md"
    5  = ".agents/skills/voice-writer/SKILL.md"
    6  = ".agents/skills/qa-checker/SKILL.md"
    7  = ".agents/skills/format-agent/SKILL.md"
    45 = ".agents/skills/persona-loader/SKILL.md"
}

if ($skillPaths.ContainsKey($Phase)) {
    $skillFile = $skillPaths[$Phase]
    $outputFile = Join-Path $RunFolder $phaseOutputMap[$Phase]

    $expectedKey = ""
    if (Test-Path $skillFile) {
        $skillContent = Get-Content $skillFile -Raw -Encoding UTF8
        if ($skillContent -match '> EXECUTION_KEY:\s*(\S+)') { $expectedKey = $Matches[1] }
    }

    $actualKey = ""
    if (Test-Path $outputFile) {
        $outputContent = Get-Content $outputFile -Raw -Encoding UTF8
        if ($outputContent -match '(?:<!--|#)\s*execution_key:\s*(\S+)(?:\s*-->)?') { $actualKey = $Matches[1] }
    }

    if ($expectedKey -eq "" -or $expectedKey -eq "PENDING" -or $expectedKey -eq "__PENDING__") {
        Log-Error "C4" "SKILL.md thieu execution_key. Chay generate-phase-key.ps1 truoc."
        $bypassFailed = $true
        $checkResults["C4"] = "FAIL"
    }
    elseif ($actualKey -eq "") {
        Log-Error "C4" "Output thieu execution_key."
        $bypassFailed = $true
        $checkResults["C4"] = "FAIL"
    }
    elseif ($expectedKey -ne $actualKey) {
        Log-Error "C4" "Key khong khop. Expected: $expectedKey | Actual: $actualKey"
        $bypassFailed = $true
        $checkResults["C4"] = "FAIL"
    }
    else {
        Write-Host "[PASS] CHECK 4: Execution key verified."
        $checkResults["C4"] = "PASS"
    }
}
else {
    $checkResults["C4"] = "SKIP"
}

# ============================================================
# CHECK 4B & 4C - DIKW POKA-YOKE
# ============================================================
$blackboard = Join-Path $RunFolder "00-blackboard.yaml"
$isNovel = $false
if (Test-Path $blackboard) {
    $bbContent = Get-Content $blackboard -Raw -Encoding UTF8
    if ($bbContent -match 'Is_Novel_Angle:\s*true') { $isNovel = $true }
}

if (-not $isNovel -and $Phase -ge 1) {
    $dikwFile = Join-Path $RunFolder "00.5-dikw-combo.md"
    
    if (-not (Test-Path $dikwFile)) {
        Log-Error "C4BC" "DikwBridgeAgent chua tao file (00.5-dikw-combo.md)."
        $bypassFailed = $true
        $checkResults["C4BC"] = "FAIL"
    }
    else {
        $dikwContent = Get-Content $dikwFile -Raw -Encoding UTF8
        
        $hasKey = $dikwContent -match '<!-- BUNDLE_KEY:\s*([A-Za-z0-9]+)\s*-->'
        if (-not $hasKey) {
            Log-Error "C4BC" "DikwBridgeAgent chua chay script hoac thieu BUNDLE_KEY."
            $bypassFailed = $true
            $checkResults["C4BC"] = "FAIL"
        }
        else {
            $expectedKey = $Matches[1]
            
            if ($Phase -ge 1 -and $Phase -le 5) {
                $outputPath = Join-Path $RunFolder $phaseOutputMap[$Phase]
                
                if (-not (Test-Path $outputPath)) {
                    Log-Error "C4BC" "Thieu file output cua Phase $Phase."
                    $bypassFailed = $true
                    $checkResults["C4BC"] = "FAIL"
                }
                else {
                    $outContent = Get-Content $outputPath -Raw -Encoding UTF8
                    if ($outContent -notmatch "<!-- bundle_key:\s*\[?$expectedKey\]?\s*-->") {
                        Log-Error "C4BC" "Agent chua doc file Combo hoac dien sai BUNDLE_KEY."
                        $bypassFailed = $true
                        $checkResults["C4BC"] = "FAIL"
                    }
                    else {
                        $checkResults["C4BC"] = "PASS"
                    }
                }
            }
            else {
                $checkResults["C4BC"] = "PASS"
            }
        }
    }
}
else {
    $checkResults["C4BC"] = "SKIP"
}

# ============================================================
# CHECK 5 - Re-run validation script
# ============================================================
$validationScripts = @{
    1  = @{ Script = ".agents/skills/idea-curator/scripts/validate-idea.ps1"; Param = "IdeaPath"; File = "01-idea-brief.md" }
    2  = @{ Script = ".agents/skills/insight-agent/scripts/validate-research.ps1"; Param = "ResearchPath"; File = "02-research-brief.md" }
    3  = @{ Script = ".agents/skills/hook-engineer/scripts/validate-hook.ps1"; Param = "HookPath"; File = "03-hook.md" }
    4  = @{ Script = ".agents/skills/structure-designer/scripts/validate-outline.ps1"; Param = "OutlinePath"; File = "04-outline.md" }
    5  = @{ Script = ".agents/skills/voice-writer/scripts/validate-draft.ps1"; Param = "DraftPath"; File = "05-draft.md" }
    6  = @{ Script = ".agents/skills/qa-checker/scripts/validate-qa.ps1"; Param = "QAResultPath"; File = "06-qa-result.md" }
    7  = @{ Script = ".agents/skills/format-agent/scripts/validate-format.ps1"; Param = "DraftPath"; File = "07-final.md" }
    45 = @{ Script = ".agents/skills/persona-loader/scripts/validate-persona-pack.ps1"; Param = "PackPath"; File = "04.5-persona-pack.md" }
}

if ($validationScripts.ContainsKey($Phase)) {
    $vs = $validationScripts[$Phase]
    $targetFile = Join-Path $RunFolder $vs.File

    if (Test-Path $vs.Script) {
        $paramName = $vs.Param
        $argList = @("-ExecutionPolicy", "Bypass", "-File", $vs.Script, "-$paramName", $targetFile)
        if ($Phase -eq 7) {
            $argList += @("-SourceDraftPath", (Join-Path $RunFolder "05-draft.md"))
        }
        if ($Phase -eq 45) {
            $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
            $personaPath = ""
            if (Test-Path $bbPath) {
                $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
                if ($bbContent -match 'Persona_Path:\s*"?([^"\r\n]+)"?') { $personaPath = $Matches[1].Trim() }
            }
            $argList += @("-PersonaPath", $personaPath)
        }

        $proc = Start-Process powershell -ArgumentList $argList -Wait -PassThru -NoNewWindow
        $rerunExit = $proc.ExitCode

        if ($rerunExit -eq 0) {
            Write-Host "[PASS] CHECK 5: Re-run validation PASS for Phase $Phase"
            $checkResults["C5"] = "PASS"
        }
        else {
            Log-Error "C5" "Re-run validation FAIL for Phase $Phase."
            $qualityFailed = $true
            $checkResults["C5"] = "FAIL"
        }
    }
    else {
        Write-Host "[WARN] CHECK 5: Validation script not found: $($vs.Script)"
        $checkResults["C5"] = "SKIP"
    }
}
elseif ($Phase -eq 0) {
    # CHECK 5B - Phase 0 inline validation
    $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
    if (-not (Test-Path $bbPath)) {
        Log-Error "C5" "00-blackboard.yaml khong ton tai."
        $qualityFailed = $true
        $checkResults["C5"] = "FAIL"
    }
    else {
        $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
        $requiredFields = @("topic", "Target_Pillar", "Is_Novel_Angle", "Persona_Path")
        $missingFields = @()
        foreach ($field in $requiredFields) {
            $fieldMatch = [regex]::Match($bbContent, "(?m)^$field\s*:\s*(.*)$")
            $isEmpty = $true
            if ($fieldMatch.Success) {
                $rawVal = $fieldMatch.Groups[1].Value.Trim().Trim('"').Trim("'").Trim()
                $isEmpty = ($rawVal.Length -eq 0)
            }
            if ($isEmpty) { $missingFields += $field }
        }
        if ($missingFields.Count -gt 0) {
            $missing = $missingFields -join ", "
            Log-Error "C5" "Blackboard thieu/rong: $missing"
            $qualityFailed = $true
            $checkResults["C5"] = "FAIL"
        }
        else {
            Write-Host "[PASS] CHECK 5: Blackboard fields validated."
            $checkResults["C5"] = "PASS"
        }

        $topicMatch = [regex]::Match($bbContent, '(?m)^topic:\s*"?([^"\r\n]+)"?')
        if ($topicMatch.Success) {
            $topicVal = $topicMatch.Groups[1].Value.Trim()
            $wordCount = ($topicVal -split '_').Count
            if ($topicVal -notmatch '^[a-z][a-z0-9_]{2,40}$' -or $wordCount -gt 4) {
                Log-Error "C5" "topic '$topicVal' sai format."
                $qualityFailed = $true
                $checkResults["C5"] = "FAIL"
            }
        }

        $ppMatch = [regex]::Match($bbContent, '(?m)^Persona_Path:\s*"?([^"\r\n]+)"?')
        if ($ppMatch.Success) {
            $ppVal = $ppMatch.Groups[1].Value.Trim()
            if ($ppVal -match '\\\\') {
                Log-Error "C5" "Persona_Path chua escaped backslash."
                $qualityFailed = $true
                $checkResults["C5"] = "FAIL"
            }
        }
    }
}
else {
    $checkResults["C5"] = "SKIP"
}

# ============================================================
# UPDATE SENTINEL CHECKLIST
# ============================================================
function Update-SentinelChecklist {
    param(
        [string]$RunFolder,
        [int]$Phase,
        [string]$Status,
        [hashtable]$CheckResults
    )

    $phaseMeta = [ordered]@{
        "0"  = @{ Name = "Semantic Router"; Output = "00-blackboard.yaml" }
        "1"  = @{ Name = "Idea Curator"; Output = "01-idea-brief.md" }
        "2"  = @{ Name = "Insight Agent"; Output = "02-research-brief.md" }
        "3"  = @{ Name = "Hook Engineer"; Output = "03-hook.md" }
        "4"  = @{ Name = "Structure Designer"; Output = "04-outline.md" }
        "45" = @{ Name = "Persona Loader"; Output = "04.5-persona-pack.md" }
        "5"  = @{ Name = "Voice Writer"; Output = "05-draft.md" }
        "6"  = @{ Name = "QA Checker"; Output = "06-qa-result.md" }
        "7"  = @{ Name = "Format Agent"; Output = "07-final.md" }
    }

    $tempFolder = Join-Path $RunFolder ".temp"
    if (-not (Test-Path $tempFolder)) { New-Item -ItemType Directory -Path $tempFolder -Force | Out-Null }
    $dataPath = Join-Path $tempFolder "sentinel-data.json"

    $data = @{}
    if (Test-Path $dataPath) {
        # [Nhóm code: Try-Catch I/O] Chống sập Sentinel nếu file json bị hỏng do cắt điện/crash
        try {
            $raw = Get-Content $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($raw) { foreach ($prop in $raw.PSObject.Properties) { $data[$prop.Name] = $prop.Value } }
        }
        catch {
            Write-Host "[WARN] Lỗi đọc sentinel-data.json, hệ thống sẽ tự khởi tạo lại cấu trúc."
        }
    }

    $timestamp = (Get-Date).ToUniversalTime().AddHours(7).ToString("HH:mm")
    $checksStr = ($CheckResults.GetEnumerator() | Sort-Object Name | ForEach-Object {
            $icon = switch ($_.Value) { "PASS" { [char]0x2705 } "FAIL" { [char]0x274C } default { [char]0x23ED } }
            "$($_.Key)$icon"
        }) -join " "

    # [Nhóm code: Bảo tồn lỗi theo Phase an toàn]
    $existingErrors = @()
    if ($data.ContainsKey("$Phase")) {
        $errs = $data["$Phase"].errors
        if ($null -ne $errs) { foreach ($e in @($errs)) { $existingErrors += $e } }
    }
    $mergedErrors = @()
    foreach ($e in $existingErrors) { $mergedErrors += $e }
    foreach ($e in $script:errorLogs) { $mergedErrors += $e }

    $data["$Phase"] = @{
        status    = $Status
        timestamp = $timestamp
        checks    = $checksStr
        errors    = $mergedErrors
    }

    # [Nhóm code: Vá lỗi Serialization của PowerShell]
    $data | ConvertTo-Json -Depth 5 | Set-Content $dataPath -Encoding UTF8

    $runName = Split-Path $RunFolder -Leaf
    $now = (Get-Date).ToUniversalTime().AddHours(7).ToString("dd/MM/yyyy HH:mm")
    $md = @()
    $md += "# Sentinel Execution Checklist"
    $md += ""
    $md += "> Auto-generated by ``detect-bypass.ps1``. KHÔNG chỉnh sửa thủ công."
    $md += "> Run: ``$runName``"
    $md += "> Cập nhật: $now (GMT+7)"
    $md += ""
    $md += "### Ghi chú ký hiệu (Legend)"
    $md += "**1. Trạng thái Phase:**"
    $md += "- **[PASS]** : Hoàn thành hợp lệ, không phát hiện vi phạm."
    $md += "- **[HALT]** : Dừng hệ thống lập tức do phát hiện vi phạm luật cố ý (Bypass)."
    $md += "- **[RETRY]**: Sai định dạng đầu ra (Quality Fail), hệ thống đang tự động sửa lỗi (tối đa 3 lần)."
    $md += ""
    $md += "**2. Kết quả kiểm tra (Checks):**"
    $md += "✅ Đạt | ❌ Vi phạm | ⏭️ Bỏ qua (Không áp dụng ở Phase này)"
    $md += ""
    $md += "**3. Mã kiểm tra (Chốt chặn Sentinel):**"
    $md += "- **C0** : Prerequisite (Kiểm tra output các Phase trước, chặn nhảy cóc)."
    $md += "- **C1** : Script Scanner (Chặn lén tạo file script để lách luật)."
    $md += "- **C2** : Vault Guard (Chặn ghi file vào không gian vault/)."
    $md += "- **C3** : QA Forgery (Chặn hành vi tự chế điểm số QA ảo)."
    $md += "- **C4** : Execution Key (Xác minh Agent thực sự đã đọc SKILL.md)."
    $md += "- **C4BC**: DIKW Poka-yoke (Xác minh luồng DIKW Bridge chạy đúng)."
    $md += "- **C5** : Quality Validate (Chấm điểm lại, validate định dạng đầu ra)."
    $md += ""
    $md += "| Phase | Agent | Output | Trạng thái | Thời điểm | Checks |"
    $md += "|:------|:------|:-------|:-----------|:----------|:-------|"

    foreach ($phaseKey in @("0", "1", "2", "3", "4", "45", "5", "6", "7")) {
        $meta = $phaseMeta[$phaseKey]
        $displayPhase = if ($phaseKey -eq "45") { "4.5" } else { $phaseKey }

        if ($data.ContainsKey($phaseKey)) {
            $entry = $data[$phaseKey]
            $statusStr = switch ($entry.status) {
                "PASS" { "**[PASS]**" }
                "HALT" { "**[HALT]**" }
                "RETRY" { "**[RETRY]**" }
                default { $entry.status }
            }
            $md += "| $displayPhase | $($meta.Name) | ``$($meta.Output)`` | $statusStr | $($entry.timestamp) | $($entry.checks) |"
        }
        else {
            $md += "| $displayPhase | $($meta.Name) | ``$($meta.Output)`` | - | - | - |"
        }
    }

    # [Nhóm code: Render báo cáo lỗi Markdown]
    $allErrors = @()
    foreach ($phaseKey in @("0", "1", "2", "3", "4", "45", "5", "6", "7")) {
        if ($data.ContainsKey($phaseKey)) {
            $errs = $data[$phaseKey].errors
            if ($null -ne $errs) { foreach ($e in @($errs)) { $allErrors += $e } }
        }
    }

    if ($allErrors.Count -gt 0) {
        $md += ""
        $md += "### ⚠️ Lịch sử Lỗi (Error Log)"
        $md += "| Thời điểm | Phase | Check | Chi tiết lỗi |"
        $md += "|:----------|:------|:------|:-------------|"
        foreach ($err in $allErrors) {
            $errPhase = if ([string]$err.phase -eq "45") { "4.5" } else { $err.phase }
            $safeMsg = [string]$err.message
            if ($safeMsg) { $safeMsg = $safeMsg.Replace("|", "/").Replace("`n", " ").Replace("`r", "") }
            $md += "| $($err.timestamp) | $errPhase | $($err.check) | $safeMsg |"
        }
    }
    
    $mdPath = Join-Path $RunFolder "sentinel-checklist.md"
    $md -join "`n" | Set-Content $mdPath -Encoding UTF8
}

$status = "PASS"
if ($bypassFailed) { $status = "HALT" }
elseif ($qualityFailed) { $status = "RETRY" }

Update-SentinelChecklist -RunFolder $RunFolder -Phase $Phase -Status $status -CheckResults $checkResults

# ============================================================
# KET QUA
# ============================================================
if ($bypassFailed) {
    Write-Host "[SENTINEL HALT] Phase $Phase -- BYPASS DETECTED. Dung pipeline. Escalate User."
    exit 1
}
if ($qualityFailed) {
    Write-Host "[SENTINEL RETRY] Phase $Phase -- Quality check FAIL. Agent tu sua output roi chay lai Sentinel."
    exit 2
}

# ============================================================
# EXTRACT NEXT STEP GUIDANCE (SSOT)
# ============================================================
$workflowFile = ".agents/workflows/content-post.md"
if (Test-Path $workflowFile) {
    $content = Get-Content $workflowFile -Raw -Encoding UTF8
    
    $tagToFind = $Phase
    if ($Phase -eq 0) {
        $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
        $isNovelForNext = $false
        if (Test-Path $bbPath) {
            $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
            if ($bbContent -match 'Is_Novel_Angle:\s*true') { $isNovelForNext = $true }
        }
        if ($isNovelForNext) { $tagToFind = "1" } else { $tagToFind = "DIKW" }
    }
    elseif ($Phase -eq 4) {
        $tagToFind = "45"
    }
    elseif ($Phase -eq 45) {
        $tagToFind = "5"
    }
    else {
        $tagToFind = [string]($Phase + 1)
    }

    if ($tagToFind -ne "8") {
        $pattern = "(?s)<!-- NEXT_GUIDANCE:\s*$tagToFind\s*-->(.*?)<!-- /NEXT_GUIDANCE:\s*$tagToFind\s*-->"
        if ($content -match $pattern) {
            Write-Host ""
            Write-Host "============================================================"
            Write-Host "[NEXT STEP GUIDANCE]"
            Write-Host "============================================================"
            Write-Host $Matches[1].Trim()
            Write-Host "============================================================"
        }
    }
}

# (Da xoa Auto Checkpoint cu vi he thong da chuyen sang Continuous State Tracking thong qua sentinel-data.json)

# --- KEY CLEAR (chi Phase 7) ---
if ($Phase -eq 7) {
    $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
    $pPath = ""
    if (Test-Path $bbPath) {
        $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
        if ($bbContent -match 'Persona_Path:\s*"?([^"\r\n]+)"?') { $pPath = $Matches[1].Trim() }
    }

    $keyScript = ".agents/scripts/generate-phase-key.ps1"
    $keyArgs = @("-ExecutionPolicy", "Bypass", "-File", $keyScript, "-Action", "Clear")
    if ($pPath) { $keyArgs += @("-PersonaPath", $pPath) }
    $keyProc = Start-Process powershell -ArgumentList $keyArgs -Wait -PassThru -NoNewWindow

    Write-Host "`n[INFO] Auto-restoring format..."
    $restoreScript = ".agents/scripts/apply-format.ps1"
    if (Test-Path $restoreScript) {
        $restoreArgs = @("-ExecutionPolicy", "Bypass", "-File", $restoreScript, "-Action", "restore")
        $restoreProc = Start-Process powershell -ArgumentList $restoreArgs -Wait -PassThru -NoNewWindow
    }
}

Write-Host "[SENTINEL PASS] Phase $Phase PASS"
exit 0
