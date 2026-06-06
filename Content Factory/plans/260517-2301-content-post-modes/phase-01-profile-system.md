# Phase 01: Profile System

**Tên file:** phase-01-profile-system.md
**Last update:** 19/05/2026 06:17 (GMT+7)
**Vai trò:** Chi tiết thiết kế và triển khai hệ thống Profile.
**Được sử dụng khi nào?:** Khi thực thi Phase 01.
**Output:** 2 file: `profiles/default.json` + `.agents/scripts/apply-profile.ps1`
**Tóm tắt logic hoạt động:** Tạo file config mặc định và script quản lý profile (validate, patch prompt, restore). Agent hỏi user qua chat và tạo active.json — script KHÔNG interactive.

Status: ✅ Complete
Dependencies: Không

---

## Objective

Tạo hệ thống Profile gồm:
1. File `profiles/default.json` — chứa tất cả giá trị mặc định (= giá trị hardcode hiện tại).
2. Script `apply-profile.ps1` — **không interactive** — chỉ validate JSON, patch prompt files, restore.

**Phân tách vai trò (fix V1):**
- **Agent (AI):** Hỏi user qua chat, thu thập câu trả lời, tạo `profiles/active.json`.
- **Script:** Validate active.json (ràng buộc R1–R8), patch prompt files, restore.

---

## Task 1: Tạo `profiles/default.json`

**Vị trí:** `Content Factory/profiles/default.json`

**Nội dung chính xác:**

```json
{
  "_meta": {
    "description": "Format Profile — Cấu hình cấu trúc bài viết cho pipeline content-post",
    "version": "1.0",
    "last_update": "17/05/2026"
  },

  "mode": "auto",

  "section_separator": {
    "marker": "⁂",
    "blank_lines_above": 1,
    "blank_lines_below": 1
  },

  "paragraph_separator": {
    "marker": "",
    "blank_lines_above": 1,
    "blank_lines_below": 0
  },

  "chain_separator": {
    "marker": "",
    "blank_lines_above": 0,
    "blank_lines_below": 0
  },

  "sentences_per_paragraph": {
    "min": 3,
    "max": 5
  },

  "sentences_per_normal_chain": {
    "min": 1,
    "max": 2
  },

  "sentences_per_long_chain": {
    "min": 3,
    "max": 5
  },

  "long_chains_per_article": {
    "min": 3,
    "max": 5
  },

  "long_chain_context": "Sử dụng chuỗi câu dài khi cần tạo độ sâu cảm xúc hoặc dẫn dắt lập luận phức tạp (thường ở phần Story hoặc Deep Dive).",

  "output_elements": {
    "title": false,
    "section_heading": false,
    "paragraph_heading": false
  },

  "section_heading_spacing": {
    "blank_lines_above": 1,
    "blank_lines_below": 0
  },

  "paragraph_heading_spacing": {
    "blank_lines_above": 1,
    "blank_lines_below": 0
  },

  "word_count_total": {
    "min": 1500,
    "max": 1800
  },

  "word_count_per_section": {
    "Hook": { "min": 80, "max": 120 },
    "Story": { "min": 200, "max": 300 },
    "Deep Dive": { "min": 700, "max": 900 },
    "Pivot": { "min": 200, "max": 300 },
    "Closing": { "min": 100, "max": 150 }
  },

  "word_count_per_paragraph": {
    "max": 400
  },

  "very_short_sentence_threshold": 4
}
```

**Ghi chú:**
- **`mode` (fix V4):** Field mới. Giá trị: `"auto"`, `"basic"`, `"advanced"`. Script validator dùng field này để quyết định severity: `auto` → chain checks là WARN, `basic`/`advanced` → FAIL.
- `sentences_per_long_chain` và `long_chains_per_article`: Có thể là `null` (chưa cấu hình). R4/R5 tự động skip khi null. Khi user set giá trị, R4/R5 sẽ validate.
- `long_chain_context`: Mô tả ngữ nghĩa, chỉ patch vào prompt, không dùng trong script.
- **`output_elements` (B8-B10):** Quyết định title/heading có trong output cuối không. Voice-writer LUÔN viết tất cả marker. Format-agent strip/giữ dựa trên giá trị này.
- **`section_heading_spacing`, `paragraph_heading_spacing` (A2-A3):** Chỉ có ý nghĩa khi `output_elements.section_heading = true` hoặc `paragraph_heading = true`. Format-agent dùng giá trị này để format spacing quanh heading.

---

## Task 2: Tạo `.agents/scripts/apply-profile.ps1`

**Vị trí:** `Content Factory/.agents/scripts/apply-profile.ps1`

**Tham số:**

```powershell
param(
    [ValidateSet("validate", "patch", "restore")]
    [string]$Action = "validate",

    [string]$ProfilePath = "profiles/active.json",
    [string]$DefaultPath = "profiles/default.json"
)
```

**Logic hoạt động (theo Action):**

### Action = "validate"

Đọc `$ProfilePath`, kiểm tra ràng buộc R1–R8 (tùy theo field `mode`). Output:

```
Exit 0 → JSON hợp lệ, in "VALIDATION PASSED"
Exit 1 → In danh sách lỗi cụ thể, ví dụ:
  [FAIL] R3: Đoạn tối đa (4 câu) < chuỗi bình thường tối đa (5 câu)
  [FAIL] R5: Chuỗi dài tối thiểu (4) phải > chuỗi bình thường tối đa (5)
```

Khi `mode = "auto"` hoặc `mode = "basic"` → chỉ check R1–R5.
Khi `mode = "advanced"` → check R1–R8.

### Action = "patch"

1. Đọc `profiles/active.json`.
2. **Pre-flight check (fix V6):** Verify TẤT CẢ find-patterns tồn tại trong target files TRƯỚC khi patch. Nếu bất kỳ pattern nào thiếu → ABORT, in danh sách pattern thiếu + file, exit 1.
3. Backup mỗi file target: `[file].bak` (chỉ tạo nếu chưa có).
4. Thực hiện string replacement theo bảng patch (Phase 03).

### Action = "restore"

Với mỗi file `.bak` trong danh sách target:
1. Copy `.bak` → file gốc.
2. Xóa `.bak`.

Nếu không có `.bak` nào → in "Nothing to restore", exit 0 (không lỗi).

---

## Task 3: Validation Logic trong apply-profile.ps1

**Hàm Parse-Range (dùng khi validate JSON, không phải khi thu thập input):**

```powershell
function Test-Range($obj, $name) {
    if (-not $obj.min -and $obj.min -ne 0) { return "[FAIL] $name: thiếu 'min'" }
    if (-not $obj.max -and $obj.max -ne 0) { return "[FAIL] $name: thiếu 'max'" }
    if ($obj.min -gt $obj.max) { return "[FAIL] $name: min ($($obj.min)) > max ($($obj.max))" }
    return $null
}
```

**Validation Rules (theo BRIEF §5.2):**

```powershell
$errors = @()
$p = Get-Content $ProfilePath -Raw -Encoding UTF8 | ConvertFrom-Json

# --- Kiểm tra format cơ bản ---
foreach ($field in @("sentences_per_paragraph", "sentences_per_normal_chain",
                     "sentences_per_long_chain", "long_chains_per_article")) {
    $err = Test-Range $p.$field $field
    if ($err) { $errors += $err }
}

# --- R1: B1 ≠ B2 ---
$b1 = $p.section_separator; $b2 = $p.paragraph_separator
if (-not $b1.marker -and -not $b2.marker) {
    $b1Total = $b1.blank_lines_above + $b1.blank_lines_below
    $b2Total = $b2.blank_lines_above + $b2.blank_lines_below
    if ($b1Total -le $b2Total) {
        $errors += "[FAIL] R1: Section separator ($b1Total dòng trống) phải > paragraph separator ($b2Total dòng trống) khi cùng không có marker"
    }
} elseif ($b1.marker -and $b2.marker -and $b1.marker -eq $b2.marker) {
    $errors += "[FAIL] R1: Section marker '$($b1.marker)' trùng paragraph marker"
}

# --- R2: B2 ≠ B4 (tương tự R1) ---
# ... (cùng logic)

# --- R3: B3.max >= B5.max ---
if ($p.sentences_per_paragraph.max -lt $p.sentences_per_normal_chain.max) {
    $errors += "[FAIL] R3: sentences_per_paragraph.max ($($p.sentences_per_paragraph.max)) < sentences_per_normal_chain.max ($($p.sentences_per_normal_chain.max))"
}

# --- R4: B3.max >= B6.max ---
if ($p.sentences_per_paragraph.max -lt $p.sentences_per_long_chain.max) {
    $errors += "[FAIL] R4: sentences_per_paragraph.max ($($p.sentences_per_paragraph.max)) < sentences_per_long_chain.max ($($p.sentences_per_long_chain.max))"
}

# --- R5: B6.min > B5.max ---
if ($p.sentences_per_long_chain.min -le $p.sentences_per_normal_chain.max) {
    $errors += "[FAIL] R5: sentences_per_long_chain.min ($($p.sentences_per_long_chain.min)) phải > sentences_per_normal_chain.max ($($p.sentences_per_normal_chain.max))"
}

# --- R6, R7, R8: chỉ khi mode = advanced ---
if ($p.mode -eq "advanced") {
    # R6, R7, R8...
}

if ($errors.Count -eq 0) {
    Write-Host "VALIDATION PASSED"; exit 0
} else {
    $errors | ForEach-Object { Write-Host $_ }; exit 1
}
```

---

## Task 4: Quy trình tương tác (Agent-side, ghi vào content-post.md)

Agent thực hiện flow sau khi user chọn chế độ Basic/Advanced:

1. Agent hỏi từng biến qua chat (hiển thị bảng câu hỏi).
2. User trả lời (format `x-y` hoặc đơn).
3. Agent tự parse câu trả lời: `3-5` → `{"min":3,"max":5}`. `3` → `{"min":3,"max":3}`. Invalid → hỏi lại.
4. Sau khi thu thập đủ → Agent tạo `profiles/active.json` (merge vào default.json, set `mode`).
5. Agent chạy: `apply-profile.ps1 -Action validate`
6. Exit 0 → chạy `apply-profile.ps1 -Action patch`. Exit 1 → Agent đọc output, giải thích lỗi cho user, hỏi sửa biến nào.

Cho chế độ Auto:
1. Agent copy `profiles/default.json` → `profiles/active.json` (hoặc dùng `write_to_file`).
2. Không cần validate (default luôn hợp lệ). Không cần patch (giá trị = mặc định).

---

## Task 5: Encoding Safety (ASCII-only refactor)

**Vấn đề:** PowerShell 5 cần BOM để đọc UTF-8. AI tools edit `.ps1` → mất BOM → crash. Ảnh hưởng tất cả `.ps1` files.

**Giải pháp 3 tầng:**

### Tầng 1: Code
- Tạo `profiles/patch-patterns.json` chứa tất cả find/replace patterns (tiếng Việt)
- Refactor `apply-profile.ps1` → 100% ASCII:
  - Error messages → English
  - Comments → English
  - Patterns → đọc từ `patch-patterns.json` bằng `Get-Content -Encoding UTF8`

### Tầng 2: Workspace Rule
- Thêm vào `GEMINI.md` (Workspace Rules):
```
File `.ps1` PHẢI chứa 100% ASCII. Không viết tiếng Việt hay bất kỳ ký tự non-ASCII nào 
trong file `.ps1` (kể cả comments). Nội dung non-ASCII lưu trong `.json`, 
đọc runtime bằng `-Encoding UTF8`.
```

### Tầng 3: Script Header
- Mỗi file `.ps1` có comment header:
```powershell
# ENCODING RULE: This file MUST contain ASCII-only characters.
# All non-ASCII content (Vietnamese patterns, messages) must be stored
# in JSON files and read at runtime with -Encoding UTF8.
# Reason: PowerShell 5 requires BOM for UTF-8, which AI tools may strip.
```

### Áp dụng cho các Phase khác
- Phase 02: Khi sửa `validate-draft.ps1` → cũng chuyển sang ASCII-only
- Phase 04: Khi sửa `validate-format.ps1` → cũng chuyển sang ASCII-only

---

## Files to Create

| File | Purpose |
|------|---------|
| `profiles/default.json` | Bộ tham số mặc định + field `mode` |
| `profiles/patch-patterns.json` | Tất cả find/replace patterns (non-ASCII) |
| `.agents/scripts/apply-profile.ps1` | Script validate/patch/restore (ASCII-only, không interactive) |

## Test Criteria

- [ ] `apply-profile.ps1 -Action validate` với default.json → VALIDATION PASSED.
- [ ] `apply-profile.ps1 -Action validate` với JSON có B3=`3-4`, B5=`3-5` → exit 1, báo R3.
- [ ] `apply-profile.ps1 -Action restore` khi không có `.bak` → "Nothing to restore", exit 0.
- [ ] File `.ps1` không chứa bất kỳ ký tự non-ASCII nào.
- [ ] `apply-profile.ps1 -Action patch` → pre-flight check pass → tạo `.bak` → patch files. (Test khi Phase 03 xong)
- [ ] `apply-profile.ps1 -Action patch` với SKILL.md đã bị sửa tay → pre-flight FAIL, ABORT. (Test khi Phase 03 xong)

---

Next Phase: `phase-02-validator-overhaul.md`
