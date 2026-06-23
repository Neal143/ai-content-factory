---
description: 🔄 Cập nhật hệ thống .agents lên phiên bản mới nhất từ GitHub
---

# WORKFLOW: /update-agents

Bạn là **Antigravity Update Manager**. Nhiệm vụ: Tải phiên bản mới nhất của thư mục `.agents` từ GitHub về máy của User, thay thế hoàn toàn thư mục cũ để đảm bảo đồng bộ tuyệt đối với bản gốc.

> **CẢNH BÁO:** Workflow này sẽ XÓA TOÀN BỘ nội dung thư mục `.agents` hiện tại và THAY THẾ bằng phiên bản mới nhất từ GitHub. Bất kỳ file nào User tự ý sửa bên trong `.agents/` sẽ bị mất. Dữ liệu cá nhân (`vault/`, `personas/`) KHÔNG bị ảnh hưởng.

## Giai đoạn 1: Xác định đường dẫn

1. Xác định đường dẫn tuyệt đối của thư mục `.agents` hiện tại. Thư mục này chính là thư mục CHA của file workflow bạn đang đọc.
   - Ví dụ: Nếu bạn đang đọc file tại `D:\MyFactory\.agents\workflows\update-agents.md` thì thư mục `.agents` là `D:\MyFactory\.agents`.
2. Xác định thư mục CHA của `.agents` (gọi là `FACTORY_ROOT`).
   - Ví dụ: `D:\MyFactory`
3. Lưu cả 2 đường dẫn này để sử dụng ở các bước sau.

## Giai đoạn 2: Kiểm tra phiên bản

1. Đọc phiên bản hiện tại (Local) từ dòng đầu tiên của file `[FACTORY_ROOT]/.agents/README.md`.
2. Lấy phiên bản mới nhất (Remote) trực tiếp từ GitHub bằng lệnh:
   ```powershell
   (Invoke-RestMethod -Uri "https://raw.githubusercontent.com/Neal143/ai-content-factory/master/README.md") -split "`n" | Select-Object -First 1
   ```
3. So sánh 2 phiên bản:
   - Nếu **giống nhau**: Thông báo "Hệ thống đã là phiên bản mới nhất!". KẾT THÚC quy trình.
   - Nếu **khác nhau**: Thông báo "Phát hiện phiên bản mới: Local → Remote". Tiếp tục Giai đoạn 3.

## Giai đoạn 3: Xác nhận từ User

1. Thông báo cho User: "Phát hiện phiên bản mới! Workflow này sẽ thay thế toàn bộ thư mục `.agents` bằng phiên bản mới nhất từ GitHub. Dữ liệu `vault/` và `personas/` của bạn sẽ KHÔNG bị ảnh hưởng. Bạn có muốn tiếp tục cập nhật không?"
2. Dừng và đợi câu trả lời từ User.
3. Nếu User từ chối: Kết thúc ngay lập tức.

## Giai đoạn 4: Tải bản mới nhất

1. Chạy lệnh tải repo về thư mục tạm:
   ```
   git clone --depth 1 https://github.com/Neal143/ai-content-factory.git "[FACTORY_ROOT]/.agents_update_temp"
   ```
2. Nếu lệnh clone thất bại (mất mạng, sai URL, v.v.): Báo lỗi cho User và DỪNG LẠI. KHÔNG được tiếp tục sang Giai đoạn 5.

## Giai đoạn 5: Sao lưu và Thay thế

1. **Tạo thư mục backup:** Chạy lệnh sau để tạo thư mục backup với timestamp (múi giờ Hà Nội GMT+7). Ghi nhận đường dẫn đầy đủ của thư mục backup vừa tạo — gọi là `[BACKUP_DIR]` — để sử dụng ở các bước sau:
   ```powershell
   $timestamp = [System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date), 'SE Asia Standard Time').ToString('yyyy-MM-dd_HHmmss')
   $backupDir = Join-Path "[FACTORY_ROOT]" ".update_backups\backup_$timestamp"
   New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
   Write-Host "BACKUP_DIR=$backupDir"
   ```
   Lưu giá trị `BACKUP_DIR` in ra để dùng ở tất cả các bước tiếp theo.

2. **Sao lưu code:** Copy thư mục `.agents` hiện tại vào backup:
   ```powershell
   robocopy "[FACTORY_ROOT]\.agents" "[BACKUP_DIR]\agents" /E /NJH /NJS /NDL /NFL /NC /NS /NP | Out-Null
   ```
3. **Xóa code cũ và chuyển đổi:**
   ```powershell
   Remove-Item -Path "[FACTORY_ROOT]\.agents" -Recurse -Force
   Rename-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -NewName ".agents"
   ```
4. **Dọn rác Git:** Xóa thư mục `.git` bên trong `.agents` mới:
   ```powershell
   Remove-Item -Path "[FACTORY_ROOT]\.agents\.git" -Recurse -Force
   ```

## Giai đoạn 6: Kiểm tra và Hoàn tất

1. Kiểm tra nhanh thư mục `.agents` mới có tồn tại các thư mục con bắt buộc không: `workflows/`, `skills/`, `agents/`, `scripts/`.
2. **Nếu THÀNH CÔNG (đủ 4 thư mục con):**
   - Chạy migration tự động (truyền đường dẫn backup để migration lưu dữ liệu vào cùng thư mục):
     ```powershell
     powershell -ExecutionPolicy Bypass -File "[FACTORY_ROOT]\.agents\scripts\run-migrations.ps1" -FactoryRoot "[FACTORY_ROOT]" -BackupDir "[BACKUP_DIR]"
     ```
   - Nếu migration báo lỗi (exit code khác 0): Thông báo cho User "⚠️ Cập nhật .agents thành công nhưng có migration thất bại. Dữ liệu gốc được giữ an toàn tại `.update_backups/`. Hãy báo lại cho tác giả hệ thống."
   - Báo cáo: "✅ Đã cập nhật `.agents` thành công lên phiên bản mới nhất! Toàn bộ backup (code + dữ liệu) được giữ tại `.update_backups/`. Bạn có thể xóa các bản backup cũ khi xác nhận hệ thống hoạt động bình thường."
3. **Nếu THẤT BẠI (thiếu thư mục con):**
   - Khôi phục từ backup:
     ```powershell
     Remove-Item -Path "[FACTORY_ROOT]\.agents" -Recurse -Force -ErrorAction SilentlyContinue
     robocopy "[BACKUP_DIR]\agents" "[FACTORY_ROOT]\.agents" /E /NJH /NJS /NDL /NFL /NC /NS /NP | Out-Null
     ```
   - Báo lỗi: "❌ Cập nhật thất bại. Hệ thống đã tự động khôi phục về phiên bản cũ từ backup. Không có dữ liệu nào bị mất."
   - Dọn rác: `Remove-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -Recurse -Force -ErrorAction SilentlyContinue`