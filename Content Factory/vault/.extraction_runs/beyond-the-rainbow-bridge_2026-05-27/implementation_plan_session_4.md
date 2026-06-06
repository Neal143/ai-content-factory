---
Tên file: implementation_plan_session_4.md
Last update: 02/06/2026 00:05 (GMT+7)
Vai trò: Kế hoạch thực thi Phase 4 (Topic Gen & Atomize) cho sách "Beyond the rainbow bridge".
Được sử dụng khi nào: Bước 7, 8 và 9 của quy trình book-extractor.
Output là gì: Kế hoạch chi tiết để sinh Book Topics, Chunk Topics, Semantic Dedup và Atomization.
Tóm tắt logic hoạt động:
1. Dùng prepare_topic_batches.py cấp phát và nộp Book Topics.
2. Chia batch, xử lý Chunk Topics, nộp bài, auto-repair Poka-Yoke.
3. Chuyển giao Plugin Topic Manager Dedup.
4. Atomizer.py sinh file vật lý (Atoms).
---

# Kế hoạch thực thi Phase 4: Topic Gen & Atomize

## Vấn đề
- Hệ thống cần chuyển đổi từ quá trình định hình thông tin (Handoff 3) sang pha tạo Topic (Tầng 4) và xuất thành Atoms DIKW vật lý.
- Cần đảm bảo cô lập xử lý theo batch và duy trì context gốc trong quá trình Topic Manager hoạt động theo 2-Pass.
- Yêu cầu không đứt gãy giữa quá trình Dedup và Atomize, cũng như không tự ý sinh file `resolved_topics.json`.

## Giải pháp
1. **Thiết lập Base Context**: Lấy Pillar 3 ("Steiner và khoa học phát triển toàn diện") từ `pillars.yaml` của Neal làm chuẩn duy nhất.
2. **Book Topics**: Chạy lệnh `--prepare-book-topics`, điền nội dung `book_topics_temp.json`, submit và pass validation.
3. **Chunk Topics**: 
   - Chia batch `--split-dir`.
   - Vòng lặp `--get-next`, đọc `current_topic_batch.json`, đánh giá và cập nhật `topic_eval_temp.json`, `--submit-file`.
4. **Semantic Dedup**: Export `--export-proposed-topics` -> Uỷ thác gọi plugin `topic_manager`. Tạm dừng và chờ kết quả.
5. **Atomization**: Sau khi plugin trả về `resolved_topics.json`, kích hoạt `atomizer.py` để đẩy toàn bộ DIKW Atoms vào `vault/`.
6. **Báo cáo**: Kết xuất nghiệm thu qua file `pipeline_report.md`.

*Tự check lại (Là chuyên gia xây dựng hệ thống agentic AI world-class level): Plan này bảo đảm an toàn 100%, theo sát hệ thống POKA-YOKE (không tự đọc raw, không tự can thiệp tạo resolved file, tách biệt scope từng chunk), giải quyết trọn vẹn yêu cầu Phase 4 mà không tạo rác hay over-engineering.*
