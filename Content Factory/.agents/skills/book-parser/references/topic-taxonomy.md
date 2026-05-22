# Topic Taxonomy — Book Parser

Hướng dẫn xác định 3 tầng topics (Broad / Medium / Narrow) cho sách ở 2 level: Book Topics và Chunk Topics.

---

## Quy tắc chung (áp dụng cho cả Book Topics và Chunk Topics)

Mỗi topic là một cặp `(id, label)`:
- **`id`**: English snake_case, 2-5 từ, dạng danh từ/cụm danh từ (VD: `goal_setting_framework`). Không dùng tên riêng, không dùng mệnh đề nhân quả.
- **`label`**: Tiếng Việt đầy đủ dấu, đọc tự nhiên như tên một bài viết ngắn (VD: `Khung thiết lập mục tiêu tổ chức`).
- **Tái sử dụng:** Mọi topic — kể cả Narrow — phải có thể gắn vào ≥3 nội dung khác trong cùng Pillar.
- **Quan hệ cấp độ:** `Broad ⊇ Medium ⊇ Narrow` về độ bao quát.

---

## Book Topics (phản ánh toàn bộ cuốn sách)

**Broad — Miền vấn đề của cuốn sách** *(bắt buộc)*
Vùng vấn đề mà cuốn sách đặt ra. Đủ rộng để ≥5 cuốn khác trong cùng Pillar dùng chung, nhưng không phải tên lĩnh vực/ngành. Nếu topic có thể dùng làm tên một sub-field học thuật → quá rộng, cần hẹp xuống.

**Medium — Luận điểm trung tâm của cuốn sách** *(bắt buộc)*
Cái mà cuốn sách lập luận hoặc đề xuất — phân biệt cuốn sách này với các cuốn khác trong cùng Broad. Phải cụ thể hơn Broad, nhưng vẫn bao quát toàn bộ cuốn sách.

**Narrow — Lăng kính hoặc cơ chế đặc thù của cuốn sách** *(tùy chọn)*
Cách tiếp cận, đối tượng áp dụng, hoặc cơ chế đặc trưng mà cuốn sách dùng để triển khai luận điểm. Chỉ sinh khi yếu tố này rõ ràng và nhất quán xuyên suốt cuốn sách — không phải chỉ xuất hiện ở một chương.

---

## Chunk Topics (phản ánh từng chunk/chương)

**Broad — Sub-miền mà chunk khai thác** *(bắt buộc)*
Phải nằm trong hoặc bằng Book Broad — không được rộng hơn. Đủ để ≥3–5 chunk từ các cuốn khác nhau dùng chung. Có thể trùng Book Broad nếu chunk đại diện trực tiếp cho miền chính.

**Medium — Luận điểm cốt lõi của chunk** *(bắt buộc)*
Điều mà chunk này lập luận hoặc chứng minh — phải là một sub-claim cụ thể trong hành trình luận điểm của Book Medium. Không được trùng Book Medium (quá rộng), không được là mô tả một ví dụ cụ thể (quá hẹp).

**Narrow — Pattern cơ chế hoặc tình huống trong chunk** *(tùy chọn)*
Pattern mà chunk dùng để minh họa hoặc chứng minh luận điểm — không phải tên sự kiện hay nhân vật cụ thể, mà là kiểu sự kiện đó đại diện. Chỉ sinh khi pattern đủ rõ và có thể nhận diện lại ở nội dung khác.

---

## Quan hệ giữa Book và Chunk Topics

```
Book Broad  ⊇  Chunk Broad
Book Medium  →  Chunk Medium  (Chunk là sub-argument của Book)
Narrow (cả 2 cấp): reusable pattern, không phải định danh duy nhất
```

---

## Kiểm tra nhanh trước khi chốt topics

| Kiểm tra | Nếu không đạt |
|---|---|
| `id` có dùng tên riêng / mệnh đề nhân quả không? | Viết lại thành cụm danh từ snake_case |
| `label` có đọc như tên bài viết không? | Viết lại — bỏ mệnh đề nhân quả, rút gọn |
| Broad có thể dùng làm tên sub-field học thuật không? | Hẹp xuống |
| Narrow có phải tên sự kiện/nhân vật cụ thể không? | Nâng lên thành pattern |
| Chunk Broad có rộng hơn Book Broad không? | Thu hẹp Chunk Broad |
| Chunk Medium có trùng Book Medium không? | Cụ thể hóa xuống |
| Narrow có thể gắn vào ≥3 nội dung khác không? | Điều chỉnh abstraction |
