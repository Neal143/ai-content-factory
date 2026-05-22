---
description: 💾 Lưu Checkpoint an toàn cho .agents
---
# WORKFLOW: /admin-checkpoint

> ⚠️ CẢNH BÁO: Đây là quy trình Meta-layer chỉ dùng để quản trị hệ thống .agents. Tuyệt đối không dùng cho quá trình sản xuất content.

// turbo-all

## Giai đoạn 1: Lấy thông tin (Tự động)
1. Tuyệt đối KHÔNG ĐƯỢC HỎI User "Anh/chị vừa làm gì?". Bạn là AI, bạn phải tự biết!
2. Hãy tự đọc ngữ cảnh cuộc hội thoại, hoặc chạy nhanh `git status` / `git diff` để tự hiểu và tự đưa ra quyết định nội dung cập nhật.
3. Chỉ khi User chủ động gõ kèm lý do (VD: `/admin-checkpoint sửa xong pipeline`) thì mới ưu tiên dùng lý do của User. Nếu không, hãy tự viết dựa trên phân tích.

## Giai đoạn 2: Thực thi
1. **Lưu Code (Git Commit):**
   - Chạy lệnh: `git add .`
   - Chạy lệnh: `git commit -m "feat/fix: [Tóm tắt ngắn gọn]"`
   - Lấy mã hash: `git rev-parse --short HEAD`
2. **Gắn Tag (Git Tag):**
   - Tự động sinh một tag dễ nhớ và hợp lý (VD: `v5.2.x-fix-pipeline` hoặc `feat-user-auth`).
   - Chạy lệnh: `git tag [tên-tag]`
3. **Cập nhật sổ ghi chép (`d:\AI\AI content factory - v3.7B\CHECKPOINTS_LOG.md`):**
   - Cập nhật dòng `- **Last update**: DD/MM/YYYY HH:MM (GMT+7)`
   - Thêm nội dung sau vào **ngay bên dưới dòng `## Lịch sử Checkpoints`** (tức là chèn lên đầu danh sách):
   ```markdown
   ### 📅 Ngày [DD/MM/YYYY] ([HH:MM])
   #### [Lý do ngắn gọn]
   - **Mã khôi phục:** `[mã hash]`
   - **Thẻ (Tag):** `[tên-tag]`
   - **Nội dung chính:**
     - **📱 Sản phẩm / Business:** [Tóm tắt các thay đổi về mặt tính năng, giá trị giải quyết được theo ngôn ngữ dễ hiểu cho Non-Tech]
     - **🛠️ Kỹ thuật (Tech):** [Tóm tắt các file đã sửa, logic, cấu trúc thay đổi code/script để Dev bảo trì]
   ```

## Giai đoạn 3: Báo cáo
1. Báo cáo siêu ngắn gọn: "✅ Đã lưu checkpoint thành công! Mã khôi phục: `[hash]` - Tag: `[tag]`".
2. KHÔNG CẦN giải thích dông dài trừ khi User hỏi.
