---
name: phase-02-gi-backfill.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Phase
usage: Hướng dẫn thực thi Phase 2 — Re-run Topic Generation + Backfill topics cho GI_ atoms
output: resolved_topics.json mới + toàn bộ GI_ atoms có topics đúng topic_map.yaml IDs
logic: Re-run Phase 1 book-parser cho good-inside → sinh topics đúng → viết script backfill chỉ update trường topics
---

# Phase 02: Good-Inside Topic Backfill

**Trạng thái:** ⬜ Pending
**Nhóm BRIEF:** C
**Dependencies:** Phase 1 (topic_map.yaml có thể được cập nhật bởi Semantic Dedup)

---

## Task 2.1: Re-run Phase 1 Topic Generation cho Good-Inside

**Mục tiêu:** Sinh topics đúng cho good-inside qua Semantic Dedup, tạo `resolved_topics.json`.

**Input có sẵn trong run folder** `.extraction_runs/good-inside_2026-05-21/`:
- `parsed_metadata.json` (332KB)
- `audience_decision_map.json` (13KB)
- File cache: `vault/02-sources/books/Good Inside.md`

**Thao tác:** Thực thi đúng `book-parser/SKILL.md` Phase 1 (Bước 1.1 → 1.5) cho good-inside:

1. **Bước 1.1 — Chọn Pillar:** Đọc `personas/Neal/pillars.yaml` → chọn 1 Pillar phù hợp nhất với nội dung Good Inside (Dr. Becky Kennedy).
2. **Bước 1.2 — Sinh Book Topics:** Đọc `topic-taxonomy.md` → sinh 2-3 cặp `(id, label)` cho cả cuốn sách. Format: English snake_case, 2-5 từ.
3. **Bước 1.3 — Sinh Chunk Topics:** Sinh 2-3 topics **riêng biệt** cho **từng chunk** (31 chunks, mỗi chunk PHẢI có topics khác nhau nếu nội dung khác nhau).
4. **Bước 1.4 — Self-Check Gate:** Chạy Poka-Yoke checklist trong `topic-taxonomy.md`.
5. **Bước 1.5 — Semantic Dedup (Batch Mode):** Đọc `topic_manager.md` → Chạy Batch Mode → Tạo `proposed_topics.json` → Chạy `topic_manager.py batch-commit` → Output `resolved_topics.json`.

**Output kỳ vọng:** File `.extraction_runs/good-inside_2026-05-21/resolved_topics.json`:
```json
{
  "book": ["resolved_id_1", "resolved_id_2"],
  "2": ["resolved_id_3", "resolved_id_4"],
  "3": ["resolved_id_5", "resolved_id_6"],
  ...
}
```

**Kiểm tra:**
- File `resolved_topics.json` tồn tại trong run folder.
- File `proposed_topics.json` tồn tại trong run folder.
- `topic_map.yaml` đã được cập nhật (nếu có topic mới).
- Mỗi chunk có topics riêng biệt (không 30 chunks cùng topics).

---

## Task 2.2: Tạo lại `atomizer_context.json`

**File:** `.extraction_runs/good-inside_2026-05-21/atomizer_context.json`

**Thao tác:** Đọc `resolved_topics.json` (output Task 2.1) → tạo lại file theo SKILL.md L80-L96:

```json
{
    "source_acronym": "GI",
    "book_meta": {
        "book_name": "Good Inside",
        "author": "Dr. Becky Kennedy",
        "year": "2022"
    },
    "book_topics": [],
    "chunk_topics_map": {}
}
```

- `book_topics`: Copy từ `resolved_topics.json["book"]`
- `chunk_topics_map`: Copy các key số từ `resolved_topics.json`

> ⚠️ PHẢI đọc từ `resolved_topics.json` và copy nguyên. KHÔNG tự tổng hợp từ working memory (SKILL.md L96).

**Kiểm tra:** So sánh `atomizer_context.json` mới với `resolved_topics.json` → dữ liệu phải khớp 100%.

---

## Task 2.3: Viết và chạy script backfill topics

**Mục tiêu:** Update **chỉ trường `topics`** trong frontmatter từng file `GI_*`. Giữ nguyên mọi trường khác (bao gồm vivid data).

> ⚠️ **KHÔNG re-run `atomizer.py`** — `curate_vivids.py` đã gắn vivid data (`vivid_insights`, `vivid_knowledges`) vào frontmatter sau lần parse đầu. Re-atomize sẽ reset vivid về `[]`.

**Script cần tạo:** `.agents/skills/dikw-bridge/scripts/backfill-topics.py`

**Logic hoạt động:**
1. Đọc `atomizer_context.json` → lấy `book_topics` và `chunk_topics_map`.
2. **Build mapping `filename → chunk_index`** bằng `extraction_baseline.csv`:
   - Đọc CSV → filter rows có `section == "atom"`.
   - Mỗi row có `chunk` (= chunk_index), `category` (insight/knowledge/story/quote/evidence), `id` (tên gốc tiếng Việt).
   - Áp dụng hàm `slugify_vi()` (copy từ `atomizer.py` L52-71) lên `id` → sinh slug.
   - Tạo filename theo quy tắc `atomizer.py` L185-230:
     - insight: `GI_{slug}.md`
     - knowledge (solution/concept): `GI_{slug}.md`
     - story: `GI_story-{slug}-{chunk}.md`
     - quote: `GI_quote-{slug}-{chunk}.md`
     - evidence: `GI_data-{slug}-{chunk}.md`
   - Kết quả: dict `{ "GI_slug.md": chunk_index, ... }`
3. Quét tất cả file `GI_*` trong 6 thư mục `vault/01-Atomic/` (`Insights/`, `Solutions/`, `Concepts/`, `Stories/`, `Quotes/`, `Data-Points/`).
4. Với mỗi file:
   - Tra mapping → lấy chunk_index.
   - Tính topics mới = `book_topics + chunk_topics_map[chunk_index]` (deduplicated, tương đương `get_topics()` trong `atomizer.py` L338-348).
   - Đọc file → tách frontmatter (block đầu tiên giữa 2 dòng `---`) và body.
   - Replace dòng `topics: [...]` trong frontmatter bằng topics mới (format `json.dumps()`).
   - Ghi lại file = frontmatter mới + body gốc (không thay đổi).
5. In report: số file đã update, danh sách topics mới cho từng file.

**Input:**
- `--context`: Path đến `atomizer_context.json`
- `--metadata`: Path đến `parsed_metadata.json`
- `--vault`: Path đến `vault/01-Atomic/`
- `--prefix`: Prefix file cần update (mặc định `GI_`)
- `--dry-run`: Preview changes mà không ghi file

**Kiểm tra:**
1. Chạy `--dry-run` trước → review output.
2. Chạy thật → mở 3-5 file GI_ trong Obsidian → xác nhận `topics` đã đúng topic_map.yaml IDs.
3. Xác nhận `vivid_insights`, `vivid_knowledges` vẫn nguyên vẹn (không bị reset).
4. Xác nhận body content không bị thay đổi.

---

**Hoàn thành Phase 2 → Chuyển sang Phase 3.**
