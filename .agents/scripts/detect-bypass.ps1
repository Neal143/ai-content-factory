# File       : detect-bypass.ps1
# Last update: 21/05/2026 11:22 (GMT+7)
# Vai tro    : Phat hien hanh vi bypass cua LLM trong pipeline content-post
# Dung khi   : content-post.md goi sau khi moi Phase ghi xong output
# Output     : Exit 0 = PASS | Exit 1 = FAIL (kem danh sach vi pham)
# Logic      : Check 1-3 luon chay. Check 4-5 kiem tra execution key va re-run validation.
#              Phase 4 PASS: goi create-checkpoint.ps1 de luu trang thai fail-safe.
#              Phase 7 PASS: goi generate-phase-key.ps1 de rotate key + set PIPELINE_STATUS.
<#
.SYNOPSIS
    Anti-Bypass Sentinel
.PARAMETER RunFolder
    Duong dan run folder hien tai (vd: output/runs/2026-04-28_topic-slug/)
.PARAMETER Phase
    Phase vua hoan thanh (1-7)
#>

param(
    [Parameter(Mandatory=$true)][string]$RunFolder,
    [Parameter(Mandatory=$true)][int]$Phase
)

$failed = $false

# ============================================================
# CHECK 1 - Script rac trong output/ root VA workspace root
# Ly do: LLM tao .py/.js/.sh de hardcode noi dung
# ============================================================
$forbiddenExtensions = @("*.py","*.js","*.sh")
$scanPaths = @("output", ".")
$forbidden = @()
foreach ($scanPath in $scanPaths) {
    if (Test-Path $scanPath) {
        $forbidden += Get-ChildItem -Path "$scanPath\*" -Include $forbiddenExtensions -File -ErrorAction SilentlyContinue |
            Where-Object { $_.DirectoryName -eq (Resolve-Path $scanPath).Path }
    }
}
if ($forbidden.Count -gt 0) {
    Write-Host "[FAIL] BYPASS DETECTED [Check 1]: Script bi cam: $($forbidden.FullName -join ', ')"
    $failed = $true
}

# ============================================================
# CHECK 2 - File ghi sai vao vault/output/ (duong dan bi cam)
# Ly do: LLM ghi ra vault/output/posts/ thay vi output/posts/
# ============================================================
$vaultFiles = Get-ChildItem -Path "vault/output/" -Recurse -File -ErrorAction SilentlyContinue
if ($vaultFiles) {
    Write-Host "[FAIL] BYPASS DETECTED [Check 2]: File bi ghi vao vault/output/: $($vaultFiles.Name -join ', ')"
    $failed = $true
}

# ============================================================
# CHECK 3 - qa_score hardcode ma 06-qa-result.md chua ton tai
# Ly do: LLM hardcode qa_score: 130/130 ma khong thuc su chay QA Checker
# Chi kiem tra tu Phase 6 tro di (Phase 5 draft chua can co qa-result)
# ============================================================
if ($Phase -ge 6) {
    $draftPath = Join-Path $RunFolder "05-draft.md"
    if (Test-Path $draftPath) {
        $content = Get-Content $draftPath -Raw -Encoding UTF8
        $hasScore = $content -match 'qa_score:\s*\d+'
        $hasQAFile = Test-Path (Join-Path $RunFolder "06-qa-result.md")
        if ($hasScore -and -not $hasQAFile) {
            Write-Host "[FAIL] BYPASS DETECTED [Check 3]: qa_score hardcode trong 05-draft.md nhung 06-qa-result.md chua ton tai."
            $failed = $true
        }
    }
}

# ============================================================
# CHECK 4 - Execution Key Verification (chung minh Agent doc SKILL.md)
# Ly do: Agent bypass doc SKILL.md, chay bang implicit memory.
# Key duoc inject vao SKILL.md o cuoi pipeline truoc do (boi detect-bypass.ps1 Phase 7).
# Agent phai doc SKILL.md de lay key, ghi vao output. Check nay doi chieu.
# ============================================================
$skillPaths = @{
    0 = ".agents/skills/semantic-router/SKILL.md"
    1 = ".agents/skills/idea-curator/SKILL.md"
    2 = ".agents/skills/insight-agent/SKILL.md"
    3 = ".agents/skills/hook-engineer/SKILL.md"
    4 = ".agents/skills/structure-designer/SKILL.md"
    5 = ".agents/skills/voice-writer/SKILL.md"
    6 = ".agents/skills/qa-checker/SKILL.md"
    7 = ".agents/skills/format-agent/SKILL.md"
    45 = ".agents/skills/persona-loader/SKILL.md"
}
$outputFiles = @{
    0 = "00-blackboard.yaml"; 1 = "01-idea-brief.md"; 2 = "02-research-brief.md"; 3 = "03-hook.md"
    4 = "04-outline.md"; 5 = "05-draft.md"; 6 = "06-qa-result.md"; 7 = "07-final.md"
    45 = "04.5-persona-pack.md"
}

if ($skillPaths.ContainsKey($Phase)) {
    $skillFile = $skillPaths[$Phase]
    $outputFile = Join-Path $RunFolder $outputFiles[$Phase]

    # Lay key tu SKILL.md
    $expectedKey = ""
    if (Test-Path $skillFile) {
        $skillContent = Get-Content $skillFile -Raw -Encoding UTF8
        if ($skillContent -match '> EXECUTION_KEY:\s*(\S+)') { $expectedKey = $Matches[1] }
    }

    # Lay key tu output file
    $actualKey = ""
    if (Test-Path $outputFile) {
        $outputContent = Get-Content $outputFile -Raw -Encoding UTF8
        if ($outputContent -match '(?:<!--|#)\s*execution_key:\s*(\S+)(?:\s*-->)?') { $actualKey = $Matches[1] }
    }

    # So khop
    if ($expectedKey -eq "" -or $expectedKey -eq "PENDING" -or $expectedKey -eq "__PENDING__") {
        Write-Host "[FAIL] BYPASS DETECTED [Check 4]: SKILL.md thieu execution_key. Chay generate-phase-key.ps1 truoc."
        $failed = $true
    }
    elseif ($actualKey -eq "") {
        Write-Host "[FAIL] BYPASS DETECTED [Check 4]: Output thieu execution_key."
        $failed = $true
    }
    elseif ($expectedKey -ne $actualKey) {
        Write-Host "[FAIL] BYPASS DETECTED [Check 4]: Key khong khop. Expected: $expectedKey | Actual: $actualKey"
        $failed = $true
    }
    else {
        Write-Host "[PASS] CHECK 4: Execution key verified."
    }
}

# ============================================================
# CHECK 5 - Re-run validation script (chong Agent bia ket qua PASS)
# Ly do: Agent co the khong goi script ma tu bia ket qua.
# Sentinel tu chay lai script tuong ung, neu FAIL thi Agent da bia.
# ============================================================
$validationScripts = @{
    1 = @{ Script = ".agents/skills/idea-curator/scripts/validate-idea.ps1";         Param = "IdeaPath";     File = "01-idea-brief.md" }
    2 = @{ Script = ".agents/skills/insight-agent/scripts/validate-research.ps1";     Param = "ResearchPath"; File = "02-research-brief.md" }
    3 = @{ Script = ".agents/skills/hook-engineer/scripts/validate-hook.ps1";         Param = "HookPath";     File = "03-hook.md" }
    4 = @{ Script = ".agents/skills/structure-designer/scripts/validate-outline.ps1"; Param = "OutlinePath";  File = "04-outline.md" }
    5 = @{ Script = ".agents/skills/voice-writer/scripts/validate-draft.ps1";         Param = "DraftPath";    File = "05-draft.md" }
    6 = @{ Script = ".agents/skills/qa-checker/scripts/validate-qa.ps1";              Param = "QAResultPath"; File = "06-qa-result.md" }
    7 = @{ Script = ".agents/skills/format-agent/scripts/validate-format.ps1";        Param = "DraftPath";    File = "07-final.md" }
    45 = @{ Script = ".agents/skills/persona-loader/scripts/validate-persona-pack.ps1"; Param = "PackPath";    File = "04.5-persona-pack.md" }
}

if ($validationScripts.ContainsKey($Phase)) {
    $vs = $validationScripts[$Phase]
    $targetFile = Join-Path $RunFolder $vs.File

    if (Test-Path $vs.Script) {
        # Build argument list (khong dung splatting vi goi external process)
        $paramName = $vs.Param
        $argList = @("-ExecutionPolicy", "Bypass", "-File", $vs.Script, "-$paramName", $targetFile)
        if ($Phase -eq 7) {
            $argList += @("-SourceDraftPath", (Join-Path $RunFolder "05-draft.md"))
        }
        # Phase 45: truyen them -PersonaPath de validate-persona-pack.ps1 doi chieu keys
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
        }
        else {
            Write-Host "[FAIL] BYPASS DETECTED [Check 5]: Re-run validation FAIL for Phase $Phase."
            $failed = $true
        }
    }
    else {
        $scriptPath = $vs.Script
        Write-Host "[WARN] CHECK 5: Validation script not found: $scriptPath"
    }
}
elseif ($Phase -eq 0) {
    # CHECK 5B - Phase 0 (Semantic Router): inline validate 00-blackboard.yaml
    # Khong co validation script rieng, nen check truc tiep 4 fields bat buoc.
    $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
    if (-not (Test-Path $bbPath)) {
        Write-Host "[FAIL] BYPASS DETECTED [Check 5]: 00-blackboard.yaml khong ton tai."
        $failed = $true
    }
    else {
        $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
        $requiredFields = @("topic", "Target_Pillar", "Is_Novel_Angle", "Persona_Path")
        $missingFields = @()
        foreach ($field in $requiredFields) {
            # Extract gia tri sau dau ':', strip quotes va whitespace, check co noi dung thuc su
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
            Write-Host "[FAIL] BYPASS DETECTED [Check 5]: Blackboard thieu/rong cac field: $missing"
            $failed = $true
        }
        else {
            Write-Host "[PASS] CHECK 5: Blackboard fields validated for Phase 0."
        }

        # CHECK 5C - Topic ID format: snake_case, 2-4 tu
        $topicMatch = [regex]::Match($bbContent, '(?m)^topic:\s*"?([^"\r\n]+)"?')
        if ($topicMatch.Success) {
            $topicVal = $topicMatch.Groups[1].Value.Trim()
            $wordCount = ($topicVal -split '_').Count
            if ($topicVal -notmatch '^[a-z][a-z0-9_]{2,40}$' -or $wordCount -gt 4) {
                Write-Host "[FAIL] BYPASS DETECTED [Check 5C]: topic '$topicVal' khong dung format (snake_case, 2-4 tu)."
                $failed = $true
            }
        }

        # CHECK 5D - Persona_Path khong chua backslash kep
        $ppMatch = [regex]::Match($bbContent, '(?m)^Persona_Path:\s*"?([^"\r\n]+)"?')
        if ($ppMatch.Success) {
            $ppVal = $ppMatch.Groups[1].Value.Trim()
            if ($ppVal -match '\\\\') {
                Write-Host "[FAIL] BYPASS DETECTED [Check 5D]: Persona_Path chua escaped backslash: $ppVal"
                $failed = $true
            }
        }
    }
}

# ============================================================
# KET QUA
# ============================================================
if ($failed) {
    Write-Host "[SENTINEL FAIL] Phase $Phase -- Dung pipeline. Escalate User ngay lap tuc."
    exit 1
}

# --- AUTO CHECKPOINT (Phase 4 va Phase 7 - fail-safe) ---
# Phase 4 ghi in_progress (fail-safe anchor), Phase 7 ghi completed. Agent khong can tu tao.
if ($Phase -eq 4 -or $Phase -eq 7) {
    $cpScript = ".agents/scripts/create-checkpoint.ps1"
    if (Test-Path $cpScript) {
        $cpArgs = @("-ExecutionPolicy", "Bypass", "-File", $cpScript, "-RunFolder", $RunFolder)
        $cpProc = Start-Process powershell -ArgumentList $cpArgs -Wait -PassThru -NoNewWindow
        if ($cpProc.ExitCode -ne 0) {
            Write-Host "[WARN] Checkpoint creation failed. Thong bao User."
        }
    } else {
        Write-Host "[WARN] create-checkpoint.ps1 khong ton tai."
    }
}

# --- KEY ROTATION (chi Phase 7) ---
# generate-phase-key.ps1 rotate key moi + tu set PIPELINE_STATUS = SAN SANG
if ($Phase -eq 7) {
    # Lay PersonaPath tu blackboard
    $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
    $pPath = ""
    if (Test-Path $bbPath) {
        $bbContent = Get-Content $bbPath -Raw -Encoding UTF8
        if ($bbContent -match 'Persona_Path:\s*"?([^"\r\n]+)"?') { $pPath = $Matches[1].Trim() }
    }

    # Rotate key cho session tiep theo
    $keyScript = ".agents/scripts/generate-phase-key.ps1"
    $keyArgs = @("-ExecutionPolicy", "Bypass", "-File", $keyScript)
    if ($pPath) { $keyArgs += @("-PersonaPath", $pPath) }
    $keyProc = Start-Process powershell -ArgumentList $keyArgs -Wait -PassThru -NoNewWindow
    if ($keyProc.ExitCode -eq 0) {
        Write-Host "[OK] Key rotation completed for next session."
    } else {
        Write-Host "[WARN] Key rotation failed. Keys se duoc tao lai o lan chay tiep theo."
    }
}

Write-Host "[SENTINEL PASS] Phase $Phase PASS"
exit 0
