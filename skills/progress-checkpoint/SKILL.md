---
name: Progress Checkpoint
description: "Lưu trạng thái dữ liệu Content Factory tại một thời điểm bất kỳ. Cho phép rollback về save point khi cần."
last_update: 11/08/2026 00:20 (GMT+7)
---

# Progress Checkpoint Skill

> **Tên file**: .agents/skills/progress-checkpoint/SKILL.md
> **Vai trò**: Tạo save point cho toàn bộ dữ liệu Content Factory (trừ .agents/) bằng git snapshot riêng biệt. Cho phép rollback về bất kỳ save point nào.
> **Sử dụng khi**: Cuối mỗi session/phase trong pipeline dài (book-extractor, process-inbox...), hoặc khi user muốn lưu trạng thái trước thao tác quan trọng.
> **Output**: Git commit + tag `snap/[label]`, entry mới trong `progress-checkpoints.md` ở root Content Factory.
> **Tóm tắt logic**: Script PowerShell quản lý git riêng biệt (.save-data/) để snapshot data. 3 actions: save, list, rollback.

## Cách sử dụng

### 1. Save — Lưu trạng thái hiện tại

Agent chạy lệnh sau (CWD = Content Factory root):
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/progress-checkpoint/scripts/save_progress.ps1" -Action save -Label "[label-slug]" -Description "[Mô tả ngắn gọn về trạng thái hiện tại]"
```

**Params:**
- `-Label` (bắt buộc): Slug identifier, VD: `book-extractor-phase2`, `before-calibration`
- `-Description` (tùy chọn): Mô tả chi tiết. Nếu không truyền, dùng Label làm mô tả.

**Agent tự động tạo Label và Description** dựa trên context workflow đang chạy. VD:
- Workflow book-extractor Phase 2 hoàn thành → Label: `book-extractor-phase2`, Description: `Hoàn thành Vivid Curation, cache đã lọc xong`

### 2. List — Xem danh sách save points

Agent chạy:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/progress-checkpoint/scripts/save_progress.ps1" -Action list
```

Hoặc: Agent đọc file `progress-checkpoints.md` ở root Content Factory.

### 3. Rollback — Khôi phục từ save point

> ⚠️ **BẮT BUỘC hỏi user xác nhận trước khi chạy rollback.** Đây là thao tác destructive — ghi đè toàn bộ data hiện tại bằng data từ save point.

Agent chạy:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/progress-checkpoint/scripts/save_progress.ps1" -Action rollback -Label "[label-slug]"
```

Script tự động tạo save point `before-rollback-[timestamp]` trước khi rollback để đảm bảo an toàn.

## Lưu ý kỹ thuật

- **Git data** lưu ở `.save-data/` (root Content Factory), KHÔNG phải `.git/`
- **File log** `progress-checkpoints.md` ở root Content Factory — user mở xem bất kỳ lúc nào
- `.save-data/` và `progress-checkpoints.md` **KHÔNG bị ảnh hưởng** khi chạy `/update-agents` (vì nằm ngoài `.agents/`)
- Skill chỉ snapshot **data** (vault/, personas/, docs/, plans/, các file ở root). `.agents/` KHÔNG được snapshot.
