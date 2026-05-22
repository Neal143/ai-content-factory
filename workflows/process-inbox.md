---
description: Xử lý và phân loại ghi chú thô từ Inbox
---

# 📥 Workflow: Xử lý Hộp thư đến (Process Inbox)

> **LỆNH**: `/process-inbox`

Quy trình chạy ngầm dọn dẹp thư mục `00-Inbox/`, đọc file thô chưa định dạng và tự động chuyển về đúng thư mục loại nguyên liệu (Atom type).

## Hướng dẫn thực thi

### Bước 1: Quét Inbox
Đọc danh sách toàn bộ file trong `vault/00-Inbox/` đang có status: `pending`. (Bỏ qua các file đã processed).

### Bước 2: Phân tách & Định tuyến (Skill Routing)
Với MỖI file pending, tiến hành phân tích ngữ nghĩa:
1. **Xử lý Cấu trúc Hỗn hợp:** Nếu file chứa ghép nhiều nội dung khác biệt (ví dụ: 1 phần kể chuyện + 1 phần trích dẫn sách), BẮT BUỘC phải chẻ nhỏ nội dung thành các khối (blocks) độc lập.
2. **Cấp phát Topic:** Bắt buộc cấp phát mảng `topics` cho từng khối. Tham chiếu `pillars.yaml` để đảm bảo Topic trực thuộc một Pillar rõ ràng.
3. **Skill Routing:** Tùy tính chất từng khối, gọi skill tương ứng để xử lý:
   - Nếu khối nội dung là **Câu Chuyện (Story)** → Gọi skill `story-architect` để tiến hành phân rã kép (L → File A, SPTOL → File B).
   - Nếu khối nội dung thuộc 5 loại còn lại (**Insights, Solutions, Concepts, Quotes, Data-Points**) → Gọi skill `inbox-processor` để gán nhãn và cấy Graph Meta-tags.

### Bước 3: Hoàn tất (Finalize)
1. Update trạng thái frontmatter của file GỐC thành `status: processed`.
2. Báo cáo tổng số file thô đã dọn dẹp và số lượng Atoms con được bóc tách thành công vào `vault/01-Atomic/`.