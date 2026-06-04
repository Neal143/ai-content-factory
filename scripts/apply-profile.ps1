# ENCODING RULE: This file MUST contain ASCII-only characters.
# All non-ASCII content (Vietnamese patterns, messages) must be stored
# in JSON files and read at runtime with -Encoding UTF8.
# Reason: PowerShell 5 requires BOM for UTF-8, which AI tools may strip.

# ============================================================
# File: apply-profile.ps1
# Role: Manage profile for content-post pipeline.
#   - validate: Check constraints R1-R8 in active.json
#   - patch: Backup + string-replace prompt files using active.json and patch-patterns.json
#   - restore: Restore prompt files from .bak
# Usage: Run before/after the content-post pipeline.
# Output: Exit 0 (success) or Exit 1 (fail + error list).
# ============================================================

param(
    [ValidateSet("validate", "patch", "restore")]
    [string]$Action = "validate",

    [string]$ProfilePath = "profiles/active.json",
    [string]$DefaultPath = "profiles/default.json",
    [string]$PatternsPath = "profiles/patch-patterns.json"
)

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

# Check if object has min/max and min <= max
function Test-Range($obj, $name) {
    if ($null -eq $obj) { return "[FAIL] ${name} - field missing" }
    if (-not $obj.PSObject.Properties['min'] -and $obj.min -ne 0) { return "[FAIL] ${name} - missing 'min'" }
    if (-not $obj.PSObject.Properties['max'] -and $obj.max -ne 0) { return "[FAIL] ${name} - missing 'max'" }
    if ($obj.min -gt $obj.max) { return "[FAIL] ${name} - min ($($obj.min)) > max ($($obj.max))" }
    return $null
}

# String replacement utility
function Invoke-Patch {
    param([string]$FilePath, [string]$Find, [string]$Replace)

    if (-not (Test-Path $FilePath)) {
        Write-Host "  WARNING: File not found: $FilePath"
        return $false
    }

    # Backup if not exists
    $bakPath = "$FilePath.bak"
    if (-not (Test-Path $bakPath)) {
        Copy-Item $FilePath $bakPath
    }

    $content = Get-Content $FilePath -Raw -Encoding UTF8
    if ($content.Contains($Find)) {
        $content = $content.Replace($Find, $Replace)
        Set-Content $FilePath $content -Encoding UTF8 -NoNewline
        Write-Host "  PATCHED: $FilePath"
        return $true
    }
    else {
        Write-Host "  WARNING: Pattern not found in ${FilePath}: '$($Find.Substring(0, [Math]::Min(50, $Find.Length)))...'"
        return $false
    }
}



# ============================================================
# FILES TO PATCH/RESTORE
# ============================================================
$targetFiles = @(
    ".agents/skills/voice-writer/SKILL.md",
    ".agents/skills/voice-writer/references/writing-rules.md",
    ".agents/skills/structure-designer/SKILL.md"
)

# ============================================================
# ACTION: VALIDATE
# ============================================================
if ($Action -eq "validate") {
    if (-not (Test-Path $ProfilePath)) {
        Write-Host "[FAIL] Profile not found: $ProfilePath"
        exit 1
    }

    try {
        $p = Get-Content $ProfilePath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        Write-Host "[FAIL] Invalid JSON: $ProfilePath"
        exit 1
    }

    $errors = @()

    # --- Min/max range validation ---
    foreach ($field in @("sentences_per_paragraph", "sentences_per_normal_chain",
            "sentences_per_long_chain", "long_chains_per_article")) {
        if ($null -eq $p.$field) { continue }  # B8/B9 can be null
        $err = Test-Range $p.$field $field
        if ($err) { $errors += $err }
    }

    # --- R1: B1 != B3 ---
    $b1 = $p.section_separator; $b2 = $p.paragraph_separator
    if (-not $b1.marker -and -not $b2.marker) {
        $b1Total = $b1.blank_lines_above + $b1.blank_lines_below
        $b2Total = $b2.blank_lines_above + $b2.blank_lines_below
        if ($b1Total -le $b2Total) {
            $errors += "[FAIL] R1: Section separator ($($b1Total) blank lines) must be > paragraph separator ($($b2Total) blank lines) when both have no marker"
        }
    }
    elseif ($b1.marker -and $b2.marker -and $b1.marker -eq $b2.marker) {
        $errors += "[FAIL] R1: Section marker '$($b1.marker)' conflicts with paragraph marker"
    }

    # --- R2: B3 != B6 ---
    $b4 = $p.chain_separator
    if (-not $b2.marker -and -not $b4.marker) {
        $b2Total = $b2.blank_lines_above + $b2.blank_lines_below
        $b4Total = $b4.blank_lines_above + $b4.blank_lines_below
        if ($b2Total -gt 0 -and $b4Total -gt 0 -and $b2Total -le $b4Total) {
            $errors += "[FAIL] R2: Paragraph separator ($($b2Total) blank lines) must be > chain separator ($($b4Total) blank lines) when both have no marker"
        }
    }
    elseif ($b2.marker -and $b4.marker -and $b2.marker -eq $b4.marker) {
        $errors += "[FAIL] R2: Paragraph marker '$($b2.marker)' conflicts with chain marker"
    }

    # --- R3: B5.max >= B7.max ---
    if ($p.sentences_per_paragraph.max -lt $p.sentences_per_normal_chain.max) {
        $errors += "[FAIL] R3: sentences_per_paragraph.max ($($p.sentences_per_paragraph.max)) < sentences_per_normal_chain.max ($($p.sentences_per_normal_chain.max))"
    }

    # --- R4: B5.max >= B8.max ---
    if ($null -ne $p.sentences_per_long_chain) {
        if ($p.sentences_per_paragraph.max -lt $p.sentences_per_long_chain.max) {
            $errors += "[FAIL] R4: sentences_per_paragraph.max ($($p.sentences_per_paragraph.max)) < sentences_per_long_chain.max ($($p.sentences_per_long_chain.max))"
        }
    }

    # --- R5: B8.min > B7.max ---
    if ($null -ne $p.sentences_per_long_chain) {
        if ($p.sentences_per_long_chain.min -le $p.sentences_per_normal_chain.max) {
            $errors += "[FAIL] R5: sentences_per_long_chain.min ($($p.sentences_per_long_chain.min)) must be > sentences_per_normal_chain.max ($($p.sentences_per_normal_chain.max))"
        }
    }

    # --- R6, R7, R8: advanced mode only ---
    if ($p.mode -eq "advanced") {
        # R6: A2.min >= sum(A3.min)
        $sumMin = 0
        foreach ($sec in @("Hook", "Story", "Deep Dive", "Pivot", "Closing")) {
            $sumMin += $p.word_count_per_section.$sec.min
        }
        if ($p.word_count_total.min -lt $sumMin) {
            $errors += "[FAIL] R6: word_count_total.min ($($p.word_count_total.min)) < total section min ($sumMin)"
        }

        # R7: A2.max <= sum(A3.max) * 1.1
        $sumMax = 0
        foreach ($sec in @("Hook", "Story", "Deep Dive", "Pivot", "Closing")) {
            $sumMax += $p.word_count_per_section.$sec.max
        }
        $ceiling = [math]::Floor($sumMax * 1.1)
        if ($p.word_count_total.max -gt $ceiling) {
            $errors += "[FAIL] R7: word_count_total.max ($($p.word_count_total.max)) > total section max * 1.1 ($ceiling)"
        }

        # R8: A4.max <= A2.max
        if ($p.word_count_per_paragraph.max -gt $p.word_count_total.max) {
            $errors += "[FAIL] R8: word_count_per_paragraph.max ($($p.word_count_per_paragraph.max)) > word_count_total.max ($($p.word_count_total.max))"
        }
    }

    if ($errors.Count -eq 0) {
        Write-Host "VALIDATION PASSED"
        exit 0
    }
    else {
        $errors | ForEach-Object { Write-Host $_ }
        exit 1
    }
}

# ============================================================
# ACTION: PATCH
# ============================================================
if ($Action -eq "patch") {
    if (-not (Test-Path $ProfilePath)) {
        Write-Host "[FAIL] Profile not found: $ProfilePath"
        exit 1
    }
    if (-not (Test-Path $PatternsPath)) {
        Write-Host "[FAIL] Patterns file not found: $PatternsPath"
        exit 1
    }

    $p = Get-Content $ProfilePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $pat = Get-Content $PatternsPath -Raw -Encoding UTF8 | ConvertFrom-Json

    Write-Host "=== PRE-FLIGHT CHECK ==="
    $preflightFail = $false

    # List of find-patterns to verify
    $checks = @(
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_no_write_all_find },
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_word_count_find },
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_paragraph_length_find },
        @{ File = ".agents/skills/voice-writer/references/writing-rules.md"; Pattern = $pat.writing_rules.wr_total_words_find },
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_chain_find },
        @{ File = ".agents/skills/voice-writer/references/writing-rules.md"; Pattern = $pat.writing_rules.wr_chain_find }
    )

    if ($p.mode -eq "advanced") {
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_total_find }
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_hook_find }
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_story_find }
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_deep_dive_find }
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_pivot_find }
        $checks += @{ File = ".agents/skills/structure-designer/SKILL.md"; Pattern = $pat.structure_designer.sd_closing_find }
    }

    foreach ($check in $checks) {
        if (-not (Test-Path $check.File)) {
            Write-Host "  [PREFLIGHT FAIL] File not found: $($check.File)"
            $preflightFail = $true
            continue
        }
        $content = Get-Content $check.File -Raw -Encoding UTF8
        if (-not $content.Contains($check.Pattern)) {
            $shortPattern = $check.Pattern.Substring(0, [Math]::Min(60, $check.Pattern.Length))
            Write-Host "  [PREFLIGHT FAIL] Pattern not found in $($check.File): '$shortPattern...'"
            $preflightFail = $true
        }
    }

    if ($preflightFail) {
        Write-Host "`n[ABORT] Pre-flight check failed. No files were modified."
        exit 1
    }
    Write-Host "  Pre-flight check PASSED"

    Write-Host "`n=== PATCHING ==="
    $vwPath = ".agents/skills/voice-writer/SKILL.md"
    $wrPath = ".agents/skills/voice-writer/references/writing-rules.md"
    $sdPath = ".agents/skills/structure-designer/SKILL.md"

    # voice-writer/SKILL.md
    Invoke-Patch $vwPath $pat.voice_writer.vw_no_write_all_find ($pat.voice_writer.vw_no_write_all_replace -replace '{min}', $p.word_count_total.min -replace '{max}', $p.word_count_total.max)
    Invoke-Patch $vwPath $pat.voice_writer.vw_word_count_find ($pat.voice_writer.vw_word_count_replace -replace '{min}', $p.word_count_total.min -replace '{max}', $p.word_count_total.max)
    Invoke-Patch $vwPath $pat.voice_writer.vw_paragraph_length_find ($pat.voice_writer.vw_paragraph_length_replace -replace '{min}', $p.sentences_per_paragraph.min -replace '{max}', $p.sentences_per_paragraph.max)

    # writing-rules.md
    Invoke-Patch $wrPath $pat.writing_rules.wr_total_words_find ($pat.writing_rules.wr_total_words_replace -replace '{min}', $p.word_count_total.min -replace '{max}', $p.word_count_total.max)


    # Chain instructions (find/replace in SKILL.md)
    Invoke-Patch $vwPath $pat.voice_writer.vw_chain_find ($pat.voice_writer.vw_chain_replace -replace '{n_min}', $p.sentences_per_normal_chain.min -replace '{n_max}', $p.sentences_per_normal_chain.max -replace '{lc_min}', $p.long_chains_per_article.min -replace '{lc_max}', $p.long_chains_per_article.max -replace '{l_min}', $p.sentences_per_long_chain.min -replace '{l_max}', $p.sentences_per_long_chain.max)

    # Chain instructions (find/replace in writing-rules.md)
    Invoke-Patch $wrPath $pat.writing_rules.wr_chain_find ($pat.writing_rules.wr_chain_replace -replace '{n_min}', $p.sentences_per_normal_chain.min -replace '{n_max}', $p.sentences_per_normal_chain.max -replace '{lc_min}', $p.long_chains_per_article.min -replace '{lc_max}', $p.long_chains_per_article.max -replace '{l_min}', $p.sentences_per_long_chain.min -replace '{l_max}', $p.sentences_per_long_chain.max)

    # structure-designer (advanced mode)
    if ($p.mode -eq "advanced") {
        Invoke-Patch $sdPath $pat.structure_designer.sd_total_find ($pat.structure_designer.sd_total_replace -replace '{min}', $p.word_count_total.min -replace '{max}', $p.word_count_total.max)
        Invoke-Patch $sdPath $pat.structure_designer.sd_hook_find ($pat.structure_designer.sd_hook_replace -replace '{min}', $p.word_count_per_section.Hook.min -replace '{max}', $p.word_count_per_section.Hook.max)
        Invoke-Patch $sdPath $pat.structure_designer.sd_story_find ($pat.structure_designer.sd_story_replace -replace '{min}', $p.word_count_per_section.Story.min -replace '{max}', $p.word_count_per_section.Story.max)
        Invoke-Patch $sdPath $pat.structure_designer.sd_deep_dive_find ($pat.structure_designer.sd_deep_dive_replace -replace '{min}', $p.word_count_per_section.'Deep Dive'.min -replace '{max}', $p.word_count_per_section.'Deep Dive'.max)
        Invoke-Patch $sdPath $pat.structure_designer.sd_pivot_find ($pat.structure_designer.sd_pivot_replace -replace '{min}', $p.word_count_per_section.Pivot.min -replace '{max}', $p.word_count_per_section.Pivot.max)
        Invoke-Patch $sdPath $pat.structure_designer.sd_closing_find ($pat.structure_designer.sd_closing_replace -replace '{min}', $p.word_count_per_section.Closing.min -replace '{max}', $p.word_count_per_section.Closing.max)
    }

    Write-Host "`n=== PATCH COMPLETE ==="
    exit 0
}

# ============================================================
# ACTION: RESTORE
# ============================================================
if ($Action -eq "restore") {
    $restoredCount = 0

    foreach ($file in $targetFiles) {
        $bakPath = "$file.bak"
        if (Test-Path $bakPath) {
            Copy-Item $bakPath $file -Force
            Remove-Item $bakPath
            Write-Host "  RESTORED: $file"
            $restoredCount++
        }
    }

    if ($restoredCount -eq 0) {
        Write-Host "Nothing to restore"
    }
    else {
        Write-Host "`n$restoredCount file(s) restored."
    }
    exit 0
}
