---
name: Audience File Structure Standard
description: Tiêu chuẩn kỹ thuật định dạng Dashboard tĩnh, cấu trúc YAML, và Dataview Query cho 100% tệp Audience được khởi tạo mới.
---

# Tiêu Chuẩn Cấu Trúc File Audience

Bất cứ khi nào Sub-LLM quyết định Khởi tạo một tệp Audience mới, tệp vật lý này BẮT BUỘC phải được đổ khuôn theo định dạng Dashboard dưới đây để phục vụ cho luồng truy vấn động của hệ thống Dataview.

## 1. Lưu ý Định Danh Nguồn Cội
File Audience đóng vai trò là "Cái Phễu" hứng dữ liệu, nó KHÔNG phải là một "Nguyên liệu nguyên thủy" trích xuất trực tiếp từ 1 đoạn text như Atom. Do đó, Audience Atom **Tuyệt đối KHÔNG có các biến số rác** như `source_name`, `confidence`, `status`, hay `topics`.

## 2. Khuôn Đúc Mã Nguồn (Single Source of Truth)

> ⚠️ **LƯU Ý:** Frontmatter hiện do script `write_audience_files.py` sinh tự động bằng PyYAML. Agent KHÔNG tự tay tạo frontmatter. Phần dưới đây chỉ mang giá trị tham khảo cấu trúc.

Để tránh rủi ro "bảo trì 2 nơi" (Phải sửa song song template khi mở rộng hệ thống), hệ thống áp dụng cơ chế kế thừa khối động (Dynamic Chunk Inheritance):

**Bước 1: Trích xuất Dữ liệu gốc**
Truy xuất trực tiếp tệp lưu trữ trung tâm: `.agents/skills/persona-interviewer/assets/persona-template/audience.yaml`.
- **Cắt lấy ĐÚNG phần `# --- JTBD ROUTING CHUNK ---`**. Bỏ qua hoàn toàn phần `# --- PHYSICAL & HABITS CHUNK ---`.

**Bước 2: Nạp dữ liệu nội suy (Payload Output)**
Đối với khối JTBD vừa cắt ra, điền trực tiếp các giá trị bóc được (`audience_level`, `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `aliases`, và `parent_audience`) vào các field tương ứng để tạo thành `YAML Frontmatter` hoàn chỉnh. **Lưu ý: `parent_audience` và `aliases` nếu có phần tử thì BẮT BUỘC phải xuất định dạng YAML Chunk Array (xuống dòng, gạch đầu dòng) để chống lỗi mảng của Dataview.**
Ví dụ:
```yaml
parent_audience:
  - "[[slug1]]"
  - "[[slug2]]"
```
*(Nếu là mảng rỗng thì giữ nguyên syntax `[]`)*

```yaml
---
# [Toàn bộ khối JTBD ROUTING CHUNK lấy từ audience.yaml sau khi điền values]
---
```

## 3. Khung Dashboard Vật Lý (Dataview Chunks)

Phần ruột `.md` bên dưới khối YAML sẽ tuân thủ cú pháp Dashboard truy vấn ngược:

````markdown
# 🎯 [Job_performer] muốn [Main_job] [Circumstance]

## 🧠 Bức tranh Tâm lý (Insights)
*(Khu vực hiển thị tự động toàn bộ Insights đang bám rễ vào tập khách hàng này)*
```dataview
TABLE insight_type, source_name
FROM "01-Atomic/Insights"
WHERE contains(belongs_to_audience, this.file.link)
```

## 💊 Kho Giải pháp (Solutions)
*(Truy vấn tự động các Solutions/Concepts đang phục vụ Insights thuộc tệp Audience này)*
```dataview
TABLE knowledge_type, source_name
FROM "01-Atomic/Solutions" OR "01-Atomic/Concepts"
FLATTEN supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```

## 📖 Kho Evidences
*(Truy vấn tự động các Data-Points, Stories, Quotes liên đới với tệp Audience này)*
```dataview
TABLE type, source_name
FROM "01-Atomic/Data-Points" OR "01-Atomic/Stories" OR "01-Atomic/Quotes"
FLATTEN supports_knowledge AS sk
FLATTEN sk.supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```
````
