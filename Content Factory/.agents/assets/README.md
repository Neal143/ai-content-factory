# .agents/assets/ — System-level Assets

Last update: 30/06/2026 00:55 (GMT+7)

Thư mục này chứa các template và scaffold dùng để khởi tạo và duy trì
cấu trúc Content Factory cho user. Đây là **single source of truth**
cho toàn bộ folder và foundation file mà hệ thống tạo ra.

## Cấu trúc

| Folder | Mục đích | Sử dụng bởi |
|--------|----------|-------------|
| `factory-scaffold/` | Template cấu trúc thư mục + foundation files | `sync-factory-scaffold.ps1`, `init_vault.ps1` |
| `persona-template/` | 7 file YAML template cho persona mới | `init_vault.ps1` |

## Quy tắc

1. **Thêm folder/file mới:** Thêm vào `factory-scaffold/` tại đúng vị trí.
   Folder rỗng cần `.gitkeep`. Script sync sẽ tự động tạo cho user.
2. **Sửa nội dung template:** Sửa trực tiếp trong `factory-scaffold/`.
   Lưu ý: chỉ áp dụng cho **user mới**. User cũ cần numbered migration
   để cập nhật (xem `.agents/migrations/README.md`).
3. **KHÔNG đặt asset riêng của skill vào đây.** Chỉ đặt asset dùng chung
   (system-level). Asset riêng của skill đặt tại `skills/[tên-skill]/assets/`.
