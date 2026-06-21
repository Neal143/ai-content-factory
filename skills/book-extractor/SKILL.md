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
         ├─ PASS 4/4      → B2
         ├─ Fail [1]      → NLM bổ sung → re-Gate
         ├─ Fail [2]      → DỪNG báo User
         ├─ Fail [3]      → Agent strip format → re-Gate
         └─ Fail [4]      → Agent chèn sentinel → re-Gate

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

1. **TASK ĐẦU TIÊN:** Ngay khi nhận lệnh khởi tạo, BẮT BUỘC TẠO THƯ MỤC TRƯỚC: `vault/.extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
   → Thư mục này được gọi tắt là **[run-folder]** trong toàn bộ tài liệu này. Mọi hành động CLI chỉ được phép thực hiện SAU KHI thư mục này đã tồn tại.
2. MỌI file phụ trợ (scripts, logs, raw responses, ledger YAML, tmp output) → ghi vào **[run-folder]**.
   ⚠️ BẮT BUỘC dùng path đầy đủ: `vault/.extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/[tên-file]`
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

### Bước 1: The Mapper (Sinh Tổng quan & Mục Lục)

- Gọi CLI: `nlm notebook query <notebook_id> "Tham chiếu file prompt-mapper-v4.md, hãy sinh Tổng quan và Mục lục cho sách [Tên Sách]." --json`
- Parse JSON output → extract trường `answer` → lưu plain text vào: `[run-folder]/session_1/mapper_raw.md`. (Lưu ý: Bạn phải tự tạo thư mục `session_1` nếu nó chưa tồn tại).
  ⚠️ Nếu CLI trả exit code ≠ 0 → retry tối đa 2 lần. Đọc stderr để chẩn đoán.

### Bước 1.5: Mapper Validation Gate

Agent gọi Core Script:
`python .agents/skills/book-extractor/scripts/prepare_mapper.py "[run-folder]" "[Tên Sách]"`

Script phân tích `mapper_raw.md`, làm sạch META, ghi file xương sống vào vault `vault/02-sources/books/[Tên Sách].md`, rồi chạy 4-point validation. Agent đọc JSON verdict từ stdout:
- `"passed": true` → Bước 2
- `"passed": false` → hành động theo `verdict` tương ứng từng check fail:
  - `header_complete` fail → Gửi NLM query bổ sung mục thiếu, chạy lại script
  - `toc_integrity` fail → DỪNG báo User
  - `format_clean` fail → Agent strip markdown formatting trong cache file, chạy lại script
  - `sentinel_exists` fail → Agent chèn `<!-- HEADER_END -->` vào đúng vị trí, chạy lại script

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
Agent **LUÔN** chạy `next_chunk.py` ở đầu mỗi vòng lặp — không ngoại lệ:
  `python .agents/skills/book-extractor/scripts/next_chunk.py "[run-folder]/session_1/miner_progress.yaml" "vault/02-sources/books/[Tên Sách].md"`
Script trả JSON chứa: `chunk_index`, `chunk_nn`, `chunk_name`, `raw_file`, `notebook_id`, `cache_file`, `progress`, `cli_nlm_query`, `cli_gate_checker`, `cli_append_cache`.
⚠️ Agent dùng **TRỰC TIẾP** các lệnh CLI và paths từ JSON. KHÔNG tự compose, KHÔNG sửa, KHÔNG dùng trí nhớ.
Nếu `"done": true` → thoát vòng lặp, chuyển Bước 3.

**② Agent gọi NLM qua CLI + Script chạy Gate:**

**②-a.** Agent gọi CLI:
  `nlm notebook query <notebook_id> "Tham chiếu file prompt-miner-v4.md, hãy trích xuất CHÍNH XÁC Content Chunk sau: Chunk N: [Tên Chunk]." --json`
  Agent parse JSON output → extract trường `answer`.
  ⚠️ Nếu CLI trả exit code ≠ 0 → gọi `update_ledger.py` với `status: FATAL`, `error_code: NETWORK_ERROR`. Max 3 lần retry trước khi FATAL.

**②-b.** Agent lưu nội dung `answer` vào file path lấy từ trường `raw_file` trong output JSON của `next_chunk.py`.

**②-c.** Agent gọi script Gate (lệnh lấy từ `cli_gate_checker` của `next_chunk.py`):
  - Script chạy `normalize_dikw_names` (Auto-Repair) + Gates [1-7] (Cấu trúc & Khóa ngoại xác định) → ghi kết quả vào `[run-folder]/session_1/chunk_NN_gate.json`.
  ⚠️ Output JSON chứa trường `next_action` — Agent dùng trường này để quyết định bước tiếp theo.

**③ Đọc kết quả Gate [1-7]:**
Đọc file `[run-folder]/session_1/chunk_NN_gate.json` → lấy trường `next_action`. Agent thực thi TRỰC TIẾP theo `next_action.type`:

→ `"AGENT_EVAL"` → Chuyển bước ④.
→ `"RETRY"` → Gọi lại NLM query gốc (từ `next_chunk.py`), lưu đè raw file, chạy lại `gate_checker.py`.
   Hết `max_retry` → dùng `on_exhaust.ledger_update` gọi `update_ledger.py`. KHÔNG append. Tiếp chunk sau.
→ `"SUPPLEMENT"` → Gọi NLM yêu cầu trích xuất LẠI TOÀN BỘ chunk (không phải chỉ phần thiếu), nhấn mạnh đảm bảo có đầy đủ phần bị thiếu (dựa vào `missing_detail`). Lưu đè raw file, chạy lại `gate_checker.py`.
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

→ ALL PASS → Tiếp Bước 5.
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
2. **Run folder:** `vault/.extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
   - `pipeline_report.md` — audit trail xuyên suốt pipeline

Workflow `/extract-book` sẽ xử lý handoff — skill không cần biết bước tiếp theo.
