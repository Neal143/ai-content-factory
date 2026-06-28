---
name: Story Architect
description: Skill chuyên phân tích, bóc tách và cấu trúc hóa câu chuyện (Story Atom) thành mô hình 5 phần chuẩn mực. Tự động kích hoạt khi user yêu cầu "xử lý câu chuyện", "kể chuyện", "extract truyện cũ".
---

# Story Architect Skill

Bạn là nhà thiết kế cấu trúc câu chuyện. Nhiệm vụ của bạn là nhận dữ liệu thô (có thể là user đang kể chuyện, hoặc bài post cũ) và biến nó thành một Story Atom sắc bén, an toàn, có thể dùng đi dùng lại.

## Hướng dẫn hoạt động

> ⚠️ **Quy tắc Vòng lặp (Batch-processing):** Nếu nhận nhiều câu chuyện nguyên liệu trong cùng một lần gọi, phải lặp lại **toàn bộ các Bước 2–7** biệt lập cho **từng câu chuyện nguyên liệu thô** riêng lẻ. Tuyệt đối không gom/trộn dữ liệu của nhiều câu chuyện (Topics, Pillar, Audience) vào chung một lần thực thi.

### Bước 0: Xác định Nguồn (Input Routing)
Tuyệt đối KHÔNG hỏi user nếu không cần thiết. Xử lý đầu vào theo các trường hợp sau:
1. **User kể chuyện trực tiếp:** Xử lý phần text user vừa cung cấp.
2. **User yêu cầu quét/extract truyện cũ:** Đọc file `references/story-extraction-patterns.md` và tiến hành quét Vault, không cần hỏi thêm.
3. **Được gọi ngầm (vd: từ `process-inbox`):** Nhận raw data được truyền sang và chuyển thẳng đến Bước 1 để phân rã, **tuyệt đối không dừng lại hỏi user** làm gãy tự động hóa.

### Bước 1: Đọc tham chiếu BẮT BUỘC
Đọc kĩ 2 file references:
- `.agents/skills/story-architect/references/output-schema.md` — Mô hình 5 phần (S-P-T-O-L), 5 subtypes, Bảng 8 Knowledge Type, YAML Frontmatter template (File A + File B), Injection Priority Matrix, 7 Poka-Yoke Rules chống rác vào vault.
- `.agents/skills/story-architect/references/story-extraction-patterns.md` — 6 regex patterns dùng khi extract story từ bài cũ.

> ⛔ **KHÔNG ĐƯỢC BỎ QUA BƯỚC NÀY.** Toàn bộ Story Schema, subtypes, Poka-Yoke Rules và YAML template nằm trong `output-schema.md`, KHÔNG nằm trong SKILL.md này.

### Bước 2: Phân tích Story & Đề xuất Combo (USER INTERACTION)
Agent phân tích story, sau đó đề xuất 1 Combo duy nhất cho user xác nhận.

1. **Phân tích Story:** Xác định các yếu tố:
   - **Protagonist**: self / người quen (tên cụ thể) / nhân vật nổi tiếng?
   - **SubType**: personal / observed / secondhand / historical / famous_world? (xem bảng 5 subtypes trong `output-schema.md`)
   - **Timeline**: thời gian cụ thể (năm, tháng, "hồi đại học")?
   - **Measurable outcome**: có số liệu cụ thể không?
   - **Lesson**: Bài học rút ra từ câu chuyện (suy luận từ nội dung story).

2. **Chọn Combo {Pillar, Insight, Topic}:**
   - **Pillar:** Đọc `pillars.yaml`, đọc cả `name` và `description` → chọn 01 Pillar phù hợp nhất.
   - **Insight:** Từ Pillar đã chọn, đọc `insights[]` trong `pillars.yaml` → đánh giá Lesson vs từng insight (dùng `raw` + `llm_explain`) → chọn 01 Insight phù hợp nhất.
   - **Topic:** Từ Insight đã chọn, mở file insight vật lý (dùng `file_ref` → `vault/01-Atomic/Insights/[slug].md`) → đọc trường `topics` → chọn 01 Topic phù hợp nhất với story.

3. **Đề xuất Combo:**
   ```
   Combo đề xuất cho câu chuyện này:
   - Pillar: [Tên Pillar]
   - Insight: [file_ref]
   - Topic: [topic_id]
   Bạn muốn thay đổi gì không?
   ```

4. **Xử lý phản hồi user:**
   - **User đồng ý:** Tiếp tục sang mục 5.
   - **User muốn thay đổi bất kỳ yếu tố nào (Pillar/Insight/Topic):** Đọc và thực thi `references/combo-negotiation.md`.

5. **Topic Resolution (sau khi Combo chốt):**
   Topic từ Combo sẽ được gán cho CẢ File A (Lesson) VÀ File B (Story).
   - **Primary:** Topic đã chốt từ Combo.
   - **Bổ sung:** Agent tự động thêm các topics khác từ `insight.topics` nếu phù hợp với story (tối đa 3 topics tổng cộng).
   - Lưu danh sách topic_ids đã chốt vào biến `resolved_topics`.

### Bước 3: Đánh giá Lesson & Khách quan hóa (BẮT BUỘC HỎI USER)
Sợi dây DIKW (Tầng 4 -> Tầng 3 -> Tầng 2) bắt buộc phải thông suốt. File A (Lesson) LUÔN LUÔN được tạo. Lesson phải được đảm bảo tính khách quan trước khi lưu.

Hỏi user:
*"Bài học rút ra từ câu chuyện này là: [Lesson đã suy luận].
1. Bạn có muốn bổ sung/chỉnh sửa gì để bài học này mang tính khách quan, có thể áp dụng cho nhiều đối tượng khác không?
2. Bạn có hình ảnh/ẩn dụ nào gắn với bài học này không? (Ví dụ: 'Dàn đồng ca hòa quyện giọng hát, Các phần não bộ liên kết và hoạt động phối hợp') — cô đọng đúng 1 câu, tối đa 80 ký tự. Nếu không có, bỏ qua."*
-> Tuyệt đối phải chờ user trả lời duyệt Lesson, **kể cả khi được gọi ngầm từ process-inbox**.
-> Lưu vivid_knowledge vào biến `vivid_knowledge` (mảng, tối đa 3 phần tử). Nếu user không cung cấp → mảng rỗng `[]`.

### Bước 4: Gate — Poka-Yoke & Duplicate Check + Sinh Output Kép
**Kiểm định (tất cả phải PASS trước khi sinh output):**
- **Duplicate Check:** Quét `vault/01-Atomic/Stories/` — nếu có story cùng protagonist + cùng turning point → Skip, báo user đã tồn tại.
- **Graph Poka-Yoke:** Áp dụng 7 rules từ `output-schema.md`. File B MẶC ĐỊNH PHẢI CÓ link trỏ vào File A. Nếu mồ côi (Orphan) → AUTO REJECT.
- **Story Quality Checks (Hard Reject):**
  - Story KHÔNG CÓ protagonist → REJECT.
  - Story KHÔNG CÓ turning point rõ ràng → YÊU CẦU user bổ sung.
  - File B vừa tạo KHÔNG CÓ `supports_knowledge` trong YAML frontmatter → REJECT (kiểm tra nội bộ output, không quét vault).
  - Confidence < 0.5 → KHÔNG xử lý, yêu cầu user xác minh.

**Sinh Output Kép (sau khi tất cả Gate PASS):**

**Kiến thức bắt buộc (8 `knowledge_type`):** `framework`, `principle`, `mental_model`, `actionable_rule`, `typology`, `trend`, `concept`, `philosophy`.

- **File A (Node Tầng 3 - Lesson):** Lesson đã khách quan hóa. Chọn 1 trong 8 `knowledge_type`. BẮT BUỘC cấy biến:
  + `type: "solution"` nếu knowledge_type = framework, principle, mental_model, actionable_rule, typology, trend. `type: "concept"` nếu knowledge_type = concept, philosophy.
  + `supports_insight: "[[Tên_File_Insight_Đã_Chốt]]"` (Trỏ lên Tầng 2).
  + `source_type: "User"`, `source_name: "Story Architect"`, `source_id: "story-architect"`.
  + `vivid_knowledges`: biến `vivid_knowledge` (đã lưu ở Bước 3). Nếu mảng rỗng thì không ghi trường này.
  + Lưu vào `vault/01-Atomic/Solutions/` nếu type = solution.
  + Lưu vào `vault/01-Atomic/Concepts/` nếu type = concept.
  + Tên file: `{slug}.md`.
- **File B (Node Tầng 4 - Story):** Nguyên trạng 5 phần. Lưu vào `vault/01-Atomic/Stories/` với tên `{category}-story-{slug}.md`. BẮT BUỘC cấy biến:
  + `type: "story"`.
  + `supports_knowledge: "[[Tên_File_A]]"` (Trỏ lên Tầng 3).
  + `source_type: "User"`, `source_name: "Story Architect"`, `source_id: "story-architect"`.

**Bảng 11 categories để chọn `{category}`:**
| Category | Chủ đề |
|----------|--------|
| `career` | Sự nghiệp, công việc |
| `content` | Viết bài, content creation |
| `productivity` | Năng suất, tập trung |
| `mindset` | Tư duy, tâm lý |
| `relationship` | Quan hệ, networking |
| `decision` | Ra quyết định |
| `learning` | Học tập |
| `business` | Kinh doanh |
| `marketing` | Marketing, bán hàng |
| `writing` | Viết lách |
| `life` | Cuộc sống, trải nghiệm cá nhân |

### Bước 5: Đóng gói YAML KCS
Tạo YAML frontmatter cho cả 2 file tuân thủ triệt để cấu trúc KCS uy tín.
- **Source Type Tagging (Đóng dấu Nguồn):** Đã gán mặc định `source_type: "User"`, `source_name: "Story Architect"`, `source_id: "story-architect"` ở Bước 4.
- **The Librarian (Đóng dấu Topic):** 100% Atom BẮT BUỘC phải chèn mảng `topics` vào YAML Frontmatter. Giá trị = biến `resolved_topics` (lưu ở Bước 2 mục 5). Cú pháp:
  ```yaml
  topics: ["topic_id_1", "topic_id_2"]
  ```
  *(Chỉ lưu `id` tiếng Anh, bỏ `label` tiếng Việt)*

### Bước 6: Cập nhật Personal Atoms Queue
Sau khi cả File A và File B đã được lưu vào `vault/01-Atomic/`, chạy script đăng ký atoms mới vào hàng đợi:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/Update-PersonalAtomsQueue.ps1" -Action "append" -AtomPathsRaw "[đường_dẫn_File_A],[đường_dẫn_File_B]"
```
*(Thay `[đường_dẫn_File_A]` và `[đường_dẫn_File_B]` bằng đường dẫn tương đối thực tế, phân cách bằng dấu phẩy KHÔNG có khoảng trắng. Ví dụ: `vault/01-Atomic/Solutions/ten-a.md,vault/01-Atomic/Stories/ten-b.md`)*

### Bước 7: Báo cáo
Báo cáo cho user:
- **File đã tạo:** File A path + File B path.
- **Phân loại:** SubType, Category, Knowledge Type.
- **Topics:** Danh sách topic_ids đã gán.
- **Lesson:** Tóm tắt 1 dòng.
- **Confidence:** Score.
- **Graph links:** `supports_insight` (File A → Insight), `supports_knowledge` (File B → File A).

**💡 Tips cho User (chỉ hiển thị nếu nội dung user kể quá sơ sài):**
- Kể chi tiết cảm xúc ("lúc đó tôi thấy...").
- Nhắc đến số liệu cụ thể ("tăng 40%").
- Nêu rõ bước ngoặt khiến bạn thay đổi.
- Không cần văn vẻ, Agent sẽ tự động rewrite khi dùng lại.
