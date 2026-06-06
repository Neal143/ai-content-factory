# Phase 02: Update Book Parser & Extractors (Chuẩn hóa Dữ liệu Mới)
Last Update: 24/05/2026 16:55 (GMT+7)
Status: ✅ Complete
Dependencies: Phase 01

## Objective
Chỉnh sửa kịch bản tạo file Atom vật lý (Cụ thể là `atomizer.py` của `book-parser`) để luồng thực thi đảm bảo 100% việc sinh và ghi nhận `source_type` và `source_id` trực tiếp vào YAML Frontmatter.

## Directions (100% Error-free guarantee)
1. **Xác định vị trí sửa CỐT LÕI (Atomizer Script)**:
   - File Python: `Content Factory/.agents/skills/book-parser/scripts/atomizer.py`
2. **Chỉnh sửa Logic Code (Can thiệp sâu vào Python):**
   - **Vị trí 1 (Ghi nhận `source_id` vào YAML Frontmatter)**: Trong hàm `build_frontmatter(atom)` (khoảng dòng 237-291), chèn thêm `source_id` vào YAML output.
     - *Trước khi sửa*:
       ```python
       # Source
       lines.append('source_type: book')
       lines.append(f'source_name: {json.dumps(atom["source_name"], ensure_ascii=False)}')
       lines.append('confidence: 0.9')
       ```
     - *Sau khi sửa*:
       ```python
       # Source
       lines.append('source_type: book')
       lines.append(f'source_name: {json.dumps(atom["source_name"], ensure_ascii=False)}')
       if atom.get("source_id"):
           lines.append(f'source_id: {json.dumps(atom["source_id"], ensure_ascii=False)}')
       lines.append('confidence: 0.9')
       ```
   - **Vị trí 2 (Tính toán và gán `source_id` trong `run_atomizer`)**: Ở đầu hàm `run_atomizer(metadata, context, vault_root, ...)` (khoảng dòng 736-745), tính toán `source_id` từ `book_meta.book_name`.
     - *Trước khi sửa*:
       ```python
       acr = context["source_acronym"]
       source_name = build_source_name(context)
       build_adm_lookup(context)
       ```
     - *Sau khi sửa*:
       ```python
       acr = context["source_acronym"]
       source_name = build_source_name(context)
       build_adm_lookup(context)
       
       # Trích xuất book_name để sinh source_id
       bm = context.get("book_meta", {})
       book_name = bm.get("book_name", "unknown")
       source_id = slugify_vi(book_name)
       ```
   - **Vị trí 3 (Nhúng `source_id` vào từng Core Atom)**: Trong vòng lặp tạo atom dict (khoảng dòng 796-808), nhúng `source_id` vào dict.
     - *Trước khi sửa*:
       ```python
       # Build atom dict
       atom = {
           "type": atom_type,
           "sub_field_name": classification.get("sub_field_name"),
           "sub_field_value": classification.get("sub_field_value"),
           "topics": topics,
           "source_name": source_name,
           "folder": classification["folder"],
           "filename": filename,
           "body_text": body,
           "chunk_idx": chunk_idx,
       }
       ```
     - *Sau khi sửa*:
       ```python
       # Build atom dict
       atom = {
           "type": atom_type,
           "sub_field_name": classification.get("sub_field_name"),
           "sub_field_value": classification.get("sub_field_value"),
           "topics": topics,
           "source_name": source_name,
           "source_id": source_id,  # Gán source_id đã slugify
           "folder": classification["folder"],
           "filename": filename,
           "body_text": body,
           "chunk_idx": chunk_idx,
       }
       ```
3. **Cập nhật Book Extractor (Nếu cần):**
   - Đảm bảo rằng tệp `atomizer_context.json` do Agent sinh ra luôn chứa `book_meta` với `book_name` đầy đủ. (Thực tế là đã có sẵn trong cấu trúc hiện tại của `book-extractor` pipeline).
4. **Deadcode/Rác Check**: Đảm bảo không có dòng code trùng lặp hoặc các hàm sinh slug không nhất quán.

## Files to Create/Modify
- `.agents/skills/book-parser/scripts/atomizer.py` (Trọng tâm)

---
Next Phase: phase-03-semantic-router.md

