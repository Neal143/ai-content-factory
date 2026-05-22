# DEV SESSION & ARCHITECTURE STATE

- **Tên file**: DEV_SESSION.md
- **Last update**: 14/05/2026 17:55 (GMT+7)
- **Vai trò**: Lưu trữ tiến độ phát triển và luật kiến trúc cho thư mục .agents.
- **Được sử dụng khi nào**: Đầu mỗi phiên chat mới về phát triển hệ thống.

## 1. Trạng thái hiện tại (Current Status)
- Đang tập trung vào: Tái cấu trúc Mermaid Blueprint cho AI Content Factory.
- Nhiệm vụ vừa hoàn thành:
  - Hoàn thành Sub-task 1.1: Quét `content-post.md` và tái cấu trúc sơ đồ `factory-system.mmd`.
  - Thiết lập thành công 2 Entry point độc lập (`start_new`, `start_resume`) và khép kín vòng lặp Checkpoint.
  - Chuẩn hóa 100% tài liệu kỹ thuật `content_pipeline.md`: Loại bỏ hoàn toàn ngôn từ diễn giải nhánh (đã có trên sơ đồ), chỉ giữ lại metadata kỹ thuật thuần túy (Output file, Terminal command, execution_key).
- Task đang treo: Tiếp tục Sub-task 1.2 (Đọc và phân tích `generate-phase-key.ps1` để map vào sơ đồ).

## 2. Kiến trúc cốt lõi (Core Directives)
1. Tách biệt Parent/Child: Hệ thống Meta-layer không tác động luồng Content.
2. 100% Poka-yoke: Mọi validate script phải dùng exit-code.
3. Token efficiency: Loại bỏ prose thừa trong SKILL.md.
4. System File Immutability: Agent đang chạy tác vụ sản xuất (Runtime Scope) KHÔNG ĐƯỢC tự ý sửa file trong `.agents/`. Phải escalate User.

## 3. Nhật ký Quyết định (Decision Log)
| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 04/05/2026 | Khởi tạo Factory Admin Meta-layer | Chống Context Drift, tạo lưới an toàn cho refactor. |
| 05/05/2026 | Hotfix validate-qa.ps1 (dòng 152) | Sửa crash PowerShell 5.1 do em-dash + nested interpolation. Hợp thức hóa bản vá đã áp dụng. |
| 05/05/2026 | Thêm Core Directive #4: System File Immutability | Ngăn Agent runtime tự ý sửa system files, buộc escalate User. |
| 14/05/2026 | Phân tách 2 Entry Points trên Mermaid Blueprint | Khép kín vòng lặp Multi-session bằng cách tách riêng `start_new` và `start_resume`. Cải thiện tính minh bạch của luồng. |
| 14/05/2026 | Quy tắc soạn `_info` (Document File Immutability) | File note cấm chứa văn xuôi diễn giải lại các nhánh rẽ của đồ thị. Chỉ lưu trữ cấu hình kỹ thuật thuần túy (tham số, đường dẫn, lệnh cấm). |
