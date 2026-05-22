---
name: Book Parser (The Atomizer)
description: Skill phân rã sách thành Atom vật lý. Được gọi DUY NHẤT 1 LẦN bởi /atomize-book sau Bước 2 (book-audience-matcher). Phase 1: Tự động sinh Book Topics & Chunk Topics, Reverse-Sync topic_manager.md — không Human-in-the-loop. Phase 2: Atomization (tiếp ngay sau Phase 1 trong cùng 1 lần gọi).
---

# Book Parser Skill (The Atomizer)

// turbo-all

Bạn là chuyên gia phân rã hạt nhân (Atomizer). Nhiệm vụ của bạn là lấy file Raw Markdown từ `02-sources/books/`, phân rã thành Atom vật lý theo đúng cấu trúc 4 Tầng DIKW trước khi Commit I/O ra đĩa.

Skill này được `/atomize-book` gọi **1 lần duy nhất**. Phase 1 và Phase 2 thực thi tuần tự trong cùng 1 conversation context.

---

## PHASE 1: Topic Generation

**INPUT Phase 1 (nhận từ /atomize-book sau Bước 2):**
- File cache path: `vault/02-sources/books/[Tên Sách].md`
- Run folder path: `.extraction_runs/[ten-sach-slug-khong-dau]_[YYYY-MM-DD]/`
  *(Run-folder được /atomize-book truyền trực tiếp qua INPUT. Thư mục đã tồn tại từ lúc /extract-book chạy. Trong tài liệu này gọi tắt là `[run_folder]`. KHÔNG tự derive.)*
- Audience Decision Map: Array of entries, mỗi entry có `scope`, `chunk_index`, `audience_filename`, ... từ book-audience-matcher (xem schema tại book-audience-matcher/SKILL.md)

### Bước 1: Sinh Topic Tự Động & Reverse-Sync

Ngay khi nhận INPUT, thực hiện tuần tự hoàn toàn tự động — **không dừng chờ User**.

**Bước 1.1 — Chọn Pillar gốc (duy nhất toàn book):**
Đọc `pillars.yaml` của Persona đang active. Chọn **01 Pillar** phù hợp nhất với nội dung tổng thể của sách. Pillar này **bất biến** — dùng chung cho Book Topics và mọi Chunk Topics trong toàn bộ pipeline.

**Bước 1.2 — Sinh Book Topics (2-3 topics, phản ánh toàn bộ cuốn sách):**
Đọc hướng dẫn đầy đủ tại `.agents/skills/book-parser/references/topic-taxonomy.md` → Section **"Book Topics"** và **"Quy tắc chung"**. Sinh 2-3 cặp `(id, label)` theo đúng định nghĩa Broad / Medium / Narrow. Chạy **Kiểm tra nhanh** trước khi chốt.

> ⚠️ **Quy tắc Vòng lặp (Chunk Isolation):** Từ Bước 1.3 trở đi, phải thực thi **biệt lập cho từng chunk riêng lẻ** — không gom, không trộn:
> - **Cách ly Rác (Warning Isolation):** Trực tiếp BỎ QUA toàn bộ quy trình (không bóc tác Topic, không rã Atom) đối với bất kỳ Chunk nào chứa chuỗi cờ `> [!warning]`. Ghi nhận dang sách Chunk bị skip ra màn hình chờ Human xử lý.
> - **Bước 1.3:** Sinh Chunk Topics độc lập cho từng chunk.
> - **Bước 1.5:** Chạy Semantic Dedup độc lập cho từng nhóm topic (Book Topics, Chunk 01 Topics, Chunk 02 Topics,...).
>
> Tuyệt đối không trộn Topics của nhiều chunk/nhóm vào chung một lần thực thi phân tích.

**Bước 1.3 — Sinh Chunk Topics (2-3 topics mỗi chunk):**
Với **từng chunk** trong file cache, đọc hướng dẫn tại `.agents/skills/book-parser/references/topic-taxonomy.md` → Section **"Chunk Topics"** và **"Quan hệ giữa Book và Chunk Topics"**. Sinh 2-3 cặp `(id, label)` theo đúng định nghĩa. Chạy **Kiểm tra nhanh** trước khi chốt. Cùng Pillar đã chọn ở Bước 1.1.

**Bước 1.4 — Self-Check Gate (Poka-Yoke Topics):**
Chạy toàn bộ checklist trong `topic-taxonomy.md` → Section "Kiểm tra nhanh" lên tất cả topics vừa sinh (Book + Chunk).
- **Fallback Lớp 1 (Auto-Repair):** Với mỗi vi phạm, **đọc lại nội dung nguồn** (toàn bộ file cache nếu là Book Topic, chunk cụ thể nếu là Chunk Topic) **và** đọc lại định nghĩa tầng tương ứng trong `topic-taxonomy.md`, sau đó **regenerate lại topic vi phạm** với vi phạm đã được nhận diện làm constraint. Ghi log sửa đổi ra CLI.
- **Fallback Lớp 2 (Drop & Flag):** Nếu sau khi đọc lại và regenerate vẫn không tạo được topic hợp lệ → **drop topic đó**, ghi cảnh báo ra CLI, tiếp tục với các topics còn lại. Không dừng flow.

**Bước 1.5 — Semantic Dedup (Batch Mode):**

Trước khi quét, BẮT BUỘC phải chuẩn bị sẵn 4 biến tương ứng trong working memory cho **từng nhóm topic riêng lẻ** (nhóm Book Topics, riêng nhóm Chunk 01 Topics, Chunk 02 Topics,...):
- `id`: mảng `[id_rong] [id_trung] ([id_hep])` của nhóm đó.
- `label`: mảng `"[label rộng]" "[label trung]" ("[label hẹp]")` của nhóm đó.
- `pillar`: Tên Pillar đã chốt chung ở Bước 1.1.
- `audience`: Wikilink trỏ vào file Audience đặc thù lấy ra ứng với mảng topic đang xử lý (từ Audience Decision Map nhận ở phần INPUT).

👉 **HÀNH ĐỘNG:** Đọc và thực thi file `topic_manager.md` tại `.agents/references/topic_manager/topic_manager.md` *(workspace root-relative — KHÔNG nằm trong `vault/`, không được prefix thêm `vault/`)*, sử dụng **Chế độ Batch** (xem Section "Chế độ Batch" trong topic_manager.md). Không dừng chờ.

Sau khi script `batch-commit` chạy xong, đọc file `[run_folder]/resolved_topics.json` để lấy:
- `book_topics`: mảng `[resolved_id]` của Book Topics.
- `chunk_topics_map`: dict `{ chunk_index: [resolved_id, ...] }` của Chunk Topics.


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

### Bước 2.2: Đóng gói Context
Tạo file `[run_folder]/atomizer_context.json` bằng cách **đọc trực tiếp `[run_folder]/resolved_topics.json`** (output của Bước 1.5) và copy dữ liệu sang. File JSON PHẢI có đúng cấu trúc sau:
```json
{
  "source_acronym": "[từ-viết-tắt-của-sách-mũi-tên]",
  "book_meta": {
      "book_name": "Tên Sách",
      "author": "Tác Giả",
      "year": "Năm xuất bản"
  },
  "book_topics": [],          // Copy từ resolved_topics.json["book"]
  "chunk_topics_map": {}      // Copy các key số từ resolved_topics.json
}
```

> ⚠️ **KHÔNG** nhúng `audience_decision_map` vào file này. Script `atomizer.py` đọc trực tiếp từ file `audience_decision_map.json` qua argument `--decision-map` (xem Bước 2.3).

> ⚠️ **KHÔNG** tự tổng hợp `book_topics` hoặc `chunk_topics_map` từ working memory. Đọc từ `resolved_topics.json` và copy nguyên.

### Bước 2.3: Chạy Atomizer Script
Thực thi lệnh Python sau để đẩy data xuống Disk:
```bash
python .agents/skills/book-parser/scripts/atomizer.py \
    "[run_folder]/parsed_metadata.json" \
    "[run_folder]/atomizer_context.json" \
    vault/ \
    --decision-map "[run_folder]/audience_decision_map.json" \
    --baseline     "[run_folder]/extraction_baseline.csv" \
    --report       "[run_folder]/pipeline_report.md"
```

> ⚠️ **LUẬT THÉP:** KHÔNG TỰ PHÂN RÃ FILE BẰNG TAY (Agent execution). 
> - Toàn bộ logic phân mảng DIKW (Tầng 2, 3, 4), đóng dấu YAML Frontmatter, cấy Topics, xử lý Vivid (ký sinh), sinh File Name Slugify, và Gate Validation (POKA-YOKE) **đã được nhúng cứng vào script `atomizer.py`**.
> - Nếu script báo lỗi Quarantine (DLQ), file lỗi tự động được chuyển vảo `01-Atomic/_DLQ/`.

### Bước 2.4: Báo Cáo Cuối Cùng
Lấy Standard Output (stdout) từ `atomizer.py`, tổng hợp và báo cáo lại cho người dùng:
1. Số lượng Atoms đã tạo.
2. Danh sách Wikilinks đã thành công.
3. Số lượng Vivid đã gắn (Appended) và số lượng Vivid dự bị (Cap Reserved).
4. Số lượng lỗi Quarantine (nếu có) và nguyên nhân.
5. Thông báo hoàn tất quá trình `/atomize-book`.
