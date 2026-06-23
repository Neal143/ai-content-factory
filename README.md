# 🏭 AI Content Factory v3.8.0

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

## 🚀 Hướng dẫn Onboarding (Dành cho người mới)

Nếu đây là lần đầu tiên bạn (hoặc AI IDE của bạn) tải hệ thống này về, bạn **bắt buộc** phải khai báo thông tin cá nhân (Persona) để hệ thống biết bạn là ai, cách bạn viết gì và tệp độc giả của bạn là gì.

1. Khởi động IDE hỗ trợ AI (như Antigravity/Cursor).
2. Tải hệ thống về làm Workspace:
   ```bash
   git clone https://github.com/Neal143/ai-content-factory.git
   ```
3. Gõ lệnh `/onboarding-persona` vào cửa sổ chat với AI để kích hoạt hệ thống phỏng vấn khai báo thông tin.
4. Trả lời các câu hỏi AI đưa ra. AI sẽ tự động phân tích và tạo cấu hình Persona hoàn chỉnh lưu vào máy bạn.

## 📜 Danh mục Workflows hiện có

Sau khi đã Onboard thành công, hệ thống cung cấp sẵn các bộ định tuyến (Workflows) dưới đây để phục vụ cho mọi nhu cầu sản xuất nội dung của bạn. Chỉ cần gõ `/[tên-workflow]` để AI tự động kích hoạt:

- ✍️ **`/content-post`**: Dây chuyền sản xuất nội dung mạng xã hội (Pipeline 7 giai đoạn liên tục qua các Sub-Agents).
- 📚 **`/book-extractor`**: Cỗ máy bóc tách và phân rã sách nguyên quyển thành mạng lưới tri thức nguyên tử DIKW (Chia 4 Sessions tự động chống tràn bộ nhớ).
- 📥 **`/process-inbox`**: Trợ lý phân loại và xử lý các ghi chú/ý tưởng thô vụn từ Inbox.
- 📖 **`/story-bank`**: Công cụ nhập liệu và cấu trúc hóa các trải nghiệm/câu chuyện cá nhân để làm chất liệu viết bài.
- 🔄 **`/transfer-extraction`**: Trình xuất/nhập (Export/Import) dữ liệu sách giữa các môi trường Factory khác nhau.
- 🎭 **`/onboarding-persona`**: Cỗ máy phỏng vấn tạo và điều chỉnh tệp DNA giọng văn (Persona) cho tác giả.
- 🔄 **`/update-agents`**: Cập nhật lõi hệ thống `.agents` lên phiên bản mới nhất từ GitHub (tự động chạy migration cấu trúc vault/personas nếu có).

---

*Thiết kế và kiến trúc bởi Neal143. Dành cho mục đích giáo dục & tham khảo về Multi-Agent Systems.*
