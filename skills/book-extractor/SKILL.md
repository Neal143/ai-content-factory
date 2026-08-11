---
name: Book Extractor (The Miner)
description: Kỹ năng chuyên môn giao tiếp với NotebookLM để trích xuất sách theo chiến lược Hybrid Flatten TOC và vòng lặp phân rã Chunk. Bao gồm Mapper Validation Gate, 8-Point Quality Gate (script + Agent), Normalizer Pass, và Semantic Integrity Check.
---

---
> 🤖 **SYSTEM INSTRUCTION (AGENT):** Tra cứu bản đồ rẽ nhánh bên dưới để định vị trạng thái hiện tại, sau đó nhảy xuống mục tương ứng trong thân bài để đọc chi tiết lệnh.
> ⚠️ Nếu có mâu thuẫn giữa Reference Card và hướng dẫn chi tiết bên dưới → **hướng dẫn chi tiết là chuẩn.**

```text
=== BOOK EXTRACTOR — STATE MACHINE REFERENCE CARD ===

[B0]   PRE-FLIGHT         → Tạo run-folder → nlm source list → add nếu thiếu mapper-v4 / miner-v4

[B1]   MAPPER             → NLM query → lưu mapper_raw.md

[B1.5] MAPPER GATE        → prepare_mapper.py → Kiểm tra 4 điểm
         ├─ Fail [1]      → NLM bổ sung → re-Gate
         ├─ Fail [2]      → DỪNG báo User
         ├─ Fail [3]      → Agent strip format → re-Gate
         ├─ Fail [4]      → Agent chèn sentinel → re-Gate
         └─ PASS 4/4      → User Review TOC Gate → User xác nhận → B2

[B2]   LEDGER + MINER LOOP
       Khởi tạo: init_ledger.py → mở editor cho User

       Resume (nếu có ledger cũ): Đọc ledger → verify cache → sync nếu mismatch → tiếp PENDING nhỏ nhất

       Loop: ① next_chunk.py → ② NLM query → save_raw → gate_checker (Auto-Repair + Script Gates)
      gate_checker: [SHIFT-LEFT] normalize → [1-2] Cấu trúc | [3-5] Nội dung | [6] Optional | [7] Link Khóa Ngoại
  → ③ đọc kết quả
  ├─ PASS Script Gate    → ④ Agent Gate [8] → ghi agent_gate.json
  │     ├─ PASS          → append_cache → ⑤ update ledger → ①
  │     └─ FAIL [8]      → NLM hiệu đính → re-eval (1x) → fallback: append +warning → ⑤ → ①
         ├─ SUPPLEMENT [3-6]    → NLM trích xuất lại toàn bộ chunk → re-gate (2x) → fallback: append ±warning → ⑤ → ①
         ├─ RETRY [1]           → re-query (2x) → SKIPPED + append skeleton
         ├─ RETRY [2]           → re-query (2x) → FATAL
         ├─ RETRY mạng ②-a     → re-query (3x) → FATAL
         └─ FATAL [2]           → ledger FATAL, không append → ⑤ → ①
       done:true → B3

[B3]   POST-MINE           → post_mine.py: Sentinel → Count → Integrity Audit → Normalizer
                            └─ FATAL → DỪNG báo User

[B4]   AUDIT + REPORT      → audit_cache.py: Gates [1-6] per-chunk + mining stats
         ├─ ALL PASS        → B5
         └─ Có FAIL         → DỪNG báo User (re-mine hoặc chấp nhận)

[B5]   NO GRAPH ROUTING     → Trả cache file + run-folder về /extract-book pipeline
```
---

# Book Extractor Skill (The Miner)

// turbo-all

Bạn là chuyên gia điều phối trích xuất sách quy mô lớn. Nhiệm vụ của bạn là chẻ nhỏ sách, giao tiếp với NotebookLM thông qua **CLI `nlm`** (cài global) để truyền Prompt và đào mỏ tri thức thô. File cấu trúc cuối cùng được lưu Cache tại `vault/02-sources/books/[Tên Sách].md`.

> 📐 **Chuẩn cấu trúc file output:** Mọi file sách xuất ra phải tuân thủ schema tại
> `.agents/skills/book-extractor/references/raw-book-structure.md`

---

## QUY TẮC VỆ SINH (HYGIENE)

1. **TASK ĐẦU TIÊN:** Ngay khi nhận lệnh khởi tạo, BẮT BUỘC TẠO THƯ MỤC TRƯỚC: `vault/extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
   → Thư mục này được gọi tắt là **[run-folder]** trong toàn bộ tài liệu này. Mọi hành động CLI chỉ được phép thực hiện SAU KHI thư mục này đã tồn tại.
2. MỌI file phụ trợ (scripts, logs, raw responses, ledger YAML, tmp output) → ghi vào **[run-folder]**.
   ⚠️ BẮT BUỘC dùng path đầy đủ: `vault/extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/[tên-file]`
   TUYỆT ĐỐI KHÔNG dùng tên file bare (vd: `t.json`, `output.json`) — hệ thống sẽ ghi nhầm ra root workspace.
3. **CẤM REDIRECT RA ROOT:** Khi dùng công cụ (như `run_command`) cho tác vụ chạy script, KHÔNG sử dụng toán tử chuyển hướng `> file.txt` vào root. Hãy đọc trực tiếp Standard Output. Nếu bắt buộc xuất log/file tạm, tham số `Cwd` phải là `[run-folder]` hoặc redirect dùng đường dẫn tuyệt đối xuất vào `[run-folder]`.
4. File output CUỐI CÙNG (raw book đã qua Normalizer) → ghi vào `vault/02-sources/books/[Tên Sách].md`
5. TUYỆT ĐỐI KHÔNG sinh file trực tiếp ở root workspace.

---

## Hướng dẫn hoạt động

### Bước 0: Pre-flight & Khởi tạo Run Folder

- **Phải đảm bảo `[run-folder]` đã tồn tại theo Quy tắc vệ sinh số 1.**
- Kiểm tra NotebookLM sources qua CLI:
  - Gọi `nlm source list <notebook_id>` → kiểm tra danh sách sources theo title.
  - Nếu chưa có source title chứa `prompt-mapper-v4.md`:
    Gọi CLI: `nlm source add <notebook_id> --file "[Đường dẫn tuyệt đối tới .agents/skills/book-extractor/prompt-mapper-v4.md]" --wait`
  - Nếu chưa có source title chứa `prompt-miner-v4.md`:
    Gọi CLI: `nlm source add <notebook_id> --file "[Đường dẫn tuyệt đối tới .agents/skills/book-extractor/prompt-miner-v4.md]" --wait`
  - Nếu chưa có source title chứa `prompt-jtbd-chunk-v1.md`:
    Gọi CLI: `nlm source add <notebook_id> --file "[Đường dẫn tuyệt đối tới .agents/skills/book-extractor/prompt-jtbd-chunk-v1.md]" --wait`

### Bước 1: The Mapper (Sinh Tổng quan & Mục Lục)

- Agent gọi script Orchestrator: `python .agents/skills/book-extractor/scripts/run_mapper.py "[run-folder]"`
- Lệnh tự động đọc data, gọi NLM và lưu kết quả vào `[run-folder]/session_1/mapper_raw.md`. 
  ⚠️ Nếu script trả error code ≠ 0 → retry tối đa 2 lần. Đọc stderr để chẩn đoán.

### Bước 1.5: Mapper Validation Gate

Agent gọi Core Script:
`python .agents/skills/book-extractor/scripts/prepare_mapper.py "[run-folder]" "[Tên Sách]"`

Script phân tích `mapper_raw.md`, làm sạch META, ghi file xương sống vào vault `vault/02-sources/books/[Tên Sách].md`, rồi chạy 4-point validation. Agent đọc JSON verdict từ stdout:
- `"passed": false` → hành động theo `verdict` tương ứng từng check fail:
  - `header_complete` fail → Gửi NLM query bổ sung mục thiếu, chạy lại script
  - `toc_integrity` fail → DỪNG báo User
  - `format_clean` fail → Agent strip markdown formatting trong cache file, chạy lại script
  - `sentinel_exists` fail → Agent chèn `<!-- HEADER_END -->` vào đúng vị trí, chạy lại script
- `"passed": true` → **User Review TOC Gate:**
  1. Mở file `user_action.file` trong editor cho User.
  2. Gửi nội dung `user_action.message` cho User.
  3. **DỪNG** — Chờ User phản hồi (Tuân thủ `agent_instruction`).
  4. Nếu User nói "tiếp tục" → Bước 2.
  5. Nếu User nói "đã sửa xong" → chạy lại `prepare_mapper.py` để re-validate → PASS thì Bước 2, FAIL thì xử lý verdict rồi quay lại gate.

### Bước 2: Khởi tạo Ledger + The Miner (Vòng lặp Agent-Orchestrated)

**Khởi tạo Ledger:**
`python .agents/skills/book-extractor/scripts/init_ledger.py "[run-folder]" "[cache-file]" "[notebook_id]"`

Script tạo `miner_progress.yaml` tự động từ thông tin trong cache file. Nếu file đã tồn tại → dùng Resume Protocol.
Sau khi tạo, **mở file `miner_progress.yaml` trong editor** để user theo dõi.


**Vòng lặp Miner (Agent điều phối per-chunk):**

Agent điều phối vòng lặp, gọi NLM qua CLI (`nlm`) và script `gate_checker.py` xử lý **từng chunk một**.
Agent **KHÔNG ĐƯỢC PHÉP** tự viết code lập trình vòng lặp hay dùng Python tự chế.

**🔄 Resume Protocol (Khi tiếp tục run bị dừng giữa chừng):**

Nếu đây KHÔNG phải run mới (tức `miner_progress.yaml` đã tồn tại và có chunk DONE):
1. Đọc `miner_progress.yaml` → xác nhận `mapper_completed: true`.
2. Đọc file cache `vault/02-sources/books/[Tên Sách].md`:
   - Verify `<!-- HEADER_END -->` tồn tại.
   - Đếm `<data_chunk>` trong file = số chunks có `status: DONE` trong ledger.
3. Nếu mismatch (đếm ≠ DONE count) → chạy `post_mine.py` Phase 1+2 trước khi mine tiếp.
4. Nếu OK → tiếp tục từ chunk PENDING nhỏ nhất bình thường.

**LẶP cho đến khi không còn chunk PENDING:**

**① Nhận lệnh chunk tiếp theo:**
Agent **LUÔN** chạy `next_chunk.py` ở đầu mỗi vòng lặp (1 chunk), Agent chạy core script:
  `python .agents/skills/book-extractor/scripts/next_chunk.py "[run-folder]/session_1/miner_progress.yaml" "[run-folder]/session_1/cache_file.md"`
Script trả JSON chứa: `chunk_index`, `chunk_nn`, `chunk_name`, `raw_file`, `cache_file`, `progress`, `cli_run_jtbd`, `cli_run_miner`, `cli_gate_checker`, `cli_append_cache`.
⚠️ Agent dùng **TRỰC TIẾP** các lệnh CLI và paths từ JSON. KHÔNG tự compose, KHÔNG sửa, KHÔNG dùng trí nhớ.
Nếu `"done": true` → thoát vòng lặp, chuyển Bước 3.

**② Agent gọi NLM qua CLI (2-Phase Extraction):**

**Phase 1 — JTBD Identification:**

**②-1a.** Agent gọi script chạy JTBD:
  Agent chạy trực tiếp lệnh được cung cấp trong trường `cli_run_jtbd` của `next_chunk.py`.
  Script sẽ tự động đọc dữ liệu, gọi NLM và lưu kết quả vào thư mục `jtbd_raw`.
  ⚠️ Nếu script trả error code ≠ 0 → báo lỗi mạng, retry max 3 lần. Đọc stderr để chẩn đoán.

**②-1b.** Agent gọi gate_checker.py chế độ JTBD-only:
  `python .agents/skills/book-extractor/scripts/gate_checker.py "[run-folder]/session_1/jtbd_raw/chunk_NN_jtbd.txt" [chunk_index] "READ_FROM_CACHE" --jtbd-only`
  (Không truyền tên tiếng Việt vào tham số 3 để tránh lỗi PowerShell).

**②-1c.** Đọc kết quả từ file `[run-folder]/session_1/jtbd_raw/chunk_NN_jtbd_gate.json` → lấy trường `type`:
→ `"JTBD_PASS"` → Lưu `audience` và `evidence` cho Phase 2. Chuyển Phase 2.
→ `"JTBD_SKIP"` → Chunk không có JTBD. **Bỏ qua hoàn toàn Phase 2.** Cập nhật ledger thành DONE:
   `python .agents/skills/book-extractor/scripts/update_ledger.py "[ledger_path]" [chunk_index] DONE`
   Thông báo cho user: `"Chunk NN: [NO_JTBD_FOUND] — bỏ qua trích xuất, chuyển chunk tiếp theo."`
   Quay lại bước ①.
→ `"JTBD_RETRY"` → Agent đọc `violation_detail` từ gate file, rồi chạy lại `cli_run_jtbd` nhưng **nối thêm** `--feedback "[violation_detail]"`. Ví dụ:
   `python .../run_jtbd.py "[run-folder]" [chunk_index] "[cache_file]" --feedback "main_job: Loi [2] CAM dung VA/HOAC gop nhieu y"`
   Script sẽ nối feedback vào query gửi NLM → NLM biết lần trước sai gì → xác suất sửa đúng cao hơn.
   Lưu đè file `chunk_NN_jtbd.txt`, chạy lại gate_checker.
   Hết `max_retry` (3 lần) → Dùng `[NO_JTBD_FOUND]` làm fallback. Cập nhật ledger DONE, bỏ qua Phase 2, chuyển chunk sau (xử lý giống `JTBD_SKIP`).

**Phase 2 — Content Extraction:**

**②-2a.** Agent gọi script chạy Content:
  Agent chạy trực tiếp lệnh được cung cấp trong trường `cli_run_miner` của `next_chunk.py`.
  Script sẽ tự động ghép Audience, Evidence từ Phase 1, gọi NLM và lưu kết quả vào `raw_file`.
  ⚠️ Nếu script trả error code ≠ 0 → báo lỗi mạng, retry max 3 lần. Đọc stderr để chẩn đoán.

**②-2c.** Agent gọi inject_jtbd.py (đọc JTBD từ Phase 1 response file, không truyền tiếng Việt qua CLI args):
  `python .agents/skills/book-extractor/scripts/inject_jtbd.py "[raw_file]" --jtbd-response "[run-folder]/session_1/jtbd_raw/chunk_NN_jtbd.txt"`

**②-2d.** Agent gọi gate_checker.py (full mode — lệnh lấy từ `cli_gate_checker` của `next_chunk.py`):
  → Gate [3] tự PASS (JTBD đã inject). Gates [1-2, 4-7] kiểm tra nội dung.

**③ Đọc kết quả Gate [1-7] (từ Phase 2):**

**Xử lý `filler_warning`:**

NLM đôi khi hallucination loop — chèn các cụm từ có nghĩa nhưng KHÔNG liên quan nội dung
vào nhiều câu khác nhau (ví dụ: "sùng kính" chèn vào câu nói về giày, áo, thức ăn).
Script `gate_checker.py` dùng frequency analysis phát hiện bigrams lặp ≥6 lần/chunk.

Nếu output `gate_checker.py` chứa `⚠️ Gate [1.5] WARNING`:
1. Đọc bigrams bị flag cùng các câu ví dụ (context) được in ra ngay bên dưới.
2. Đánh giá trực tiếp từ các câu ví dụ đó:
   - Bigrams **chèn vô nghĩa** ở nhiều câu không liên quan → tự retry NLM
   - Bigrams **là thuật ngữ chuyên môn** dùng nhất quán → bỏ qua, tiếp tục
   - **Không chắc** → hỏi user

Đọc file `[run-folder]/session_1/chunk_NN_gate.json` → lấy trường `next_action`. Agent thực thi TRỰC TIẾP theo `next_action.type`:

→ `"AGENT_EVAL"` → Chuyển bước ④.
→ `"RETRY"` → Gọi lại NLM query Phase 2, lưu đè raw file, inject JTBD lại, chạy lại gate_checker.
   Hết `max_retry` → dùng `on_exhaust.ledger_update` gọi `update_ledger.py`. KHÔNG append. Tiếp chunk sau.
→ `"SUPPLEMENT"` → Gọi NLM yêu cầu trích xuất LẠI TOÀN BỘ chunk (không phải chỉ phần thiếu), nhấn mạnh đảm bảo có đầy đủ phần bị thiếu (dựa vào `missing_detail`). Lưu đè raw file, inject JTBD, chạy lại gate_checker.
   Hết `max_retry` → dùng `on_exhaust.cli_append` và `on_exhaust.ledger_update`.

**④ Agent đánh giá Gate [8] (Semantic Alignment):**
Đọc file `[run-folder]/session_1/chunk_NN_raw.txt`. Thực hiện:

**[8] SEMANTIC ALIGNMENT (Agent chấm điểm):**
- Trục 1 (Audience→Insight): JTBD Audience có khớp chặt với Insight không? Chấm 1-5.
- Trục 2 (Insight→Knowledge): Tri thức có thực sự hỗ trợ Insight không? Chấm 1-5.
- ⚠️ **Mỗi trục riêng lẻ phải đạt điểm số ≥ 4.** Bất kỳ trục nào có điểm số < 4 đều FAIL.

**⛔ BẮT BUỘC GHI LOG:** Dùng `agent_gate_template` từ `next_action` để tạo file `agent_gate.json`:
  - Điền các giá trị đánh giá vào template → ghi vào path `next_action.agents_gate_file`.
  - Verdict hợp lệ: `"PASS"` | `"FAIL_AXIS_1"` | `"FAIL_AXIS_2"`
  ❌ Agent KHÔNG ĐƯỢC gọi `append_cache.py` nếu chưa ghi file này.

**Quyết định của Agent (dựa trên verdict + lệnh từ `next_action`):**

→ PASS [8]: Gọi `next_action.on_pass.cli_append`. Dùng `next_action.on_pass.ledger_update`.
→ FAIL [8] (nếu có trục bị chấm điểm < 4): Thực hiện theo `next_action.on_fail_axis` (NLM hiệu đính, max 1 retry, fallback CLI).

**⑤ Cập nhật Ledger + Tiếp tục:**
Gọi script `update_ledger.py` với `status` và `error_code` lấy từ `next_action.ledger_update`:
  `python .agents/skills/book-extractor/scripts/update_ledger.py "[run-folder]/session_1/miner_progress.yaml" <chunk_index> <status> [error_code]`
  Script trả JSON summary gồm `progress` và `milestone`. Nếu `milestone: true` → in progress summary.
  Quay lại bước ①.

Lưu ý: Noise format (**, `, ngoặc kép) KHÔNG phải lý do retry — Normalizer (Bước 3) sẽ xử lý.

**⛔ KẾT THÚC LOOP → BẮT BUỘC gọi Bước 3 (Post-Mine) ngay lập tức.**


---

### Bước 3: Post-Mine + Normalizer Pass

**Agent gọi Script khi kết thúc vòng lặp Bước 2:**
`python .agents/skills/book-extractor/scripts/post_mine.py "[path-to-cache-file]" --run-folder "[run-folder]"`

Script thực thi 4 giai đoạn tự động (Sentinel → Count → Integrity Audit → Normalizer), ghi report vào `[run-folder]/session_1/post_mine_report.txt`.

**⛔ POST-MINE MANDATORY CHECKPOINT:**
Ngay khi terminal in ra "POST-MINE COMPLETE", Agent có nghĩa vụ NGAY LẬP TỨC:
1. Đọc nội dung file `[run-folder]/session_1/post_mine_report.txt`
2. Nếu không chứa "FATAL" → TIẾN THẲNG sang Bước 4 (Audit + Report).
❌ Nếu chứa "FATAL" → DỪNG NGAY. Report lỗi cho User. KHÔNG tiếp sang Bước 4.

### Bước 4: Audit + Report (POKA-YOKE cuối cùng)

Agent gọi script:
`python .agents/skills/book-extractor/scripts/audit_cache.py "vault/02-sources/books/[Tên Sách].md" --ledger "[run-folder]/session_1/miner_progress.yaml" --report "[run-folder]/pipeline_report.md"`

Script thực hiện 2 việc:
1. **Quality Audit**: Chạy Gates [1-6] trên từng chunk trong file vault đã normalize.
2. **Mining Stats**: Đọc ledger → thống kê DONE/SKIPPED/FATAL + warning types.

→ ALL PASS → Chuyển sang Bước 5 (Hệ thống đã tự động format cache ngầm).
→ Có FAIL → DỪNG. Báo user danh sách chunk FAIL kèm chi tiết gate.
  User quyết định: (1) Re-mine chunks đó, (2) Chấp nhận và tiếp tục.



### Bước 5: Nguyên Tắc Tối Thượng (No Graph Routing)

- **Miner TUYỆT ĐỐI KHÔNG tham gia định tuyến Graph (DIKW Routing).**
- Bất chấp trong file Prompt có nhắc đến `supports_insight` hay `supports_knowledge`, Miner chỉ thực hiện đào xúc (Mine) và đắp vào tệp tổng (`[Tên Sách].md`).
- Việc xử lý Logic Ánh xạ bản đồ, gắn Pillar, nối Graph là nhiệm vụ ĐỘC QUYỀN của `book-parser` (Atomizer) ở công đoạn ngay sau đó. Miner không can thiệp!

---

### OUTPUT

Skill trả về **2 artifacts** cho `/extract-book`:
1. **File cache:** `vault/02-sources/books/[Tên Sách].md`
2. **Run folder:** `vault/extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
   - `pipeline_report.md` — audit trail xuyên suốt pipeline

Workflow `/extract-book` sẽ xử lý handoff — skill không cần biết bước tiếp theo.
