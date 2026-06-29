---
Tên file: process-inbox.md
Last update: 29/06/2026 22:11 (GMT+7)
Vai trò: Cổng nạp liệu đa kênh (Omni-channel Router) tiếp nhận và định tuyến dữ liệu thô.
Được sử dụng khi nào: Khi User muốn nạp ý tưởng qua Chat, trích xuất dữ liệu cũ, hoặc dọn dẹp các điểm nạp liệu tĩnh (Fixed Entry Points) trong Inbox.
Output: Dữ liệu được định tuyến chính xác cho các Skills xử lý lõi (story-architect, inbox-processor).
Tóm tắt logic: Hỗ trợ 3 syntax (Chat, Extract, Mặc định quét tĩnh). Áp dụng định tuyến tuyệt đối dựa trên tên file. Ghi chèn (Prepend) raw data lên đầu file lưu trữ tĩnh kèm Backlink và xóa trắng file gốc ở Inbox.
---

# 📥 Workflow: Xử lý Hộp thư đến (Omni-channel Router)

> **LỆNH**:
> - `/process-inbox [Nội dung text]` (Nạp trực tiếp qua Chat)
> - `/process-inbox extract` (Truy xuất bài cũ trong Vault)
> - `/process-inbox` (Quét mặc định 7 file tĩnh trong Inbox)

## Hướng dẫn thực thi

### Bước 1: Tiếp nhận Đầu vào (Intake)
- **TH 1 (Chat):** Nếu user nhập text trực tiếp, hệ thống dùng text đó làm raw data.
- **TH 2 (Extract):** Quét các file cũ chưa bóc tách trong Vault.
- **TH 3 (Mặc định):** Quét đúng 7 file nạp liệu tĩnh trong thư mục `00-Inbox/`: `Concepts.md`, `Data-Points.md`, `Insights.md`, `Quotes.md`, `Solutions.md`, `Stories.md`, `Uncategorized.md`. Bỏ qua bất kỳ file nào khác. Bỏ qua logic YAML frontmatter.

### Bước 2: Phân tách & Định tuyến (Zero-Hallucination Routing)
Ủy quyền toàn bộ thao tác xử lý cho Skills:
1. **Chia nhỏ (nếu cần):** Tự động chẻ nhỏ nội dung trong file thành các khối độc lập dựa trên khoảng trắng hoặc dấu ngăn cách `---`.
2. **Định tuyến tuyệt đối:** Dựa vào tên file (Ví dụ `Quotes.md`), hệ thống ngầm gán Type tương ứng cho toàn bộ các khối bên trong.
   - Giao toàn bộ khối từ `Stories.md` (hoặc text nạp trực tiếp được nhận diện là câu chuyện) cho skill `story-architect`.
   - Giao các khối từ 6 file còn lại cho skill `inbox-processor`. (File `Uncategorized.md` sẽ do AI tự suy luận Type).

### Bước 3: Hoàn tất & Tái sinh (Reverse-Chronological Logging)
Áp dụng cho **tất cả** các trường hợp đầu vào:
- **TH 3 (Mặc định):** Ghi log vào file `Processed/` tương ứng với tên file giỏ (Ví dụ: `Quotes.md` → `Processed/Quotes.md`).
- **TH 1 (Chat):** Ghi log vào `Processed/Uncategorized.md`.
- **TH 2 (Extract):** Ghi log vào file `Processed/` tương ứng với type đã routing.

Quy trình ghi log:
1. Đọc nội dung file lưu trữ tương ứng nằm trong thư mục `vault/00-Inbox/Processed/`.
2. Ghi thêm nội dung khối Raw Data vừa xử lý **LÊN ĐẦU FILE** (Prepend) theo đúng format thời gian thực:
   ```markdown
   ## DD/MM/YYYY HH:MM:SS (GMT+7)
   [Nội dung Raw Data nguyên bản của User]
   🔗 Đã xử lý thành Atom: [[Tên_File_Atom_Sinh_Ra]]

   ---
   ```
3. Chỉ với TH 3 (Mặc định): Làm rỗng nội dung vừa nạp trong file gốc ở `00-Inbox/`. **Tuyệt đối không xóa file vật lý** — chỉ xóa nội dung bên trong.
4. Báo cáo tổng số Atoms được bóc tách an toàn vào `vault/01-Atomic/`.