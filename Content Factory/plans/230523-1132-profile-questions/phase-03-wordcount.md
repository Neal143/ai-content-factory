# Phase 03: Fix Default Word Count

> File: plans/230523-1132-profile-questions/phase-03-wordcount.md
> Last update: 23/05/2026 22:15 (GMT+7)

## Bối cảnh

default.json cũ có lỗi tính toán: total 1500-1800 nhưng tổng section min = 1280, max = 1770 (không bằng total). Sửa lại:
- Total: 1300-1800
- Sections: 6/16/52/16/10 % → tổng = 100%

## Giá trị mới

| Section | % | min (6% × 1300) | max (6% × 1800) |
|---------|---|-----------------|-----------------|
| Hook | 6% | 78 | 108 |
| Story | 16% | 208 | 288 |
| Deep Dive | 52% | 676 | 936 |
| Pivot | 16% | 208 | 288 |
| Closing | 10% | 130 | 180 |
| **Tổng** | **100%** | **1300** | **1800** |

## Tasks

### Task 1: Cập nhật default.json

**File**: `profiles/default.json`

| Dòng | Key | Trước | Sau |
|------|-----|-------|-----|
| 67 | `word_count_total.min` | 1500 | 1300 |
| 68 | `word_count_total.max` | 1800 | 1800 (giữ nguyên) |
| 75-76 | `Hook` | 80, 120 | 78, 108 |
| 79-80 | `Story` | 200, 300 | 208, 288 |
| 83-84 | `Deep Dive` | 700, 900 | 676, 936 |
| 87-88 | `Pivot` | 200, 300 | 208, 288 |
| 91-92 | `Closing` | 100, 150 | 130, 180 |

### Task 2: Cập nhật canonical voice-writer/SKILL.md

**File**: `.agents/skills/voice-writer/SKILL.md`

Tìm mọi chỗ ghi "1500-1800" liên quan đến word count → đổi thành "1300-1800".

**Dòng 40:**
- Trước: `TUYỆT ĐỐI KHÔNG viết toàn bộ 1500-1800 từ trong 1 lượt.`
- Sau: `TUYỆT ĐỐI KHÔNG viết toàn bộ 1300-1800 từ trong 1 lượt.`

**Dòng 68:**
- Trước: `tổng word count (mục tiêu: 1500-1800 từ, ưu tiên ngữ nghĩa hơn con số tuyệt đối)`
- Sau: `tổng word count (mục tiêu: 1300-1800 từ, ưu tiên ngữ nghĩa hơn con số tuyệt đối)`

### Task 3: Cập nhật canonical writing-rules.md

**File**: `.agents/skills/voice-writer/references/writing-rules.md`

Tìm mọi chỗ ghi "1500" liên quan đến word count → đổi thành "1300".

### Task 4: Cập nhật patch-patterns.json

**File**: `profiles/patch-patterns.json`

Các find patterns chứa "1500" cần đổi thành "1300":
- Dòng 5: `vw_no_write_all_find`: `1500-1800` → `1300-1800`
- Dòng 8: `vw_word_count_find`: `1500-1800` → `1300-1800`
- Dòng 19: `wr_total_words_find`: `1500-1800` → `1300-1800`
- Dòng 52: `sd_total_find`: `1500-1800` → `1300-1800`

Các find patterns section cần đổi thành giá trị mới:
- Dòng 55: `sd_hook_find`: `80-120` → `78-108`
- Dòng 57: `sd_story_find`: `200-300` → `208-288`
- Dòng 59: `sd_deep_dive_find`: `700-900` → `676-936`
- Dòng 61: `sd_pivot_find`: `200-300` → `208-288`
- Dòng 63: `sd_closing_find`: `100-150` → `130-180`

> ⚠️ Chỉ đổi giá trị trong find patterns. Replace patterns dùng `{min}/{max}` placeholder nên không cần sửa.
> ⚠️ `sd_story_find` và `sd_pivot_find` cùng giá trị cũ (200-300) nhưng khác context text — sửa đúng dòng.

### Task 5: Cập nhật structure-designer/SKILL.md

**File**: `.agents/skills/structure-designer/SKILL.md`

**Dòng 19** (total):
- Trước: `Phân bổ tổng 1500-1800 từ (KHÔNG quá 1800):`
- Sau: `Phân bổ tổng 1300-1800 từ (KHÔNG quá 1800):`

**Dòng 23-27** (bảng section word counts):

| Dòng | Section | Trước | Sau |
|------|---------|-------|-----|
| 23 | Hook | `80-120` | `78-108` |
| 24 | Story | `200-300` | `208-288` |
| 25 | Deep Dive | `700-900` | `676-936` |
| 26 | Pivot | `200-300` | `208-288` |
| 27 | Closing | `100-150` | `130-180` |

## Verification

1. ✅ default.json: Σ section.min = 1300 = total.min
2. ✅ default.json: Σ section.max = 1800 = total.max
3. ✅ R6 pass: 1300 ≥ 1300
4. ✅ R7 pass: 1800 ≤ 1800 × 1.1 = 1980
5. ✅ voice-writer/SKILL.md: dòng 40 và 68 đều đổi 1500 → 1300
6. ✅ writing-rules.md: dòng 61 đổi 1500 → 1300
7. ✅ patch-patterns.json: 4 find patterns total + 5 find patterns section đổi
8. ✅ structure-designer/SKILL.md: dòng 19 (total) + dòng 23-27 (5 sections) đổi
9. ✅ active.json: không cần sửa (tự tạo lại từ default.json khi chạy pipeline)
10. ✅ Chạy `apply-profile.ps1 -Action validate` với default values phải PASS
