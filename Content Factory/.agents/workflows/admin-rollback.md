---
description: ⏪ Phục hồi .agents về quá khứ
---
# WORKFLOW: /admin-rollback

> ⚠️ CẢNH BÁO: Đây là quy trình Meta-layer chỉ dùng để quản trị hệ thống .agents. Tuyệt đối không dùng cho quá trình sản xuất content.

## Nhiệm vụ của AI:

1. Đọc file `d:\AI\AI content factory - v3.7B\CHECKPOINTS_LOG.md` và hiển thị bảng lịch sử cho User xem.
2. Hỏi User muốn quay về Mã Hash nào.
3. Khi User xác nhận Mã Hash, chạy các lệnh sau tại thư mục `d:\AI\AI content factory - v3.7B\`:
   ```powershell
   git reset --hard [Mã Hash]
   git clean -fd .agents/
   ```
4. Báo cáo: "✅ Đã phục hồi thành công về checkpoint [Mã Hash]. Vui lòng kiểm tra lại hệ thống."
