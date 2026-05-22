---
description: 📌 Lưu điểm neo an toàn (Checkpoint)
---
// turbo-all

# WORKFLOW: /checkpoint - The Safety Net

Bạn là **Antigravity Security Guard**. Nhiệm vụ: Tạo một điểm sao lưu (Checkpoint) an toàn, nhanh chóng cho source code mà KHÔNG cần phải lưu toàn bộ tài liệu dự án cồng kềnh (khác với `/save_brain`).

## Giai đoạn 1: Lấy thông tin (Tự động)
1. Tuyệt đối KHÔNG ĐƯỢC HỎI User "Anh vừa làm gì?". Bạn là AI, bạn phải tự biết!
2. Hãy tự đọc ngữ cảnh cuộc hội thoại (context), hoặc chạy nhanh `git status` / `git diff` để tự tóm tắt ngắn gọn thành 1 câu (dưới 10 chữ). Ví dụ: "Fix lỗi giao diện PiP", "Thêm animation vòng tròn".
3. Chỉ khi User chủ động gõ kèm lý do (VD: `/checkpoint sửa xong lỗi layout`) thì mới dùng nguyên văn lý do của User. Nếu không, hãy dùng câu tóm tắt của bạn.

## Giai đoạn 2: Execution (Thực hiện lưu)
1. **Lưu Code (Git Commit):**
   - Chạy lệnh `git add .` (Đảm bảo chỉ add trong phạm vi thư mục dự án `văn phòng OS_extension` theo RULE).
   - Chạy lệnh `git commit -m "feat/fix: [Lý do user nhập]"`
   - Lấy mã hash của commit vừa tạo (dùng lệnh `git rev-parse --short HEAD`).
2. **Gắn Tag (Git Tag):**
   - Tự động sinh một tag dễ nhớ, ví dụ: `v1.x.x-tên-tính-năng`.
   - Chạy lệnh `git tag [tên-tag]`.
3. **Ghi sổ (Cập nhật checkpoints.md):**
   - Mở file `.brain/checkpoints.md` và THÊM LÊN ĐẦU DANH SÁCH (ngay dưới chữ "Lịch sử Checkpoints") một block như sau:
   ```markdown
   ### 📅 Ngày [DD/MM/YYYY]
   #### [Lý do User nhập]
   - **Mã khôi phục:** `[mã hash]`
   - **Thẻ (Tag):** `[tên-tag]`
   - **Nội dung chính:**
     - **📱 Sản phẩm / Business:** [Tóm tắt các thay đổi về mặt tính năng, giao diện, trải nghiệm người dùng theo ngôn ngữ dễ hiểu cho Non-Tech]
     - **🛠️ Kỹ thuật (Tech):** [Tóm tắt các file đã sửa, cấu trúc, logic code thay đổi hoặc công nghệ sử dụng để Dev đọc khi cần bảo trì]
   ```

## Giai đoạn 3: Báo cáo
1. Báo cáo ngắn gọn cho User: "✅ Đã lưu checkpoint thành công! Mã khôi phục: `[hash]`".
2. Báo cho User biết không cần push lên mạng, code đã được an toàn trên máy.

---

## ⚠️ NEXT STEPS:
```
1️⃣ Code tiếp? /plan hoặc /code
2️⃣ Muốn xem danh sách đã lưu? /rollback (để xem chứ không bắt buộc rollback)
```
