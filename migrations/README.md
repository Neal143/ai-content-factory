# Migrations

Thư mục này chứa các script cập nhật dữ liệu user khi hệ thống nâng cấp phiên bản.

## Cơ chế đồng bộ tự động (Sync)

Hệ thống sử dụng `.agents/assets/factory-scaffold/` làm **single source of truth** cho:
- Cấu trúc thư mục (vault/, personas/)
- Foundation files (inbox files, guide files)

Script `sync-factory-scaffold.ps1` tự động chạy khi user update hệ thống
(`/update-agents` → `run-migrations.ps1`). Nó tạo folder/file nếu chưa tồn tại,
**KHÔNG BAO GIỜ** ghi đè file đã có.

**Khi thêm folder hoặc foundation file mới:**
1. Thêm trực tiếp vào `.agents/assets/factory-scaffold/` tại đúng vị trí
2. Folder rỗng cần có `.gitkeep` để Git track
3. `sync-factory-scaffold.ps1` sẽ tự động tạo cho user cũ khi update
4. **KHÔNG cần viết migration script** cho trường hợp này

## Khi nào CẦN viết migration script (numbered)?

Chỉ khi cần thao tác **KHÔNG THỂ** xử lý bằng "tạo mới nếu chưa có":
- Đổi tên folder/file đã tồn tại (xem pattern bên dưới)
- Di chuyển file từ vị trí cũ sang vị trí mới
- Sửa nội dung file đã tồn tại ở phía user (VD: cập nhật `_Huong-dan.md`)

## Quy tắc đặt tên
- Format: `NNN_mo-ta-ngan.ps1` (VD: `003_rename-content-folder.ps1`)
- Số thứ tự tăng dần, không trùng, không nhảy số

## Quy tắc viết script
- Nhận tham số `$FactoryRoot` (đường dẫn gốc factory)
- **BẮT BUỘC** idempotent (kiểm tra trước khi tạo/đổi tên/di chuyển)
- Trả exit code 0 = thành công, khác 0 = thất bại
- Dùng tiếng Anh hoặc tiếng Việt không dấu trong comment (rule encoding .ps1)

## Quy tắc an toàn dữ liệu
- **KHÔNG BAO GIỜ** xóa folder hoặc file có dữ liệu user
- Hệ thống tự động backup `vault/` và `personas/` trước khi chạy migration
- **KHÔNG được thao tác trên `.update_backups/`**

## Pattern: Đổi tên folder/file (RENAME)

> **Lưu ý:** `sync-factory-scaffold.ps1` chạy **TRƯỚC** migrations. Nếu scaffold đã có
> folder/file mới (tên mới), sync sẽ tạo folder **RỖNG** trước khi migration chạy.
> Vì vậy, **KHÔNG ĐƯỢC dùng `Rename-Item`** (sẽ lỗi vì destination đã tồn tại).
> Dùng pattern move-contents:

```powershell
$oldPath = Join-Path $FactoryRoot "vault\01-Atomic\Stories"
$newPath = Join-Path $FactoryRoot "vault\01-Atomic\Narratives"

if (Test-Path $oldPath) {
    # New path co the da ton tai (do sync tao folder rong)
    if (-not (Test-Path $newPath)) {
        New-Item -ItemType Directory -Path $newPath -Force | Out-Null
    }
    # Di chuyen toan bo noi dung tu old sang new
    Get-ChildItem -Path $oldPath | Move-Item -Destination $newPath -Force
    # Xoa folder cu (da rong)
    Remove-Item -Path $oldPath -Recurse -Force
    Write-Host "Renamed: Stories/ -> Narratives/"
}
```
