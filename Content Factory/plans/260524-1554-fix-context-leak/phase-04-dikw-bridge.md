# Phase 04: Update DIKW Bridge (Sửa Lỗ hổng Tìm kiếm & Lọc Kép)
Last Update: 24/05/2026 16:55 (GMT+7)
Status: ✅ Complete
Dependencies: Phase 03

## Objective
Thiết lập "Màng lọc Toàn Cục" cho DIKW Bridge. Đảm bảo triệt để việc chặn Atom rác từ sách lạ, nhưng KHÔNG bóp chết các Nguồn phụ trợ dùng chung (như Viral Posts).

## Directions (100% Error-free guarantee)
1. **Xác định vị trí sửa**: `.agents/skills/dikw-bridge/SKILL.md`.

2. **Thiết lập Màng Lọc Nguồn Toàn Cục (Smart Global Pre-Filter):**
   - **Vị trí 1 (Metadata Frontmatter của SKILL.md)**: Chỉ rõ nguồn đầu vào nhận thêm `Target_Source_IDs` từ Blackboard.
     - *Trước khi sửa*:
       ```markdown
       ---
       name: DIKW Bridge
       description: Skill đóng vai trò cầu nối, quét kho dữ liệu Obsidian (Vault) để tìm nguyên liệu liên quan đến topic và xếp thứ hạng theo mô hình DIKW.
       last_update: 21/05/2026 11:22 (GMT+7)
       ---
       ```
     - *Sau khi sửa*:
       ```markdown
       ---
       name: DIKW Bridge
       description: Skill đóng vai trò cầu nối, quét kho dữ liệu Obsidian (Vault) để tìm nguyên liệu liên quan đến topic và xếp thứ hạng theo mô hình DIKW.
       last_update: 24/05/2026 16:55 (GMT+7)
       ---
       ```
   - **Vị trí 2 (Bổ sung thủ tục Smart Global Pre-Filter trước Bước 2)**: Chèn thêm mục bộ lọc nguồn ngay sau Bước 1 và trước Bước 2.
     - *Nội dung bổ sung*:
       ```markdown
       ### Thủ tục phụ: Smart Global Pre-Filter (Màng Lọc Nguồn Toàn Cục)
       Trước khi thực hiện các phép lọc chuyên sâu ở Bước 2, hãy đọc `Target_Source_IDs` từ Blackboard (`00-blackboard.yaml`).
       
       1. **Nếu `Target_Source_IDs` CÓ RÀNG BUỘC (mảng có phần tử, ví dụ: `["good-inside"]`):**
          - Quét tất cả các file MD trong **Nguồn 1** (`vault/01-Atomic/` gồm 6 thư mục con: `Stories`, `Solutions`, `Insights`, `Concepts`, `Quotes`, `Data-Points`).
          - Đọc trường `source_id` trong frontmatter của từng file.
          - **LOẠI BỎ NGAY LẬP TỨC** các file thuộc `vault/01-Atomic/` ra khỏi danh sách ứng viên đưa vào Rổ nguyên liệu nếu file đó không chứa thuộc tính `source_id` hoặc giá trị `source_id` không nằm trong mảng `Target_Source_IDs`.
          - ⛔ **QUY TẮC BẢO TOÀN (Zero-breakage Rule):** Màng lọc này TUYỆT ĐỐI KHÔNG ÁP DỤNG cho các file quét từ các **Nguồn 2-4** (như `Viral Posts/`, `Posted/`, `Reflective Writing.md`). Những file này không có `source_id` và thuộc về tài nguyên dùng chung của Persona, phải được giữ nguyên vẹn để đi tiếp vào vòng chấm điểm như bình thường.
       
       2. **Nếu `Target_Source_IDs` TRỐNG (mảng rỗng hoặc null, tức viết tự do):**
          - Bỏ qua màng lọc này, giữ nguyên toàn bộ các file ứng viên và đi tiếp vào Bước 2.
       ```

## Files to Create/Modify
- `.agents/skills/dikw-bridge/SKILL.md`

---
Next Phase: Hoàn thành Plan.
