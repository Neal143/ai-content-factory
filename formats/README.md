# Format Profile — Giải thích các trường cấu hình

> File: profiles/README.md
> Last update: 19/05/2026 21:00 (GMT+7)
> Vai trò: Tài liệu giải thích ý nghĩa từng trường trong file `default.json` và `active.json`.
> Sử dụng khi: Cần hiểu ý nghĩa các trường cấu hình trước khi chỉnh sửa hoặc tạo profile mới.
> Output: Không có — đây là tài liệu tham khảo.

## Tổng quan

Mỗi lần chạy pipeline `/content-post`, hệ thống đọc file `active.json` để biết cấu trúc bài viết mong muốn. File `default.json` là bản gốc không bao giờ sửa — chỉ dùng làm mẫu.

---

## `_meta`

| Trường | Ý nghĩa |
|--------|---------|
| `description` | Mô tả file này là gì |
| `version` | Phiên bản format profile |
| `last_update` | Ngày cập nhật gần nhất |

## `mode`

Chế độ viết: `"auto"`, `"basic"`, hoặc `"advanced"`.
- **auto**: Dùng mặc định, không hỏi user.
- **basic**: User tùy chỉnh cấu trúc (10 biến B1-B10).
- **advanced**: User tùy chỉnh toàn diện (thêm 5 biến A1-A6).

## `section_separator` — Cách ngăn giữa các phần (Hook ↔ Story ↔ Deep Dive...)

| Trường | Ý nghĩa | Ví dụ |
|--------|---------|-------|
| `marker` | Ký hiệu ngăn cách. `"⁂"` = dấu asterism. `""` = chỉ dùng dòng trống | `"⁂"` |
| `blank_lines_above` | Số dòng trống phía trên marker | `1` |
| `blank_lines_below` | Số dòng trống phía dưới marker | `1` |

## `paragraph_separator` — Cách ngăn giữa các đoạn văn trong cùng 1 phần

Cấu trúc giống `section_separator`. Mặc định: không marker, 1 dòng trống phía trên.

## `chain_separator` — Cách ngăn giữa các chuỗi câu trong cùng 1 đoạn

Cấu trúc giống `section_separator`. Mặc định: không marker, không dòng trống (viết liền).

## `sentences_per_paragraph` — Số câu trong mỗi đoạn văn

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `min` | Ít nhất bao nhiêu câu | 3 |
| `max` | Nhiều nhất bao nhiêu câu | 5 |

## `sentences_per_normal_chain` — Số câu trong chuỗi câu bình thường

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `min` | Ít nhất | 1 |
| `max` | Nhiều nhất | 2 |

## `sentences_per_long_chain` — Số câu trong chuỗi câu dài

Chuỗi câu dài dùng khi cần tạo chiều sâu cảm xúc hoặc lập luận phức tạp.

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `min` | Ít nhất | 3 |
| `max` | Nhiều nhất | 5 |

## `long_chains_per_article` — Số chuỗi câu dài trong cả bài

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `min` | Ít nhất | 3 |
| `max` | Nhiều nhất | 5 |

## `long_chain_context`

Văn bản mô tả khi nào nên dùng chuỗi câu dài. Agent đọc câu này để quyết định vị trí đặt chuỗi dài.

## `output_elements` — Các thành phần hiển thị trong bài viết cuối cùng

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `title` | Có hiển thị tiêu đề bài? | `false` (ẩn) |
| `section_heading` | Có hiển thị heading từng phần (Hook, Story...)? | `false` (ẩn) |
| `paragraph_heading` | Có hiển thị heading từng đoạn? | `false` (ẩn) |

## `section_heading_spacing` / `paragraph_heading_spacing`

Khoảng cách dòng trống xung quanh heading (chỉ có ý nghĩa khi `output_elements` bật `true`).

## `word_count_total` — Tổng số từ toàn bài

| Trường | Ý nghĩa | Mặc định |
|--------|---------|----------|
| `min` | Ít nhất | 1500 |
| `max` | Nhiều nhất | 1800 |

## `word_count_per_section` — Số từ mỗi phần (chỉ dùng ở mode advanced)

| Phần | min | max |
|------|-----|-----|
| Hook | 80 | 120 |
| Story | 200 | 300 |
| Deep Dive | 700 | 900 |
| Pivot | 200 | 300 |
| Closing | 100 | 150 |

## `word_count_per_paragraph` — Số từ tối đa mỗi đoạn

Mặc định: 400 từ. Nếu đoạn nào vượt → script validation báo lỗi.

## `very_short_sentence_threshold`

Số từ tối thiểu để 1 câu được tính là "câu đầy đủ". Mặc định: 4.
Câu ngắn hơn 4 từ → 2 câu ngắn gộp lại mới tính bằng 1 câu, tránh viết bài toàn câu cụt.
