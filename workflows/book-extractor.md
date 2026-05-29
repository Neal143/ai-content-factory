---
description: Workflow hợp nhất xử lý sách khép kín từ trích xuất thô, tinh lọc vivid đến phân rã DIKW (Chạy phân đoạn qua 4 Session độc lập để giải phóng Token Context Window)
last_update: 30/05/2026 06:15 (GMT+7)
---

# 📖 Workflow: Book Extractor Pipeline (4-Session Architecture)

- **Tên file**: .agents/workflows/book-extractor.md
- **Last update**: 28/05/2026 22:35 (GMT+7)
- **Vai trò**: Điều phối quy trình xử lý sách khép kín từ NotebookLM thành các Atoms trong Obsidian Vault thông qua 3 phiên làm việc tách biệt.
- **Sử dụng khi**: Người dùng khởi chạy lệnh `/book-extractor [Tên Sách] trong [Tên Notebook]`.
- **Output**: Các Atoms DIKW được phân rã hoàn chỉnh và lưu trữ trong Obsidian Vault.
- **Tóm tắt logic hoạt động**: 
  - Session 1 (Phase 1): Trích xuất sách thô từ NotebookLM -> Báo cáo & Handoff 1.
  - Session 2 (Phase 2): Tinh lọc vivid (Vivid Curation) & Niêm phong dữ liệu -> Báo cáo & Handoff 2.
  - Session 3 (Phase 3): Phân giải đối tượng độc giả → Báo cáo & Handoff 3.
  - Session 4 (Phase 4): Sinh Topics (batch processing) & Phân rã các Atoms DIKW vật lý vào Obsidian Vault.

---

## 🛠️ SESSION 1: KHAI THÁC THÔ (PHASE 1)

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

### Bước 2 (Phase 1): Trích xuất Sách thô

- **Sub-Agent**: **BookExtractorAgent** (Nhận thức tại `.agents/agents/book-extractor/AGENT.md`)
- **Mục đích**: Trích xuất nội dung sách thô từ NotebookLM thành Raw Markdown có cấu trúc.
- **Input**:
  - `book_name`, `notebook_name`, `run_folder`, `cache_file` từ Blackboard.
- **Output**:
  - File cache thô: `vault/02-sources/books/[Tên Sách].md`
  - Ledger tiến trình: `miner_progress.yaml` trong thư mục chạy.
- **Hành động của Agent chính (BREAKPOINT 1 - GIẢI PHÓNG TOKEN)**:
  1. Chạy chốt chặn an toàn (POKA-YOKE Gate) sau khi sub-agent hoàn tất: Đọc báo cáo chất lượng tại run-folder. Nếu phát hiện lỗi cảnh báo nghiêm trọng (`FATAL` hoặc `WARNING`), tạm dừng tiến trình và báo lỗi cho người dùng.
  2. Nếu đạt yêu cầu (ALL PASS), in báo cáo tổng kết tiến trình khai thác thô Phase 1 trong khung chat.
  3. **Cập nhật Blackboard**: Ghi đè thuộc tính `current_phase: 2` vào tệp tin `00-blackboard.yaml`.
  4. **Dừng tiến trình chạy của Session hiện tại ở đây** để giải phóng Token Context Window (tránh tràn Token do Phase 1 đã ngốn >90% token).
  5. Sinh ra một đoạn **Handoff Prompt 1** sử dụng định dạng Markdown Codeblock dưới đây để người dùng dễ dàng copy sang cuộc hội thoại mới:
     
     ```text
     **[Hệ thống] Chuyển giao tiến trình xử lý sách (Session Bàn giao 1)**

     - **Workflow đang chạy**: `/book-extractor` (Pipeline bóc tách sách - Phase 2).
     - **Sách đang xử lý**: [Tên Sách thực tế từ Blackboard] (Notebook ID: [Notebook ID thực tế từ Blackboard])
     - **Run Folder**: [Đường dẫn thực tế của run_folder từ Blackboard]
     - **Cache File**: [Đường dẫn thực tế của cache_file từ Blackboard]
     - **Trạng thái hiện tại**: 
       + Phase 1 (Miner) đã hoàn tất trích xuất thô thành công. Post-Mine Report đạt 100% PASS.
       + Tệp blackboard tĩnh `00-blackboard.yaml` đã cập nhật trạng thái đầu ra `current_phase: 2`.

     **[Yêu cầu thực thi ngay]**
     1. Đọc tệp tin workflow tại d:\AI\AI content factory - v3.7B\.agents\workflows\book-extractor.md để nắm quy trình tổng thể.
     2. Sử dụng công cụ đọc tệp để nạp toàn bộ cấu hình từ `00-blackboard.yaml` trong thư mục chạy [Đường dẫn thực tế của run_folder từ Blackboard] nhằm khôi phục 100% ngữ cảnh trạng thái.
     3. Kích hoạt ngay **Bước 3.5 (Phase 2: Vivid Curation - Tinh lọc & Niêm phong Dữ liệu)** để bắt đầu phiên làm việc thứ 2.
     4. Bắt đầu ngay lập tức và không cần giải thích thêm!
     ```
     
  6. Hướng dẫn người dùng mở một cuộc hội thoại mới (New Conversation) hoàn toàn sạch sẽ, sau đó dán đoạn prompt bàn giao trên vào để tiếp tục thực hiện Phase 2.

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

- **Sub-Agent**: **VividCuratorAgent** (Nhận thức tại `.agents/agents/curate-vivids/AGENT.md`)
- **Mục đích**: Đánh giá chất lượng vivid metadata, lọc bỏ các vivid sáo rỗng hoặc bịa đặt, và thực hiện niêm phong dữ liệu cuốn sách.
- **Input**:
  - `book_name`, `cache_file`, `run_folder` từ Blackboard.
- **Quy trình thực thi**: Triệu gọi các script tự động hóa theo chuẩn `.agents/skills/curate-vivids/SKILL.md`:
  1. Gọi `extract_vivids.py` để trích xuất candidates kèm ngữ cảnh chunk chi tiết sang JSON.
  2. Chấp hành các bộ lọc loại thải và rubric đánh giá của VividCurator để sinh `discards.json`.
  3. Gọi `apply_curation.py` để lọc file cache thô, ghi curation log và tự động chạy các sealing scripts (`extract_metadata.py` + `generate_baseline.py`).
- **Output**:
  - Cập nhật đè lên file cache `vault/02-sources/books/[Tên Sách].md` (thay các vivid DISCARD thành `[NOT_FOUND]`).
  - Curation log: `vivid_curation_log.json`
  - Các tệp niêm phong: `parsed_metadata.json` và `pipeline_report.md` (baseline) trong run-folder.
- **Hành động của Agent chính (BREAKPOINT 2 - GIẢI PHÓNG TOKEN)**:
  1. Đọc nội dung file `vivid_curation_log.json` để in ra báo cáo tổng kết chi tiết số lượng vivid đã giữ lại (KEEP) và bị loại bỏ (DISCARD).
  2. **Cập nhật Blackboard**: Ghi đè thuộc tính `current_phase: 3` vào tệp tin `00-blackboard.yaml`.
  3. **Dừng tiến trình chạy của Session hiện tại ở đây** để bảo vệ Context Window khỏi sự tích lũy token trước khi bước vào khâu phân rã Atoms vô cùng nặng nề.
  4. Sinh ra một đoạn **Handoff Prompt 2** sử dụng định dạng Markdown Codeblock dưới đây để người dùng dễ dàng copy sang cuộc hội thoại mới:

     ```text
     **[Hệ thống] Chuyển giao tiến trình xử lý sách (Session Bàn giao 2)**

     - **Workflow đang chạy**: `/book-extractor` (Pipeline bóc tách sách - Phase 3: Phân giải Đối tượng Độc giả).
     - **Sách đang xử lý**: [Tên Sách thực tế từ Blackboard]
     - **Run Folder**: [Đường dẫn thực tế của run_folder từ Blackboard]
     - **Cache File**: [Đường dẫn thực tế của cache_file từ Blackboard]
     - **Trạng thái hiện tại**: 
       + Phase 2 (Vivid Curation) đã hoàn tất tinh lọc vivid, ghi log curation và niêm phong dữ liệu thô thành công.
       + Tệp blackboard tĩnh `00-blackboard.yaml` đã cập nhật trạng thái đầu ra `current_phase: 3`.

     **[Yêu cầu thực thi ngay]**
     1. Đọc tệp tin workflow tại d:\AI\AI content factory - v3.7B\Content Factory\.agents\workflows\book-extractor.md để nắm quy trình tổng thể.
     2. Sử dụng công cụ đọc tệp để nạp toàn bộ cấu hình từ `00-blackboard.yaml` trong thư mục chạy [Đường dẫn thực tế của run_folder từ Blackboard] nhằm khôi phục 100% ngữ cảnh trạng thái.
     3. Khởi chạy ngay **Bước 5 (Phase 3: Phân giải Đối tượng Độc giả)** để thực hiện phân giải audience.
     4. Bắt đầu ngay lập tức và không cần giải thích thêm!
     ```

  5. Hướng dẫn người dùng mở một cuộc hội thoại mới (New Conversation) hoàn toàn sạch sẽ, sau đó dán đoạn prompt bàn giao trên vào để tiếp tục thực hiện Phase 3 & 4.

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

- **Sub-Agent**: **BookAudienceMatcherAgent** (Nhận thức tại `.agents/agents/book-audience-matcher/AGENT.md`)
- **Mục đích**: Phân giải JTBD và so khớp Semantic để map/tạo các file đối tượng độc giả vật lý.
- **Input**:
  - `cache_file`, `run_folder` từ Blackboard và tệp metadata đã niêm phong `parsed_metadata.json`.
- **Output**:
  - Bản đồ quyết định độc giả: `audience_decision_map.json` ghi nhận trên đĩa trong run-folder.
  - Các file đối tượng độc giả vật lý mới tạo trong `01-Atomic/Audiences/`.
- **Hành động của Agent chính**:
- **Hành động của Agent chính (BREAKPOINT 3 - GIẢI PHÓNG TOKEN)**:
  1. Đọc kết quả phân giải audience từ BookAudienceMatcherAgent.
  2. **Cập nhật Blackboard**: Ghi đè `current_phase: 4` vào `00-blackboard.yaml`.
  3. **Dừng tiến trình chạy của Session hiện tại ở đây** để giải phóng Token Context Window.
  4. Sinh ra một đoạn **Handoff Prompt 3** sử dụng định dạng Markdown Codeblock:

     ```text
     **[Hệ thống] Chuyển giao tiến trình xử lý sách (Session Bàn giao 3)**

     - **Workflow đang chạy**: `/book-extractor` (Pipeline bóc tách sách - Phase 4: Topic Gen & Atomize).
     - **Sách đang xử lý**: [Tên Sách thực tế từ Blackboard]
     - **Run Folder**: [Đường dẫn thực tế của run_folder từ Blackboard]
     - **Cache File**: [Đường dẫn thực tế của cache_file từ Blackboard]
     - **Trạng thái hiện tại**: 
       + Phase 3 (Audience Matcher) đã hoàn tất phân giải đối tượng độc giả thành công.
       + Audience Decision Map đã ghi tại [run_folder]/audience_decision_map.json.
       + Tệp blackboard tĩnh `00-blackboard.yaml` đã cập nhật trạng thái `current_phase: 4`.

     **[Yêu cầu thực thi ngay]**
     1. Đọc tệp tin workflow tại d:\AI\AI content factory - v3.7B\Content Factory\.agents\workflows\book-extractor.md để nắm quy trình tổng thể.
     2. Sử dụng công cụ đọc tệp để nạp toàn bộ cấu hình từ `00-blackboard.yaml` trong thư mục chạy [Đường dẫn thực tế của run_folder từ Blackboard] nhằm khôi phục 100% ngữ cảnh trạng thái.
     3. Khởi chạy ngay **Bước 7 (Phase 4: Topic Gen & Atomize)** để hoàn tất quy trình.
     4. Bắt đầu ngay lập tức và không cần giải thích thêm!
     ```

  5. Hướng dẫn người dùng mở một cuộc hội thoại mới (New Conversation) hoàn toàn sạch sẽ, sau đó dán đoạn prompt bàn giao trên vào để tiếp tục thực hiện Phase 4.

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

- **Sub-Agent**: **BookParserAgent** (Nhận thức tại `.agents/agents/book-parser/AGENT.md`)
- **Mục đích**: Sinh Topics tự động qua batch processing, chạy Semantic Dedup, rồi phân rã cấu trúc sách thành các file Atoms vật lý lưu vào Obsidian Vault.
- **Input**:
  - `cache_file`, `run_folder` từ Blackboard và bản đồ độc giả `audience_decision_map.json`.
- **Output**:
  - Các file Atom vật lý (Circumstance, Concept, Insight, Solution) được ghi xuống Obsidian Vault.
  - Cập nhật Baseline CSV.
- **Hành động của Agent chính**:
  - Cập nhật Blackboard `current_phase: completed` và tự động chuyển sang Bước 9.

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
