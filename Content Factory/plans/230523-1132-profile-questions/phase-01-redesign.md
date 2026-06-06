# Phase 01: Redesign Questions

> File: plans/230523-1132-profile-questions/phase-01-redesign.md
> Last update: 23/05/2026 21:35 (GMT+7)

## Bối cảnh

- Heading **thuộc về** section/paragraph đó (không phải separator)
- Separator và heading là 2 đối tượng độc lập, spacing cộng dồn là đúng
- Khi cả separator lẫn heading tồn tại: separator đứng trước, heading đứng sau
- A2/A3 (spacing heading) chỉ có ý nghĩa khi B9/B10 = yes → gộp thành sub-question
- Nhóm câu hỏi theo đối tượng (section → paragraph → chain → hiển thị) để user dễ theo dõi

## Ảnh hưởng

| File | Cần sửa? | Lý do |
|------|----------|-------|
| `profile-selector/SKILL.md` | ✅ | Reorder + redesign questions |
| Tất cả file khác | ❌ | Không reference B/A numbers, chỉ đọc JSON keys |

## Tasks

### Task 1: Reorder + Redesign danh sách B1–B10

**File**: `.agents/skills/profile-selector/SKILL.md`
**Vị trí**: Dòng 68-89 (toàn bộ block Basic questions)

**Trước** (dòng 68-89):
```text
**Danh sách câu hỏi Basic (B1–B10):**
‎```text
[B1] Phân tách giữa các section:
     — Marker hiển thị giữa các section (mặc định: không có, chỉ dòng trống. Nhập ký hiệu nếu muốn, VD: ———, ***): ___
     — Số dòng trống phía trên marker (mặc định: 1): ___
     — Số dòng trống phía dưới marker (mặc định: 1): ___
[B2] Phân tách giữa các đoạn văn:
     — Marker hiển thị giữa các đoạn (mặc định: không có): ___
     — Số dòng trống phía trên (mặc định: 1): ___
     — Số dòng trống phía dưới (mặc định: 0): ___
[B3] Số câu mỗi đoạn (mặc định: 8-10): ___
[B4] Phân tách giữa các chuỗi câu trong đoạn:
     — Marker hiển thị giữa các chuỗi (mặc định: không có): ___
     — Số dòng trống phía trên (mặc định: 0): ___
     — Số dòng trống phía dưới (mặc định: 0): ___
[B5] Số câu mỗi chuỗi bình thường (mặc định: 1-2): ___
[B6] Số câu mỗi chuỗi dài (mặc định: 3-5): ___
[B7] Số chuỗi dài mỗi bài (mặc định: 3-5): ___
[B8] Bài viết có title trong output cuối? (mặc định: không): ___
[B9] Section có heading trong output cuối? (mặc định: không): ___
[B10] Đoạn có heading trong output cuối? (mặc định: không): ___
‎```
```

**Sau** (dòng 68-103):
```text
**Danh sách câu hỏi Basic (B1–B10):**
‎```text
══ SECTION ══
[B1] Phân tách giữa các section:
     — Marker (mặc định: không có. VD: ———, ***): ___
     — Dòng trống phía trên (mặc định: 1): ___
     — Dòng trống phía dưới (mặc định: 1): ___
[B2] Section có heading? (mặc định: không): ___
     — Nếu có — dòng trống phía trên heading (mặc định: 1): ___
     — Nếu có — dòng trống phía dưới heading (mặc định: 0): ___
     💡 Khi cả B1 marker lẫn B2 heading cùng bật: [section trước] → separator → heading → [section sau]. Spacing cộng dồn.

══ PARAGRAPH ══
[B3] Phân tách giữa các đoạn văn:
     — Marker (mặc định: không có): ___
     — Dòng trống phía trên (mặc định: 1): ___
     — Dòng trống phía dưới (mặc định: 0): ___
[B4] Đoạn có heading? (mặc định: không): ___
     — Nếu có — dòng trống phía trên heading (mặc định: 1): ___
     — Nếu có — dòng trống phía dưới heading (mặc định: 0): ___
     💡 Khi cả B3 marker lẫn B4 heading cùng bật: [đoạn trước] → separator → heading → [đoạn sau]. Spacing cộng dồn.
[B5] Số câu mỗi đoạn (mặc định: 8-10): ___
     💡 2 câu dưới 4 từ liền nhau được tính là 1 câu.

══ CHAIN ══
[B6] Phân tách giữa các chuỗi câu trong đoạn:
     — Marker (mặc định: không có): ___
     — Dòng trống phía trên (mặc định: 0): ___
     — Dòng trống phía dưới (mặc định: 0): ___
[B7] Số câu mỗi chuỗi bình thường (mặc định: 1-2): ___
[B8] Số câu mỗi chuỗi dài (mặc định: 3-5): ___
[B9] Số chuỗi dài mỗi bài (mặc định: 3-5): ___

══ HIỂN THỊ ══
[B10] Bài viết có title trong output cuối? (mặc định: không): ___
‎```
```

**Mapping cũ → mới:**

| Cũ | Mới | Nội dung |
|----|-----|----------|
| B1 | B1 | Section separator |
| B9+A2 | B2 | Section heading + spacing |
| B2 | B3 | Paragraph separator |
| B10+A3 | B4 | Paragraph heading + spacing |
| B3 | B5 | Câu/đoạn |
| B4 | B6 | Chain separator |
| B5 | B7 | Câu/chuỗi thường |
| B6 | B8 | Câu/chuỗi dài |
| B7 | B9 | Chuỗi dài/bài |
| B8 | B10 | Title |

---

### Task 2: Xóa A2/A3 + Renumber Advanced

**File**: `.agents/skills/profile-selector/SKILL.md`
**Vị trí**: Dòng 91-99 (block Advanced)

**Trước:**
```text
**Câu hỏi bổ sung Nâng cao (A1–A6):**
‎```text
[A1] Ngữ cảnh sử dụng chuỗi dài: ___
[A2] Spacing heading section — dòng trống trên/dưới (ví dụ: 1-0): ___
[A3] Spacing heading đoạn — dòng trống trên/dưới (ví dụ: 1-0): ___
[A4] Số từ toàn bài (ví dụ: 1500-1800, dung sai ±10%): ___
[A5] Số từ mỗi section: ___
[A6] Số từ tối đa mỗi đoạn: ___
‎```
```

**Sau:**
```text
**Câu hỏi bổ sung Nâng cao (A1–A4):**
‎```text
[A1] Ngữ cảnh sử dụng chuỗi dài (mặc định: tạo chiều sâu cảm xúc hoặc lập luận phức tạp): ___
[A2] Số từ toàn bài (mặc định: 1300-1800, dung sai ±10%): ___
[A3] Phân bổ từ mỗi section — nhập % hoặc số tuyệt đối (mặc định: 6/16/52/16/10 %): ___
     💡 Thứ tự: Hook / Story / Deep Dive / Pivot / Closing. Nếu nhập %, agent tính min-max dựa trên A2. Tổng phải = 100%.
[A4] Số từ tối đa mỗi đoạn (mặc định: 400): ___
‎```
```

---

### Task 3: Cập nhật mô tả 3B + 3C + last_update

**File**: `.agents/skills/profile-selector/SKILL.md`

**Dòng 10** (last_update body):
- Trước: `> Last update: 19/05/2026 15:41 (GMT+7)`
- Sau: `> Last update: 23/05/2026 (GMT+7)`

**3B dòng 49:**
- Trước: `Agent hỏi user 10 biến (B1–B10) qua chat (xem danh sách câu hỏi bên dưới).`
- Sau: giữ nguyên (vẫn 10 biến B1–B10)

**3C dòng 64:**
- Trước: `Tương tự Basic nhưng hỏi thêm 5 biến (A1–A6), set "mode":"advanced".`
- Sau: `Tương tự Basic nhưng hỏi thêm 4 biến (A1–A4), set "mode":"advanced".`

**Bước 2 dòng 29:**
- Trước: `3️⃣ Thử nghiệm Nâng cao — Tùy chỉnh toàn diện (+ heading, word count)`
- Sau: `3️⃣ Thử nghiệm Nâng cao — Tùy chỉnh toàn diện (+ word count)`
  > Lý do: heading đã chuyển sang Basic (B2/B4)

---

## Mapping B/A mới → JSON key (cho agent parse)

Agent đọc câu trả lời user → ghi vào `active.json` theo JSON key:

| Câu hỏi | JSON key | Ghi chú |
|----------|----------|---------|
| B1 marker | `section_separator.marker` | |
| B1 trên/dưới | `section_separator.blank_lines_above/below` | |
| B2 on/off | `output_elements.section_heading` | true/false |
| B2 spacing | `section_heading_spacing.blank_lines_above/below` | Chỉ hỏi khi B2=yes |
| B3 marker | `paragraph_separator.marker` | |
| B3 trên/dưới | `paragraph_separator.blank_lines_above/below` | |
| B4 on/off | `output_elements.paragraph_heading` | true/false |
| B4 spacing | `paragraph_heading_spacing.blank_lines_above/below` | Chỉ hỏi khi B4=yes |
| B5 | `sentences_per_paragraph.min/max` | |
| B6 marker | `chain_separator.marker` | |
| B6 trên/dưới | `chain_separator.blank_lines_above/below` | |
| B7 | `sentences_per_normal_chain.min/max` | |
| B8 | `sentences_per_long_chain.min/max` | |
| B9 | `long_chains_per_article.min/max` | |
| B10 | `output_elements.title` | true/false |
| A1 | `long_chain_context` | string |
| A2 | `word_count_total.min/max` | |
| A3 | `word_count_per_section.{Section}.min/max` | Nếu user nhập %, tính: min = A2.min × %, max = A2.max × %. Validate script kiểm tra R6/R7. |
| A4 | `word_count_per_paragraph.max` | |

## Verification

1. ✅ B1-B2 (section) nằm cạnh nhau
2. ✅ B3-B4-B5 (paragraph) nằm cạnh nhau
3. ✅ B6-B9 (chain) nhóm riêng
4. ✅ B10 (title/hiển thị) cuối cùng
5. ✅ A2/A3 cũ đã xóa, heading spacing gộp vào B2/B4
6. ✅ Ghi chú stacking rõ ràng tại B2 và B4
7. ✅ Tổng B vẫn = 10 (không đổi count dòng 49)
8. ✅ Tổng A = 4 (cập nhật dòng 64)
9. ✅ Mapping B→JSON key rõ ràng, agent ghi đúng active.json
10. ✅ apply-profile.ps1 đọc JSON keys → không bị ảnh hưởng bởi renumber
11. ✅ Comments R1-R8 trong apply-profile.ps1 → cập nhật ở Phase 02
12. ✅ last_update dòng 10 cập nhật
