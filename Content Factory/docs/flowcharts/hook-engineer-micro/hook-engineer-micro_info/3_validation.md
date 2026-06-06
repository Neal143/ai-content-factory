## val_start
Script `validate-hook.ps1` làm Quality Gate cuối cùng của Phase 3. Khởi chạy Script.

## val_check_file
Sử dụng `Test-Path $HookPath` kiểm tra file Hook Brief.

## val_fail_file
Dừng ngay pipeline với Exit 1.

## val_length
Quét tìm dòng `(?i)core\s*hook\s*[:：]\s*(.+)`.

## val_find_core
Kiểm tra xem regex có tìm thấy dòng Core Hook hay không.

## val_count
Tách chuỗi theo khoảng trắng (`-split '\s+'`) và đếm số lượng từ.

## val_length_cond
Điều kiện PASS: Số từ `≤ 15 từ`. Nếu không thỏa mãn, báo WARN.

## val_rotation
Quét tìm công thức hiện tại: `(?i)(formula|cong\s*thuc|F\d+)\s*[:：]\s*(.+)` (hoặc fallback tìm trực tiếp mã qua `\b(F\d{1,2})\b`).

## val_has_history
Kiểm tra sự tồn tại của file lịch sử `hook-history.md`. *(Ngoại lệ)* Nếu file lịch sử chưa tồn tại (bài viết đầu tiên), tự động PASS tiêu chí này.

## val_check_overlap
Đối chiếu với 2 bài gần nhất: Quét `hook-history.md` bằng Regex `(?i)(?:formula|hook\s*formula)\s*[:：]\s*(\S+)`. Lấy 2 kết quả cuối cùng. Công thức đang dùng KHÔNG được nằm trong 2 công thức cũ. Bắt buộc không được trùng lặp.

## val_aggregate
Tổng hợp `$failCount` từ các bài test.

## val_exit
Script exit với mã lỗi (Failed nếu `$failCount > 0`).

## check_pass
### Self-Check Gate
- Script bước 7 exit code = 0 (0 FAIL) + Scoring bước 5 ≥ 8 → **PASS** → Chuyển Phase 4.

## revise
- Nếu FAIL → quay lại bước 4, viết lại hook với formula khác. Tối đa 2 lần retry.

## check_retry
- **Ghi log:** `[Phase 3 Self-Check] Verdict: PASS/REVISE | Attempt: N/2`

## fail
- FAIL 2 lần → dừng pipeline, escalate User.

## done
Hoàn tất Phase 3.
