---
name: post-needs-extractor
description: "Bước 4/4 của PostClassifierAgent: Xây dựng tối đa 1 Needs chuẩn công thức 4 thành phần ODI và thực hiện Semantic Dedup toàn bộ ứng viên Topic (knowledge, insight, needs, product, event) với topic_map.yaml."
last_update: 10/11/2026 19:50 (GMT+7)
---

# Post ODI Needs Extractor & Semantic Topic Dedup Skill (Bước 4/4)

> **Tên file**: .agents/skills/post-needs-extractor/SKILL.md
> **Last update**: 10/11/2026 19:50 (GMT+7)
> **Vai trò**: (1) Xây dựng tối đa 1 câu phát biểu `needs` chuẩn công thức 4 thành phần ODI đo lường trực tiếp `locked_jtbd` và `core_thesis`; (2) Thực hiện đối chiếu ngữ nghĩa (Semantic Dedup) toàn bộ ứng viên Topic hợp lệ từ Bước 3 (`knowledge`, `insight`, `product`, `event`) cùng ứng viên `needs` vừa tạo với các topics hiện có của `target_pillar` trong `topic_map.yaml`.
> **Sử dụng khi**: Được gọi ở Bước 4 bởi `PostClassifierAgent` / `classify_vault_posts.py`.
> **Output**: JSON chứa mảng `resolved_topics` (`action`, `topic_type`, `matched_id`, `proposed_id`, `label`, `evidence`, `reasoning`).
> **Tóm tắt logic hoạt động**: Xây dựng tối đa 1 `needs` chuẩn 4 thành phần ODI kèm `evidence` nguyên văn -> Gom chung với các ứng viên đã qua kiểm định từ Bước 3 -> So khớp ngữ nghĩa từng ứng viên với danh sách topics thuộc `target_pillar` trong `topic_map.yaml` (chỉ gộp trong cùng `topic_type`) -> Quyết định `reuse` (lấy `id` và `label` gốc) hoặc `create` (đặt `proposed_id` chuẩn `pN_english_snake_case`).

## 1. BẢN CHẤT CỦA NEEDS TRONG JTBD
- **Main Job (What — Đã chốt ở Bước 2)**: Công việc chức năng mà `audience_Job_performer` muốn hoàn thành.
- **Needs / Desired Outcomes (Why — Xây dựng tại bước này)**: Các tiêu chí, thước đo hiệu suất (thời gian, nỗ lực, rủi ro, khả năng...) mà `audience_Job_performer` dùng để đánh giá xem `audience_main_job` có được thực hiện thành công hay không.
- **Trần số lượng**: Tối đa **1** câu phát biểu `needs` cho mỗi bài viết (hoặc `[]` nếu bài viết thuần tin tức thời sự/tổng hợp không chứa tiêu chí đo lường hiệu suất chức năng).

## 2. CÔNG THỨC 4 THÀNH PHẦN BẮT BUỘC (4-PART ODI FORMULA)
Mỗi câu trong nhóm `needs` BẮT BUỘC được cấu thành từ đúng 4 thành phần theo thứ tự:

```text
[1. Hướng cải tiến (Direction)] + [2. Đơn vị đo lường (Unit of Measure)] + [3. Đối tượng của nhu cầu (Object of the Need)] + [4. Bối cảnh làm rõ (Clarifier)]
```

1. **Hướng cải tiến (`Direction of Change`)**:
   - BẮT BUỘC mở đầu bằng **`"Giảm thiểu"`** (Minimize — ưu tiên dùng cho thời gian, công sức, rủi ro, nguy cơ, sai sót, chi phí) hoặc **`"Tối đa hóa"`** (Maximize — dùng cho khả năng, xác suất đạt kết quả đúng).
2. **Đơn vị đo lường (`Unit of Measure`)**:
   - Phải có danh từ chỉ đơn vị đo lường ngay sau hướng cải tiến: `thời gian cần thiết để...`, `nỗ lực bỏ ra để...`, `rủi ro / nguy cơ...`, `tần suất xảy ra...`, `khả năng...`, `xác suất...`, `chi phí phát sinh khi...`.
3. **Đối tượng kiểm soát (`Object of the Need`)**:
   - Biến số hoặc khía cạnh cụ thể trong quá trình thực hiện `audience_main_job` chịu tác động trực tiếp.
4. **Bối cảnh làm rõ (`Clarifier`)**:
   - Cụm bổ ngữ chỉ điều kiện, hoàn cảnh phát sinh nhu cầu gắn với `audience_circumstance`.

## 3. BẢNG ĐỐI CHIẾU LỖI SAI & CÁCH KHẮC PHỤC
| Câu phát biểu SAI ❌ | Lỗi vi phạm | Câu phát biểu ĐÚNG CHUẢN 4 THÀNH PHẦN ✅ |
| :--- | :--- | :--- |
| ❌ *"Giúp cha mẹ chọn trường tiểu học nhanh chóng và đúng đắn qua bộ tiêu chí."* | Chứa từ đệm (*"Giúp"*); chứa giải pháp (*"bộ tiêu chí"*); gộp *"và"* vi phạm đơn trị; tính từ mơ hồ (*"nhanh chóng"*). | ✅ **"Giảm thiểu thời gian cần thiết để đánh giá mức độ phù hợp của các trường tiểu học khi con chuẩn bị vào lớp 1"** |
| ❌ *"Giảm thời gian và công sức kèm con học bài mỗi tối."* | Dùng từ nối *"và"* gộp 2 đơn vị đo lường (*thời gian* VÀ *công sức*). | ✅ **"Giảm thiểu thời gian cần thiết để hướng dẫn con hoàn thành bài tập về nhà mỗi tối"** |
| ❌ *"Cha mẹ hết lo âu khi áp dụng phương pháp kỷ luật tích cực."* | Chứa cảm xúc mơ hồ (*"hết lo âu"*) và chứa giải pháp (*"kỷ luật tích cực"*). | ✅ **"Giảm thiểu nguy cơ làm tổn thương lòng tự trọng của trẻ khi uốn nắn các hành vi lệch chuẩn"** |

## 4. CHECKLIST 6 TIÊU CHÍ NGHIỆM THU BẮT BUỘC
1. Mở đầu chính xác bằng `"Giảm thiểu "` hoặc `"Tối đa hóa "`.
2. Có đơn vị đo lường tường minh (*thời gian, nỗ lực, rủi ro, nguy cơ, khả năng, tần suất, chi phí*).
3. **Solution-Agnostic**: Không chứa bất kỳ tên sản phẩm, thương hiệu, công cụ hay phương pháp nào.
4. **Atomic (Đơn trị)**: Tuyệt đối không chứa từ nối `"và"`, `"hoặc"`, `"kiêm"`, `"đồng thời"`.
5. **Bền vững 50 năm**: Giữ nguyên giá trị đo lường đối với `audience_main_job` bất kể công nghệ thay đổi.
6. **Job Performer Perspective**: Đo lường trực tiếp thành công của `audience_Job_performer`.
7. **`evidence` (Bắt buộc)**: Trích dẫn nguyên văn 1 câu trong thân bài chứng minh nhu cầu này có thật trong bài viết.

## 5. QUY TẮC SEMANTIC TOPIC DEDUP VỚI `topic_map.yaml`
Gom toàn bộ các ứng viên Topic hợp lệ từ Bước 3 (`knowledge`, `insight`, `product`, `event`) cùng ứng viên `needs` vừa tạo để so khớp với danh sách các topics thuộc `target_pillar` trong `topic_map.yaml`:

1. **Khóa loại (`topic_type`)**:
   - CHỈ so khớp và merge hai topic khi có **CÙNG `topic_type`**. Tuyệt đối KHÔNG merge `insight` vào `knowledge` hay `product` vào `needs`.
2. **Tiêu chí so khớp ngữ nghĩa**:
   - **Synonym**: Dùng từ đồng nghĩa (*"kỷ luật tích cực"* vs *"kỷ luật không nước mắt"*).
   - **Paraphrase**: Diễn đạt lại cùng bản chất khái niệm.
   - **Reorder**: Đảo trật tự ngữ pháp không đổi nghĩa.
3. **Quyết định `action`**:
   - **`reuse`**: Nếu tìm thấy topic trong `topic_map.yaml` trùng khớp bản chất:
     - `"action": "reuse"`
     - `"matched_id"`: Điền nguyên văn `id` của topic trong `topic_map.yaml`.
     - `"label"`: Điền nguyên văn `label` gốc của topic trong `topic_map.yaml`.
     - `"proposed_id"`: `""`.
   - **`create`**: Nếu là chủ đề hoàn toàn mới chưa từng xuất hiện:
     - `"action": "create"`
     - `"matched_id"`: `""`.
     - `"proposed_id"`: Đặt ID theo cú pháp `pN_[english_snake_case]` (với `pN_` là tiền tố của `target_pillar`, ví dụ: `p1_natural_consequences_discipline`).
     - `"label"`: Giữ nguyên nhãn tiếng Việt có dấu chuẩn (4–12 từ).

## 6. ĐỊNH DẠNG JSON ĐẦU RA
Chỉ trả về JSON theo cấu trúc:
```json
{
  "resolved_topics": [
    {
      "action": "reuse",
      "topic_type": "knowledge",
      "matched_id": "p1_natural_consequences_discipline",
      "proposed_id": "",
      "label": "Kỷ luật tự nhiên thông qua hệ quả hành vi",
      "evidence": "Trẻ sẽ tự học được cách chịu trách nhiệm khi được trải nghiệm chính hệ quả hành vi của mình",
      "reasoning": "Trùng khớp hoàn toàn với topic hiện có trong topic_map.yaml"
    },
    {
      "action": "create",
      "topic_type": "needs",
      "matched_id": "",
      "proposed_id": "p1_minimize_risk_of_damaging_child_self_esteem",
      "label": "Giảm thiểu nguy cơ làm tổn thương lòng tự trọng của trẻ khi uốn nắn hành vi lệch chuẩn",
      "evidence": "Người lớn quát mắng hay dán nhãn tiêu cực chỉ khiến trẻ co cụm và tự ti",
      "reasoning": "Needs chuẩn 4 thành phần ODI chưa có trong topic_map.yaml"
    }
  ]
}
```
