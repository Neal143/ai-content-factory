---
name: Story Architect
description: Skill chuyên phân tích, bóc tách và cấu trúc hóa Câu chuyện cá nhân (Personal Story) thành mô hình 5 phần chuẩn mực. Đánh giá tính chân thực của story.
---

# Story Architect Skill

Bạn là nhà thiết kế cấu trúc câu chuyện. Nhiệm vụ của bạn là nhận dữ liệu thô (có thể là user đang kể chuyện, hoặc bài post cũ) và biến nó thành một Story Atom sắc bén, an toàn, có thể dùng đi dùng lại.

## Hướng dẫn hoạt động

> ⚠️ **Quy tắc Vòng lặp (Batch-processing):** Nếu nhận nhiều câu chuyện nguyên liệu trong cùng một lần gọi, phải lặp lại **toàn bộ các Bước 2–6** biệt lập cho **từng câu chuyện nguyên liệu thô** riêng lẻ. Tuyệt đối không gom/trộn dữ liệu của nhiều câu chuyện (Topics, Pillar, Audience) vào chung một lần thực thi.

### Bước 1: Đọc tham chiếu BẮT BUỘC
Đọc kĩ 2 file references:
- `.agents/skills/story-architect/references/story-schema.md` — Mô hình 5 phần (S-P-T-O-L), 5 subtypes, Injection Priority Matrix, YAML Frontmatter template, 7 Poka-Yoke Rules chống rác vào vault.
- `.agents/skills/story-architect/references/story-extraction-patterns.md` — 6 regex patterns dùng khi extract story từ bài cũ.

> ⛔ **KHÔNG ĐƯỢC BỎ QUA BƯỚC NÀY.** Toàn bộ Story Schema, subtypes, Poka-Yoke Rules và YAML template nằm trong `story-schema.md`, KHÔNG nằm trong SKILL.md này.

### Bước 2: Phân tích raw story
Xác định:
- **Protagonist**: self / người quen (tên cụ thể) / nhân vật nổi tiếng?
- **SubType**: personal / observed / secondhand / historical / famous_world? (xem bảng 5 subtypes trong `story-schema.md`)
- **Timeline**: thời gian cụ thể (năm, tháng, "hồi đại học")?
- **Topic (Sinh 2-3 topics đa tầng làm biến `[id]` và `[label]`):** Xác định 2-3 cặp `(id, label)` phản ánh câu chuyện theo phổ độ rộng (1 rộng + 1 trung + 1 hẹp tùy chọn). Toàn bộ topics phải nhất quán với 01 Pillar cụ thể mà Story match. Đọc `pillars.yaml`, dựa trên `name` và `description` của mỗi Pillar để chọn Pillar phù hợp nhất với nội dung câu chuyện.
  - **`id`**: English snake_case (ví dụ: `patience_in_parenting`).
  - **`label`**: Tiếng Việt đầy đủ dấu (ví dụ: `Kiên nhẫn trong nuôi dạy con`).
  - **Topic rộng (Broad):** Thường map với emotion/theme của story.
  - **Topic trung (Medium/Central):** Map với lesson/insight cốt lõi của story — bắt buộc 100%.
  - **Topic hẹp (Narrow/Optional):** Map với tình huống cụ thể trong story nếu có tính phổ quát.
- **Measurable outcome**: có số liệu cụ thể không?

### Bước 3: Sinh Output Kép (Split-Output Generation)
Bóc tách raw story thành 2 thực thể Markdown hoàn toàn độc lập theo chuẩn DIKW Graph:

**Kiến thức bắt buộc (8 `knowledge_type`):** `framework`, `principle`, `mental_model`, `actionable_rule`, `typology`, `trend`, `concept`, `philosophy`.

**Hành động 1: Trích xuất L (Lesson) thành File A (Node Tầng 3)**
- Quét vùng Lesson của câu chuyện, ép Agent chọn chính xác **1 trong 8 `knowledge_type`** nêu trên.
- Lưu File A vào thư mục `Solutions/` (nếu type = framework, principle, mental_model, actionable_rule, typology, trend) hoặc `Concepts/` (nếu type = concept, philosophy).
- **Cấy Link Tầng 2:** Sử dụng Pillar mà Story đã match, truy xuất Pillar đó để tìm ra Insight phù hợp nhất. Cấy biến định danh `supports_insight: "[Tên_Insight_Tầng_2]"` vào Frontmatter của File A.
- Định dạng tên: `{slug}.md`.

**Hành động 2: Nguyên trạng Story Atom thành File B (Node Tầng 4)**
- File B VẪN BẢO QUẢN toàn vẹn 5 vùng cốt truyện: Situation → Problem → Turning Point → Outcome → Lesson (Tuyệt đối không cắt bỏ Lesson của File B).
- BẮT BUỘC cấy YAML `supports_knowledge: "[Tên_File_A]"` để KHÓA THẲNG ĐÍCH DANH từ File B về File A vừa sinh ra.
- Format tên file B: `{category}-story-{slug}.md`. Lưu vào thư mục `vault/01-Atomic/Stories/`.

### Bước 4: Gate — Poka-Yoke & Duplicate Check
Cả 2 kiểm định này phải PASS trước khi tiếp tục. Fail bất kỳ điều nào thì dừng và báo user ngay, không xử lý tiếp.
- **Duplicate Check:** Quét `vault/01-Atomic/Stories/` — nếu có story cùng protagonist + cùng turning point → Skip, báo user đã tồn tại.
- **Graph Poka-Yoke:** Áp dụng 7 rules từ `story-schema.md`. File B MẶC ĐỊNH PHẢI CÓ link trỏ vào File A. Nếu mồ côi (Orphan) → AUTO REJECT.

### Bước 5: Semantic Dedup (Topic Manager)

BẮT BUỘC phải chuẩn bị sẵn 4 biến trong working memory cho **câu chuyện nguyên liệu thô đang xử lý**:
- `id`: `[id_rong] [id_trung] ([id_hep])`.
- `label`: `"[label rộng]" "[label trung]" ("[label hẹp]")`.
- `pillar`: `[Tên Pillar đã match ở Bước 2]`
- `audience`: Wikilink trỏ duy nhất vào file Big Audience gốc (file có `audience_level: big` nằm trong thư mục `vault/01-Atomic/Audiences/`).

👉 **HÀNH ĐỘNG:** Đọc và thực thi ngay file `.agents/references/topic_manager/topic_manager.md` tại chỗ.

Lưu mảng `[resolved_id]` trả về vào biến `story_resolved_topics` trong working memory. Cả File A và File B sẽ dùng chung biến này để điền vào `topics:`. (Biến `belongs_to_audience` ghi vào Atom vẫn dùng lại wikilink Big Audience trên).

### Bước 6: Đóng gói YAML KCS
Tạo YAML frontmatter cho cả 2 file tuân thủ triệt để cấu trúc KCS uy tín.
- **The Librarian (Đóng dấu Topic):** 100% Atom (kể cả File A và File B) BẮT BUỘC phải chèn mảng `topics` vào YAML Frontmatter. Giá trị của mảng này là biến `story_resolved_topics` đã lưu trong working memory ở Bước 5. Cú pháp bắt buộc:
  ```yaml
  topics: ["id_rong", "id_trung"]
  # hoặc nếu có topic hẹp:
  topics: ["id_rong", "id_trung", "id_hep"]
  ```
  *(Lưu ý: Chỉ lưu `id` tiếng Anh vào frontmatter, bỏ qua `label` tiếng Việt. Thứ tự mảng: rộng → trung → hẹp)*

