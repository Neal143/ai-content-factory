---
description: Workflow hợp nhất xử lý sách khép kín từ trích xuất thô, tinh lọc vivid đến phân rã DIKW (Chạy phân đoạn qua 4 Session độc lập để giải phóng Token Context Window)
last_update: 30/05/2026 06:15 (GMT+7)
---

# 📖 Workflow: Book Extractor Pipeline (4-Session Architecture)

- **Tên**: .agents/workflows/book-extractor.md
- **Vai trò**: Điều phối bóc tách sách qua 4 sessions độc lập.
- **Sử dụng**: `/book-extractor [Sách] trong [Notebook]`
- **Logic**:
  - S1 (P1): Trích xuất thô → Handoff 1
  - S2 (P2): Vivid Curation & Niêm phong → Handoff 2
  - S3 (P3): Phân giải Audience → Handoff 3
  - S4 (P4): Batch Topics & Rã Atoms → Báo cáo

---

## 🛠️ SESSION 1: KHAI THÁC THÔ (PHASE 1)

### Bước 1: Tiếp nhận Lệnh & Khởi tạo Blackboard (Agent chính thực hiện)

1. **Khởi tạo Thư mục chạy**:
   - Tạo thư mục chạy: `vault/.extraction_runs/[ten-sach-slug]_[YYYY-MM-DD]/` (với slug là tên sách viết thường, không dấu, ngăn cách bằng dấu gạch nối).
2. **Tạo Blackboard**:
   - Tạo tệp `00-blackboard.yaml` trong thư mục chạy để duy trì ngữ cảnh toàn pipeline:
     ```yaml
     book_name: "[Tên Sách]"
     notebook_name: "[Tên Notebook]"
     notebook_id: "" # Sẽ do BookExtractorAgent cập nhật ở Phase 1
     run_folder: "vault/.extraction_runs/[slug]_[YYYY-MM-DD]/"
     cache_file: "vault/02-sources/books/[Tên Sách].md"
     slug: "[slug]"
     current_phase: 1
     ```

### Bước 2 (Phase 1): Trích xuất Sách thô

- **Sub-Agent**: BookExtractorAgent
- **Input**: `book_name`, `notebook_name`, `run_folder`, `cache_file` (từ Blackboard)
- **Output**: `vault/02-sources/books/[Tên Sách].md`, `miner_progress.yaml`
- **Agent chính (BREAKPOINT 1)**:
  1. Chạy POKA-YOKE (dừng nếu FATAL/WARNING). Nếu PASS, in báo cáo.
  2. **Cập nhật Blackboard**: Ghi đè `current_phase: 2`.
  3. **DỪNG TIẾN TRÌNH**. Yêu cầu user mở New Chat và dán Handoff Prompt:
     ```text
     **[Hệ thống] Handoff 1**
     Workflow: `/book-extractor` (Phase 2)
     Sách: [Tên Sách] (ID: [Notebook ID]) | Run: [run_folder] | Cache: [cache_file]
     Trạng thái: Phase 1 PASS. `current_phase: 2`.
     Yêu cầu:
     1. Đọc `.agents\workflows\book-extractor.md`.
     2. Nạp cấu hình từ `00-blackboard.yaml` trong [run_folder].
     3. Kích chạy **Bước 3.5 (Phase 2: Vivid Curation)** ngay lập tức.
     ```

---

## 🧹 SESSION 2: TINH LỌC & NIÊM PHONG (PHASE 2)

### Bước 3: Tiếp nhận Handoff 1 & Khôi phục Context (Chỉ áp dụng ở Session mới)

- **Tác nhân thực hiện**: Agent chính điều phối (khi nhận được Handoff Prompt 1 ở cuộc hội thoại mới).
- **Mục đích**: Nạp lại trạng thái, khôi phục context từ Blackboard tĩnh trên đĩa để bắt đầu Session 2.
- **Input**: Đường dẫn `run_folder` do người dùng cung cấp trong prompt bàn giao.
- **Hành động của Agent chính**:
  1. Sử dụng công cụ đọc tệp tin `00-blackboard.yaml` trong thư mục `run_folder` đã cung cấp.
  2. Nạp toàn bộ các tham số cấu hình (tên sách, notebook, cache file, run folder) vào Context làm việc của Session mới.
  3. Đảm bảo nạp đúng giá trị `current_phase: 2` từ Blackboard.
  4. Tự động chuyển tiếp tiến trình sang **Bước 4 (Phase 2)** để gọi VividCuratorAgent.

### Bước 4 (Phase 2): Tinh lọc & Niêm phong Dữ liệu

- **Sub-Agent**: VividCuratorAgent
- **Quy trình**:
  1. Chạy `extract_vivids.py` → JSON.
  2. Áp dụng rubric VividCurator → sinh `discards.json`.
  3. Chạy `apply_curation.py` → lọc cache, ghi log, chạy sealing (`extract_metadata.py`, `generate_baseline.py`).
- **Output**: Cập nhật cache (thay vivid DISCARD bằng `[NOT_FOUND]`), `session_2/vivid_curation_log.json`, `parsed_metadata.json`, `pipeline_report.md`.
- **Agent chính (BREAKPOINT 2)**:
  1. In báo cáo từ `session_2/vivid_curation_log.json` (KEEP/DISCARD).
  2. **Cập nhật Blackboard**: Ghi đè `current_phase: 3`.
  3. **DỪNG TIẾN TRÌNH**. Yêu cầu user mở New Chat và dán Handoff Prompt:
     ```text
     **[Hệ thống] Handoff 2**
     Workflow: `/book-extractor` (Phase 3)
     Sách: [Tên Sách] | Run: [run_folder] | Cache: [cache_file]
     Trạng thái: Phase 2 PASS. `current_phase: 3`.
     Yêu cầu:
     1. Đọc `.agents\workflows\book-extractor.md`.
     2. Nạp cấu hình từ `00-blackboard.yaml` trong [run_folder].
     3. Khởi chạy **Bước 5 (Phase 3: Audience Matcher)** ngay lập tức.
     ```

---

## 🎯 SESSION 3: PHÂN GIẢI ĐỐI TƯỢNG ĐỘC GIẢ (PHASE 3)

### Bước 5: Tiếp nhận Handoff 2 & Khôi phục Context (Chỉ áp dụng ở Session mới)

- **Tác nhân thực hiện**: Agent chính điều phối (khi nhận được Handoff Prompt 2 ở cuộc hội thoại mới).
- **Mục đích**: Nạp lại trạng thái, khôi phục context từ Blackboard tĩnh trên đĩa để bắt đầu Session 3 (Phase 3: Phân giải Đối tượng Độc giả).
- **Input**: Đường dẫn `run_folder` do người dùng cung cấp trong prompt bàn giao.
- **Hành động của Agent chính**:
  1. Sử dụng công cụ đọc tệp tin `00-blackboard.yaml` trong thư mục `run_folder` đã cung cấp.
  2. Nạp toàn bộ các tham số cấu hình (tên sách, notebook, cache file, run folder) vào Context làm việc của Session mới.
  3. Đảm bảo nạp đúng giá trị `current_phase: 3` từ Blackboard.
  4. Tự động chuyển tiếp tiến trình sang **Bước 6 (Phase 3)** để gọi BookAudienceMatcherAgent.

### Bước 6 (Phase 3): Phân giải Đối tượng Độc giả

- **Sub-Agent**: BookAudienceMatcherAgent
- **Input**: `cache_file`, `run_folder`, `parsed_metadata.json`
- **Output**: `audience_decision_map.json`, các file Audience trong `01-Atomic/Audiences/`
- **Agent chính (BREAKPOINT 3)**:
  1. Đọc kết quả phân giải audience.
  2. **Cập nhật Blackboard**: Ghi đè `current_phase: 4`.
  3. **DỪNG TIẾN TRÌNH**. Yêu cầu user mở New Chat và dán Handoff Prompt:
     ```text
     **[Hệ thống] Handoff 3**
     Workflow: `/book-extractor` (Phase 4)
     Sách: [Tên Sách] | Run: [run_folder] | Cache: [cache_file]
     Trạng thái: Phase 3 PASS. `current_phase: 4`.
     Yêu cầu:
     1. Đọc `.agents\workflows\book-extractor.md`.
     2. Nạp cấu hình từ `00-blackboard.yaml` trong [run_folder].
     3. Khởi chạy **Bước 7 (Phase 4: Topic Gen & Atomize)** ngay lập tức.
     ```

---

## 💎 SESSION 4: TOPIC GEN & PHÂN RÃ ATOMS (PHASE 4)

### Bước 7: Tiếp nhận Handoff 3 & Khôi phục Context (Chỉ áp dụng ở Session mới)

- **Tác nhân thực hiện**: Agent chính điều phối (khi nhận được Handoff Prompt 3 ở cuộc hội thoại mới).
- **Mục đích**: Nạp lại trạng thái, khôi phục context từ Blackboard tĩnh trên đĩa để bắt đầu Session 4 (Phase 4: Topic Gen & Atomize).
- **Input**: Đường dẫn `run_folder` do người dùng cung cấp trong prompt bàn giao.
- **Hành động của Agent chính**:
  1. Sử dụng công cụ đọc tệp tin `00-blackboard.yaml` trong thư mục `run_folder` đã cung cấp.
  2. Nạp toàn bộ các tham số cấu hình (tên sách, notebook, cache file, run folder) vào Context làm việc của Session mới.
  3. Đảm bảo nạp đúng giá trị `current_phase: 4` từ Blackboard.
  4. Tự động chuyển tiếp tiến trình sang **Bước 8 (Phase 4)** để gọi BookParserAgent.

### Bước 8 (Phase 4): Sinh Topics (Batch) & Phân rã Atoms DIKW

- **Sub-Agent**: BookParserAgent
- **Mục đích**: Batch sinh Topics, Semantic Dedup, phân rã Atoms.
- **Input**: `cache_file`, `run_folder`, `audience_decision_map.json`.
- **Output**: Các Atoms ghi vào Obsidian, cập nhật Baseline CSV.
- **Agent chính**: Cập nhật `current_phase: completed` → chuyển Bước 8.5.

### Bước 8.5 (Phase 4): Đóng dấu Metadata ngược lại Nguồn gốc
- **Sub-Agent**: Agent chính điều phối
- **Hành động**: BẮT BUỘC thực thi lệnh sau để chèn metadata vào file markdown nguồn:
  ```powershell
  python .agents/scripts/patch_source_metadata.py --run-folder "[run-folder]"
  ```
- **Agent chính**: Sau khi lệnh chạy thành công, chuyển sang Bước 9.

---

## 🏁 BÁO CÁO NGHIỆM THU

### Bước 9: Báo cáo Nghiệm thu (Agent chính thực hiện)

Khi Phase 4 hoàn tất thành công:
1. Đọc nội dung tệp tin báo cáo `pipeline_report.md` từ run-folder.
2. In ra báo cáo tổng kết chi tiết cho người dùng bao gồm:
   - Tổng quan số lượng Atoms/Vivids thực tế đã lưu đĩa so với Baseline ban đầu.
   - Danh sách các nhóm đối tượng độc giả (Audiences) mới được tạo.
   - Số lượng Atoms bị lỗi hoặc bị cô lập trong vùng cách ly `_DLQ/`.
3. Báo cáo hoàn tất quy trình xử lý sách thành công, an toàn và chính thức nghiệm thu cuốn sách vào Obsidian Vault.
