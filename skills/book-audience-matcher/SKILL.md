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
  Path đầy đủ bắt buộc: `[run-folder]/session_3/audiences_parsed.json`
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
       [đường dẫn file cache] --output_json "[run-folder]/session_3/audiences_parsed.json"
```
Đọc JSON output: `result["book"]` = JTBD thô cấp sách; `result["chunks"]` = list JTBD thô theo `CHUNK_index`.

**Bước 2 — Phân Lô Dữ Liệu (Script):**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_calibration_batches.py \
    --parsed-json "[run-folder]/session_3/audiences_parsed.json" \
    --split-dir "[run-folder]/session_3/calib_batches" \
    --batch-size 5
```

**Bước 3 — JTBD Calibration (Chu trình xử lý tịnh tiến):**
Đọc `.agents/skills/book-audience-matcher/references/JTBD-base.md`. Lặp lại chu trình sau cho đến khi hệ thống báo hoàn thành:

1. **Cấp phát dữ liệu:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_calibration_batches.py \
    --session-dir "[run-folder]/session_3/calib_batches" --get-next
```
> Dùng `view_file` đọc `[run-folder]/session_3/calib_batches/current_calib_batch.json` để lấy danh sách cần xử lý.

2. **Nội suy dữ liệu:** Với mỗi mục, bóc tách 4 biến (Performer, Job, Circumstance, Aliases) theo quy tắc:
   - `audience_main_job` & `audience_circumstance`: Giữ nguyên giá trị bóc được từ khối Main Job và Circumstance của dữ liệu gốc.
   - `audience_Job_performer`: Input gốc thường để mặc định là "Người". **BẮT BUỘC** suy luận ra Danh xưng cụ thể dựa trên `audience_main_job` (VD: "nuôi con" → "bố mẹ"). Ngoại lệ: Nếu hành động chung chung (VD: "ăn cơm") → Giữ nguyên là "Người".
   - `aliases`: Kết hợp `audience_main_job` + `audience_circumstance` và tự suy ra 2-3 cụm từ đồng nghĩa phổ biến (VD: "quản lý thời gian" + "khi bắt đầu công việc" → "tổ chức công việc cho lính mới").

3. **Ghi tệp kết quả tạm:** Hệ thống đã tự động tạo sẵn tệp `[run-folder]/session_3/calib_batches/calib_eval_temp.json` điền sẵn mật khẩu và cấu trúc. Hãy mở tệp đó ra bằng công cụ chỉnh sửa tệp (hoặc overwrite bằng write_to_file), thay thế CÁC TRƯỜNG `[ĐIỀN VÀO ĐÂY]` bằng câu trả lời nội suy của bạn, lưu lại và gọi lệnh nộp bài.

4. **Nộp bài:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_calibration_batches.py \
    --session-dir "[run-folder]/session_3/calib_batches" \
    --submit-file "[run-folder]/session_3/calib_batches/calib_eval_temp.json"
```

5. Chờ phản hồi. Nếu có lỗi, sửa và nộp lại. Nếu script báo hoàn thành (đã tự động sinh `jtbd_calibrated.json`), tiến tới Giai đoạn 2.



---

### Giai đoạn 2: 3-Verdict Semantic Match (Map-Reduce)

> ⛔ **FATAL RULE:** Tuyệt đối KHÔNG ĐƯỢC PHÉP tự viết script Python/Bash/PowerShell để bypass vòng lặp dedup hoặc batch decision. Bước 2.1b (Rolling Dedup) và Bước 2.3 là Năng Lực Suy Luận Bắt Buộc của LLM — phải đi qua password gate của script hệ thống cấp phép, KHÔNG được bypass.

**Bước Bắt Buộc Đầu Tiên:** Dùng `view_file` nạp 2 tài liệu:
1. `.agents/skills/book-audience-matcher/references/semantic-match.md`
2. `.agents/skills/book-audience-matcher/references/self-check-gate.md`

**Bước 2.1 — Internal Dedup (Rolling Batch có khóa):**

> ⛔ **CẤM TUYỆT ĐỐI**: KHÔNG ĐƯỢC PHÉP dùng `view_file`, `cat` đọc file trong `session_3/dedup_batches/`. KHÔNG ĐƯỢC PHÉP tự viết script sinh `internal_map.json`.

**Bước 2.1a — Phân Lô Dữ Liệu Dedup (Script):**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_dedup_batches.py \
    --jtbd-calibrated "[run-folder]/session_3/jtbd_calibrated.json" \
    --split-dir "[run-folder]/session_3/dedup_batches" \
    --batch-size 5
```

**Bước 2.1b — Rolling Dedup (Vòng lặp có khóa):**

Đọc `semantic-match.md` Phần 1 + Phần 2A. Lặp lại đến khi báo hoàn thành:

1. **Lấy Batch hiện tại:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_dedup_batches.py \
    --session-dir "[run-folder]/session_3/dedup_batches" --get-next
```
> Script xuất `[run-folder]/session_3/dedup_batches/current_dedup_batch.json`. Đọc bằng `view_file`. File chứa `anchors` (những Audience đã chốt từ batch trước) và `items_to_process`.

2. **Xử lý:** Với mỗi chunk trong `items_to_process`:
   - Sinh `id`, `semantic_query`, `file_ref` (Quy tắc ở Phần 1 `semantic-match.md`).
   - Đối chiếu với các `anchors` (IDENTICAL/DISTINCT/AMBIGUOUS).
   - Đối chiếu chéo với các chunks khác trong cùng `items_to_process`.
   - Ghi nhận parent (nội bộ batch hoặc từ anchors).

3. **Tạo file kết quả** Hệ thống đã tự động tạo sẵn tệp `[run-folder]/session_3/dedup_batches/dedup_eval_temp.json` điền sẵn mật khẩu và cấu trúc. Hãy mở tệp đó ra, thay thế CÁC TRƯỜNG `[ĐIỀN VÀO ĐÂY]` bằng câu trả lời của bạn, lưu lại và gọi lệnh nộp bài.
   > `collapse_target`: Giữ nguyên `null` (distinct), hoặc điền uid từ anchors, hoặc điền uid từ items_to_process (nếu trùng).

4. **Nộp Bài:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_dedup_batches.py \
    --session-dir "[run-folder]/session_3/dedup_batches" \
    --submit-file "[run-folder]/session_3/dedup_batches/dedup_eval_temp.json"
```

5. Chờ phản hồi. Nếu có lỗi, sửa và nộp lại. Nếu script báo batch tiếp theo → Quay lại bước 1. Nếu "🎉 HOÀN THÀNH" → Chuyển sang Bước 2.2.

**Bước 2.2 — Phân Lô Dữ Liệu (Script):**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_audience_batches.py \
    --internal-map "[run-folder]/session_3/internal_map.json" \
    --split-dir "[run-folder]/session_3/audience_batches" \
    --batch-size 5
```

> ⛔ **CẤM TUYỆT ĐỐI**: KHÔNG ĐƯỢC PHÉP dùng `view_file`, `cat`, hay bất kỳ công cụ nào đọc trực tiếp file trong thư mục `session_3/audience_batches/`. KHÔNG ĐƯỢC PHÉP tự viết script truy cập thư mục này.

**Bước 2.3 — External Match theo batch (Vòng lặp tuần tự có khóa):**

Lặp lại cho đến khi hệ thống báo hoàn thành:

1. **Lấy Batch hiện tại:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_audience_batches.py \
    --session-dir "[run-folder]/session_3/audience_batches" --get-next
```
> Script xuất file `[run-folder]/session_3/audience_batches/current_audience_batch.json`. Dùng `view_file` đọc file này để lấy nội dung batch và `batch_password`.

2. **Xử lý:** Đọc `_audience_index.yaml`. Thực hiện Phần 2B trong `semantic-match.md` cho các items trong batch. Áp dụng 3-Verdict (IDENTICAL/DISTINCT/AMBIGUOUS).

3. **Tạo file kết quả:** Hệ thống đã tự động tạo sẵn tệp `[run-folder]/session_3/audience_batches/audience_eval_temp.json` điền sẵn mật khẩu và cấu trúc. Hãy mở tệp đó ra, thay thế CÁC TRƯỜNG `[ĐIỀN VÀO ĐÂY]` bằng câu trả lời của bạn, lưu lại và gọi lệnh nộp bài.

4. **Nộp Bài:**
```bash
python .agents/skills/book-audience-matcher/scripts/prepare_audience_batches.py \
    --session-dir "[run-folder]/session_3/audience_batches" \
    --submit-file "[run-folder]/session_3/audience_batches/audience_eval_temp.json"
```

5. Nếu hệ thống in batch tiếp theo → Quay lại bước 1.
   Nếu hệ thống in "🎉 HOÀN THÀNH" → File `collected_decisions.json` đã được tạo. Chuyển sang Bước 2.4.

**Bước 2.4 — Biên dịch Decision Map (Script):**
```bash
python .agents/skills/book-audience-matcher/scripts/compile_decision_map.py \
    --internal-map "[run-folder]/session_3/internal_map.json" \
    --collected-decisions "[run-folder]/session_3/collected_decisions.json" \
    --audience-index "vault/01-Atomic/Audiences/_audience_index.yaml" \
    --output "[run-folder]/audience_decision_map.json"
```
Script tự động: Validate UID completeness, Reference Substitution, Expand chunk_mapping, Tính Level DAG (tra Index), Resolve internal parents cho merge.

**Output Giai đoạn 2:** File `audience_decision_map.json` (chuẩn schema hiện hành) → chuyển thẳng Giai đoạn 3.

---

### Giai đoạn 3: Tạo File Audience Vật Lý

**Bước 3.1 — Xác nhận Audience Decision Map:** File `[run-folder]/audience_decision_map.json` đã được tạo tự động bởi script ở Bước 2.4. **KHÔNG ghi đè lại.** Chuyển thẳng sang Bước 3.2.

**Bước 3.2 — Gọi script tạo file:**
```bash
python .agents/skills/book-audience-matcher/scripts/write_audience_files.py \
    --decision-map "[run-folder]/audience_decision_map.json" \
    --calibrated-jtbd "[run-folder]/session_3/jtbd_calibrated.json" \
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
    --baseline          "[run-folder]/extraction_baseline.csv" \
    --decision-map      "[run-folder]/audience_decision_map.json" \
    --vault-root        "vault/" \
    --audiences-parsed  "[run-folder]/session_3/audiences_parsed.json" \
    --report            "[run-folder]/pipeline_report.md"
```

Script thực hiện 2 việc:
1. **Verification:** Đối chiếu audience rows trong baseline CSV với file vật lý trên disk → update DONE/MISSING.
2. **Enrichment:** Ghép `jtbd_raw` từ `audiences_parsed.json` vào Audience Decision Map → ghi đè lại. Mở Audience Decision Map sẽ thấy rõ JTBD gốc đã trở thành audience nào.

---


### Giai đoạn 4: Tổng Hợp & Trả Kết Quả

- In tóm tắt ra Chat: book audience (merge/create + level), số chunk merge, số chunk create, danh sách file mới tạo.
- Trả Audience Decision Map hoàn chỉnh về `/atomize-book` (entry `"book"` + N entries chunk) để làm đầu vào cho **Bước 3 (Topic Gate + Atomization):**
