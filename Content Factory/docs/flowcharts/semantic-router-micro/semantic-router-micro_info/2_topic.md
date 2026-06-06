## RunScript
### Bước 3: Quét Direct Match
Đối chiếu cơ học input ngắn (không dài hơn 1 tiêu đề bài viết) với `topic_map.yaml`. Chạy:

`powershell -ExecutionPolicy Bypass -File .agents/skills/semantic-router/scripts/direct_match.ps1 -Topic "[yêu cầu tạo nội dung]" -TopicMapPath "[Persona_Path]/topic_map.yaml" -Pillar "$Target_Pillar"`

**Phân luồng output:**
- `MATCH`: Trích xuất `mapped_topic` (id), `Target_Pillar` (pillar), `Target_Audience` (audience) → **Bước 8**.
- `MISS` hoặc input quá dài: → **Bước 4**.

## GenTopic
### Bước 4: Sinh Topic truy vấn
Agent tự sinh tối đa 2 Topic. Format chung: `id` = English snake_case 2-4 từ, `label` = tiếng Việt, ngắn, tự nhiên như tên 1 bài viết.
- **Topic Trung** [BẮT BUỘC]: Luận điểm cốt lõi.
- **Topic Hẹp** [TÙY CHỌN]: Chỉ sinh khi input có bối cảnh sự kiện cụ thể. 

Ví dụ: *"Dạy con tự xử lý cảm xúc tức giận khi bị bạn giành đồ chơi"*
→ Trung: `parenting_emotional_regulation` / `Dạy con điều chỉnh cảm xúc`
→ Hẹp: `toddlers_sharing_conflict` / `Dạy con xử lý xung đột tranh giành đồ chơi`

## MapTopic
### Bước 5: Đối chiếu Topic Map
Đối chiếu Topic từ Bước 4 với `topic_map.yaml`:
- **Lọc:** Nếu có `Target_Pillar`, chỉ quét topic thuộc `pillar_parents` tương ứng. Nếu ủy quyền, quét toàn bộ.
- **Matching:** Đối chiếu ngữ nghĩa dựa trên cả `id` (English) và `label` (tiếng Việt), dùng cả hai làm tín hiệu bổ trợ.
- **Cascade:** Nếu khớp nhiều entry → chọn duy nhất entry có cấp phân nhánh sâu nhất (hẹp nhất).

Phân luồng:
- **Matched:** Trích xuất `mapped_topic` (id gốc trong Map), loại bỏ id tạm từ Bước 4. Ánh xạ `Target_Pillar`, `Target_Audience` → **Bước 8**.
- **Miss:** Bảo lưu id Topic Hẹp làm `novel_angle` → **Bước 6**.
