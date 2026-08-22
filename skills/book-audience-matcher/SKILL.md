---
name: Book Audience Matcher
description: Nhận đường dẫn file cache sách từ book-extractor, trả về Audience Decision Map, Audience_index.yaml và các file Audience vật lý. Được gọi bởi /book-extractor (Session 3).
---

# Book Audience Matcher Skill

// turbo-all

Nhiệm vụ: **Audience Resolution**. Nhận JTBD đã chuẩn hóa từ skill jtbd-calibrator, so khớp LLM Semantic Match với kho `01-Atomic/Audiences/`, tạo file Audience vật lý nếu cần, và trả về Audience Decision Map đầy đủ `audience_filename`.

## QUY TẮC VỆ SINH (HYGIENE)

Skill này chạy trong workflow `/book-extractor` (Session 3 - conversation riêng, SAU khi Skill 1 jtbd-calibrator đã hoàn tất). Run-folder đã được tạo sẵn — KHÔNG tạo mới.

- **Thư mục dùng chung:** `[run-folder]`
  *(Dùng run-folder path được Agent truyền trực tiếp qua INPUT. KHÔNG tự derive.)*
- File tạm (JSON output từ script, debug logs) → BẮT BUỘC ghi vào thư mục `[run-folder]/session_3/`.
  TUYỆT ĐỐI KHÔNG dùng bất kỳ tên file bare nào ở thư mục hiện tại.

---

## Input (Nhận từ Agent điều phối)

```text
INPUT (nhận từ Agent):
- Run folder path: `vault/extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`

Bắt buộc phải có sẵn trong run-folder (từ các Phase/Skill trước):
- `parsed_metadata.json` (Manifesto Metadata)
- `extraction_baseline.csv` (Manifesto Tracking)
- `session_3/jtbd_calibrated.json` (Được tạo ra bởi skill jtbd-calibrator)
- `session_3/audiences_parsed.json` (Được tạo ra bởi skill jtbd-calibrator - dùng cho bước Verify)
```

## Output (Trả về cho /book-extractor Session 3)

Skill này sẽ trực tiếp tác động vào Vault và tạo các tài liệu nội bộ trả về cho `/book-extractor`:

1. **Các file Audience vật lý:** Được tạo/merge trong `vault/01-Atomic/Audiences/`
2. **Sổ tay Audience Index:** Cập nhật file `_audience_index.yaml`
3. **Audience Decision Map:** File JSON (`audience_decision_map.json`) chứa quyết định nối map và đã được enrich `jtbd_raw`.
4. **Cập nhật Baseline:** Cột `status` của các row Audience trong `extraction_baseline.csv` được ghi đè thành `DONE` hoặc `MISSING`.

Cấu trúc file `audience_decision_map.json` (dùng cho Bước 8 (Phase 4) của /book-extractor):
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
   - Sinh `semantic_query`, `file_ref` (Quy tắc ở Phần 1 `semantic-match.md`).
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
    --vault-root "vault/" \
    --source-name "[Tên sách đầy đủ (bởi Tác giả, Năm)]" \
    --source-link "[Tên-file-sách-trong-02-sources-không-extension]"
```

> **Cách lấy giá trị `--source-name` và `--source-link`:**
> 1. Đọc `[run-folder]/parsed_metadata.json` > `book` object → lấy `book_name`, `author`, `year`.
> 2. `--source-name` = `"{book_name} (bởi {author}, {year})"`.
> 3. `--source-link` = Quét thư mục `vault/02-sources/books/` → tìm file `.md` có tên chứa từ khóa chính của `book_name` → lấy tên file (không extension). Nếu không tìm thấy → để trống.

Script tự động xử lý:
- Join Audience Decision Map với Calibrated JTBD bằng `chunk_index` (integer) / `scope` (book)
- Tạo file `.md` cho mỗi entry `create` (YAML frontmatter bằng PyYAML + dashboard từ `audience-structure.md`)
- Cập nhật `_audience_index.yaml` (PyYAML serialize, dedup by file_ref)
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
    --report            "[run-folder]/pipeline_report.md" \
    --run-folder        "[run-folder]"
```

Script thực hiện 2 việc:
1. **Verification:** Đối chiếu audience rows trong baseline CSV với file vật lý trên disk → update DONE/MISSING.
2. **Enrichment:** Ghép `jtbd_raw` từ `audiences_parsed.json` vào Audience Decision Map → ghi đè lại. Mở Audience Decision Map sẽ thấy rõ JTBD gốc đã trở thành audience nào.

---


### Giai đoạn 4: Tổng Hợp & Trả Kết Quả

- In tóm tắt ra Chat: book audience (merge/create + level), số chunk merge, số chunk create, danh sách file mới tạo.
- Trả Audience Decision Map hoàn chỉnh về `/book-extractor` (entry `"book"` + N entries chunk) để làm đầu vào cho **Bước 8 (Phase 4: Sinh Topics & Phân rã Atoms):**
