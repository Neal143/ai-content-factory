---
name: Semantic Router
description: Định tuyến topic từ yêu cầu nội dung → ánh xạ vào topic_map, xác định Pillar, Audience.
input: Chuỗi "[yêu cầu tạo nội dung]"
output: Blackboard 6 biến: Target_Pillar, Target_Audience, topic, Is_Novel_Angle, Persona_Path, resolved_jtbd.
---

# Semantic Router Skill

> EXECUTION_KEY: eb8617a4

**Quy tắc Cốt lõi:** Skill này trả về DUY NHẤT 1 TOPIC — hoặc `mapped_topic` hoặc `novel_angle`, không bao giờ cả hai.

### Thủ tục: Pillar Duplicate Check

Đọc `output/logs/production-log.md`. Trích xuất `Pillar` của 2 bài gần nhất.
- Nếu cả 2 trùng với `Target_Pillar` → Dừng, hỏi: *"Pillar **[Target_Pillar]** đã dùng 2 bài liên tiếp. Tiếp tục hay đổi Pillar?"*
  - User tiếp tục → đi tiếp bước kế.
  - User đổi → quay Bước 1.
- Nếu không trùng → đi tiếp.

---

## Bước 1: Xác định Pillar

Đọc `[Persona_Path]/pillars.yaml` (Persona_Path đã xác định ở Bước 3 của workflow). Xác định `Target_Pillar`:

- **A — User KHÔNG nhập Pillar:**
  - In danh sách Pillar đánh số. Thêm option cuối: `N. Hãy chọn cho tôi`.
  - Tư vấn 1 Pillar phù hợp nhất.
  - ⛔ STOP — CHỜ USER PHẢN HỒI. KHÔNG tự chọn.
  - User chọn 1→N-1: chốt `Target_Pillar` → **Bước 2**.
  - User chọn N (ủy quyền): → **Bước 3** (bỏ qua Bước 2).

- **B — User CÓ nhập Pillar:**
  - Semantic Match với `pillars.yaml`.
  - Không khớp: Cảnh báo, in menu chọn lại. Gợi ý có thể chạy `/onboarding-persona` để thêm Pillar mới.
  - Khớp: chốt `Target_Pillar` → **Bước 2**.

## Bước 2: Kiểm tra trùng Pillar (Sớm)

Chỉ áp dụng khi User tự chọn Pillar (không ủy quyền).
→ Thực hiện **Pillar Duplicate Check**. Bước kế: **Bước 3**.

## Bước 3: Quét Direct Match

Đối chiếu cơ học input ngắn (không dài hơn 1 tiêu đề bài viết) với `topic_map.yaml`. Chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/semantic-router/scripts/direct_match.ps1 -Topic "[yêu cầu tạo nội dung]" -TopicMapPath "[Persona_Path]/topic_map.yaml" -Pillar "$Target_Pillar"
```

**Phân luồng output:**
- `MATCH`: Trích xuất `mapped_topic` (id), `Target_Pillar` (pillar), `Target_Audience` (audience) → **Bước 8**.
- `MISS` hoặc input quá dài: → **Bước 4**.

## Bước 4: Sinh Topic truy vấn

Agent tự sinh tối đa 2 Topic. Format chung: `id` = English snake_case 2-4 từ, `label` = tiếng Việt, ngắn, tự nhiên như tên 1 bài viết.
- **Topic Trung** [BẮT BUỘC]: Luận điểm cốt lõi.
- **Topic Hẹp** [TÙY CHỌN]: Chỉ sinh khi input có bối cảnh sự kiện cụ thể. 

Ví dụ: *"Dạy con tự xử lý cảm xúc tức giận khi bị bạn giành đồ chơi"*
→ Trung: `parenting_emotional_regulation` / `Dạy con điều chỉnh cảm xúc`
→ Hẹp: `toddlers_sharing_conflict` / `Dạy con xử lý xung đột tranh giành đồ chơi`

## Bước 5: Đối chiếu Topic Map

Đối chiếu Topic từ Bước 4 với `topic_map.yaml`:
- **Lọc:** Nếu có `Target_Pillar`, chỉ quét topic thuộc `pillar_parents` tương ứng. Nếu ủy quyền, quét toàn bộ.
- **Matching:** Đối chiếu ngữ nghĩa dựa trên cả `id` (English) và `label` (tiếng Việt), dùng cả hai làm tín hiệu bổ trợ.
- **Cascade:** Nếu khớp nhiều entry → chọn duy nhất entry có cấp phân nhánh sâu nhất (hẹp nhất).

Phân luồng:
- **Matched:** Trích xuất `mapped_topic` (id gốc trong Map), loại bỏ id tạm từ Bước 4. Ánh xạ `Target_Pillar`, `Target_Audience` → **Bước 8**.
- **Miss:** Bảo lưu id Topic Hẹp làm `novel_angle` → **Bước 6**.

## Bước 6: Gán Pillar cho Novel Angle

- Đã có `Target_Pillar`: Gán trực tiếp.
- Ủy quyền: Đọc `pillars.yaml`, tự chọn Pillar phù hợp nhất. Hỏi User xác nhận.
  - ⛔ STOP — CHỜ USER XÁC NHẬN. KHÔNG tự ý tiếp tục.

**JTBD Resolution (Novel Angle):** Đọc `[Persona_Path]/audience.yaml` → trích `audience_Job_performer`, `audience_main_job`, `audience_circumstance` → ghi vào blackboard key `resolved_jtbd`. `source_audience: "big"`.

`Is_Novel_Angle = True` → **Bước 7**.

## Bước 7: Kiểm tra trùng Pillar (Muộn)

Chỉ áp dụng khi User ủy quyền ở Bước 1 (đã qua Bước 2 → bỏ qua bước này).
→ Thực hiện **Pillar Duplicate Check**. Bước kế: **Bước 9**.

## Bước 8: Phân giải Audience & JTBD

Dựa vào `Target_Audience` từ Bước 3 hoặc Bước 5:
- Parent + Child Audience cùng trúng → chốt Parent.
- Audience ngang hàng → In CLI, chờ User chọn 1 hoặc gõ `ALL`.
  - ⛔ STOP — CHỜ USER PHẢN HỒI. KHÔNG tự chọn.
  - User chọn 1 → `Target_Audience` = string (bare slug, không `[[]]`).
  - User chọn `ALL` → resolve danh sách audience IDs cụ thể (bare slug). `Target_Audience` = YAML array. KHÔNG ghi string "ALL".

**JTBD Resolution:**
- **Single audience**: `view_file` tại `vault/01-Atomic/Audiences/[Target_Audience].md` → trích `audience_Job_performer`, `audience_main_job`, `audience_circumstance` → ghi `resolved_jtbd` vào blackboard. `source_audience` = audience ID.
- **Multi-audience**: CHƯA ghi `resolved_jtbd` (DIKW Bridge resolve sau Anchor-First).

`Is_Novel_Angle = False` → **Bước 9**.

## Bước 9: Đóng gói Blackboard

Output 6 biến:
- `topic`: 1 string ID duy nhất
- `Target_Pillar`: Tên Pillar
- `Target_Audience`: Audience ID (string), danh sách Audience IDs (YAML array), hoặc rỗng (Novel Angle)
- `Is_Novel_Angle`: True / False
- `Persona_Path`: Đường dẫn thư mục persona (đã xác định ở Bước 3 của workflow bởi `validate-persona.ps1`)
- `resolved_jtbd`: Block JTBD gồm `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `source_audience`. Có khi single audience hoặc Novel Angle. Chưa có khi multi-audience (DIKW Bridge bổ sung).

Sau khi ghi `00-blackboard.yaml`, BẮT BUỘC append 1 dòng dưới cùng: `# execution_key: [giá trị EXECUTION_KEY từ SKILL.md]`
