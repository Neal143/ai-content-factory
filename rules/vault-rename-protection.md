---
trigger: when agent is about to rename, move, or delete any markdown or yaml file within Content Factory.
---

# Vault Rename Protection

## CẢNH BÁO NGHIÊM TRỌNG (CRITICAL WARNING)

Tuyệt đối KHÔNG ĐƯỢC sử dụng các lệnh hệ điều hành (`mv`, `rename`, `Rename-Item`, `os.rename`...) để đổi tên file trực tiếp.

1. Hệ thống sử dụng mạng lưới wikilink (`[[tên-file]]`) và tham chiếu plain-text cực kỳ phức tạp (Knowledge Graph).
2. Tên file cũng đóng vai trò là ID logic trong các array (như `belongs_to_audience`).

## Quy trình bắt buộc (Mandatory Workflow)

Khi cần đổi tên bất kỳ file nào:

1. **Luôn luôn** hỏi ý kiến user trước.
2. **BẮT BUỘC** sử dụng script chuyên dụng:
   ```
   python .agents/scripts/safe_rename.py --old-name "<tên-cũ>" --new-name "<tên-mới>"
   ```
3. **Luôn chạy `--dry-run` trước** khi rename thật.
4. Kiểm tra kết quả output. Nếu mọi thứ đúng chuẩn, chạy lại bỏ `--dry-run`.

Rename trực tiếp ở cấp hệ điều hành sẽ gãy toàn bộ references, sập truy vấn Dataview,
mất toàn vẹn Knowledge Graph.

Script `safe_rename.py` đổi tên file vật lý + cập nhật tất cả references
(cả `[[name]]` và plain-text) trong toàn bộ `Content Factory/`.

## Ngoại lệ

`apply_recalibration.py` có batch rename logic riêng (rename hàng loạt, in-memory atomicity).
Nó import `collect_files_in_scope()` từ `safe_rename.py` để dùng chung scope,
nhưng giữ chiến lược thực thi riêng. Đây là ngoại lệ hợp lệ duy nhất.
