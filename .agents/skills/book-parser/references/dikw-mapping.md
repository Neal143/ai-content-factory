---
name: DIKW Book Parsing Mapping Rules
description: Quy tắc phân mảng tĩnh ánh xạ các thẻ Metadata từ NotebookLM vào 4 Tầng cấu trúc DIKW chuẩn của hệ thống.
---

# Quy Tắc Chuyển Đổi Kép & Phân Mảng Payload In-Memory

File cấu hình này dành cho Sub-LLM và quy trình Atomizer (Book Parser). Khi xử lý file thô sau bước chạy Regex, toàn bộ Atom (Payload) sinh ra In-memory phải tuân thủ nghiêm ngặt bảng ánh xạ sau để phân phối đúng 4 Tầng DIKW và tiêm mã liên kết Graph chống mồ côi.

## Quy Tắc Ghi Output
Sau khi xác định giá trị `type` và các thẻ Sub từ bảng ánh xạ dưới đây, executor PHẢI nạp các giá trị này vào đúng khuôn YAML Frontmatter được định nghĩa tại:
`.agents/skills/book-parser/references/atom-structure.md`

---

**Thông tin KCS Di truyền mặc định (Cho 100% Atoms):**
- Thừa kế toàn bộ Tên Sách, Tác giả, Năm Xuất bản từ `META_BOOK` của Mapper.
- Đóng dấu mặc định `confidence: 0.9` (do đây là sách xuất bản định danh).

---

## Bảng Ánh Xạ Logic Rẽ Nhánh

### 1. Nhóm Tầng 2 (Vấn đề / Insight)
- **Dấu hiệu nhận biết:** Tìm thấy key `insight_type` từ file NotebookLM trả về.
- **Hành động Ghi:**
  - Nạp thẻ Root `type: insight`.
  - Nạp thẻ Sub `insight_type` bằng chính giá trị nhận được (Ví dụ: `fear`, `desire`, v.v.).
- **Định tuyến Graph (Bắt buộc):** Chêm thêm cờ Graph `belongs_to_audience: "[[Link_File_Audience_Đang_Xử_Lý]]"`.
- **Lưu trữ mục tiêu:** `01-Atomic/Insights/`

### 2. Nhóm Tầng 3 (Giải pháp / Concept)
**Rẽ Nhánh 2.1: Nhóm Lý thuyết tĩnh (Concept/Philosophy)**
- **Dấu hiệu:** `knowledge_type` mang giá trị `concept` hoặc `philosophy`.
- **Hành động Ghi:** Nạp thẻ Root `type: concept`. Cấy Sub `knowledge_type: [giá trị đó]`.
- **Lưu trữ mục tiêu:** `01-Atomic/Concepts/`

**Rẽ Nhánh 2.2: Nhóm Thực thi Động (Solution)**
- **Dấu hiệu:** `knowledge_type` mang giá trị `principle`, `framework`, `mental_model`, `actionable_rule`, `typology`, `trend`.
- **Hành động Ghi:** Nạp thẻ Root `type: solution`. Cấy Sub `knowledge_type: [giá trị đó]`.
- **Lưu trữ mục tiêu:** `01-Atomic/Solutions/`

👉 **Định tuyến Graph (Bắt buộc cho cả 2.1 và 2.2):** Chêm thêm cờ Graph `supports_insight: "[[Link_Của_Insight_Hiện_Tại]]"`.

### 3. Nhóm Tầng 4 (Bằng chứng Thực chứng & Câu chuyện)
**Rẽ Nhánh 3.1: Nhóm Câu chuyện (Story/Case Study)**
- **Dấu hiệu:** `content_type` mang giá trị `story` hoặc `case_study`.
- **Hành động Ghi:** Nạp Root `type: story` ĐỒNG THỜI dán cờ uy tín `verified: true`. Giao Sub-LLM làm mịn và tự sinh thẻ `subtype` (`famous_world`, `historical`, hoặc `secondhand`).
- **Lưu trữ mục tiêu:** `01-Atomic/Stories/`

**Rẽ Nhánh 3.2: Nhóm Dữ liệu Định lượng (Data/Fact)**
- **Dấu hiệu:** `content_type` mang giá trị `shocking_fact` hoặc `evidence`.
- **Hành động Ghi:** Nạp Root `type: data-point`. Cấy Sub `data_type: [giá trị đó]`.
- **Lưu trữ mục tiêu:** `01-Atomic/Data-Points/`

**Rẽ Nhánh 3.3: Nhóm Trích dẫn (Quote)**
- **Dấu hiệu:** `content_type` mang giá trị `quote`.
- **Hành động Ghi:** Nạp Root `type: quote`. Tự động trích dẫn Origin người nói.
- **Lưu trữ mục tiêu:** `01-Atomic/Quotes/`

👉 **Định tuyến Graph (Bắt buộc cho 3.1, 3.2 và 3.3):** Chêm thêm cờ Graph `supports_knowledge: "[[Link_Của_Solution_Hoặc_Concept_Hiện_Tại]]"`.

### 4. Nhóm Nhúng Dữ Liệu Ký Sinh (Vivid)
- **Dấu hiệu:** `content_type` mang một trong các giá trị: `vivid_circumstance`, `vivid_insight`, `vivid_knowledge`.
- **Hành động Ghi:** 🛑 **CẤM SINH FILE VẬT LÝ DƯỚI MỌI HÌNH THỨC**. Route luồng thực thi chuyển toàn bộ thông tin này chạy qua kịch bản `vivid-append.md` để nối mảng, tuyệt đối không xuất xuống đĩa độc lập đối với các tập tin Atom chuẩn.
