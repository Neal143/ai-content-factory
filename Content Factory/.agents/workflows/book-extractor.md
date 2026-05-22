---
description: Workflow hợp nhất xử lý sách khép kín từ trích xuất thô, tinh lọc vivid đến phân rã DIKW (Chạy 1 phiên liên tục qua 4 Sub-Agents)
last_update: 21/05/2026 20:30 (GMT+7)
---

# 📖 Workflow: Book Extractor Pipeline

- **Tên file**: .agents/workflows/book-extractor.md
- **Last update**: 21/05/2026 20:30 (GMT+7)
- **Vai trò**: Điều phối quy trình xử lý sách khép kín từ NotebookLM thành các Atoms trong Obsidian Vault.
- **Sử dụng khi**: Người dùng khởi chạy lệnh `/book-extractor [Tên Sách] trong [Tên Notebook]`.
- **Output**: Các Atoms DIKW được phân rã hoàn chỉnh và lưu trữ trong Obsidian Vault.
- **Tóm tắt logic hoạt động**: Khởi tạo Blackboard -> Gọi tuần tự BookExtractorAgent (Trích xuất) -> VividCuratorAgent (Tinh lọc) -> BookAudienceMatcherAgent (Đối tượng độc giả) -> BookParserAgent (Phân rã DIKW) -> In báo cáo tổng hợp.

// turbo-all

---

## Hướng dẫn thực thi

### Bước 1: Tiếp nhận Lệnh & Khởi tạo Blackboard (Agent chính thực hiện)

1. **Khởi tạo Thư mục chạy**:
   - Tạo thư mục chạy: `.extraction_runs/[ten-sach-slug]_[YYYY-MM-DD]/` (với slug là tên sách viết thường, không dấu, ngăn cách bằng dấu gạch nối).
2. **Tạo Blackboard**:
   - Tạo tệp `00-blackboard.yaml` trong thư mục chạy để duy trì ngữ cảnh toàn pipeline:
     ```yaml
     book_name: "[Tên Sách]"
     notebook_name: "[Tên Notebook]"
     notebook_id: "" # Sẽ do BookExtractorAgent cập nhật ở Phase 1
     run_folder: ".extraction_runs/[slug]_[YYYY-MM-DD]/"
     cache_file: "vault/02-sources/books/[Tên Sách].md"
     slug: "[slug]"
     current_phase: 1
     ```

---

### Bước 2 (Phase 1): Trích xuất Sách thô

- **Sub-Agent**: **BookExtractorAgent** (Nhận thức tại `.agents/agents/book-extractor/AGENT.md`)
- **Mục đích**: Trích xuất nội dung sách thô từ NotebookLM thành Raw Markdown có cấu trúc.
- **Input**:
  - `book_name`, `notebook_name`, `run_folder`, `cache_file` từ Blackboard.
- **Output**:
  - File cache thô: `vault/02-sources/books/[Tên Sách].md`
  - Ledger tiến trình: `miner_progress.yaml` trong thư mục chạy.
- **Hành động của Agent chính (BREAKPOINT - GIẢI PHÓNG TOKEN)**:
  1. Chạy chốt chặn an toàn (POKA-YOKE Gate) sau khi sub-agent hoàn tất: Đọc báo cáo chất lượng tại run-folder. Nếu phát hiện lỗi cảnh báo nghiêm trọng (`FATAL` hoặc `WARNING`), tạm dừng tiến trình và báo lỗi cho người dùng.
  2. Nếu đạt yêu cầu (ALL PASS), in báo cáo tổng kết tiến trình khai thác thô Phase 1 trong khung chat.
  3. **Dừng tiến trình chạy của Session hiện tại ở đây** để bảo vệ Context Window (tránh tràn Token do Phase 1 đã ngốn >90% token).
  4. Sinh ra một đoạn **Handoff Prompt** chuyển giao tiến trình chuẩn hóa sử dụng định dạng Markdown Codeblock dưới đây để người dùng dễ dàng copy:
     
     ```text
     **[Hệ thống] Chuyển giao tiến trình xử lý sách (Session Bàn giao)**

     - **Workflow đang chạy**: `/book-extractor` (Pipeline bóc tách sách).
     - **Sách đang xử lý**: [Tên Sách thực tế từ Blackboard] (Notebook ID: [Notebook ID thực tế từ Blackboard])
     - **Run Folder**: [Đường dẫn thực tế của run_folder từ Blackboard]
     - **Cache File**: [Đường dẫn thực tế của cache_file từ Blackboard]
     - **Trạng thái hiện tại**: 
       + Phase 1 (Miner) đã hoàn tất trích xuất thô thành công. Post-Mine Report đạt 100% PASS.
       + Tệp blackboard tĩnh `00-blackboard.yaml` đã cập nhật trạng thái đầu ra `current_phase: 2`.

     **[Yêu cầu thực thi ngay]**
     1. Đọc tệp tin workflow tại d:\AI\AI content factory - v3.7B\.agents\workflows\book-extractor.md để nắm quy trình tổng thể.
     2. Sử dụng công cụ đọc tệp để nạp toàn bộ cấu hình từ `00-blackboard.yaml` trong thư mục chạy [Đường dẫn thực tế của run_folder từ Blackboard] nhằm khôi phục 100% ngữ cảnh trạng thái.
     3. Kích hoạt ngay **Phase 2 (VividCuratorAgent - Tinh lọc & Niêm phong Dữ liệu - Bước 3)** để tiếp tục thực hiện các bước còn lại của workflow. 
     4. Bắt đầu ngay lập tức và không cần giải thích thêm!
     ```
     
  5. Hướng dẫn và nhắc nhở người dùng mở một cuộc hội thoại mới (New Conversation) hoàn toàn sạch sẽ, sau đó dán đoạn prompt bàn giao trên vào để tiếp tục thực hiện Phase 2.

---

### Bước 2.5: Tiếp nhận Handoff & Khôi phục Context (Chỉ áp dụng ở Session mới)

- **Tác nhân thực hiện**: Agent chính điều phối (khi nhận được Handoff Prompt từ người dùng ở cuộc hội thoại mới).
- **Mục đích**: Nạp lại trạng thái, khôi phục context từ Blackboard tĩnh trên đĩa để tiếp tục chạy Phase 2 mà không bị mất dấu vết.
- **Input**: Đường dẫn `run_folder` do người dùng cung cấp trong prompt bàn giao.
- **Hành động của Agent chính**:
  1. Sử dụng lệnh PowerShell/Python đọc nội dung tệp tin `00-blackboard.yaml` trong thư mục `run_folder` đã cung cấp.
  2. Nạp toàn bộ các tham số cấu hình (tên sách, notebook, cache file, run folder) vào Context làm việc của Session mới.
  3. Đảm bảo nạp đúng giá trị `current_phase: 2` từ Blackboard.
  4. Tự động chuyển tiếp tiến trình sang **Bước 3 (Phase 2)** để bắt đầu gọi VividCuratorAgent mà không yêu cầu người dùng nhập lại bất kỳ tham số cấu hình nào khác.

---

### Bước 3 (Phase 2): Tinh lọc & Niêm phong Dữ liệu

- **Sub-Agent**: **VividCuratorAgent** (Nhận thức tại `.agents/agents/curate-vivids/AGENT.md`)
- **Mục đích**: Đánh giá chất lượng vivid metadata, lọc bỏ các vivid sáo rỗng hoặc bịa đặt, và thực hiện niêm phong dữ liệu cuốn sách.
- **Input**:
  - `book_name`, `cache_file`, `run_folder` từ Blackboard.
- **Output**:
  - Cập nhật đè lên file cache `vault/02-sources/books/[Tên Sách].md` (thay các vivid DISCARD thành `[NOT_FOUND]`).
  - Curation log: `vivid_curation_log.json`
  - Các tệp niêm phong: `parsed_metadata.json` và `pipeline_report.md` (baseline) trong run-folder.
- **Hành động của Agent chính**:
  - Cập nhật Blackboard `current_phase: 3` và tự động chuyển tiếp sang Phase 3.

---

### Bước 4 (Phase 3): Phân giải Đối tượng Độc giả

- **Sub-Agent**: **BookAudienceMatcherAgent** (Nhận thức tại `.agents/agents/book-audience-matcher/AGENT.md`)
- **Mục đích**: Phân giải JTBD và so khớp Semantic để map/tạo các file đối tượng độc giả vật lý.
- **Input**:
  - `cache_file`, `run_folder` từ Blackboard và tệp metadata đã niêm phong `parsed_metadata.json`.
- **Output**:
  - Bản đồ quyết định độc giả: `audience_decision_map.json` ghi nhận trên đĩa trong run-folder.
  - Các file đối tượng độc giả vật lý mới tạo trong `01-Atomic/Audiences/`.
- **Hành động của Agent chính**:
  - Cập nhật Blackboard `current_phase: 4` và tự động chuyển tiếp sang Phase 4.

---

### Bước 5 (Phase 4): Phân rã Atoms DIKW

- **Sub-Agent**: **BookParserAgent** (Nhận thức tại `.agents/agents/book-parser/AGENT.md`)
- **Mục đích**: Phân rã cấu trúc sách thành các file Atoms vật lý lưu vào Obsidian Vault.
- **Input**:
  - `cache_file`, `run_folder` từ Blackboard và bản đồ độc giả `audience_decision_map.json`.
- **Output**:
  - Các file Atom vật lý (Circumstance, Concept, Insight, Solution) được ghi xuống Obsidian Vault.
  - Cập nhật Baseline CSV.
- **Hành động của Agent chính**:
  - Cập nhật Blackboard `current_phase: completed` và tự động chuyển sang Bước 6.

---

### Bước 6: Báo cáo Nghiệm thu (Agent chính thực hiện)

Khi Phase 4 hoàn tất thành công:
1. Đọc nội dung tệp tin báo cáo `pipeline_report.md` từ run-folder.
2. In ra báo cáo tổng kết chi tiết cho người dùng bao gồm:
   - Tổng quan số lượng Atoms/Vivids thực tế đã lưu đĩa so với Baseline ban đầu.
   - Danh sách các nhóm đối tượng độc giả (Audiences) mới được tạo.
   - Số lượng Atoms bị lỗi hoặc bị cô lập trong vùng cách ly `_DLQ/`.
3. Báo cáo hoàn tất quy trình xử lý sách thành công và an toàn.
