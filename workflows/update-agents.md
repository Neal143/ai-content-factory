---
description: 🔄 Cập nhật hệ thống .agents lên phiên bản mới nhất từ GitHub
---

# WORKFLOW: /update-agents

Bạn là **Antigravity Update Manager**. Nhiệm vụ: Tải phiên bản mới nhất của thư mục `.agents` từ GitHub về máy của User, thay thế hoàn toàn thư mục cũ để đảm bảo đồng bộ tuyệt đối với bản gốc.

> **CẢNH BÁO:** Workflow này sẽ XÓA TOÀN BỘ nội dung thư mục `.agents` hiện tại và THAY THẾ bằng phiên bản mới nhất từ GitHub. Bất kỳ file nào User tự ý sửa bên trong `.agents/` sẽ bị mất. Dữ liệu cá nhân (`vault/`, `personas/`) KHÔNG bị ảnh hưởng.

## Giai đoạn 1: Xác nhận trước khi cập nhật

1. Thông báo cho User: "Workflow này sẽ thay thế toàn bộ thư mục `.agents` bằng phiên bản mới nhất từ GitHub. Dữ liệu `vault/` và `personas/` của bạn sẽ KHÔNG bị ảnh hưởng. Bạn có muốn tiếp tục không?"
2. Dừng và đợi câu trả lời từ User.
3. Nếu User từ chối: Kết thúc ngay lập tức.

## Giai đoạn 2: Xác định đường dẫn

1. Xác định đường dẫn tuyệt đối của thư mục `.agents` hiện tại. Thư mục này chính là thư mục CHA của file workflow bạn đang đọc.
   - Ví dụ: Nếu bạn đang đọc file tại `D:\MyFactory\.agents\workflows\update-agents.md` thì thư mục `.agents` là `D:\MyFactory\.agents`.
2. Xác định thư mục CHA của `.agents` (gọi là `FACTORY_ROOT`).
   - Ví dụ: `D:\MyFactory`
3. Lưu cả 2 đường dẫn này để sử dụng ở các bước sau.

## Giai đoạn 3: Tải bản mới nhất

1. Chạy lệnh tải repo về thư mục tạm:
   ```
   git clone --depth 1 https://github.com/Neal143/ai-content-factory.git "[FACTORY_ROOT]/.agents_update_temp"
   ```
2. Nếu lệnh clone thất bại (mất mạng, sai URL, v.v.): Báo lỗi cho User và DỪNG LẠI. KHÔNG được tiếp tục sang Giai đoạn 4.
3. So sánh version: Đọc dòng đầu tiên (`# 🏭 AI Content Factory vX.Y.Z`) trong cả 2 file:
   - Local: `[FACTORY_ROOT]/.agents/README.md`
   - Remote: `[FACTORY_ROOT]/.agents_update_temp/README.md`
   - Nếu version **giống nhau**: Thông báo "Hệ thống đã là phiên bản mới nhất (vX.Y.Z)!". Xóa thư mục tạm: `Remove-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -Recurse -Force`. KẾT THÚC.
   - Nếu version **khác nhau**: Thông báo "Phát hiện phiên bản mới: vX.Y.Z → vA.B.C". Tiếp tục Giai đoạn 4.

## Giai đoạn 4: Thay thế

1. **Dọn dẹp backup cũ:** Nếu `.agents_backup` tồn tại từ lần update trước, xóa nó đi (chỉ giữ backup của lần update hiện tại):
   ```powershell
   if (Test-Path "[FACTORY_ROOT]\.agents_backup") { Remove-Item -Path "[FACTORY_ROOT]\.agents_backup" -Recurse -Force }
   ```
2. **Sao lưu (An toàn):** Đổi tên thư mục `.agents` hiện tại thành `.agents_backup`:
   ```powershell
   Rename-Item -Path "[FACTORY_ROOT]\.agents" -NewName ".agents_backup"
   ```
3. **Chuyển đổi:** Đổi tên thư mục vừa tải về thành `.agents` chính thức:
   ```powershell
   Rename-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -NewName ".agents"
   ```
4. **Dọn rác Git:** Xóa thư mục `.git` bên trong `.agents` mới (vì nó là sản phẩm của lệnh clone, User không cần):
   ```powershell
   Remove-Item -Path "[FACTORY_ROOT]\.agents\.git" -Recurse -Force
   ```

## Giai đoạn 5: Kiểm tra và Dọn dẹp

1. Kiểm tra nhanh thư mục `.agents` mới có tồn tại các thư mục con bắt buộc không: `workflows/`, `skills/`, `agents/`, `scripts/`.
2. **Nếu THÀNH CÔNG (đủ 4 thư mục con):**
   - Chạy migration tự động:
     ```powershell
     powershell -ExecutionPolicy Bypass -File "[FACTORY_ROOT]\.agents\scripts\run-migrations.ps1" -FactoryRoot "[FACTORY_ROOT]"
     ```
   - Nếu migration báo lỗi (exit code khác 0): Thông báo cho User "⚠️ Cập nhật .agents thành công nhưng có migration thất bại. Hãy báo lại cho tác giả hệ thống."
   - Báo cáo: "✅ Đã cập nhật `.agents` thành công lên phiên bản mới nhất! Bản backup phiên bản cũ được giữ tại `.agents_backup/`. Nếu pipeline lỗi sau update, rollback bằng lệnh: `Rename-Item .agents .agents_failed; Rename-Item .agents_backup .agents`"
3. **Nếu THẤT BẠI (thiếu thư mục con):**
   - Khôi phục bản sao lưu:
     ```powershell
     Remove-Item -Path "[FACTORY_ROOT]\.agents" -Recurse -Force
     Rename-Item -Path "[FACTORY_ROOT]\.agents_backup" -NewName ".agents"
     ```
   - Báo lỗi: "❌ Cập nhật thất bại. Hệ thống đã tự động khôi phục về phiên bản cũ. Không có dữ liệu nào bị mất."
   - Dọn rác: `Remove-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -Recurse -Force -ErrorAction SilentlyContinue`