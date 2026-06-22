---
name: Book Parser (The Atomizer)
description: Skill phân rã sách thành Atom vật lý. Được gọi bởi book-extractor Session 4. Phase 1: Sinh Book Topics & Chunk Topics (batch processing) + Semantic Dedup. Phase 2: Atomization (tiếp ngay sau Phase 1 trong cùng 1 lần gọi).
last_update: 22/06/2026 15:42 (GMT+7)
---

# Book Parser Skill (The Atomizer)

// turbo-all

Bạn là chuyên gia phân rã hạt nhân (Atomizer). Nhiệm vụ của bạn là lấy file Raw Markdown từ `02-sources/books/`, phân rã thành Atom vật lý theo đúng cấu trúc 4 Tầng DIKW trước khi Commit I/O ra đĩa.

Skill này được `book-extractor` Session 4 gọi. Phase 1 và Phase 2 thực thi tuần tự trong cùng 1 conversation context.

---

> ⛔ **CẤM TUYỆT ĐỐI**: KHÔNG ĐƯỢC PHÉP dùng `view_file`, `cat`,
> hay bất kỳ công cụ nào đọc trực tiếp file `chunk_XX_raw.txt`
> hoặc bất kỳ file nào trong thư mục `topic_chunks/`.
> Toàn bộ nội dung chunk chỉ được truy cập thông qua
> script `prepare_topic_batches.py --get-next`.

## PHASE 1: Topic Generation

**INPUT Phase 1 (nhận từ book-extractor Session 4):**
- File cache path: `vault/02-sources/books/[Tên Sách].md`
- Run folder path: `vault/.extraction_runs/books/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
  *(Run-folder được book-extractor Session 4 truyền trực tiếp qua INPUT. Thư mục đã tồn tại từ lúc Session 1 chạy. Trong tài liệu này gọi tắt là `[run_folder]`. KHÔNG tự derive.)*
- Audience Decision Map: Array of entries, mỗi entry có `scope`, `chunk_index`, `audience_filename`, ... từ book-audience-matcher (xem schema tại book-audience-matcher/SKILL.md)

### Bước 1: Sinh Topic Tự Động & Reverse-Sync

Ngay khi nhận INPUT, thực hiện tuần tự hoàn toàn tự động — **không dừng chờ User**.

**Bước 1.1 — Đọc Tổng quan sách & Chọn Pillar gốc (duy nhất toàn book):**
1. Đọc file `[run_folder]/session_1/mapper_raw.md` để nắm rõ nội dung tổng quan của cuốn sách (thesis, big idea, tóm tắt 1 trang).
2. Xác định `[Persona_Path]`: Lấy thư mục con duy nhất trong `personas/` (VD: `personas/Vuon-ong-steiner`). Đọc `[Persona_Path]/pillars.yaml`. Dựa trên `name` và `description` của mỗi Pillar, đối chiếu với nội dung tổng quan sách vừa đọc để chọn **01 Pillar** phù hợp nhất. Pillar này **bất biến** — dùng chung cho Book Topics và mọi Chunk Topics trong toàn bộ pipeline. Giá trị `[Persona_Path]` cũng bất biến cho toàn bộ pipeline.

**Bước 1.2 — Sinh Book Topics (2-3 topics, phản ánh toàn bộ cuốn sách):**
Dựa vào kiến thức tổng quan sách đã nắm được ở Bước 1.1, tham chiếu `.agents/skills/book-parser/references/topic-taxonomy.md` → Section **"Book Topics"** và **"Quy tắc chung"**.


1. Cấp phát Template Book Topics bằng lệnh:
   ```bash
   python .agents/skills/book-parser/scripts/prepare_topic_batches.py --run-folder "[run_folder]" --prepare-book-topics
   ```
2. Mở file `[run_folder]/session_4/book_topics_temp.json` vừa được sinh ra.
3. Điền vào các trường `[ĐIỀN VÀO ĐÂY]` (Đặc biệt chú ý trường giải thích CAPTCHA `reasoning` cần ghi chi tiết).
4. Nộp bài bằng lệnh:
   ```bash
   python .agents/skills/book-parser/scripts/prepare_topic_batches.py --run-folder "[run_folder]" --submit-book-topics "[run_folder]/session_4/book_topics_temp.json"
   ```
5. Nếu bị Reject, sửa file và gọi lại lệnh nộp bài cho đến khi có thông báo `✅ PASS validation`. File `book_topics_draft.json` sẽ tự động được tạo.

> ⚠️ **Quy tắc Vòng lặp (Chunk Isolation):** Từ Bước 1.3 trở đi, phải thực thi **biệt lập cho từng chunk riêng lẻ** — không gom, không trộn:
> - **Cách ly Rác (Warning Isolation):** Chunk có `passed: false` trong gate file tự động bị script `prepare_topic_batches.py` loại bỏ khi chia batch. Không cần xử lý thủ công.
> - **Bước 1.3:** Sinh Chunk Topics qua batch loop — mỗi batch chứa tối đa 10 chunks, Agent xử lý tuần tự.
> - **Bước 1.5:** Chạy Semantic Dedup độc lập cho từng nhóm topic (Book Topics, Chunk 01 Topics, Chunk 02 Topics,...).
>
> Tuyệt đối không trộn Topics của nhiều chunk/nhóm vào chung một lần thực thi phân tích.

**Bước 1.3a — Chia batch:**
```bash
python .agents/skills/book-parser/scripts/prepare_topic_batches.py \
    --run-folder "[run_folder]" \
    --split-dir "[run_folder]/session_4/topic_chunks" \
    --batch-size 3
```

**Bước 1.3b — Vòng lặp sinh Chunk Topics (lặp đến khi script in "🎉 HOÀN THÀNH"):**

1. Lấy batch:
   ```bash
   python .agents/skills/book-parser/scripts/prepare_topic_batches.py \
       --session-dir "[run_folder]/session_4/topic_chunks" --get-next
   ```
2. Mở file `[run_folder]/session_4/current_topic_batch.json` bằng `view_file` để xem nội dung chunk.
3. Với từng chunk trong batch:
   - Tham chiếu `topic-taxonomy.md` → Section "Chunk Topics" + "Quan hệ giữa Book và Chunk Topics".
   - Sinh 2-3 cặp `(id, label)` + `tier` + `evidence` (trích nguyên văn 1 đoạn từ nội dung chunk).
   - Cùng Pillar đã chọn ở Bước 1.1. BẮT BUỘC gắn tiền tố `pN_` (lấy từ key Pillar, VD: `pillar_2` → `p2`) vào trước mọi `id`.
4. Mở tệp **đã được tạo sẵn** tại `[run_folder]/session_4/topic_eval_temp.json` và SỬA/ĐIỀN VÀO các trường `[ĐIỀN VÀO ĐÂY]`. Đừng tự tạo file mới.
5. Nộp bài:
   ```bash
   python .agents/skills/book-parser/scripts/prepare_topic_batches.py \
       --session-dir "[run_folder]/session_4/topic_chunks" \
       --submit-file "[run_folder]/session_4/topic_eval_temp.json"
   ```
6. Nếu FAIL → đọc lỗi, sửa `topic_eval_temp.json`, submit lại.
   Nếu PASS → quay lại bước 1.

**Bước 1.4 — Self-Check Gate (Poka-Yoke Topics):**
Logic Self-Check đã được nhúng vào `prepare_topic_batches.py --submit-file`:
- Script validate format (id snake_case 2-5 từ, label tiếng Việt có dấu, tier hợp lệ).
- Script validate evidence (phải là substring thực trong chunk_XX_raw.txt).
- Nếu FAIL → Agent đọc lỗi, sửa và submit lại (= Auto-Repair).
- Nếu Agent không thể sửa sau 2 lần → drop topic đó, ghi log, tiếp tục.

### Bước 1.5 — Semantic Dedup (Giao việc cho Plugin Topic Manager)

Nhằm giảm tải nhận thức cho Agent và ngăn ngừa đứt gãy dữ liệu (mất vết hoặc mất metadata), toàn bộ tiến trình Dedup được di dời sang **Plugin Topic Manager** để xử lý 2-Pass.

1. **Kết xuất dữ liệu thô bàn giao:**
   Chạy lệnh kết xuất file proposed_topics.json:
   ```bash
   python .agents/skills/book-parser/scripts/prepare_topic_batches.py --run-folder "[run_folder]" --decision-map "[run_folder]/audience_decision_map.json" --export-proposed-topics
   ```
2. **Ủy thác xử lý:**
   Hãy bàn giao toàn quyền xử lý cho Plugin `topic_manager` với 2 tham số bắt buộc:
   - `[session_4_dir]`: `[run_folder]/session_4`
   - `[Persona_Path]`: Đường dẫn thư mục persona đã xác định ở Bước 1.1 (VD: `personas/Vuon-ong-steiner`)

   Bạn KHÔNG cần phải tự suy luận đối chiếu YAML hay chạy script tại thư mục `book-parser` nữa.
3. **Đợi kết quả:**
   Hãy tạm dừng luồng chạy tại đây. Chờ cho Plugin xử lý hoàn tất các chặng Internal và External, tự động cập nhật YAML toàn cục và xuất file `session_4/resolved_topics.json`.
4. **Tiếp tục:**
   Khi đã có file `resolved_topics.json`, bạn mới được phép bước sang Phase 2 (Atom Generation).



---

## PHASE 2: Atomization (Script-Driven)

*(Tiếp ngay sau Phase 1 — Audience Decision Map và Topics đều in-scope.)*

**INPUT Phase 2 (in-scope từ Phase 1, không cần Workflow truyền lại):**
- Đường dẫn file cache (từ INPUT Phase 1)
- Run folder path `[run_folder]` (từ INPUT Phase 1)
- Audience Decision Map (từ INPUT Phase 1)
- Topics đã chốt `book_topics` và `chunk_topics_map` (từ OUTPUT Phase 1)

### Bước 2.1: Tải niêm phong Dữ Liệu (Đã có sẵn)
Dữ liệu JSON (`parsed_metadata.json`) và Baseline CSV (`extraction_baseline.csv`) đã được niêm phong hoàn chỉnh từ `/extract-book` và nằm sẵn trong `[run_folder]`. Cấu trúc Baseline đóng vai trò là Manifest cho toàn bộ pipeline. Agent KHÔNG CẦN gọi lệnh nào để parse lại ở bước này mà kế thừa file JSON có sẵn và chuyển thẳng sang Bước 2.2.

### Bước 2.2: Chạy Atomizer Script
Thực thi lệnh Python sau để đẩy data xuống Disk:
```bash
python .agents/skills/book-parser/scripts/atomizer.py \
    "[run_folder]/parsed_metadata.json" \
    vault/ \
    --acronym         "[từ-viết-tắt-của-sách-mũi-tên]" \
    --decision-map    "[run_folder]/audience_decision_map.json" \
    --resolved-topics "[run_folder]/session_4/resolved_topics.json" \
    --baseline        "[run_folder]/extraction_baseline.csv" \
    --report          "[run_folder]/pipeline_report.md"
```

> ⚠️ **LUẬT THÉP:** KHÔNG TỰ PHÂN RÃ FILE BẰNG TAY (Agent execution). 
> - Toàn bộ logic phân mảng DIKW (Tầng 2, 3, 4), đóng dấu YAML Frontmatter, cấy Topics, xử lý Vivid (ký sinh), sinh File Name Slugify, và Gate Validation (POKA-YOKE) **đã được nhúng cứng vào script `atomizer.py`**.
> - Nếu script báo lỗi Quarantine (DLQ), file lỗi tự động được chuyển vào `01-Atomic/_DLQ/`.

> ⚠️ **LUẬT THÉP POKA-YOKE:**
> - Tuyệt đối không được tự ý tạo thủ công file `resolved_topics.json` bằng cách viết tay hoặc dùng bash script `echo`. File này bắt buộc phải được sinh ra từ Bước 1.5 thông qua lệnh `--submit-dedup-batch`.
> - Nếu bạn cố tình bỏ qua Bước 1.5, script `atomizer.py` sẽ ném ra lỗi Fatal và bắt buộc bạn phải dừng luồng Phase 2 để quay lại thực hiện đúng quy trình.

### Bước 2.3: Báo Cáo Cuối Cùng
Lấy Standard Output (stdout) từ `atomizer.py`, tổng hợp và báo cáo lại cho người dùng:
1. Số lượng Atoms đã tạo.
2. Danh sách Wikilinks đã thành công.
3. Số lượng Vivid đã gắn (Appended) và số lượng Vivid dự bị (Cap Reserved).
4. Số lượng lỗi Quarantine (nếu có) và nguyên nhân.
5. Thông báo hoàn tất quá trình `/atomize-book`.
