# Phase 01: Code Modification
Status: 🟡 In Progress
Dependencies: None

> **Mô tả file**:
> - **Tên file**: `plans/260521-1114-single-session-pipeline/phase-01-code-modification.md`
> - **Last update**: 21/05/2026 11:20 (GMT+7)
> - **Vai trò**: Đặc tả chi tiết các tác vụ chỉnh sửa mã nguồn để gộp phiên chạy.
> - **Được sử dụng khi nào**: Khi thực hiện chỉnh sửa code.
> - **Output**: Các tệp tin mã nguồn và cấu hình được cập nhật hoàn chỉnh.
> - **Tóm tắt logic**: Hướng dẫn chi tiết cách chỉnh sửa từng dòng code và comment cụ thể để đảm bảo bất kỳ AI nào cũng thực thi chính xác 100%.

---

## Objective
Thực hiện điều chỉnh luồng chạy của pipeline bằng cách loại bỏ tín hiệu `[HALT]` tại Phase 4 trong `create-checkpoint.ps1`, chuẩn hóa các comment mô tả của script và cập nhật quy trình điều phối trong `content-post.md` thành chạy 1 phiên duy nhất.

## Requirements
### Functional
- [x] Sửa `create-checkpoint.ps1` để không in ra `[HALT]` signal ở cuối Phase 4.
- [ ] Chuẩn hóa comment mô tả tại dòng 6 và dòng 8 của `create-checkpoint.ps1` để đồng bộ hoàn toàn với logic mới.
- [x] Sửa `content-post.md` để kết nối Phase 4 trực tiếp sang Phase 4.5 và chuyển checkpoint thành fail-safe.

### Non-Functional
- [ ] Tuân thủ nghiêm ngặt **PowerShell Encoding Rule**: Tệp `.ps1` phải chứa 100% mã ASCII (không viết tiếng Việt có dấu trong comments và chuỗi in ra).

---

## Implementation Steps

### Task 1: Chuẩn hóa comment mô tả đầu tệp `create-checkpoint.ps1`
- **Đường dẫn**: `d:\AI\AI content factory - v3.7B\Content Factory\.agents\scripts\create-checkpoint.ps1`
- **Vị trí**: Dòng 6 và dòng 8
- **Trước khi sửa**:
  ```powershell
  # Output     : Exit 0 = OK (checkpoint.yaml da ghi + HALT signal)
  #              Exit 1 = FAIL (error message)
  # Logic      : Quet file trong RunFolder -> map sang phase -> ghi YAML -> in HALT
  ```
- **Sau khi sửa**:
  ```powershell
  # Output     : Exit 0 = OK (checkpoint.yaml da ghi)
  #              Exit 1 = FAIL (error message)
  # Logic      : Quet file trong RunFolder -> map sang phase -> ghi YAML
  ```

---

## Files to Create/Modify
- `d:\AI\AI content factory - v3.7B\Content Factory\.agents\scripts\create-checkpoint.ps1` - Loại bỏ HALT signal và chuẩn hóa comment mô tả (100% ASCII).
- `d:\AI\AI content factory - v3.7B\Content Factory\.agents\workflows\content-post.md` - Chuyển đổi luồng chạy workflow sang 1 phiên duy nhất.

## Test Criteria
- [ ] Kiểm tra nội dung file `create-checkpoint.ps1` đảm bảo không còn chứa chuỗi `[HALT]`.
- [ ] Kiểm tra encoding của `create-checkpoint.ps1` đảm bảo là 100% ASCII (không chứa ký tự non-ASCII nào).

---
Next Phase: [Phase 02: Pipeline Verification](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/plans/260521-1114-single-session-pipeline/phase-02-verification.md)
