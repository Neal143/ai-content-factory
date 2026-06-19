---
Tên file: tasks_session_4.md
Last update: 02/06/2026 00:05 (GMT+7)
Vai trò: Danh sách Task chi tiết thực thi Phase 4 (Topic Gen & Atomize).
Được sử dụng khi nào: Sau khi user ra lệnh "thực thi".
Output là gì: Hướng dẫn các lệnh thực thi script tự động.
Tóm tắt logic hoạt động: Chia nhỏ quá trình chạy thành 5 bước dễ theo dõi.
---

# Task List Session 4

- [ ] **Task 1: Tạo Book Topics**
  - Chạy lệnh `prepare_topic_batches.py --prepare-book-topics`.
  - Mở file `book_topics_temp.json`, bổ sung nội dung (với Pillar là "Steiner và khoa học phát triển toàn diện").
  - Submit bằng `prepare_topic_batches.py --submit-book-topics` cho tới khi PASS.
- [ ] **Task 2: Phân tách và Xử lý Batch Chunk Topics**
  - Chạy lệnh `prepare_topic_batches.py --split-dir ... --batch-size 3`.
  - Thực hiện vòng lặp: đọc `--get-next`, tham khảo `current_topic_batch.json`, chỉnh sửa `topic_eval_temp.json` và submit cho đến khi hết batch.
- [ ] **Task 3: Xuất Proposed Topics và Gọi Topic Manager Plugin**
  - Chạy `prepare_topic_batches.py --export-proposed-topics`.
  - Ủy thác gọi `topic_manager` plugin và **chờ kết quả** file `resolved_topics.json`.
- [ ] **Task 4: Phân rã Atoms (Phase 2)**
  - Chạy lệnh `atomizer.py` (cùng các tuỳ chọn --acronym, --decision-map, --resolved-topics, --baseline, --report).
- [ ] **Task 5: Nghiệm thu và Báo cáo**
  - Trích xuất nội dung `pipeline_report.md` và in báo cáo.
