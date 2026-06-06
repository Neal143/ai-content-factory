## val_start
Chạy script:
`powershell -ExecutionPolicy Bypass -File ".agents/skills/insight-agent/scripts/validate-research.ps1" -ResearchPath "[Đường dẫn file Research Brief]"`

## val_check_file
Kiểm tra vật lý: Nếu file research-brief.md không tồn tại thì báo lỗi và dừng toàn bộ (exit 1)

## val_fail_file
`ERROR: Research brief not found at $ResearchPath`

## val_check_numbers
**CHECK 1: KIỂM TRA ĐỘ CHI TIẾT CỦA DỮ LIỆU (Specific Numbers Count)**
- Mục đích: Ép Insight Agent phải đưa ra dẫn chứng bằng con số cụ thể, tránh việc viết chung chung sáo rỗng.
- Dấu hiệu tìm kiếm: Dùng Regex quét tìm các con số (có thể chứa dấu phẩy/chấm) đứng kèm các từ khóa như: %, phần trăm, năm, tháng, triệu, tỷ, nghìn...
- Điều kiện PASS: Bắt buộc phải quét ra từ 5 cụm số liệu trở lên.

## val_check_story
**CHECK 2: KIỂM TRA NGUỒN GỐC CÂU CHUYỆN (Story Source Tags)**
- Mục đích: Nếu bài có nhắc đến "câu chuyện", hệ thống ép buộc phải khai báo nguồn gốc (vault, famous, book, none) để chống bịa đặt (fabrication).
- Dấu hiệu tìm kiếm: Quét tìm chữ "story, stories, cau chuyen" và thẻ "source: vault/famous/book/none".
- Điều kiện PASS: 
  + Nếu nhắc đến story (>0) thì bắt buộc phải có thẻ source (>0).
  + Nếu không nhắc đến story (chỉ có data) thì tự động PASS.

## val_check_kcs
**CHECK 3: KIỂM TRA TỰ ĐÁNH GIÁ (KCS Status)**
- Mục đích: Ép Insight Agent phải tự audit bài làm của chính nó theo chuẩn Knowledge-Centered Service (KCS) trước khi nộp.
- Dấu hiệu tìm kiếm: Quét tìm cụm "KCS status: PASS" hoặc "KCS check: PASS".
- Điều kiện PASS: Chỉ PASS khi tìm thấy chính xác chữ PASS. Nếu khai báo FAIL hoặc quên khai báo đều bị đánh trượt.

## val_aggregate
Duyệt qua từng kết quả lưu trong mảng $results để in ra màn hình.

## val_exit
`exit $failCount`

## check_pass
**Verdict** (dựa trên script exit code):
- Exit code = 0 → **PASS** → Chuyển Phase 3.

## revise
- Exit code > 0 → **REVISE** → Quay bước 2, bổ sung dẫn chứng. Tối đa 2 lần retry.

## fail
- FAIL 2 lần → Dừng pipeline, escalate cho User.

## check_retry
**Ghi log:** `[Phase 2 Gate] Verdict: PASS/REVISE | Attempt: N/2`

## done
Hoàn tất Phase 2.
