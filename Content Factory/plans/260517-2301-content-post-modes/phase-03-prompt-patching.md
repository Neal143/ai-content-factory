# Phase 03: Prompt Patching

**Tên file:** phase-03-prompt-patching.md
**Last update:** 17/05/2026 23:01 (GMT+7)
**Vai trò:** Bảng ánh xạ chính xác từng vị trí cần patch trong prompt files.
**Được sử dụng khi nào?:** Khi code logic patch trong apply-profile.ps1.
**Output:** Logic patch hoàn chỉnh trong apply-profile.ps1.
**Tóm tắt logic hoạt động:** Liệt kê chính xác string cần find/replace trong mỗi file prompt, map với key trong profile JSON.

Status: ⬜ Pending
Dependencies: Phase 01

---

## Objective

1. **Sửa vĩnh viễn** voice-writer/SKILL.md: thay "dòng trống" bằng marker `⁂` giữa các section (nền tảng cho toàn bộ kiến trúc marker).
2. Định nghĩa bảng patch chính xác cho `apply-profile.ps1 -Action patch`. Mỗi entry gồm: file target, string gốc (find), string thay thế (replace, lấy từ profile).

---

## Task 0: Sửa vĩnh viễn `voice-writer/SKILL.md` — Structural Markers

> ⚠️ **Đây KHÔNG phải patch tạm. Đây là thay đổi VĨNH VIỄN, sửa 1 lần, không restore.**

**File:** `.agents/skills/voice-writer/SKILL.md`

### Task 0a: Thêm instruction Structural Markers (thay thế L56)

**Vị trí:** L56 (trong bước 3.1)

**Trước:**
```
Mỗi section kết thúc bằng 1 dòng trống
```

**Sau:**
```
LUÔN viết đầy đủ structural markers (dạng HTML comment). Tất cả marker KHÔNG được đếm vào word count.

**Markers bắt buộc:**
- Dòng đầu tiên: `<!-- TITLE: [Tiêu đề bài viết] -->`
- Trước mỗi section: `<!-- SECTION: [Tên section] -->` (Hook/Story/Deep Dive/Pivot/Closing)
- Sau SECTION marker: `<!-- SECTION_HEADING: [Heading section — AI tự đặt] -->`
- Trước mỗi đoạn: `<!-- PARAGRAPH: [Số thứ tự đoạn — đánh số liên tục 1→N trên toàn bài] -->`
- Sau PARAGRAPH marker: `<!-- PARAGRAPH_HEADING: [Heading đoạn — AI tự đặt] -->`
- Kết thúc mỗi section (trừ section cuối): marker `⁂` trên 1 dòng riêng, cách dòng trên 1 dòng trống, cách dòng dưới 1 dòng trống
```

**Lý do:** Structural markers giúp:
- Validator parse cấu trúc deterministic, không đoán (Phase 02)
- Format-agent strip/giữ title, heading, marker theo profile (Phase 04)
- Không thay đổi theo chế độ — voice-writer LUÔN viết tất cả, format-agent quyết định output cuối

### Task 0b: Thống nhất keyword `Phần` → `Section` trong `structure-designer/SKILL.md`

> ⚠️ **Đây KHÔNG phải patch tạm. Đây là thay đổi VĨNH VIỄN, sửa 1 lần.**

**File:** `.agents/skills/structure-designer/SKILL.md`

| Dòng | Trước | Sau | Ghi chú |
|------|-------|-----|---------|
| L3 | `outline 5 phần` | `outline 5 sections` | Frontmatter description |
| L18 | `Outline 5 Phần Bắt Buộc` | `Outline 5 Sections Bắt Buộc` | Heading |
| L21 | `\| Phần \|` | `\| Section \|` | Table header |

**KHÔNG sửa:** L13 `Hook 3 phần` — đây là tên artifact (hook gồm 3 thành phần), không liên quan tới 5 section.

> **Tác động tới bảng patch:** Không ảnh hưởng. P07–P13 tham chiếu nội dung cell bảng (`Phân bổ tổng`, `80-120`, `200-300`...), không tham chiếu header `Phần`.

---

## Bảng Patch

### File 1: `voice-writer/SKILL.md`

| # | Dòng | String gốc (find) — COPY CHÍNH XÁC TỪ FILE | String thay thế (từ profile) | Biến profile |
|---|------|-------------------|------------------------------|--------------|
| P01 | L40 | `TUYỆT ĐỐI KHÔNG viết toàn bộ 1500-1800 từ trong 1 lượt.` | `TUYỆT ĐỐI KHÔNG viết toàn bộ {min}-{max} từ trong 1 lượt.` | `word_count_total` |
| P02 | L60 | `tổng word count (1500-1800).` | `tổng word count ({min}-{max}).` | `word_count_total` |
| P03 | L76 | `3-5 câu/paragraph. Không viết paragraph 1 câu (trừ Hook câu đầu tiên). Không viết paragraph > 5 câu` | `{min}-{max} câu/paragraph. Không viết paragraph 1 câu (trừ Hook câu đầu tiên). Không viết paragraph > {max} câu` | `sentences_per_paragraph` |
| ~~P04~~ | — | ~~LOẠI BỎ~~ | Chuyển sang Phase 04 (format-agent) | `section_separator` |

> **Lý do loại P04 khỏi bảng voice-writer:** Voice-writer LUÔN viết `⁂` (xem Task 0 ở trên). Section separator không được patch ở đây. Thay vào đó, `apply-profile.ps1` patch `format-agent/SKILL.md` với instruction cụ thể về cách thay `⁂` trong output cuối (xem Phase 04 Task 2). Cách này giúp:
> - Validator luôn parse section bằng `⁂` — nhất quán, không rủi ro
> - Ít vị trí patch hơn → ít lỗi hơn
> - Tách rõ: nội dung (voice-writer) vs trình bày (format-agent)

**Bổ sung khi mode = advanced (P04a):** Nếu `section_headings.enabled = true`, thêm instruction vào sau dòng L54:
```
Mỗi section bắt đầu bằng heading ngắn (## Tên Section). Heading cách dòng trên {blank_lines_above} dòng trống, cách dòng dưới {blank_lines_below} dòng trống.
```

### File 2: `voice-writer/references/writing-rules.md`

| # | Dòng | String gốc (find) — COPY CHÍNH XÁC TỪ FILE | String thay thế (từ profile) | Biến profile |
|---|------|-------------------|------------------------------|--------------|
| ~~P05~~ | — | ~~LOẠI BỎ~~ | Đã sửa vĩnh viễn: "Mỗi cụm 3-5 câu" → "Mỗi đoạn". Không phải biến thử nghiệm | — |
| P06 | L59 | `Tổng bài viết: 1500-1800 từ. KHÔNG quá 1800 từ.` | `Tổng bài viết: {min}-{max} từ. KHÔNG quá {max} từ.` | `word_count_total` |

### File 3: `structure-designer/SKILL.md`

| # | Dòng | String gốc (find) — COPY CHÍNH XÁC TỪ FILE | String thay thế (từ profile) | Biến profile |
|---|------|-------------------|------------------------------|--------------|
| P07 | L19 | `Phân bổ tổng 1500-1800 từ (KHÔNG quá 1800):` | `Phân bổ tổng {min}-{max} từ (KHÔNG quá {max}):` | `word_count_total` |
| P08 | L23 | `| 80-120 | Value Promise mạnh nhất` | `| {min}-{max} | Value Promise mạnh nhất` | `word_count_per_section.Hook` |
| P09 | — | Giữ nguyên | — | — |
| P10 | L24 | `| 200-300 | Insight Identification` | `| {min}-{max} | Insight Identification` | `word_count_per_section.Story` |
| P11 | L25 | `| 700-900 | Pain Avoidance xen Value Promise` | `| {min}-{max} | Pain Avoidance xen Value Promise` | `word_count_per_section."Deep Dive"` |
| P12 | L26 | `| 200-300 | Social Proof + Value Promise` | `| {min}-{max} | Social Proof + Value Promise` | `word_count_per_section.Pivot` |
| P13 | L27 | `| 100-150 | Result Preview / Personal Commitment` | `| {min}-{max} | Result Preview / Personal Commitment` | `word_count_per_section.Closing` |

> ⚠️ **P08–P13:** String mở rộng thêm context (cell tiếp theo trong bảng) để tránh match nhầm — vì `200-300` xuất hiện ở cả Story lẫn Pivot.

**Lưu ý P08–P13:** Chỉ patch khi mode = advanced (A5). Với mode basic và auto, giữ nguyên.

**Lưu ý P09:** Số câu mỗi phần trong structure-designer (1-3, 3-5, 3-5, 2-4) là quy tắc outline, KHÔNG phải biến thử nghiệm. Voice-writer mới là nơi enforce số câu/đoạn. Không patch ở đây.

### File 4: `hook-engineer/SKILL.md`

**KHÔNG patch.** Hook word count (≤ 15 từ) nằm ngoài scope biến thử nghiệm.

### File 5: `qa-checker/SKILL.md`

**KHÔNG patch.** QA scoring criteria và sting test (7-12 từ) nằm ngoài scope.

---

## Logic Patch trong apply-profile.ps1

```powershell
function Invoke-Patch {
    param([string]$FilePath, [string]$Find, [string]$Replace)

    if (-not (Test-Path $FilePath)) {
        Write-Host "WARNING: File not found: $FilePath"
        return
    }

    # Backup nếu chưa có
    $bakPath = "$FilePath.bak"
    if (-not (Test-Path $bakPath)) {
        Copy-Item $FilePath $bakPath
    }

    $content = Get-Content $FilePath -Raw -Encoding UTF8
    if ($content.Contains($Find)) {
        $content = $content.Replace($Find, $Replace)
        Set-Content $FilePath $content -Encoding UTF8 -NoNewline
        Write-Host "  PATCHED: $FilePath"
    } else {
        Write-Host "  WARNING: Pattern not found in $FilePath: '$($Find.Substring(0, [Math]::Min(50, $Find.Length)))...'"
    }
}
```

**Danh sách patch khi Action = "patch":**

```powershell
# Đọc profile
$p = Get-Content "profiles/active.json" -Raw | ConvertFrom-Json

# --- voice-writer/SKILL.md ---
$vwPath = ".agents/skills/voice-writer/SKILL.md"
Invoke-Patch $vwPath `
    "TUYỆT ĐỐI KHÔNG viết toàn bộ 1500-1800 từ trong 1 lượt." `
    "TUYỆT ĐỐI KHÔNG viết toàn bộ $($p.word_count_total.min)-$($p.word_count_total.max) từ trong 1 lượt."

Invoke-Patch $vwPath `
    "tổng word count (1500-1800)." `
    "tổng word count ($($p.word_count_total.min)-$($p.word_count_total.max))."

Invoke-Patch $vwPath `
    "3-5 câu/paragraph. Không viết paragraph 1 câu (trừ Hook câu đầu tiên). Không viết paragraph > 5 câu" `
    "$($p.sentences_per_paragraph.min)-$($p.sentences_per_paragraph.max) câu/paragraph. Không viết paragraph 1 câu (trừ Hook câu đầu tiên). Không viết paragraph > $($p.sentences_per_paragraph.max) câu"

# --- writing-rules.md ---
$wrPath = ".agents/skills/voice-writer/references/writing-rules.md"
Invoke-Patch $wrPath `
    "Mỗi cụm 3-5 câu PHẢI có ít nhất 1 value signal." `
    "Mỗi cụm $($p.sentences_per_normal_chain.min)-$($p.sentences_per_normal_chain.max) câu PHẢI có ít nhất 1 value signal."

Invoke-Patch $wrPath `
    "Tổng bài viết: 1500-1800 từ. KHÔNG quá 1800 từ." `
    "Tổng bài viết: $($p.word_count_total.min)-$($p.word_count_total.max) từ. KHÔNG quá $($p.word_count_total.max) từ."

# --- format-agent/SKILL.md (P04 — section separator output) ---
$faPath = ".agents/skills/format-agent/SKILL.md"
$defaultMarkerInstruction = "Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng 2 dòng trống"
if ($p.section_separator.marker) {
    $newInstruction = "Thay mỗi dòng chứa `⁂` bằng marker $($p.section_separator.marker) cách dòng trên $($p.section_separator.blank_lines_above) dòng trống, cách dòng dưới $($p.section_separator.blank_lines_below) dòng trống"
} else {
    $totalBlanks = $p.section_separator.blank_lines_above + $p.section_separator.blank_lines_below
    $newInstruction = "Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng $totalBlanks dòng trống"
}
Invoke-Patch $faPath $defaultMarkerInstruction $newInstruction

# --- structure-designer/SKILL.md (chỉ khi advanced) ---
if ($p.mode -eq "advanced") {
    $sdPath = ".agents/skills/structure-designer/SKILL.md"
    Invoke-Patch $sdPath `
        "Phân bổ tổng 1500-1800 từ (KHÔNG quá 1800):" `
        "Phân bổ tổng $($p.word_count_total.min)-$($p.word_count_total.max) từ (KHÔNG quá $($p.word_count_total.max)):"
    # ... patch word count per section (P08–P13)
}
```

---

## Bổ sung prompt mới cho chain (append vào voice-writer)

Khi patch `voice-writer/SKILL.md`, **append** instruction sau bảng constraint (L76):
```
- Mỗi chuỗi câu không xuống dòng (đoạn nhỏ) nên có {normal_min}-{normal_max} câu. Được phép tối đa {long_max_count} chuỗi dài ({long_min}-{long_max} câu) trong toàn bài.
- {long_chain_context}
```

**Bổ sung cho B4 (chain separator):** Nếu `paragraph_separator` hoặc `chain_separator` khác mặc định, append thêm:
```
- Giữa các chuỗi câu trong đoạn: {B4.marker nếu có} cách dòng trên {B4.above} dòng trống, cách dòng dưới {B4.below} dòng trống.
```

---

## Test Criteria

- [ ] Chạy `apply-profile.ps1 -Mode default -Action patch` → các file prompt giữ nguyên giá trị (vì default = giá trị gốc).
- [ ] Chạy `apply-profile.ps1 -Mode basic -Action patch` với `word_count_total: {min:1200, max:1500}` → `voice-writer/SKILL.md` chứa "1200-1500".
- [ ] Chạy `apply-profile.ps1 -Action restore` → các file `.bak` được khôi phục, `.bak` bị xóa.
- [ ] File `.bak` không tồn tại → restore skip, không lỗi.

---

Next Phase: `phase-04-format-agent.md`
