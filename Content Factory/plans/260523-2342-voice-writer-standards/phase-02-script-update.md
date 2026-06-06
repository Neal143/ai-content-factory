# Phase 02: Script Hard-Gate

> **File:** plans/260523-2342-voice-writer-standards/phase-02-script-update.md
> **Last update:** 24/05/2026 13:06 (GMT+7)

Status: ✅ Complete
Dependencies: Không (Phase 01 và 02 có thể thực thi song song)

## Objective

Thêm CHECK 15/16/17 vào `validate-draft.ps1` để kiểm tra tự động các chuẩn tiếng Việt mới.

## Target File

`.agents/skills/voice-writer/scripts/validate-draft.ps1`

## Quy tắc encoding bắt buộc

`validate-draft.ps1` chạy bằng `powershell.exe` (Windows PowerShell 5.1). PS5 đọc file `.ps1` không có BOM bằng codepage ANSI → ký tự Unicode có dấu bị hỏng thành rác.

| Trường hợp | Giải pháp | Ví dụ |
|------------|-----------|-------|
| String chứa tiếng Việt có dấu | `[char]0xXXXX` | `"v" + [char]0xE0` → `"và"` |
| Regex pattern chứa ký tự Unicode | `\uXXXX` trong single-quoted string | `'\u2014'` → match em-dash |
| Display messages | Tiếng Anh (nhất quán CHECK 1-14) | `"No major punctuation errors"` |
| Comments | ASCII-safe Vietnamese | `# Cam dau hai cham` |

## Tasks

### Task 1: Chèn CHECK 15/16/17

**Vị trí:** Chèn ngay trước block `# OUTPUT REPORT` (dòng 564 trong file hiện tại).

**Mã nguồn chèn:**

```powershell
# ============================================================
# CHECK 15: Vietnamese Publishing Standards (Capitalization & Punctuation)
# Muc dich: Kiem tra viet hoa chuan, dau cau, em-dash, Oxford comma.
# ============================================================
$capPuncFails = @()

# 15.1 Colon in Headings (cam dau hai cham trong tieu de)
if ($draft -match '(?m)^#+\s+.*:') {
    $capPuncFails += "Colon in Heading"
}

# 15.2 Space before Punctuation (dau cau phai sat tu truoc)
if ($draftForCount -match '\s+[,.!?]') {
    $capPuncFails += "Space before Punctuation"
}

# 15.3 Em-dash U+2014 (cam trong tieng Viet chuan)
# Dung regex \u2014 thay vi ky tu literal de tranh encoding issues PS5
if ($draftForCount -match '\u2014') {
    $capPuncFails += "Em-dash (Change to ' - ' or rewrite)"
}

# 15.4 Oxford Comma: ", va" (cam trong tieng Viet)
# Dung [char] cho ky tu 'a' co dau huyen (U+00E0) de tranh encoding issues PS5
$oxfordPattern = '(?i),\s+v' + [char]0xE0 + '\b'
if ($draftForCount -match $oxfordPattern) {
    $capPuncFails += "Oxford comma"
}

if ($capPuncFails.Count -eq 0) {
    Add-Result "VN Punctuation" "PASS" "No major punctuation errors"
} else {
    Add-Result "VN Punctuation" "FAIL" "Found: $($capPuncFails -join ', ')"
}

# ============================================================
# CHECK 16: Prose Format
# Muc dich: Cam bullet points trong van xuoi va markdown header trong Storytelling.
# ============================================================
$proseFails = @()

# 16.1 Bullet points trong than bai viet
if ($draftForCount -match '(?m)^[-*]\s+') {
    $proseFails += "Bullets in prose"
}

# 16.2 Markdown header (##) trong storytelling (draft chi dung comment markers)
if ($draftForCount -match '(?m)^##\s') {
    $proseFails += "Markdown Headers in Storytelling"
}

# Su dung WARN thay vi FAIL de tranh false-positive (bai bio/profile cho phep bullet)
if ($proseFails.Count -eq 0) {
    Add-Result "Prose Format" "PASS" "No prose formatting errors"
} else {
    Add-Result "Prose Format" "WARN" "Found: $($proseFails -join ', ') (Review context manually)"
}

# ============================================================
# CHECK 17: AI Detection (Labels & Transitions)
# Muc dich: Quet nhan AI, lam dung tu noi, exclamation spam.
# ============================================================
$aiDetectFails = @()

# 17.1 Nhan AI dac trung tieng Anh
if ($draftForCount -match '(?i)(Key\s|Note:|Summary:)') {
    $aiDetectFails += "AI Labels (Key, Note, Summary)"
}

# 17.2 Exclamation spam (2+ dau cham than lien tiep)
if ($draftForCount -match '!!+') {
    $aiDetectFails += "Exclamation Spam"
}

# 17.3 Transition overuse (>3 lan/bai cung 1 tu noi)
# Dung [char] cho ky tu tieng Viet co dau de tranh encoding issues voi PS5
# "Tuy nhien", "Ben canh do", "Ngoai ra", "Hon nua"
$transitions = @(
    ("Tuy nhi" + [char]0xEA + "n"),
    ("B" + [char]0xEA + "n c" + [char]0x1EA1 + "nh " + [char]0x111 + [char]0xF3),
    ("Ngo" + [char]0xE0 + "i ra"),
    ("H" + [char]0x1A1 + "n n" + [char]0x1EEF + "a")
)
foreach ($trans in $transitions) {
    $count = ([regex]::Matches($draftForCount, "(?i)$([regex]::Escape($trans))")).Count
    if ($count -gt 3) { $aiDetectFails += "Overuse '$trans' ($count times)" }
}

if ($aiDetectFails.Count -eq 0) {
    Add-Result "AI Detection" "PASS" "No obvious AI markers"
} else {
    Add-Result "AI Detection" "FAIL" "Found: $($aiDetectFails -join ', ')"
}
```

**Giải thích từng CHECK:**

| CHECK | Biến dùng | Severity | Lý do severity |
|-------|-----------|----------|----------------|
| 15 VN Punctuation | `$draft` (15.1), `$draftForCount` (15.2-15.4) | FAIL | Lỗi dấu câu là lỗi kỹ thuật rõ ràng, phải sửa |
| 16 Prose Format | `$draftForCount` | WARN | Bài bio/profile cho phép bullet theo `prose-format.md` |
| 17 AI Detection | `$draftForCount` | FAIL | Nhãn AI và lạm dụng từ nối phải loại bỏ |

**Giải thích encoding từng pattern:**

| Pattern | Kỹ thuật | Tại sao an toàn |
|---------|----------|-----------------|
| `'\u2014'` | Regex Unicode escape trong single-quote | PS chuyển literal `\u2014` cho .NET regex engine, engine diễn giải thành U+2014 |
| `[char]0xE0` | PowerShell char construction | `[char]` luôn tạo Unicode char đúng trong memory, không phụ thuộc file encoding |
| `[char]0xEA`, `0x1EA1`... | PowerShell char construction | Tương tự — construct runtime, không phụ thuộc file encoding |

---

### Task 2: Cập nhật Last Update

**Vị trí:** Dòng 1.

**Trước:**
```
# Last Update: 23/05/2026 16:15 (GMT+7)
```

**Sau:**
```
# Last Update: [Ngày thực thi thực tế] (GMT+7)
```

---

### Task 3: Cập nhật mảng CHECK 14 (Ref File Keys)

**Vị trí:** Khối khai báo mảng `$refFilePaths` của CHECK 14.

**Trước:**
```powershell
$refFilePaths = @{
    "writing-rules"     = ".agents/skills/voice-writer/references/writing-rules.md"
    "anti-ai"           = ".agents/skills/voice-writer/references/anti-ai-patterns.md"
    "english-blacklist" = ".agents/skills/voice-writer/references/english-blacklist.md"
}
```

**Sau:**
```powershell
$refFilePaths = @{
    "writing-rules"     = ".agents/skills/voice-writer/references/writing-rules.md"
    "anti-ai"           = ".agents/skills/voice-writer/references/anti-ai-patterns.md"
    "english-blacklist" = ".agents/skills/voice-writer/references/english-blacklist.md"
    "capitalization"    = ".agents/skills/voice-writer/references/capitalization.md"
    "english-mixing"    = ".agents/skills/voice-writer/references/english-mixing.md"
    "prose-format"      = ".agents/skills/voice-writer/references/prose-format.md"
    "punctuation"       = ".agents/skills/voice-writer/references/punctuation.md"
    "ai-detection"      = ".agents/skills/voice-writer/references/ai-detection.md"
}
```

---

## Verification

Sau khi hoàn thành tất cả 3 task, kiểm tra:

1. ✅ Chạy script với draft mẫu có em-dash `—` → CHECK 15 FAIL
2. ✅ Chạy script với draft mẫu không có lỗi → CHECK 15/16/17 PASS
3. ✅ CHECK 16 kết quả là WARN (không phải FAIL) khi phát hiện bullet
4. ✅ Tổng số check trong report = 14 cũ + 3 mới = 17 checks
5. ✅ Script vẫn exit 0 khi tất cả PASS (WARN không tăng failCount)
6. ✅ Không có ký tự tiếng Việt có dấu nào ngoài `[char]` construction
7. ✅ CHECK 14 báo `All 8 reference file keys verified` khi chạy với draft có đầy đủ key.

---
Previous Phase: phase-01-skill-update.md
