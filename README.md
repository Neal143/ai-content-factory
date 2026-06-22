# 🏭 AI Content Factory

Chào mừng đến với **AI Content Factory** – hệ thống dây chuyền tự động hóa sáng tạo nội dung thế hệ mới, vận hành bằng mô hình các tác nhân trí tuệ nhân tạo (Agentic AI Orchestration).

> **Lưu ý:** Repository này chỉ chứa **Lõi Hệ Thống (`.agents`)** bao gồm các quy trình (workflows), hệ thống vai trò, bộ kỹ năng và mã nguồn (PowerShell/Python) điều khiển tự động hóa. Toàn bộ dữ liệu cá nhân, kho bài viết thô (`vault`) và tệp định hình cá tính (`personas`) được bảo vệ hoàn toàn tại thiết bị cục bộ.

## 🎯 Tổng quan

Hệ thống này sinh ra để thay đổi cách con người viết lách và sản xuất nội dung số. Thay vì dùng một chatbot AI hỏi/đáp đơn thuần, AI Content Factory chia nhỏ công việc ra thành một **dây chuyền lắp ráp** (Assembly Line) tinh vi. Trong đó, mỗi "Nhân viên AI" chỉ chuyên tâm vào đúng một khâu duy nhất (Lên ý tưởng, Thiết kế cấu trúc, Viết nháp, Điêu khắc câu chữ, và Kiểm toán chất lượng QA).

Hệ thống tương thích hoàn hảo với các IDE hỗ trợ AI mới nhất (như **Antigravity, Cursor, Windsurf**).

## 📂 Kiến trúc Lõi

- 🛤️ **`workflows/`**: Chứa các kịch bản thực thi vòng đời (Life-cycle). Ví dụ: quy trình từ ý tưởng thành bài đăng (`content-post`), quy trình bóc tách sách thô thành mạng lưới tri thức nguyên tử (`book-extractor`).
- 🤖 **`agents/`**: Bộ định nghĩa về nhân dạng (Persona) và giới hạn quyền hạn của từng tác nhân trong nhà máy (Idea Curator, Hook Engineer, Format Agent...).
- 🧠 **`skills/`**: Các bí kíp làm nghề (SOP) được biên soạn tinh gọn bằng Markdown (SKILL.md) nhằm "dạy" Agent cách xử lý tác vụ theo tiêu chuẩn khắt khe nhất của con người.
- 🔌 **`plugins/`**: Công cụ mở rộng độc lập (ví dụ: `topic_manager` - hệ thống la bàn quản lý và định tuyến từ khóa tự động).
- 📜 **`rules/`**: Bức tường lửa (Gatekeeper). Chứa các quy định tuyệt đối về văn phong, cấu trúc ngắt đoạn, chống dịch thuật rập khuôn và vượt qua các công cụ phát hiện AI.
- ⚙️ **`scripts/`**: Cỗ máy vận hành ngầm dưới đáy. Gồm các mã nguồn PowerShell/Python đảm nhiệm việc I/O file, nối ghép các khâu, phân rã dữ liệu (batching) và phát hiện các Agent "lách luật" (Sentinel Error Logging).

## 🚀 Khởi động nhanh (Dành cho AI IDE)

1. Mở IDE trí tuệ nhân tạo của bạn.
2. Dán đường link repo để IDE tự động tải lõi hệ thống về làm Workspace:
   ```bash
   git clone https://github.com/Neal143/ai-content-factory.git
   ```
3. Sau khi kéo code về, hãy gọi lệnh `Run Workflow` và trỏ vào một file trong mục `workflows/` (vd: `/content-post`) để nhà máy chính thức bấm máy!

---

*Thiết kế và kiến trúc bởi Neal143. Dành cho mục đích giáo dục & tham khảo về Multi-Agent Systems.*
