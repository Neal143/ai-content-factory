---
name: Book Audience Matcher
description: Nhận đường dẫn file cache sách từ book-extractor, trả về Audience Decision Map, Audience_index.yaml và các file Audience vật lý. Được gọi bởi /atomize-book (Bước 2).
---

# Book Audience Matcher Skill

// turbo-all

Nhiệm vụ: **Audience Resolution toàn diện**. Parse file sách thô, hiệu đính JTBD, so khớp LLM Semantic Match với kho `01-Atomic/Audiences/`, tạo file Audience vật lý nếu cần, và trả về Audience Decision Map đầy đủ `audience_filename`.

## QUY TẮC VỆ SINH (HYGIENE)

Skill này chạy trong workflow `/atomize-book` (conversation riêng, SAU khi `/extract-book` đã hoàn tất). Run-folder đã được tạo sẵn — KHÔNG tạo mới.

- **Thư mục dùng chung:** `[run-folder]`
  *(Dùng run-folder path được /atomize-book truyền trực tiếp qua INPUT. KHÔNG tự derive.)*
- File tạm (JSON output từ script, debug logs) → BẮT BUỘC ghi vào thư mục trên.
  Path đầy đủ bắt buộc: `[run-folder]/audiences_parsed.json`
  TUYỆT ĐỐI KHÔNG dùng `temp_audiences.json` hay bất kỳ tên file bare nào ở thư mục hiện tại.

---

## Input (Nhận từ /atomize-book)

```
INPUT (nhận từ /atomize-book):
- File cache path: `vault/02-sources/books/[Tên Sách].md`
- Run folder path: `.extraction_runs/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
  (Thư mục đã được book-extractor tạo sẵn và NIÊM PHONG dữ liệu)

Bắt buộc phải có sẵn trong run-folder (từ Phase 1):
- `parsed_metadata.json` (Manifesto Metadata)
- `extraction_baseline.csv` (Manifesto Tracking)

File cache tuân thủ `.agents/skills/book-extractor/references/raw-book-structure.md`:
- Header: META_BOOK_AUDIENCE — JTBD cấp sách (level xác định SAU Semantic Match)
- N data_chunk: META_CHUNK_AUDIENCE — JTBD cấp chunk (level xác định SAU Semantic Match)
```

## Output (Trả về cho /atomize-book)

Skill này sẽ trực tiếp tác động vào Vault và tạo các tài liệu nội bộ trả về cho `/atomize-book`:

1. **Các file Audience vật lý:** Được tạo/merge trong `vault/01-Atomic/Audiences/`
2. **Sổ tay Audience Index:** Cập nhật file `_audience_index.yaml`
3. **Audience Decision Map:** File JSON (`audience_decision_map.json`) chứa quyết định nối map và đã được enrich `jtbd_raw`.
4. **Cập nhật Baseline:** Cột `status` của các row Audience trong `extraction_baseline.csv` được ghi đè thành `DONE` hoặc `MISSING`.

Cấu trúc file `audience_decision_map.json` (dùng cho Bước 3 của Atomize):
```json
[
  {
    "scope": "book",
    "chunk_index": null,
    "action": "merge | create",
    "audience_filename": "Audience-File",
    "audience_level": "big | little | micro",
    "parent_audience": ["[[Direct-Parent-File]]"],
    "jtbd_raw": "..."
  },
  {
    "scope": "chunk",
    "chunk_index": 1,
    "action": "merge | create",
    "audience_filename": "Audience-File",
    "audience_level": "big | little | micro",
    "parent_audience": ["[[Direct-Parent-File]]"],
    "jtbd_raw": "..."
  }
]
```

> **Lưu ý:** Decision Map là **array**. Mỗi entry có `scope` (`book` hoặc `chunk`) và `chunk_index` (integer cho chunk, `null` cho book). Script join bằng `scope` cho book, `chunk_index` cho chunk — nếu Agent quên `chunk_index` cho chunk entry, script fail loud (KeyError).


## Quy Trình Thực Thi

### Giai đoạn 1: Parse File & JTBD Calibration

> ⚠️ **Cách ly Rác (Warning Isolation):** Chunks chứa cờ `> [!warning]` được script `parse_book_audiences.py` tự động cách ly — không parse, không tạo JTBD entry. Không cần Agent xử lý.

**Bước 1 — Gọi script (chống ảo giác):**
```
python .agents/skills/book-audience-matcher/scripts/parse_book_audiences.py
       [đường dẫn file cache] --output_json [run-folder]/audiences_parsed.json
```
Đọc JSON output: `result["book"]` = JTBD thô cấp sách; `result["chunks"]` = list JTBD thô theo `CHUNK_index`.

**Bước 2 — JTBD Calibration:**
- Đọc `.agents/skills/book-audience-matcher/references/JTBD-base.md`.
- Hiệu đính từng câu JTBD thô (1 book + N chunks), bóc tách 4 Core Variables theo Hướng dẫn nội suy sau:
  1. `audience_main_job` & `audience_circumstance`: Giữ nguyên giá trị bóc được từ khối Main Job và Circumstance của input.
  2. `audience_Job_performer`: Input gốc thường để mặc định là "Người". AI **BẮT BUỘC** suy luận ra Danh xưng/Chức danh cụ thể dựa trên `audience_main_job`. 
     - *Ví dụ: main_job="nuôi con" → performer="bố mẹ"; main_job="dạy học sinh" → performer="giáo viên".*
     - *Ngoại lệ: Nếu main_job chung chung không có chức danh cấu thành (ví dụ: "ăn cơm", "tìm chỗ đỗ xe") → Giữ nguyên là "Người".*
  3. `aliases`: Kết hợp `audience_main_job` + `audience_circumstance` và tự suy ra 2-3 cụm từ đồng nghĩa phổ biến tập trung vào hành động và bối cảnh.
     - *Ví dụ: main_job="quản lý thời gian", circumstance="khi bắt đầu công việc" → bí danh: "sắp xếp lịch trình lúc mới đi làm", "tổ chức công việc cho lính mới".*
- Output nội bộ: list JTBD objects chuẩn hóa theo schema sau → chuyển Giai đoạn 2:

```json
[
  {
    "scope": "book",
    "chunk_index": null,
    "chunk_name": null,
    "audience_Job_performer": "...",
    "audience_main_job": "...",
    "audience_circumstance": "...",
    "aliases": ["...", "..."]
  },
  {
    "scope": "chunk",
    "chunk_index": 1,
    "chunk_name": "Tên Chunk gốc từ TOC",
    "audience_Job_performer": "...",
    "audience_main_job": "...",
    "audience_circumstance": "...",
    "aliases": ["...", "..."]
  }
]
```
> Luôn có entry `"scope": "book"` đứng đầu — Giai đoạn 2 xử lý theo thứ tự list, book trước.

**Bước 3 — Persist:** Ghi toàn bộ list JTBD objects đã calibrate ra file JSON:
```
[run-folder]/jtbd_calibrated.json
```
File này sẽ được script `write_audience_files.py` đọc ở Giai đoạn 3 (join với Audience Decision Map).


---

### Giai đoạn 2: 3-Verdict Semantic Match

**Input:**
- List JTBD objects đã được chuẩn hóa từ Giai đoạn 1.
- Kho System Index hiện tại: `vault/01-Atomic/Audiences/_audience_index.yaml`.

**Hướng dẫn thực thi:**
- Đọc và tuân thủ nghiêm ngặt bộ rule tại: `.agents/skills/book-audience-matcher/references/semantic-match.md`.
- Xử lý tuần tự danh sách Input: **Book Audience trước**, sau đó xử lý từng **Chunk Audience** theo `chunk_index`.

**Output (Làm đầu vào cho GĐ 3):**
- Trả về JSON Audience Decision Map **dạng array** (xem schema ở phần Output Tổng Hợp). Mỗi entry gồm:
  - `scope`: `book` (entry JTBD cấp sách) hoặc `chunk` (entry JTBD cấp chunk) — lấy đúng giá trị scope từ calibrated JTBD tương ứng.
  - `chunk_index`: Integer (từ calibrated JTBD) hoặc `null` cho book.
  - `action`: `merge` hoặc `create`
  - `audience_filename`: Tên file cũ hoặc mới.
  - `audience_level`: `big`, `little`, hoặc `micro`.
  - `parent_audience`: LUÔN LUÔN LÀ MẢNG YAML `["[[slug]]"]` (Trống thì `[]`). Nếu là `merge`, agent buộc phải test mảng này để kích hoạt lệnh Append nếu có parent mới phát sinh.

---

### Giai đoạn 3: Tạo File Audience Vật Lý

**Bước 3.1 — Lưu Audience Decision Map:** Ghi Audience Decision Map ra file JSON:
```
[run-folder]/audience_decision_map.json
```

**Bước 3.2 — Gọi script tạo file:**
```bash
python .agents/skills/book-audience-matcher/scripts/write_audience_files.py \
    --decision-map "[run-folder]/audience_decision_map.json" \
    --calibrated-jtbd "[run-folder]/jtbd_calibrated.json" \
    --vault-root "vault/"
```

Script tự động xử lý:
- Join Audience Decision Map với Calibrated JTBD bằng `chunk_index` (integer) / `scope` (book)
- Tạo file `.md` cho mỗi entry `create` (YAML frontmatter bằng PyYAML + dashboard từ `audience-structure.md`)
- Cập nhật `_audience_index.yaml` (PyYAML serialize, dedup by id)
- Skip nếu file hoặc index entry đã tồn tại
- In báo cáo tóm tắt

> ⚠️ **LUẬT THÉP:** KHÔNG TỰ TAY TẠO FILE AUDIENCE HOẶC GHI INDEX BẰNG AGENT. Toàn bộ YAML serialize, dedup, template rendering, và atomic write đã được nhúng cứng vào script.


### ⛔ Self-Check Gate (cuối Giai đoạn 3 — trước khi trả kết quả)

Đọc và tuân thủ nghiêm ngặt `.agents/skills/book-audience-matcher/references/self-check-gate.md`.

---


### Giai đoạn 3b: Verify Audiences + Enrich Audience Decision Map

Agent gọi script xác minh audience và ghép `jtbd_raw` vào Audience Decision Map:
```bash
python .agents/skills/book-audience-matcher/scripts/verify_audiences.py \
    --baseline          "[run_folder]/extraction_baseline.csv" \
    --decision-map      "[run_folder]/audience_decision_map.json" \
    --vault-root        "vault/" \
    --audiences-parsed  "[run_folder]/audiences_parsed.json" \
    --report            "[run_folder]/pipeline_report.md"
```

Script thực hiện 2 việc:
1. **Verification:** Đối chiếu audience rows trong baseline CSV với file vật lý trên disk → update DONE/MISSING.
2. **Enrichment:** Ghép `jtbd_raw` từ `audiences_parsed.json` vào Audience Decision Map → ghi đè lại. Mở Audience Decision Map sẽ thấy rõ JTBD gốc đã trở thành audience nào.

---


### Giai đoạn 4: Tổng Hợp & Trả Kết Quả

- In tóm tắt ra Chat: book audience (merge/create + level), số chunk merge, số chunk create, danh sách file mới tạo.
- Trả Audience Decision Map hoàn chỉnh về `/atomize-book` (entry `"book"` + N entries chunk) để làm đầu vào cho **Bước 3 (Topic Gate + Atomization):**
