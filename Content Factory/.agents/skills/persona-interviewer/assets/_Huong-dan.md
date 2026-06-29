# Hướng dẫn sử dụng Inbox

Đây là nơi bạn ghi chép nhanh ý tưởng, kiến thức, trích dẫn... vào **đúng file** tương ứng.
Hệ thống sẽ tự động xử lý và chuyển hóa chúng thành Atoms trong `vault/01-Atomic/`.

## Cách ghi

Mở file tương ứng với loại nội dung bạn muốn ghi, viết nội dung vào:

| File | Ghi gì vào đây? | Ví dụ |
|------|-----------------|-------|
| `Insights.md` | Góc nhìn sâu, nhận xét phản biện | "Người ta nghĩ X nhưng thực ra Y vì..." |
| `Solutions.md` | Mô hình, công thức, phương pháp | "3 bước để vượt qua bất an: 1)... 2)... 3)..." |
| `Concepts.md` | Định nghĩa, khái niệm | "Deliberate Practice là việc luyện tập có chủ đích..." |
| `Quotes.md` | Trích dẫn từ sách/chuyên gia | "Charlie Munger: Invert, always invert" |
| `Data-Points.md` | Số liệu, thống kê | "Theo Harvard 2019, 73% stress đến từ..." |
| `Stories.md` | Câu chuyện cá nhân có bước ngoặt | "Năm 2019 tôi mất sạch tiền, sau đó..." |
| `Uncategorized.md` | Không biết phân loại gì | Ghi đại, hệ thống tự phân loại |

## Quy tắc ghi
- Mỗi ý tưởng cách nhau bởi 1 dòng trống hoặc dấu `---`.
- Không cần viết YAML frontmatter. Chỉ cần viết nội dung thuần.
- Ghi xong, chạy lệnh `/process-inbox` để hệ thống xử lý.

## Hệ thống xử lý như thế nào?
1. **Đọc** nội dung từ các file trên.
2. **Tách** thành các khối độc lập.
3. **Chuyển** cho skill xử lý (inbox-processor hoặc story-architect).
4. **Tạo Atoms** lưu vào `vault/01-Atomic/[Type]/` với tên file `USER_[slug].md`.
5. **Lưu log** nội dung gốc vào `Processed/[Ten_File].md` (kèm thời gian và backlink).
6. **Xóa trắng** nội dung trong file gốc để sẵn sàng cho lần ghi tiếp.

> **Lưu ý:** Các file trong thư mục này **không bao giờ bị xóa**. Chỉ nội dung bên trong bị làm rỗng sau khi xử lý.
