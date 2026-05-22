# Story Extraction Patterns — Trích xuất câu chuyện từ bài viết cũ

## Mục đích
Khi user dùng `/story-bank extract`, hệ thống sẽ quét các bài viết cũ trong vault để tìm và bóc tách câu chuyện chưa được cấu trúc hóa.

## 6 Regex Patterns phát hiện Story
Tìm các đoạn văn chứa patterns sau:

| # | Pattern | Ví dụ |
|---|---------|-------|
| 1 | `Tui có quen...` / `Tôi có một...` | "Tui có quen một anh bạn làm IT..." |
| 2 | `Hồi đó tui...` / `Ngày xưa tôi...` | "Hồi đó tui còn đang chạy startup..." |
| 3 | `Chuyện là...` / `Số là...` | "Chuyện là năm ngoái, công ty tui..." |
| 4 | `Có lần...` / `Một lần...` | "Có lần tui đi pitch trước 20 nhà đầu tư..." |
| 5 | `[Năm YYYY]...` | "Năm 2020, tui mất sạch tiền tiết kiệm..." |
| 6 | `Tui nhớ...` / `Tôi nhớ...` | "Tui nhớ cái ngày đầu tiên đi làm..." |

## Quy trình Extract
1. Scan toàn bộ files trong `vault/02-Sources/` (excluse `vault/02-Sources/01-Books/`) và các bài viết cũ.
2. Khi match pattern → trích xuất đoạn văn chứa story.
3. Chuyển đoạn trích xuất qua flow Story Architect (bóc tách 5 phần).
4. Gắn tag `source: extracted_from_post` trong frontmatter.
5. Kiểm tra duplicate trước khi lưu.
