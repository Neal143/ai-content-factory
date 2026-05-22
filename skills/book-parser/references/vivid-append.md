---
name: Vivid Auto-Append Rule
description: "Các quy tắc nội suy và xử lý dữ liệu ký sinh (Vivid) In-Memory, giới hạn Hard Cap 3, Orphan Drop và Reserve cho các Vivid vượt cap"
---

# Quy Tắc Xử Lý Dữ Liệu Ký Sinh (Vivid Auto-Append In-Memory)

Tiến trình này chỉ thực thi ở khâu HẬU KỲ (Post-processing) in-memory, khi toàn bộ khung YAML Frontmatter của các file Mẹ (Insight, Knowledge, Audience) đã được dựng sẵn trên RAM.

## 1. Định Danh & Khớp Nối Mục Tiêu (Target Host)
Hệ thống quét rổ đệm chứa các thẻ `content_type=vivid_...` và bắn tín hiệu tìm Target Host tương ứng trên In-Memory:

- **Thẻ `vivid_circumstance` (Lệnh Cập Nhật Ngoại Vi Vật Lý):** Do file Audience đã tồn tại trên đĩa nên không lưu In-Memory. Parser buộc phải thực thi mở đọc tham chiếu file tĩnh ngoài đĩa từ thẻ `audience_filename` trong Decision Map định danh, ghi chèn (Patching) mảng `vivid_circumstances: [...]` vào YAML Frontmatter và trực tiếp lưu lại (Override) trên đĩa.
- **Thẻ `vivid_insight`**: Dò ngược theo thuộc tính `supports_insight` để tìm file Insight Mẹ in-memory. Khởi tạo/ghi đè mảng tĩnh danh `vivid_insights: [...]` vào Frontmatter của Insight đó.
- **Thẻ `vivid_knowledge`**: Dò ngược theo thuộc tính `supports_knowledge` để tìm file Solution hoặc Concept Mẹ in-memory. Khởi tạo/ghi đè mảng tĩnh danh `vivid_knowledges: [...]` vào Frontmatter của Thực thể đó.

## 2. Luật Xử Lý Ngoại Lệ
Nhằm bảo vệ dữ liệu sạch và chống "bành trướng" rác trong Vault:

- **Lệnh Rớt Mồ côi (Orphan Drop):** Trong quá trình bắn tín hiệu dò Target Host, nếu Hệ Thống KHÔNG TÌM THẤY file Mẹ tương ứng (thường do Book Extractor parse lỗi), LẬP TỨC HỦY LỆNH GHI (Drop) Vivid vô gia cư này.
- **Cơ chế Sự kiên định Dữ liệu (First-Mover Canonical + Reserve):** Gắn giới hạn **Hard Cap = 3**. Trước khi ghi Vivid vào Host Mẹ, Script đếm độ dài mảng canonical (vd: `len(vivid_insights)`). Nếu mảng chưa đạt 3 → append vào mảng canonical. Nếu đã đạt 3 → append vào mảng dự bị `_reserve` cùng loại (vd: `vivid_insights_reserve`). Đúng 3 Vivid đầu tiên đóng đinh thành Neo Chính Tắc, các Vivid tiếp theo được bảo toàn trong danh sách dự bị để User xem lại và chọn lọc khi cần.

---
> ℹ️ **LƯU Ý:** Toàn bộ logic nội suy Vivid này đã được lập trình nhúng cứng (hardcoded) vào trong tập lệnh Python `atomizer.py`. Tài liệu này hiện chỉ đóng vai trò tham chiếu nguyên lý (Reference). Agent truy xuất `/atomize-book` tuyệt đối không được tự ý thực hiện nối Vivid bằng tay.
