---
name: Inbox Processor
description: Skill tự động dọn dẹp thư mục thô (00-Inbox) và gán nhãn, cấu trúc hóa thành 1 trong 7 loại Atoms.
---

# Inbox Processor Skill

Bạn là công nhân phân loại. Hàng ngày user sẽ vứt rất nhiều ghi chú lộn xộn, cụt lủn vào thư mục `vault/00-Inbox/`. Nhiệm vụ của bạn là dọn dẹp nó.

## Hướng dẫn hoạt động

### Bước 1: Quét Inbox
Quét toàn bộ file trong `vault/00-Inbox/` xem có file nào đang ở trạng thái `status: pending` không.

### Bước 2: Phân loại
Đọc file `.agents/skills/inbox-processor/references/atom-classification.md` để hiểu định nghĩa 7 loại. Đọc nội dung file pending. Quyết định phân vào 1 (hoặc max 2) loại phù hợp nhất. Nếu mơ hồ → chọn type có DIKW cao hơn (W > K > I > D). Nếu 1 file chứa nhiều loại → tách thành nhiều atoms riêng.

### Bước 3: Tiền xử lý Dữ liệu (Sinh Topic & Reverse-Sync)
> ⚠️ **Quy tắc Vòng lặp:** Phải lặp lại toàn bộ Bước 3 này cho **từng mẩu nội dung** riêng biệt. Tuyệt đối không gom/trộn lẫn Topics của nhiều mẩu nội dung vào chung một lần thực thi phân tích.

Trước khi định tuyến hay lưu file, BẮT BUỘC phải thực hiện tuần tự để có cơ sở dữ liệu:
1. **Chọn Pillar gốc:** Đọc cấu trúc `pillars.yaml`, chọn đúng **01 Pillar** đang tồn tại phù hợp nhất với nội dung của Atom.
2. **Sinh 2-3 topics đa tầng (Gán làm biến `[id]` và `[label]`):** Dựa vào Pillar vừa chọn, sinh ra 2-3 cặp `(id, label)` phản ánh nội dung theo phổ độ rộng: **1 rộng + 1 trung  + 1 hẹp (tùy chọn)**.
   - **`id`**: English snake_case, mô tả bằng 2-4 từ tiếng Anh (ví dụ: `attachment_root_of_suffering`).
   - **`label`**: Tiếng Việt đầy đủ dấu, đọc tự nhiên như tên một bài viết ngắn (ví dụ: `Attachment là gốc rễ của khổ đau`).
   - **Topic rộng (Broad):** Chủ đề bao quát mà ≥5 nội dung khác nhau trong cùng Pillar có thể dùng.
   - **Topic trung (Medium/Central) :** Luận điểm cốt lõi của nội dung — bắt buộc 100%, quan trọng nhất.
   - **Topic hẹp (Narrow/optional):** Trigger context đặc thù. Chỉ sinh khi nội dung có sự kiện/tình huống rõ ràng. Nếu không có, chỉ sinh 2 topics.
   - Tất cả topics thuộc cùng 1 Pillar đã chọn ở Bước 1.
3. **Semantic Dedup (Topic Manager):** 
   Trước khi đọc module quản lý topic, BẮT BUỘC phải chuẩn bị sẵn 4 biến tương ứng trong working memory cho Atom này:
   - `id`: `[id_rong] [id_trung] ([id_hep])`.
   - `label`: `"[label rộng]" "[label trung]" ("[label hẹp]")`.
   - `pillar`: `[Tên Pillar đã match ở Bước 1]`
   - `audience`: Wikilink trỏ duy nhất vào file Big Audience gốc (file có `audience_level: big` nằm trong thư mục `vault/01-Atomic/Audiences/`).
   
   👉 **HÀNH ĐỘNG:** Đọc và thực thi ngay file `.agents/references/topic_manager/topic_manager.md` tại chỗ. 
   
   Thu thập mảng `[resolved_id]` sau dedup để điền vào phần `topics:` trong YAML frontmatter của Atom. (Biến `belongs_to_audience` ghi vào Atom vẫn dùng lại cái link Big Audience trên).

### Bước 4: Ánh xạ DIKW (Graph Routing)
Sau khi chốt rễ Pillar ở Bước 3, hệ thống sẽ ánh xạ Atom vào sâu trong Đồ thị để chống file mồ côi:
- **Tầng 2 (Insights):** Biến `belongs_to_audience` MẶC ĐỊNH trỏ link thẳng về **Big Audience** gốc.
- **Tầng 3 (Solutions, Concepts):** Vì đã có Pillar ở Bước 3 → Lựa chọn **01 Insight** phù hợp nhất từ danh sách của Pillar đó để cắm Link. Gán `supports_insight: "[Tên_Insight]"`.
- **Tầng 4 (Stories, Quotes, Data-Points):** Suy luận đồ thị 2 nấc rễ sâu: Dùng Pillar ở Bước 3 → Chọn 01 Insight phù hợp → Tiếp tục trỏ Link xuyên suốt về **01 Solution/Concept** đặc trị trực thuộc nhánh Insight đó. Gán `supports_knowledge: "[Tên_Solution_Hoặc_Concept]"`.

### Bước 5: Tạo Atom file theo template chuẩn
Mỗi atom tạo ra PHẢI theo format trong `.agents/skills/inbox-processor/references/atom-classification.md` → Section "Atom file (01-Atomic)".
Format 4 phần: YAML frontmatter + Nội dung + Giải thích + Liên kết.
- **The Librarian (Đóng dấu Topic):** 100% Atom tạo ra BẮT BUỘC phải chèn mảng `topics` vào YAML Frontmatter. Giá trị của mảng này là danh sách `[resolved_id]` sau khi chạy Semantic Dedup (Tuyệt đối không dùng `id` gốc chưa qua kiểm duyệt). Cú pháp bắt buộc:
  ```yaml
  topics: ["id_rong", "id_trung"]
  # hoặc nếu có topic hẹp:
  topics: ["id_rong", "id_trung", "id_hep"]
  ```
  *(Lưu ý: Chỉ lưu `id` tiếng Anh vào frontmatter, bỏ qua `label` tiếng Việt. Thứ tự mảng: rộng → trung → hẹp)*

**Lưu ý cho từng type:**
- **Stories** → PHẢI có 5 phần S-P-T-O-L (xem `.agents/skills/story-architect/references/story-schema.md`). Thêm fields: `subtype`, `protagonist`, `timeline`, `outcome_measurable`.
- **Solutions** → Phần Nội dung phải có ≥ 3 bước/thành phần.
- **Quotes** → Phải ghi rõ nguồn (speaker + context).
- **Data-Points** → Phải ghi năm và nguồn nghiên cứu.

### Bước 6: Cập nhật file gốc
Sau khi extract xong, update frontmatter file gốc trong `00-Inbox/` theo format trong `.agents/skills/inbox-processor/references/atom-classification.md` → Section "File gốc — sau khi xử lý".

### Bước 7: Di chuyển & Lưu
Di chuyển atom files sang `vault/01-Atomic/[Type]/`. Đặt tên file theo slug: `[keyword-keyword].md`.

### Bước 8: Báo cáo
Report cho user:
- Số files đã xử lý
- Số atoms đã tạo (chia theo type)
- Danh sách files mới trong `01-Atomic/`

## Ví dụ

**Input** (file trong `00-Inbox/`):
```
Sau lần mất hết dữ liệu năm 2023, tôi nhận ra rằng attachment là gốc rễ của khổ đau.
Các nhà sư Tây Tạng mất 3 tháng vẽ bức tranh cát mandala rồi phá đi trong 1 phút.
Theo nghiên cứu Harvard 2019, 73% stress đến từ việc bám víu vào quá khứ.
```

**Output** (3 atoms tạo ra):
1. `01-Atomic/Insights/attachment-root-of-suffering.md` (type: insight)
2. `01-Atomic/Stories/tibetan-sand-mandala.md` (type: story, subtype: historical)
3. `01-Atomic/Data-Points/harvard-stress-attachment-2019.md` (type: data-point)
