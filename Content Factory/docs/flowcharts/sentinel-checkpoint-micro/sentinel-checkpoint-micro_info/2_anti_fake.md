## IsPhase6
Kiểm tra xem pipeline đã chạy tới Phase 6 (QA Checker) hay chưa. 

## HasScore
Chỉ áp dụng từ Phase 6 trở đi. Kiểm tra xem LLM có tự ý "bịa" điểm số `qa_score` vào trong file `05-draft.md` trong khi file kết quả thực sự `06-qa-result.md` lại chưa tồn tại hay không. Mục đích: Chống lại hành vi giả mạo kết quả kiểm tra chất lượng.

## HasKeyPhase
Kiểm tra xem Phase hiện tại có nằm trong danh sách các Phase yêu cầu Execution Key không (0 đến 7 và 45).

## CompareKey
Đối chiếu khóa thực thi:
- Đọc `expectedKey` từ `SKILL.md` (chuỗi hex).
- Đọc `actualKey` từ file output tương ứng của Phase.
- So sánh: Nếu thiếu key trong SKILL, thiếu key trong output, hoặc hai key không khớp nhau -> gán cờ `failed = $true`. Mục đích: Buộc Agent phải đọc kỹ `SKILL.md` (qua bộ nhớ từ xa) thay vì chỉ chạy bằng bộ nhớ ẩn (implicit memory).
