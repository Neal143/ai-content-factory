# Phase 01: Data Migration (Chuẩn hóa Atomic cũ)
Last Update: 24/05/2026 16:55 (GMT+7)
Status: ✅ Complete
Dependencies: None

## Objective
Tạo script PowerShell quét thư mục `vault/01-Atomic/`, trích xuất tên sách, sinh `source_id` dạng slug và `source_type: "book"`. Đảm bảo Backup an toàn và BẢO TOÀN KIẾN TRÚC.

## Directions (100% Error-free guarantee)
1. **Tạo Script**: Tạo file `scripts/migrate-source-metadata.ps1`.
2. **Logic Backup (Bắt buộc):**
   - Lệnh đầu tiên: Copy toàn bộ `vault/01-Atomic` sang folder backup `vault/01-Atomic_backup_[timestamp]`.
3. **Logic Quét & Xử lý (Chống gãy hệ thống):**
   - Đọc các file `.md` trong `vault/01-Atomic/` sử dụng `Get-ChildItem -Recurse -Filter *.md`.
   - ⛔ **Quy tắc Bypass (Chống rác/Chống vỡ kiến trúc):** BỎ QUA hoàn toàn các thư mục `Audiences/` và `_DLQ/` bằng cách lọc đường dẫn (`$file.FullName -notmatch "Audiences" -and $file.FullName -notmatch "_DLQ"`). Chỉ xử lý 6 thư mục DIKW: `Stories, Solutions, Insights, Concepts, Quotes, Data-Points`.
   - **Xử lý mã hóa tiếng Việt cực kỳ an toàn (World-class standard):**
     - Đọc nội dung file bằng cách chỉ định rõ mã hóa UTF8: `$content = [System.IO.File]::ReadAllText($file.FullName, [System.Text.Encoding]::UTF8)`.
     - Phân tích Frontmatter (phần nội dung giữa cặp `---` đầu tiên).
     - Nếu đã có dòng `source_id:` trong frontmatter, bỏ qua file này để tránh ghi đè dữ liệu đã chuẩn hóa.
     - Tìm dòng `source_name: ...`. Nếu không tìm thấy, bỏ qua hoặc ghi log cảnh báo.
     - Trích xuất tên sách từ `source_name`: Lấy phần text trước chuỗi `(bởi` hoặc `(by`. Nếu không có, lấy toàn bộ giá trị. Strip bỏ dấu ngoặc kép.
     - Hàm slugify tiếng Việt trong PowerShell: Chuyển sang lowercase, thay thế các ký tự có dấu thành không dấu (NFD normalization + loại bỏ Unicode Category 'Mn', xử lý riêng ký tự 'đ' -> 'd'), thay các ký tự đặc biệt bằng `-`, thu gọn nhiều dấu `-` liên tiếp thành 1.
       - Ví dụ: `Good Inside (bởi Dr. Becky Kennedy, 2022)` -> `good-inside`.
       - `The Whole-Brain Child (bởi Daniel J. Siegel & Tina Payne Bryson, 2011)` -> `the-whole-brain-child`.
     - Chèn `source_id: "<slug>"` ngay dưới dòng `source_name: ...`. Nếu chưa có `source_type: book`, chèn thêm dòng `source_type: book`.
     - Ghi lại file bằng .NET để đảm bảo UTF-8 không BOM (chống lỗi Font chữ tiếng Việt trên Windows):
       `[System.IO.File]::WriteAllText($file.FullName, $newContent, (New-Object System.Text.UTF8Encoding $false))`
4. **Kiểm thử**: Param `-DryRun` để in ra các thay đổi đề xuất mà không thực sự ghi file, cho phép rà soát trước.

## Files to Create/Modify
- `scripts/migrate-source-metadata.ps1`

---
Next Phase: phase-02-book-extractor.md

