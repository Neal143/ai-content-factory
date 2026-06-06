# Phase 04: Format Agent & Structural Markers

**Tên file:** phase-04-format-agent.md
**Last update:** 18/05/2026 22:20 (GMT+7)
**Vai trò:** Cập nhật format-agent để xử lý toàn bộ structural markers trong output cuối.
**Được sử dụng khi nào?:** Khi thực thi Phase 04.
**Output:** format-agent/SKILL.md và validate-format.ps1 đã cập nhật.
**Tóm tắt logic hoạt động:** Voice-writer LUÔN viết đầy đủ structural markers. Format-agent strip/giữ dựa trên profile. `apply-profile.ps1` patch SKILL.md với instruction cụ thể. `validate-format.ps1` đọc `active.json` để strip markers khi so sánh content integrity.

Status: ⬜ Pending
Dependencies: Phase 01 (profile phải tồn tại), Phase 03 (structural markers trong draft)

> **Encoding Rule:** Khi sửa `validate-format.ps1`, đảm bảo file `.ps1` chỉ chứa ASCII. Mọi chuỗi tiếng Việt chuyển vào `.json` hoặc thay bằng tiếng Anh. Xem Phase 01 Task 5.

---

## Objective

1. Sửa 1 lần `format-agent/SKILL.md`: thêm logic strip/giữ structural markers (giá trị mặc định Auto).
2. Thêm patch entries vào bảng patch Phase 03: `apply-profile.ps1` patch instruction khi Thử nghiệm.
3. Cập nhật `validate-format.ps1` (.ps1 → đọc `active.json`) để content integrity check không lệch.

---

## Task 1: Sửa 1 lần `format-agent/SKILL.md` (giá trị mặc định Auto)

**File:** `.agents/skills/format-agent/SKILL.md`

**Vị trí:** L50–L53 (bước 3, danh sách strip cho file posts/).

**Lý do thiết kế:** Structural markers cùng bản chất với `execution_key` và `ref_keys` — element kỹ thuật pipeline, không phải nội dung bài viết. Strip chúng không vi phạm FATAL RULE.

**Trước (L50–L53):**
```markdown
   - `output/posts/[YYYY-MM-DD]-[topic-slug].md`
     Strip 2 dòng comment kỹ thuật (dùng string replace, KHÔNG chỉnh nội dung khác):
     - `<!-- execution_key: ... -->`
     - `<!-- ref_keys: ... -->`
```

**Sau (giá trị mặc định Auto — sẽ bị patch khi Thử nghiệm):**
```markdown
   - `output/posts/[YYYY-MM-DD]-[topic-slug].md`
     Strip/format structural markers (dùng string replace, KHÔNG chỉnh nội dung khác):
     - `<!-- execution_key: ... -->` → Xóa
     - `<!-- ref_keys: ... -->` → Xóa
     - `<!-- TITLE: ... -->` → Xóa
     - `<!-- SECTION: ... -->` → Xóa (luôn xóa — đây là tên kỹ thuật, không phải heading)
     - `<!-- SECTION_HEADING: ... -->` → Xóa
     - `<!-- PARAGRAPH: N -->` → Xóa (luôn xóa — đây là số thứ tự kỹ thuật)
     - `<!-- PARAGRAPH_HEADING: ... -->` → Xóa
     - Marker `⁂`: Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng 2 dòng trống
```

---

## Task 2: Patch entries cho format-agent/SKILL.md

Khi user chọn Thử nghiệm, `apply-profile.ps1` **patch trực tiếp** các dòng instruction trong `format-agent/SKILL.md`:

### P04: Section separator (B1)
| String gốc (find) | Biến profile |
|-----|-----|
| `Thay mỗi dòng chứa \`⁂\` (và dòng trống bao quanh) bằng 2 dòng trống` | `section_separator` |

**Logic tạo string thay thế:**
```
Nếu section_separator.marker có giá trị (VD: "---"):
  → "Thay mỗi dòng chứa ⁂ bằng marker --- cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống"

Nếu section_separator.marker rỗng:
  → "Thay mỗi dòng chứa ⁂ (và dòng trống bao quanh) bằng {above + below} dòng trống"
```

### P15: Title (B8)
| String gốc (find) | Biến profile |
|-----|-----|
| `` `<!-- TITLE: ... -->` → Xóa `` | `output_elements.title` |

**Logic:** Nếu `title = true` → patch thành `` `<!-- TITLE: ... -->` → Giữ lại, format thành `# [Title]` ``

### P16: Section heading (B9)
| String gốc (find) | Biến profile |
|-----|-----|
| `` `<!-- SECTION_HEADING: ... -->` → Xóa `` | `output_elements.section_heading` |

**Logic:** Nếu `section_heading = true` → patch thành `` `<!-- SECTION_HEADING: ... -->` → Giữ lại, format thành `## [Heading]` cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống ``

### P17: Paragraph heading (B10)
| String gốc (find) | Biến profile |
|-----|-----|
| `` `<!-- PARAGRAPH_HEADING: ... -->` → Xóa `` | `output_elements.paragraph_heading` |

**Logic:** Nếu `paragraph_heading = true` → patch thành `` `<!-- PARAGRAPH_HEADING: ... -->` → Giữ lại, format thành `### [Heading]` cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống ``

### P18: Paragraph separator (B2)
Mặc định các đoạn cách nhau 1 dòng trống (sau khi strip PARAGRAPH marker). Nếu user muốn khác:

| String gốc (find) | Biến profile |
|-----|-----|
| *(Append — không replace)* | `paragraph_separator` |

**Logic:** Nếu `paragraph_separator.marker` có giá trị hoặc spacing ≠ mặc định → Append instruction: `Giữa các đoạn: [marker] cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống`

---

## Task 3: Cập nhật `validate-format.ps1` (đọc active.json — vĩnh viễn)

**File:** `.agents/skills/format-agent/scripts/validate-format.ps1`

**Vị trí:** CHECK 6 Content Integrity (L152–L181).

**Thay đổi:**
Trước khi so sánh, strip TẤT CẢ structural markers khỏi CẢ HAI files để so sánh thuần nội dung.

**Trước (L159–L163):**
```powershell
$sourceContent = Get-Content $SourceDraftPath -Raw -Encoding UTF8
$sourceWords = ($sourceContent -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

$finalBody = $draft -replace '(?s)^---.*?---\s*', ''
$finalWords = ($finalBody -split '\s+' | Where-Object { $_.Length -gt 0 }).Count
```

**Sau:**
```powershell
$sourceContent = Get-Content $SourceDraftPath -Raw -Encoding UTF8
# Strip TẤT CẢ structural markers trước khi đếm
$sourceClean = $sourceContent -replace '⁂', '' -replace '<!--[^>]*-->', ''
$sourceWords = ($sourceClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count

$finalBody = $draft -replace '(?s)^---.*?---\s*', ''
$finalClean = $finalBody -replace '<!--[^>]*-->', ''
$finalWords = ($finalClean -split '\s+' | Where-Object { $_.Length -gt 0 }).Count
```

---

## Files to Modify

| File | Scope thay đổi |
|------|----------------|
| `format-agent/SKILL.md` | Sửa 1 lần: thêm strip/format logic cho tất cả structural markers |
| `format-agent/SKILL.md` | Patch tạm: P04 (⁂), P15 (title), P16 (section heading), P17 (paragraph heading), P18 (paragraph separator) |
| `validate-format.ps1` | Refactor vĩnh viễn: strip tất cả markers trước content integrity check |

## Test Criteria

- [ ] Draft có đầy đủ markers → output cuối (Auto) không chứa bất kỳ marker nào, chỉ thuần nội dung.
- [ ] Draft + profile `title=true, section_heading=true` → output cuối có `# Title` và `## Heading`.
- [ ] Draft + profile `paragraph_heading=true` → output cuối có `### Heading` cho mỗi đoạn.
- [ ] Content integrity check PASS (delta ≤ 2%) khi so sánh draft có markers vs final không có markers.
- [ ] Marker `⁂` → thay bằng separator theo profile (dòng trống hoặc marker khác).

---

Next Phase: `phase-05-integration.md`
