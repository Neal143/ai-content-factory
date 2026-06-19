---
description: Workflow export/import dữ liệu Session 1 của book-extractor — export sang folder tạm hoặc import từ folder tạm vào factory
last_update: 19/06/2026 20:55 (GMT+7)
---

# 📦 Workflow: Transfer Extraction Runs (Export / Import)

- **Tên**: .agents/workflows/transfer-extraction.md
- **Last update**: 19/06/2026 20:55 (GMT+7)
- **Vai trò**: Export dữ liệu Session 1 ra folder tạm, hoặc import từ folder tạm vào đúng vị trí trong factory.
- **Sử dụng**: `/transfer-extraction`
- **Output**: Tùy mode — export tạo folder `vault/.extraction_runs_export/`, import đưa dữ liệu về `vault/.extraction_runs/books/` và `vault/02-sources/books/`.
- **Tóm tắt logic hoạt động**: Agent xác định mode (Export/Import) dựa trên context user → gọi script tương ứng → báo cáo kết quả.

---

## Xác định Mode

Agent xác định mode dựa trên yêu cầu của user:

| Context user đưa ra | Mode |
|---|---|
| Yêu cầu export / làm việc với folder trong `vault/.extraction_runs/books/` | **Export** |
| Yêu cầu import / làm việc với folder trong `vault/.extraction_runs_export/books/` | **Import** |

Nếu không rõ, hỏi user: "Bạn muốn Export hay Import?"

---

## MODE EXPORT

### Bước E1: Xác định sách cần export

#### Trường hợp A: User KHÔNG chỉ định tên sách

1. Đọc danh sách các thư mục con trong `vault/.extraction_runs/books/`.
2. Với mỗi thư mục, đọc `00-blackboard.yaml` → lấy trường `book_name`. Nếu thiếu `book_name`, derive từ tên folder (thay dấu `-` bằng khoảng trắng, title case, bỏ phần `_YYYY-MM-DD`).
3. Liệt kê cho user dạng danh sách đánh số:
   ```
   Các sách hiện có trong .extraction_runs/books:
   1. Beyond the Rainbow Bridge (beyond-the-rainbow-bridge_2026-05-27)
   2. Good Inside (good-inside_2026-05-21)
   
   Chọn số thứ tự các sách muốn export (vd: 1, 3):
   ```
4. Chờ user chọn.

#### Trường hợp B: User CHỈ ĐỊNH tên sách

1. Đọc danh sách các thư mục con trong `vault/.extraction_runs/books/`.
2. Với mỗi tên sách user đưa ra, tìm folder có tên gần khớp nhất (so sánh slug hoặc book_name từ blackboard).
3. Hiển thị tên chính xác và yêu cầu user xác nhận:
   ```
   Tìm thấy:
   - "Good Inside" → good-inside_2026-05-21
   Xác nhận export? (Y/N)
   ```

### Bước E2: Thực thi export

Gọi script với `Cwd` = `Content Factory/`:

```powershell
& ".agents/scripts/export_extraction_runs.ps1" -BookFolders "folder1","folder2" -Force
```

⚠️ Lưu ý:
- `Cwd` của lệnh PHẢI là `Content Factory/` (thư mục gốc chứa vault/).
- Nếu đây là lần export đầu tiên, bỏ flag `-Force`.
- Nếu đây là lần export tiếp theo, dùng `-Force` để ghi đè output cũ.

Agent đọc output của script và báo cáo cho user.

### Bước E3: Hướng dẫn user

Sau khi script chạy thành công, hướng dẫn user:

```
1. Mở folder: vault/.extraction_runs_export/books/
2. Copy toàn bộ nội dung vào factory mới (giữ nguyên cấu trúc folder).
3. Tại factory mới, gọi /transfer-extraction và yêu cầu import.
```

---

## MODE IMPORT

### Bước I1: Xác định sách cần import

#### Trường hợp A: User KHÔNG chỉ định tên sách

1. Đọc danh sách các thư mục con trong `vault/.extraction_runs_export/books/`.
2. Liệt kê cho user dạng danh sách đánh số (đọc `00-blackboard.yaml` lấy `book_name`):
   ```
   Các sách trong export folder sẵn sàng import:
   1. Beyond the Rainbow Bridge (beyond-the-rainbow-bridge_2026-05-27)
   2. Good Inside (good-inside_2026-05-21)
   
   Import tất cả? Hoặc chọn số thứ tự (vd: 1, 3):
   ```
3. Chờ user chọn.

#### Trường hợp B: User CHỈ ĐỊNH tên sách

Tìm folder khớp trong `vault/.extraction_runs_export/books/`, xác nhận với user.

### Bước I2: Thực thi import

Gọi script với `Cwd` = `Content Factory/`:

```powershell
# Import tat ca
& ".agents/scripts/import_extraction_runs.ps1"

# Hoac chi dinh folder cu the
& ".agents/scripts/import_extraction_runs.ps1" -BookFolders "folder1","folder2"
```

⚠️ Lưu ý:
- `Cwd` của lệnh PHẢI là `Content Factory/`.
- Script sẽ tự skip các sách có conflict (run folder hoặc cache file đã tồn tại).

Agent đọc output của script và báo cáo cho user.

### Bước I3: Xử lý kết quả

1. **Import thành công**: Báo cáo danh sách sách đã import. Gợi ý user mở `HANDOFF_SESSION2.txt` trong run folder để bắt đầu Session 2.
2. **Có conflict** — Script output liệt kê cụ thể từng conflict. Agent đọc output và báo user, có 2 loại:
   - **Run folder đã tồn tại**: `vault/.extraction_runs/books/[folder]/` đã có trong factory → sách này đã được import hoặc đã chạy pipeline trước đó.
   - **Cache file đã tồn tại**: `vault/02-sources/books/[Tên Sách].md` đã có trong factory → file sách đã tồn tại từ lần chạy khác.
   
   Agent hỏi user cách xử lý cho từng conflict:
   - Xóa folder/file cũ rồi chạy lại import
   - Bỏ qua sách bị conflict

---

## Lưu ý

- Script tự động normalize cấu trúc flat (sách cũ) thành subfolder `session_1/` khi export.
- `00-blackboard.yaml` trong export đã được reset `current_phase: 2`.
- Export folder `vault/.extraction_runs_export/` là tạm thời. Script import sẽ tự dọn nếu folder rỗng sau import.
