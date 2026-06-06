# Phase 02: Validator Overhaul

**Tên file:** phase-02-validator-overhaul.md
**Last update:** 18/05/2026 22:16 (GMT+7)
**Vai trò:** Chi tiết refactor các script validation để đọc từ profile.
**Được sử dụng khi nào?:** Khi thực thi Phase 02.
**Output:** 2 file `.ps1` đã refactor.
**Tóm tắt logic hoạt động:** Refactor validate-draft.ps1, validate-outline.ps1 để đọc threshold từ active.json thay vì hardcode. Parse bằng structural markers (TITLE, SECTION, PARAGRAPH), quy tắc đếm câu mới, mode-aware severity (Auto=WARN, Thử nghiệm=FAIL).

Status: ✅ Complete
Dependencies: Phase 01 (profiles/default.json phải tồn tại)

> **Encoding Rule:** Khi sửa `validate-draft.ps1` và `validate-outline.ps1`, đảm bảo file `.ps1` chỉ chứa ASCII. Mọi chuỗi tiếng Việt chuyển vào `.json` hoặc thay bằng tiếng Anh. Xem Phase 01 Task 5.

---

## Objective

Refactor VĨNH VIỄN các script validation để:
1. Đọc threshold từ `profiles/active.json` (fallback `profiles/default.json` nếu active không tồn tại).
2. Parse nội dung theo 3 cấp: marker → dòng trống → xuống dòng.
3. Áp dụng quy tắc đếm câu mới (câu rất ngắn: 2 = 1).
4. Thêm check mới: sentences per chain (B5, B6, B7).

---

## Task 1: Refactor `validate-draft.ps1`

**File:** `.agents/skills/voice-writer/scripts/validate-draft.ps1`

### 1.1. Thêm đọc Profile ở đầu script

**Vị trí:** Sau dòng `$ErrorActionPreference = "Stop"` (L23), thêm block:

```powershell
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
$cfgSectionMarker = if ($profile) { $profile.section_separator.marker } else { "⁂" }
$cfgSectionBlankAbove = if ($profile) { $profile.section_separator.blank_lines_above } else { 1 }
$cfgSectionBlankBelow = if ($profile) { $profile.section_separator.blank_lines_below } else { 1 }
$cfgTitleInOutput = if ($profile) { $profile.output_elements.title } else { $false }
$cfgSectionHeadingInOutput = if ($profile) { $profile.output_elements.section_heading } else { $false }
$cfgParaHeadingInOutput = if ($profile) { $profile.output_elements.paragraph_heading } else { $false }
$cfgVeryShortThreshold = if ($profile) { $profile.very_short_sentence_threshold } else { 4 }
$cfgMode = if ($profile) { $profile.mode } else { "auto" }
```

### 1.2. Thêm hàm đếm câu mới

**Vị trí:** Sau block Helper `Add-Result` (sau L56), thêm:

```powershell
# --- Hàm đếm câu theo quy tắc mới ---
# Câu bình thường (>= threshold từ): đếm 1
# Câu rất ngắn (< threshold từ): cứ 2 câu = 1, 1 câu lẻ = 0
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
```

### 1.3. Thay đổi CHECK 1: Word Count

**Thêm (trước L71):** Strip tất cả structural markers trước khi đếm từ:
```powershell
# Strip structural markers (không đếm vào word count)
$draftBody = $draftBody -replace '<!--[^>]*-->', ''
$draftBody = $draftBody -replace '⁂', ''
$words = ($draftBody -split '\s+' | Where-Object { $_.Length -gt 0 }).Count
```

**Sau (L71):**
```powershell
if ($words -ge $cfgWordCountMin -and $words -le $cfgWordCountMax) {
```

**Tương tự L72 và L75:** thay `1500-1800` bằng `$cfgWordCountMin-$cfgWordCountMax` trong chuỗi detail.

### 1.4. Parse bằng Structural Markers (thay thế CHECK 7 + 8 + 9)

**Trước (L206–L234):** CHECK 7 (No Headings) + CHECK 8 (Paragraph Count) + CHECK 9 (Max Paragraph Length) sử dụng heuristic (dòng trống, regex heading).

**Sau:** Thay toàn bộ bằng marker-based deterministic parsing:

```powershell
# ============================================================
# PARSE: Tách nội dung bằng Structural Markers
# ============================================================
# Loại bỏ frontmatter
$bodyForParse = $draft -replace '(?s)^---.*?---\s*', ''
$bodyForParse = $bodyForParse.Trim()

# --- CHECK 7a: TITLE marker ---
if ($bodyForParse -match '<!--\s*TITLE:\s*(.+?)\s*-->') {
    Add-Result "Title Marker" "PASS" "Title: $($Matches[1])"
} else {
    Add-Result "Title Marker" "FAIL" "Thiếu <!-- TITLE: ... -->"
}

# --- CHECK 7b: SECTION markers (5 sections đúng thứ tự) ---
$expectedSections = @('Hook', 'Story', 'Deep Dive', 'Pivot', 'Closing')
$sectionMatches = [regex]::Matches($bodyForParse, '<!--\s*SECTION:\s*(.+?)\s*-->')
$foundSections = @($sectionMatches | ForEach-Object { $_.Groups[1].Value.Trim() })

if ($foundSections.Count -eq 5 -and ($foundSections -join ',') -eq ($expectedSections -join ',')) {
    Add-Result "Section Markers" "PASS" "5 sections đúng thứ tự"
} else {
    Add-Result "Section Markers" "FAIL" "Expect: $($expectedSections -join ', '). Found: $($foundSections -join ', ')"
}

# --- CHECK 7c: SECTION_HEADING cho mỗi section ---
$sectionHeadings = [regex]::Matches($bodyForParse, '<!--\s*SECTION_HEADING:\s*(.+?)\s*-->')
if ($sectionHeadings.Count -eq 5) {
    Add-Result "Section Headings" "PASS" "5/5 section headings"
} else {
    Add-Result "Section Headings" "FAIL" "$($sectionHeadings.Count)/5 section headings"
}

# --- CHECK 7d: PARAGRAPH markers (số thứ tự liên tục 1→N) ---
$paraMatches = [regex]::Matches($bodyForParse, '<!--\s*PARAGRAPH:\s*(\d+)\s*-->')
$paraNumbers = @($paraMatches | ForEach-Object { [int]$_.Groups[1].Value })
$paraOK = $true
for ($i = 0; $i -lt $paraNumbers.Count; $i++) {
    if ($paraNumbers[$i] -ne ($i + 1)) { $paraOK = $false; break }
}
if ($paraOK -and $paraNumbers.Count -gt 0) {
    Add-Result "Paragraph Markers" "PASS" "$($paraNumbers.Count) paragraphs, số thứ tự 1→$($paraNumbers.Count)"
} else {
    Add-Result "Paragraph Markers" "FAIL" "Số thứ tự không liên tục hoặc thiếu: $($paraNumbers -join ', ')"
}

# --- CHECK 7e: PARAGRAPH_HEADING cho mỗi paragraph ---
$paraHeadings = [regex]::Matches($bodyForParse, '<!--\s*PARAGRAPH_HEADING:\s*(.+?)\s*-->')
if ($paraHeadings.Count -eq $paraNumbers.Count) {
    Add-Result "Paragraph Headings" "PASS" "$($paraHeadings.Count)/$($paraNumbers.Count) paragraph headings"
} else {
    Add-Result "Paragraph Headings" "FAIL" "$($paraHeadings.Count)/$($paraNumbers.Count) paragraph headings"
}

# ============================================================
# PARSE: Tách nội dung (strip markers) để đếm từ/câu
# ============================================================
$bodyClean = $bodyForParse -replace '<!--[^>]*-->', ''
$bodyClean = $bodyClean -replace '⁂', ''
$bodyClean = $bodyClean.Trim()

# Cấp 1: Tách section bằng ⁂
$sections = @($bodyForParse -split [regex]::Escape('⁂') |
              ForEach-Object { $_.Trim() } |
              Where-Object { $_ -ne '' })

# Cấp 2: Tách paragraph trong mỗi section (bằng PARAGRAPH marker)
$allParagraphs = @()
foreach ($section in $sections) {
    # Strip markers từ section content, tách bằng PARAGRAPH marker
    $paraBlocks = @($section -split '<!--\s*PARAGRAPH:\s*\d+\s*-->' |
                    ForEach-Object { $_ -replace '<!--[^>]*-->', '' } |
                    ForEach-Object { $_.Trim() } |
                    Where-Object { $_ -ne '' })
    $allParagraphs += $paraBlocks
}

# Cấp 3: Tách chuỗi câu (Chain) trong mỗi đoạn bằng xuống dòng
# (Xử lý ở CHECK 13b bên dưới)

# CHECK 8: Section Count (đã check ở 7b, giữ lại để backward compatible)
# (Bỏ qua — đã cover bởi CHECK 7b)

# CHECK 9: Max Paragraph Length (dùng nội dung đã strip marker)
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
```

### 1.5. Thay thế CHECK 13: Paragraph Sentence Count + Thêm Chain Checks

**Trước (L329–L358):** CHECK 13 kiểm tra 3-5 câu/paragraph, bỏ qua câu < 4 từ.

**Sau:** Thay thế toàn bộ bằng:

```powershell
# ============================================================
# CHECK 13a: Paragraph Sentence Count (configurable)
# CHECK 13b: Chain Sentence Count (NEW — B5, B6, B7)
# ============================================================
$badSentParas = 0
$checkedParas = 0
$totalLongChains = 0
$badChains = @()

foreach ($pb in $allParagraphs) {
    $trimmed = $pb.Trim()
    if ($trimmed.Length -lt 10) { continue }
    $checkedParas++

    # Tách đoạn thành chuỗi câu (chains) bằng xuống dòng
    $chains = @($trimmed -split '\r?\n' |
                ForEach-Object { $_.Trim() } |
                Where-Object { $_ -ne '' })

    # Đếm tổng câu trong đoạn (dùng quy tắc mới)
    $paraSentences = [regex]::Split($trimmed, '(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?…]+\s')
    $paraValidCount = Count-ValidSentences $paraSentences $cfgVeryShortThreshold

    if ($paraValidCount -lt $cfgSentPerParaMin -or $paraValidCount -gt $cfgSentPerParaMax) {
        $badSentParas++
    }

    # Kiểm tra từng chain
    foreach ($chain in $chains) {
        $chainSentences = [regex]::Split($chain, '(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?…]+\s')
        $chainValidCount = Count-ValidSentences $chainSentences $cfgVeryShortThreshold

        if ($chainValidCount -ge $cfgSentPerLongMin) {
            # Đây là chuỗi dài
            $totalLongChains++
            if ($chainValidCount -gt $cfgSentPerLongMax) {
                $badChains += "Chain(${chainValidCount}cau):QUA_DAI"
            }
        }
        elseif ($chainValidCount -gt 0) {
            # Chuỗi bình thường
            if ($chainValidCount -lt $cfgSentPerNormalMin -or $chainValidCount -gt $cfgSentPerNormalMax) {
                $badChains += "Chain(${chainValidCount}cau):NGOAI_KHOANG_$cfgSentPerNormalMin-$cfgSentPerNormalMax"
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

# Report CHECK 13b: Chain count (fix V4: mode-aware severity)
$chainSeverity = if ($cfgMode -eq "auto") { "WARN" } else { "FAIL" }
if ($badChains.Count -eq 0) {
    Add-Result "Chain Sentences" "PASS" "All chains within configured ranges"
} else {
    Add-Result "Chain Sentences" $chainSeverity "$($badChains.Count) chain(s) ngoài khoảng: $($badChains[0..2] -join ', ')..."
}

# Report CHECK 13c: Long chains per article (fix V4: mode-aware severity)
if ($totalLongChains -ge $cfgLongChainsMin -and $totalLongChains -le $cfgLongChainsMax) {
    Add-Result "Long Chain Count" "PASS" "$totalLongChains long chains (range: $cfgLongChainsMin-$cfgLongChainsMax)"
} else {
    Add-Result "Long Chain Count" $chainSeverity "$totalLongChains long chains (range: $cfgLongChainsMin-$cfgLongChainsMax)"
}
```

**Lưu ý (fix V4):**
- `$cfgMode = "auto"` → CHECK 13b và 13c dùng **WARN** (không block pipeline, vì chain là khái niệm mới, draft cũ chưa tuân thủ).
- `$cfgMode = "basic"` hoặc `"advanced"` → dùng **FAIL** (user đã chủ động thiết lập B5/B6/B7).
- `Add-Result` cần cập nhật: `WARN` không tính vào `$failCount` (đã có sẵn ở helper L55 comment: `# WARN: khong tinh vao failCount`).

### 1.7. Cập nhật biến `$paragraphs` cho các check khác

CHECK 4 (Staccato) hiện dùng global sentence split — không bị ảnh hưởng bởi thay đổi paragraph parsing.

CHECK 10 (Unique Word Ratio) dùng toàn bộ draft — không bị ảnh hưởng.

Biến `$paragraphs` cũ (L209) được dùng bởi CHECK 8, 9, 13. Sau refactor, thay bằng `$allParagraphs` và `$sections`. Xóa dòng `$paragraphs = @(($draft -split '\r?\n\s*\r?\n') | ...)` (L209) và thay mọi tham chiếu `$paragraphs` bằng `$allParagraphs`.

---

## Task 2: Refactor `validate-outline.ps1`

**File:** `.agents/skills/structure-designer/scripts/validate-outline.ps1`

### 2.1. Thêm đọc Profile

**Vị trí:** Sau `$ErrorActionPreference = "Stop"` (L20), thêm block đọc profile tương tự Task 1.1, chỉ cần extract:
```powershell
$cfgWordCountMin = if ($profile) { $profile.word_count_total.min } else { 1500 }
$cfgWordCountMax = if ($profile) { $profile.word_count_total.max } else { 1800 }
```

### 2.2. Thay đổi CHECK 1

**Trước (L44):**
```powershell
if ($totalAllocated -ge 1500 -and $totalAllocated -le 1800) {
```

**Sau:**
```powershell
if ($totalAllocated -ge $cfgWordCountMin -and $totalAllocated -le $cfgWordCountMax) {
```

**Tương tự L45, L48:** thay chuỗi detail `1500-1800` bằng `$cfgWordCountMin-$cfgWordCountMax`.

---

## Task 3: validate-hook.ps1 — KHÔNG thay đổi

Hook word count (≤ 15 từ) không nằm trong danh sách biến thử nghiệm. File này giữ nguyên.

---

## Files to Modify

| File | Scope thay đổi |
|------|----------------|
| `validate-draft.ps1` | Major: đọc profile, parse 3 cấp, hàm đếm câu mới, 3 check mới |
| `validate-outline.ps1` | Minor: đọc profile, thay 2 giá trị hardcode |

## Test Criteria

- [ ] `validate-draft.ps1` chạy với `profiles/default.json` → kết quả GIỐNG HỆT phiên bản cũ (regression test).
- [ ] Thay `profiles/active.json` với `sentences_per_paragraph: {min:2, max:7}` → check 13a dùng khoảng 2-7.
- [ ] Draft có marker `⁂` → script tách đúng sections.
- [ ] Draft không có marker → fallback tách bằng dòng trống.
- [ ] Câu "Đúng vậy. Không sai. Câu dài ở đây nè bạn ơi." → Count-ValidSentences = 2 (2 short = 1, 1 normal = 1).
- [ ] `validate-outline.ps1` chạy với profile `word_count_total: {min:1200, max:1500}` → check khoảng mới.

---

Next Phase: `phase-03-prompt-patching.md`
