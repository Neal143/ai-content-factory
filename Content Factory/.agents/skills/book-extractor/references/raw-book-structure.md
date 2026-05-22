---
name: Raw Book File Structure Standard
description: >
  Tiêu chuẩn kỹ thuật bắt buộc cho file output của book-extractor.
  Mọi file sách khai thác từ NotebookLM đều PHẢI tuân thủ schema này.
  Là Single Source of Truth cho book-audience-matcher và book-parser.
---

# Raw Book File Structure Standard

## Vị trí lưu trữ
`vault/02-sources/books/[Tên Sách Đã Sanitize].md`

---

## Phần 1: Header Chunk (DUY NHẤT 1 lần, đứng đầu file, TRƯỚC mọi data_chunk)

```
META_BOOK: book_name=[Tên sách] | author=[Tác giả] | year=[Năm] | topics=[Chủ đề] | total_chunks=[N]
META_BOOK_AUDIENCE: book_audience=Người muốn [Main job] khi [Circumstance]
```

| Trường | Ghi chú |
|--------|---------|
| `total_chunks` | Số chunk trong TOC — dùng POKA-YOKE Bước 3 của Workflow |
| `META_BOOK_AUDIENCE` | Plaintext, KHÔNG có dấu ngoặc kép quanh "Người", KHÔNG có markdown formatting |

Phần còn lại của header (Tổng quan 1.1→1.8, Thesis Statement, TOC_MASTER) nằm ngoài data_chunk và không có thẻ META.

### Sentinel Marker (BẮT BUỘC)

Sau TOC_MASTER và trước `<data_chunk>` đầu tiên, PHẢI có dòng:

```
<!-- HEADER_END -->
```

---

## Phần 2: Content Chunks (lặp lại N lần, theo thứ tự TOC_MASTER)

### Collapsible Header Pattern

Mỗi chunk có **1 heading bên NGOÀI** `<data_chunk>` để Obsidian có thể fold/unfold:

```
## Chunk N: [Tên Chunk gốc từ TOC]

> 🎯 [JTBD từ META_CHUNK_AUDIENCE] | 🔥 [insight_name từ Mục ①]

<data_chunk>
META_CHUNK: CHUNK=[Tên Chunk gốc từ TOC] | CHUNK_index=[N, bắt đầu từ 1]
META_CHUNK_AUDIENCE: chunk_audience=Người muốn [Main job] khi [Circumstance]

[Nội dung ①②③④⑤ với các thẻ META: bên trong]

</data_chunk>
```

**Quy tắc format META:**
- `META_CHUNK:` và `META_CHUNK_AUDIENCE:` là **plaintext thuần** — KHÔNG được có `**` (bold), `` ` `` (backtick), hay bất kỳ markdown formatting nào.
- `META_CHUNK_AUDIENCE:` dùng `Người` (KHÔNG có dấu ngoặc kép `"Người"`).

**Trường hợp chunk bị SKIPPED (Gate [1] exhaust — response < 200 ký tự sau retry 2 lần):**
```
## Chunk N: [Tên Chunk]

> 🎯 Unknown Audience | 🔥 Unknown Insight

<data_chunk>
> [!warning] SKIPPED_SHORT_CONTENT
[Nội dung ngắn NLM trả về]
</data_chunk>
```

---

## Ghi chú cho Downstream Skills

- `META_BOOK_AUDIENCE` (1 dòng duy nhất, nằm trong header) → `book-audience-matcher` đọc trước.
- `META_CHUNK_AUDIENCE` (N dòng — mỗi `<data_chunk>` chứa đúng 1 dòng) → `book-audience-matcher` đọc sau, theo thứ tự `CHUNK_index`.
- Heading `## Chunk N:` và summary line `> 🎯 ... | 🔥 ...` nằm NGOÀI `<data_chunk>` — downstream parser BỎ QUA chúng, chỉ đọc nội dung bên trong `<data_chunk>`.
- Mọi phân tích về level, parent-child, hierarchy là trách nhiệm của `book-audience-matcher` — không được xử lý tại đây.
