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
   - Đảm bảo chạy lệnh tại thư mục (Cwd): `d:\AI\AI content factory - v3.7B\Content Factory`
   - Chạy lệnh `git add .agents/` (TUYỆT ĐỐI CHỈ add thư mục `.agents/`, KHÔNG được dùng `git add .` để tránh lưu nhầm `vault` hay `personas`).
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

## Giai đoạn 2.5: Kiểm tra Migration (Chỉ áp dụng cho Content Factory)

1. Chạy script detect để tự động quét `git diff HEAD~1` tìm các thay đổi về cấu trúc thư mục hoặc manifest:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents\scripts\detect-structure-changes.ps1" -FactoryRoot "Content Factory"
   ```
2. Nếu output là `[OK]` (exit code 0): Bỏ qua, không cần migration.
3. Nếu output là `[WARNING]` (exit code 1): BẮT BUỘC HỎI User:
   "Phát hiện code mới vừa tạo/đổi tên folder, hoặc manifest vừa được cập nhật. Có cần tạo migration script cho user cũ không?"
4. Nếu User trả lời "Có":
   - Đọc file `Content Factory/.agents/migrations/README.md` để nắm quy tắc viết migration.
   - Quét các file `*.ps1` trong `Content Factory/.agents/migrations/` để xác định số thứ tự tiếp theo.
   - Tạo file migration mới (VD: `002_add-content-plan.ps1`) theo đúng quy tắc trong README.md.
   - CẬP NHẬT `Content Factory/.agents/migrations/structure-manifest.txt` với tên folder mới.
   - Commit bổ sung: `git add "Content Factory/.agents/migrations/" ; git commit -m "migration: [mô tả ngắn]"`
   - Cập nhật lại mã khôi phục trong checkpoints.md bằng hash của commit migration (commit cuối cùng).
5. Nếu User trả lời "Không": Bỏ qua.

## Giai đoạn 3: Báo cáo & Đề xuất Push
1. Báo cáo ngắn gọn cho User: "✅ Đã lưu checkpoint thành công! Mã khôi phục: `[hash]`".
2. **Phân tích cập nhật:** AI đánh giá các thay đổi vừa commit để phân loại quy mô:
   - *Patch*: Sửa bug, update prompt/tài liệu.
   - *Minor*: Thêm workflow/skill mới.
   - *Major*: Thay đổi kiến trúc, flow chính.
3. **Xác định phiên bản mới:** Đọc phiên bản hiện tại từ dòng 1 của file `Content Factory/.agents/README.md` (định dạng `# 🏭 AI Content Factory vX.Y.Z`) và tính toán phiên bản mới phù hợp với phân loại trên.
4. **HỎI User:** *"Dựa trên các thay đổi, tôi đề xuất cập nhật hệ thống lên bản **v[Phiên bản mới]** (Lý do: ...). Bạn có muốn ghi nhận phiên bản này và push cập nhật lên GitHub không?"* Dừng và đợi câu trả lời từ User.

## Giai đoạn 4: Đóng gói và Push lên GitHub (Chỉ khi User đồng ý)
1. Nếu User trả lời "Có": 
   - **Cập nhật mã phiên bản:**
     - TỰ ĐỘNG đọc nội dung file `Content Factory/.agents/README.md`, thay thế dòng 1 thành `# 🏭 AI Content Factory v[Phiên bản mới]` và lưu file.
     - Đảm bảo lệnh được chạy tại thư mục: `d:\AI\AI content factory - v3.7B\Content Factory`.
     - Chạy lệnh commit: `git add ".agents/README.md" ; git commit -m "chore: bump version to v[Phiên bản mới]"`
   - **Tách nhánh và Push:**
     - Đảm bảo lệnh tiếp theo chạy tại thư mục GỐC (Cwd): `d:\AI\AI content factory - v3.7B` (lưu ý: KHÔNG phải Content Factory).
     - Chạy lệnh 1 (Dọn nhánh cũ + Tách nhánh siêu tốc): `git branch -D agents-only 2>$null; git subtree split --prefix="Content Factory/.agents" --rejoin -b agents-only`
     - Chạy lệnh 2 (Gắn tag bản phát hành): `git tag -f v[Phiên bản mới] agents-only`
     - Chạy lệnh 3 (Đẩy lên mạng): `git push agents-origin agents-only:master v[Phiên bản mới]`
   - Báo cáo: "✅ Đã push thành công thư mục `.agents` lên GitHub với phiên bản `v[Phiên bản mới]`."
2. Nếu User trả lời "Không" hoặc từ chối: Bỏ qua và kết thúc.

---

## ⚠️ NEXT STEPS:
```
1️⃣ Code tiếp? /plan hoặc /code
2️⃣ Muốn xem danh sách đã lưu? /rollback (để xem chứ không bắt buộc rollback)
```
