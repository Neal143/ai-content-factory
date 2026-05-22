# Last Update: 19/05/2026 20:15 (GMT+7)
<#
.SYNOPSIS
    Validate Draft - Objective checks for Phase 5 (Voice Writer)
.DESCRIPTION
    Check "physical" metrics of the draft post.
    This script DOES NOT evaluate creative quality.
    Only checks objective measures: word count, banned words, anti-AI patterns, pronouns, fillers, punctuation.
.PARAMETER DraftPath
    Path to draft.md file
.PARAMETER BlacklistPath
    Path to english-blacklist.md file
.NOTES
    Last Update: 19/05/2026
#>

param(
    [Parameter(Mandatory = $true)][string]$DraftPath,
    [string]$BlacklistPath = ".agents/skills/voice-writer/references/english-blacklist.md",
    [string]$PersonaPath = ""
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

# --- Extract config values (fallback to current defaults) ---
$cfgWordCountMin = if ($profile) { $profile.word_count_total.min } else { 1500 }
$cfgWordCountMax = if ($profile) { $profile.word_count_total.max } else { 1800 }
$cfgMaxParaWords = if ($profile) { $profile.word_count_per_paragraph.max } else { 400 }
$cfgSentPerParaMin = if ($profile) { $profile.sentences_per_paragraph.min } else { 3 }
$cfgSentPerParaMax = if ($profile) { $profile.sentences_per_paragraph.max } else { 5 }
$cfgSentPerNormalMin = if ($profile) { $profile.sentences_per_normal_chain.min } else { 3 }
$cfgSentPerNormalMax = if ($profile) { $profile.sentences_per_normal_chain.max } else { 5 }
$cfgSentPerLongMin = if ($profile) { $profile.sentences_per_long_chain.min } else { 6 }
$cfgSentPerLongMax = if ($profile) { $profile.sentences_per_long_chain.max } else { 8 }
$cfgLongChainsMin = if ($profile) { $profile.long_chains_per_article.min } else { 0 }
$cfgLongChainsMax = if ($profile) { $profile.long_chains_per_article.max } else { 2 }
$cfgTitleInOutput = if ($profile) { $profile.output_elements.title } else { $false }
$cfgSectionHeadingInOutput = if ($profile) { $profile.output_elements.section_heading } else { $false }
$cfgParaHeadingInOutput = if ($profile) { $profile.output_elements.paragraph_heading } else { $false }
$cfgVeryShortThreshold = if ($profile) { $profile.very_short_sentence_threshold } else { 4 }
$cfgMode = if ($profile) { $profile.mode } else { "auto" }

# Auto-detect PersonaPath tu blackboard neu chua truyen
if (-not $PersonaPath) {
    $bbPath = Join-Path (Split-Path $DraftPath -Parent) "00-blackboard.yaml"
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

$VoiceDnaPath = Join-Path $PersonaPath "voice-dna.yaml"

$results = @()
$passCount = 0
$failCount = 0

# --- Helper ---
function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{
        Check  = $check
        Status = $status
        Detail = $detail
    }
    if ($status -eq "PASS") { $script:passCount++ }
    elseif ($status -eq "FAIL") { $script:failCount++ }
    # WARN: does not count towards failCount, does not block pipeline
}

# --- New sentence counting rule ---
# Normal sentence (>= threshold words): counts as 1
# Very short sentence (< threshold words): 2 sentences = 1, remainder = 0
function Count-ValidSentences([string[]]$sentences, [int]$threshold) {
    $normalCount = 0
    $shortCount = 0
    foreach ($s in $sentences) {
        $wc = ($s -split '\s+' | Where-Object { $_ -ne '' }).Count
        if ($wc -ge $threshold) {
            $normalCount++
        } elseif ($wc -gt 0) {
            $shortCount++
        }
    }
    $fromShort = [math]::Floor($shortCount / 2)
    return $normalCount + $fromShort
}

# --- Read draft ---
if (-not (Test-Path $DraftPath)) {
    Write-Host "ERROR: Draft not found at $DraftPath"
    exit 1
}
$draft = Get-Content $DraftPath -Raw -Encoding UTF8
$lines = Get-Content $DraftPath -Encoding UTF8

# --- Stripped version: remove structural markers for content checks (3-6, 10) ---
$draftForCount = $draft -replace '<!--[^>]*-->', ''
$draftForCount = $draftForCount -replace [string][char]0x2042, ''
$linesForCount = $draftForCount -split '\r?\n'

# ============================================================
# CHECK 1: Word Count (Configurable)
# ============================================================
# $draftForCount already stripped above (line 117-119)
$words = ($draftForCount -split '\s+' | Where-Object { $_ -ne '' }).Count
if ($words -ge $cfgWordCountMin -and $words -le $cfgWordCountMax) {
    Add-Result "Word Count" "PASS" "$words words (range: $cfgWordCountMin-$cfgWordCountMax)"
}
else {
    Add-Result "Word Count" "FAIL" "$words words (range: $cfgWordCountMin-$cfgWordCountMax)"
}

# ============================================================
# CHECK 2: Banned Words (English Blacklist)
# ============================================================
$bannedWords = @()
if (Test-Path $BlacklistPath) {
    $blacklistContent = Get-Content $BlacklistPath -Encoding UTF8
    foreach ($line in $blacklistContent) {
        if ($line.Contains('|')) {
            $cols = $line.Split('|')
            if ($cols.Length -ge 3) {
                $word = $cols[2].Trim()
                if (-not [string]::IsNullOrWhiteSpace($word) -and $word -notmatch ' T. c.m|---') {
                    $bannedWords += $word
                }
            }
        }
    }
}
else {
    Write-Host "WARNING: Blacklist file not found at $BlacklistPath"
}

$foundBanned = @()
foreach ($word in $bannedWords) {
    # Case-insensitive, word boundary match
    if ($draft -match "(?i)\b$([regex]::Escape($word))\b") {
        $foundBanned += $word
    }
}
if ($foundBanned.Count -eq 0) {
    Add-Result "Banned Words" "PASS" "0 banned words found"
}
else {
    Add-Result "Banned Words" "FAIL" "Found: $($foundBanned -join ', ')"
}

# ============================================================
# CHECK 3: Anti-AI Pattern - Dash Connector
# ============================================================
# Pattern: "X - Y - Z" (word-space-dash-space-word repeated)
$dashMatches = [regex]::Matches($draftForCount, '\w+\s+-\s+\w+\s+-\s+\w+')
if ($dashMatches.Count -eq 0) {
    Add-Result "Anti-AI: Dash Connector" "PASS" "0 dash connector patterns"
}
else {
    Add-Result "Anti-AI: Dash Connector" "FAIL" "$($dashMatches.Count) pattern(s) found"
}

# ============================================================
# CHECK 4: Anti-AI Pattern - Staccato (2+ consecutive sentences <= 8 words)
# ============================================================
$sentences = [regex]::Split($draftForCount, "(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?$([char]0x2026)]+\s+")
$staccatoCount = 0
$consecutive = 0
foreach ($s in $sentences) {
    $sWords = ($s -split '\s+' | Where-Object { $_ -ne '' }).Count
    if ($sWords -le 8 -and $sWords -gt 0) {
        $consecutive++
        if ($consecutive -ge 2) { $staccatoCount++ }
    }
    else {
        $consecutive = 0
    }
}
if ($staccatoCount -eq 0) {
    Add-Result "Anti-AI: Staccato" "PASS" "0 staccato patterns"
}
else {
    Add-Result "Anti-AI: Staccato" "FAIL" "$staccatoCount staccato sequence(s)"
}

# ============================================================
# CHECK 5: Anti-AI Pattern - Anaphora (3+ lines starting the same way)
# ============================================================
$lineStarts = $linesForCount | ForEach-Object {
    if ($_ -match '^\s*(\S+\s+\S+)') { $Matches[1].ToLower() }
}
$grouped = $lineStarts | Where-Object { $_ } | Group-Object | Where-Object { $_.Count -ge 3 }
if ($grouped.Count -eq 0) {
    Add-Result "Anti-AI: Anaphora" "PASS" "0 anaphora patterns"
}
else {
    $examples = ($grouped | ForEach-Object { "'$($_.Name)' x$($_.Count)" }) -join '; '
    Add-Result "Anti-AI: Anaphora" "FAIL" "Found: $examples"
}

# ============================================================
# CHECK 6: Punctuation Limits - Max 3 ellipsis (...), Max 3 exclamation (!)
# ============================================================
$ellipsisCount = ([regex]::Matches($draftForCount, '\.{3}')).Count
$exclamationCount = ([regex]::Matches($draftForCount, '!')).Count

if ($ellipsisCount -le 3) {
    Add-Result "Punctuation: Ellipsis" "PASS" "$ellipsisCount/3 max"
}
else {
    Add-Result "Punctuation: Ellipsis" "FAIL" "$ellipsisCount/3 max"
}
if ($exclamationCount -le 3) {
    Add-Result "Punctuation: Exclamation" "PASS" "$exclamationCount/3 max"
}
else {
    Add-Result "Punctuation: Exclamation" "FAIL" "$exclamationCount/3 max"
}

# ============================================================
# PARSE: Extract content using Structural Markers
# ============================================================
# Remove frontmatter
$bodyForParse = $draft -replace '(?s)^---.*?---\s*', ''
$bodyForParse = $bodyForParse.Trim()

# --- CHECK 7a: TITLE marker ---
if ($bodyForParse -match '<!--\s*TITLE:\s*(.+?)\s*-->') {
    Add-Result "Title Marker" "PASS" "Title: $($Matches[1])"
} else {
    Add-Result "Title Marker" "FAIL" "Missing <!-- TITLE: ... -->"
}

# --- CHECK 7b: SECTION markers (5 sections in order) ---
$expectedSections = @('Hook', 'Story', 'Deep Dive', 'Pivot', 'Closing')
$sectionMatches = [regex]::Matches($bodyForParse, '<!--\s*SECTION:\s*(.+?)\s*-->')
$foundSections = @($sectionMatches | ForEach-Object { $_.Groups[1].Value.Trim() })

if ($foundSections.Count -eq 5 -and ($foundSections -join ',') -eq ($expectedSections -join ',')) {
    Add-Result "Section Markers" "PASS" "5 sections in correct order"
} else {
    Add-Result "Section Markers" "FAIL" "Expect: $($expectedSections -join ', '). Found: $($foundSections -join ', ')"
}

# --- CHECK 7c: SECTION_HEADING for each section ---
$sectionHeadings = [regex]::Matches($bodyForParse, '<!--\s*SECTION_HEADING:\s*(.+?)\s*-->')
if ($sectionHeadings.Count -eq 5) {
    Add-Result "Section Headings" "PASS" "5/5 section headings"
} else {
    Add-Result "Section Headings" "FAIL" "$($sectionHeadings.Count)/5 section headings"
}

# --- CHECK 7d: PARAGRAPH markers (continuous sequence 1->N) ---
$paraMatches = [regex]::Matches($bodyForParse, '<!--\s*PARAGRAPH:\s*(\d+)\s*-->')
$paraNumbers = @($paraMatches | ForEach-Object { [int]$_.Groups[1].Value })
$paraOK = $true
for ($i = 0; $i -lt $paraNumbers.Count; $i++) {
    if ($paraNumbers[$i] -ne ($i + 1)) { $paraOK = $false; break }
}
if ($paraOK -and $paraNumbers.Count -gt 0) {
    Add-Result "Paragraph Markers" "PASS" "$($paraNumbers.Count) paragraphs, sequence 1->$($paraNumbers.Count)"
} else {
    Add-Result "Paragraph Markers" "FAIL" "Sequence not continuous or missing: $($paraNumbers -join ', ')"
}

# --- CHECK 7e: PARAGRAPH_HEADING for each paragraph ---
$paraHeadings = [regex]::Matches($bodyForParse, '<!--\s*PARAGRAPH_HEADING:\s*(.+?)\s*-->')
if ($paraHeadings.Count -eq $paraNumbers.Count) {
    Add-Result "Paragraph Headings" "PASS" "$($paraHeadings.Count)/$($paraNumbers.Count) paragraph headings"
} else {
    Add-Result "Paragraph Headings" "FAIL" "$($paraHeadings.Count)/$($paraNumbers.Count) paragraph headings"
}

# ============================================================
# PARSE: Strip markers to count words/sentences
# ============================================================
$bodyClean = $bodyForParse -replace '<!--[^>]*-->', ''
$bodyClean = $bodyClean -replace [string][char]0x2042, ''
$bodyClean = $bodyClean.Trim()

# Level 1: Split sections by ASTERISM (if used) or fallback
$sections = @($bodyForParse -split [regex]::Escape([char]0x2042) |
              ForEach-Object { $_.Trim() } |
              Where-Object { $_ -ne '' })

# Level 2: Split paragraphs within each section
$allParagraphs = @()
foreach ($section in $sections) {
    $paraBlocks = @($section -split '<!--\s*PARAGRAPH:\s*\d+\s*-->' |
                    ForEach-Object { $_ -replace '<!--[^>]*-->', '' } |
                    ForEach-Object { $_.Trim() } |
                    Where-Object { $_ -ne '' })
    $allParagraphs += $paraBlocks
}

# CHECK 8: Section Count (covered by 7b)

# CHECK 9: Max Paragraph Length (using marker-stripped content)
$longParas = @()
for ($i = 0; $i -lt $allParagraphs.Count; $i++) {
    $pWords = ($allParagraphs[$i] -split '\s+' | Where-Object { $_ -ne '' }).Count
    if ($pWords -gt $cfgMaxParaWords) {
        $longParas += "P$($i+1):${pWords}w"
    }
}
if ($longParas.Count -eq 0) {
    Add-Result "Max Paragraph Length" "PASS" "All paragraphs <= $cfgMaxParaWords words"
} else {
    Add-Result "Max Paragraph Length" "FAIL" "Over-length: $($longParas -join ', ')"
}

# ============================================================
# CHECK 10: Unique Word Ratio (>= 30%)
# Ly do: Copy-paste loop va padding lap lai co ratio rat thap.
# Bai tieng Viet binh thuong: 35-50%. Nguong 30% la floor an toan.
# GIOI HAN: Check nay KHONG bat duoc word salad da dang tu vung.
# Check 8-9 la tuyen phong ve chinh cho loi cau truc.
# ============================================================
$allWords = $draftForCount.ToLower() -split '\s+' | Where-Object { $_ -ne '' }
$uniqueWords = ($allWords | Select-Object -Unique)
if ($allWords.Count -gt 0) {
    $ratio = [math]::Round(($uniqueWords.Count / $allWords.Count) * 100, 1)
}
else {
    $ratio = 0
}
if ($ratio -ge 30) {
    Add-Result "Unique Word Ratio" "PASS" "${ratio}% unique ($($uniqueWords.Count)/$($allWords.Count), min: 30%)"
}
else {
    Add-Result "Unique Word Ratio" "FAIL" "${ratio}% unique ($($uniqueWords.Count)/$($allWords.Count), min: 30%)"
}

# ============================================================
# CHECK 11: Pronoun Self Compliance (voice-dna.yaml)
# Ly do: AI co the bo qua doc voice-dna va dung sai pronoun.
# Script tu doc file goc va doi chieu voi draft.
# ============================================================
if (Test-Path $VoiceDnaPath) {
    $voiceDna = Get-Content $VoiceDnaPath -Raw -Encoding UTF8
    if ($voiceDna -match 'self:\s*"([^"]+)"') {
        $pronounList = $Matches[1] -split ',' | ForEach-Object { $_.Trim() }
        $foundPronouns = @()
        foreach ($p in $pronounList) {
            if ($p -and $draft -match "(?i)$([regex]::Escape($p))") {
                $foundPronouns += $p
            }
        }
        if ($foundPronouns.Count -gt 0) {
            Add-Result "Pronoun Self" "PASS" "Found: $($foundPronouns -join ', ')"
        }
        else {
            Add-Result "Pronoun Self" "FAIL" "None of [$($pronounList -join ', ')] found in draft"
        }
    }
    else {
        Add-Result "Pronoun Self" "WARN" "Could not parse pronouns.self from $VoiceDnaPath"
    }
}
else {
    Add-Result "Pronoun Self" "WARN" "voice-dna.yaml not found at $VoiceDnaPath"
}

# ============================================================
# CHECK 12: Filler Count Compliance (voice-dna.yaml)
# Ly do: AI co the viet bai khong co filler hoac qua nhieu filler.
# Script tu doc file goc va dem so luong filler trong draft.
# ============================================================
if (Test-Path $VoiceDnaPath) {
    $voiceDnaLines = Get-Content $VoiceDnaPath -Encoding UTF8
    $inFillerBlock = $false
    $fillerMin = -1
    $fillerMax = -1
    $fillerLibrary = @()
    foreach ($vdLine in $voiceDnaLines) {
        if ($vdLine -match '^\s{2}fillers:\s*$') { $inFillerBlock = $true; continue }
        if ($inFillerBlock -and $vdLine -match '^\s{2}\w' -and $vdLine -notmatch '^\s{4}') { $inFillerBlock = $false }
        if ($inFillerBlock) {
            if ($vdLine -match 'min_per_post:\s*(\d+)') { $fillerMin = [int]$Matches[1] }
            if ($vdLine -match 'max_per_post:\s*(\d+)') { $fillerMax = [int]$Matches[1] }
            if ($vdLine -match 'library:\s*\[([^\]]+)\]') {
                $fillerLibrary = $Matches[1] -split ',' | ForEach-Object { $_.Trim().Trim('"').Trim("'") } | Where-Object { $_ -ne '' }
            }
        }
    }
    if ($fillerMin -ge 0 -and $fillerMax -gt 0 -and $fillerLibrary.Count -gt 0) {
        $draftRaw = Get-Content $DraftPath -Raw -Encoding UTF8
        $fillerTotal = 0
        foreach ($f in $fillerLibrary) {
            $escapedFiller = [regex]::Escape($f)
            $fillerTotal += ([regex]::Matches($draftRaw, "(?i)$escapedFiller")).Count
        }
        if ($fillerTotal -ge $fillerMin -and $fillerTotal -le $fillerMax) {
            Add-Result "Filler Count" "PASS" "$fillerTotal fillers (range: $fillerMin-$fillerMax)"
        }
        else {
            Add-Result "Filler Count" "FAIL" "$fillerTotal fillers (range: $fillerMin-$fillerMax)"
        }
    }
    else {
        Add-Result "Filler Count" "WARN" "Could not parse filler config from $VoiceDnaPath"
    }
}

# ============================================================
# CHECK 13a: Paragraph Sentence Count (configurable)
# CHECK 13b: Chain Sentence Count (configurable)
# ============================================================
$badSentParas = 0
$checkedParas = 0
$totalLongChains = 0
$badChains = @()

foreach ($pb in $allParagraphs) {
    $trimmed = $pb.Trim()
    if ($trimmed.Length -lt 10) { continue }
    $checkedParas++

    # Split paragraph into chains using newline
    $chains = @($trimmed -split '\r?\n' |
                ForEach-Object { $_.Trim() } |
                Where-Object { $_ -ne '' })

    # Count total sentences in the paragraph using the new rule
    $paraSentences = [regex]::Split($trimmed, "(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?$([char]0x2026)]+\s")
    $paraValidCount = Count-ValidSentences $paraSentences $cfgVeryShortThreshold

    if ($paraValidCount -lt $cfgSentPerParaMin -or $paraValidCount -gt $cfgSentPerParaMax) {
        $badSentParas++
    }

    # Check each chain
    foreach ($chain in $chains) {
        $chainSentences = [regex]::Split($chain, "(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?$([char]0x2026)]+\s")
        $chainValidCount = Count-ValidSentences $chainSentences $cfgVeryShortThreshold

        if ($chainValidCount -ge $cfgSentPerLongMin) {
            # Long chain
            $totalLongChains++
            if ($chainValidCount -gt $cfgSentPerLongMax) {
                $badChains += "Chain(${chainValidCount}sentences):TOO_LONG"
            }
        }
        elseif ($chainValidCount -gt 0) {
            # Normal chain
            if ($chainValidCount -lt $cfgSentPerNormalMin -or $chainValidCount -gt $cfgSentPerNormalMax) {
                $badChains += "Chain(${chainValidCount}sentences):OUT_OF_RANGE_$cfgSentPerNormalMin-$cfgSentPerNormalMax"
            }
        }
    }
}

# Report CHECK 13a
if ($badSentParas -eq 0) {
    Add-Result "Paragraph Sentences" "PASS" "All $checkedParas paragraphs within $cfgSentPerParaMin-$cfgSentPerParaMax sentences"
} else {
    Add-Result "Paragraph Sentences" "FAIL" "$badSentParas/$checkedParas paragraphs outside $cfgSentPerParaMin-$cfgSentPerParaMax range"
}

# Report CHECK 13b: Chain count
$chainSeverity = "FAIL"
if ($badChains.Count -eq 0) {
    Add-Result "Chain Sentences" "PASS" "All chains within configured ranges"
} else {
    Add-Result "Chain Sentences" $chainSeverity "$($badChains.Count) chain(s) out of range: $($badChains[0..2] -join ', ')..."
}

# Report CHECK 13c: Long chains per article
if ($totalLongChains -ge $cfgLongChainsMin -and $totalLongChains -le $cfgLongChainsMax) {
    Add-Result "Long Chain Count" "PASS" "$totalLongChains long chains (range: $cfgLongChainsMin-$cfgLongChainsMax)"
} else {
    Add-Result "Long Chain Count" $chainSeverity "$totalLongChains long chains (range: $cfgLongChainsMin-$cfgLongChainsMax)"
}

# ============================================================
# CHECK 14: Reference File Keys (chung minh Agent doc 3 file tham chieu)
# Ly do: Agent dung memory thay vi doc file vat ly writing-rules, anti-ai, english-blacklist.
# Logic: Doc FILE_KEY tu 3 ref file, doi chieu voi ref_keys comment trong draft.
# ============================================================
$refFilePaths = @{
    "writing-rules"     = ".agents/skills/voice-writer/references/writing-rules.md"
    "anti-ai"           = ".agents/skills/voice-writer/references/anti-ai-patterns.md"
    "english-blacklist" = ".agents/skills/voice-writer/references/english-blacklist.md"
}

$expectedRefKeys = @{}
foreach ($name in $refFilePaths.Keys) {
    $refPath = $refFilePaths[$name]
    if (Test-Path $refPath) {
        $refContent = Get-Content $refPath -Raw -Encoding UTF8
        if ($refContent -match '(?m)^> FILE_KEY:\s*(\S+)') {
            $expectedRefKeys[$name] = $Matches[1]
        }
    }
}

# Parse ref_keys comment tu draft
# Dung $draft (da khai bao o L43, global scope, -Raw -Encoding UTF8)
$actualRefKeys = @{}
if ($draft -match '<!--\s*ref_keys:\s*([^>]+)-->') {
    $keysPart = $Matches[1].Trim()
    foreach ($pair in $keysPart.Split(',')) {
        $pair = $pair.Trim()
        if ($pair -match '^([\w-]+)=(\S+)$') {
            $actualRefKeys[$Matches[1]] = $Matches[2]
        }
    }
}

$refKeysFail = $false
$pendingWarn = $false
foreach ($name in $refFilePaths.Keys) {
    $expected = $expectedRefKeys[$name]
    if (-not $expected) {
        $pendingWarn = $true
        continue
    }
    if ($expected -eq "PENDING") {
        $pendingWarn = $true
        continue
    }
    $actual = $actualRefKeys[$name]
    if ($actual -ne $expected) {
        $refKeysFail = $true
        break
    }
}

if ($pendingWarn) {
    Add-Result "Ref File Keys" "WARN" "FILE_KEY PENDING - generate-phase-key.ps1 NOT RUN. Run script before Phase 1."
}
elseif ($refKeysFail) {
    Add-Result "Ref File Keys" "FAIL" "ref_keys in draft mismatch FILE_KEY in reference files - Agent did not read physical files"
}
else {
    Add-Result "Ref File Keys" "PASS" "All 3 reference file keys verified"
}

# ============================================================
# OUTPUT REPORT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  DRAFT VALIDATION REPORT (Phase 5)"
Write-Host "========================================="
Write-Host ""

foreach ($r in $results) {
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}

Write-Host ""
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
if ($failCount -eq 0) {
    Write-Host "  Verdict: ALL OBJECTIVE CHECKS PASSED"
}
else {
    Write-Host "  Verdict: $failCount ISSUE(S) NEED FIXING"
}
Write-Host "========================================="
Write-Host ""

# Return exit code
exit $failCount
