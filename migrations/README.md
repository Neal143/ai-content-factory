# Migrations

Thư mục này chứa các script cập nhật cấu trúc `vault/` và `personas/` khi hệ thống nâng cấp phiên bản.

## Quy tắc đặt tên
- Format: `NNN_mo-ta-ngan.ps1` (VD: `001_add-dlq-folder.ps1`)
- Số thứ tự tăng dần, không được trùng, không được nhảy số

## Quy tắc viết script
- Nhận tham số `$FactoryRoot` (đường dẫn gốc factory)
- BẮT BUỘC idempotent (kiểm tra trước khi tạo/đổi tên/di chuyển)
- Trả exit code 0 = thành công, khác 0 = thất bại
- Dùng tiếng Anh hoặc tiếng Việt không dấu trong comment (rule encoding PowerShell)
- Khi thêm folder hệ thống mới, BẮT BUỘC cập nhật `structure-manifest.txt` TRƯỚC, sau đó mới tạo migration script.

## Quy tắc an toàn dữ liệu
- **KHÔNG BAO GIỜ** xóa folder hoặc file có dữ liệu user (`vault/`, `personas/`, `docs/`, `plans/`)
- Chỉ thực hiện: tạo mới folder, đổi tên folder/file, di chuyển file
- Khi đổi tên: PHẢI kiểm tra cả source tồn tại VÀ destination chưa tồn tại
- Hệ thống tự động backup `vault/` và `personas/` trước khi chạy migration. Nếu migration thất bại, user có thể khôi phục từ `.update_backups/`
- **KHÔNG được thao tác trên `.update_backups/`** — đây là thư mục backup của user, không thuộc phạm vi migration

## Ví dụ tạo folder mới
```powershell
param([string]$FactoryRoot)
$target = Join-Path $FactoryRoot "vault\05-NewSection"
if (-not (Test-Path $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
exit 0
```

## Ví dụ đổi tên folder
```powershell
param([string]$FactoryRoot)
$old = Join-Path $FactoryRoot "vault\03-Content"
$new = Join-Path $FactoryRoot "vault\03-Published"
if ((Test-Path $old) -and (-not (Test-Path $new))) { Rename-Item -Path $old -NewName "03-Published" }
exit 0
```
