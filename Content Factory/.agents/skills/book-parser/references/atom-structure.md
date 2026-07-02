---
name: Atom File Structure Standard
description: Tiêu chuẩn kỹ thuật vật lý thiết lập cấu trúc 4 phần và khuôn đúc YAML Frontmatter cho 100% File Atom được tuồn vào Vault.
---

# Tiêu Chuẩn Cấu Trúc File Atom

Bất kỳ nguyên liệu tri thức nào sau khi Book Parser phân rã ĐỀU PHẢI thỏa mãn định dạng vật lý dưới đây trước khi Commit I/O Write xuống đĩa cứng.

## 1. Quy Tắc Định Danh
- **Cấu trúc Naming:** `[SOURCE_ACRONYM]_[KEYWORD_SLUG].md`
  - `SOURCE_ACRONYM`: Viết tắt chữ cái đầu của Tên sách nguồn (ví dụ: `twbc`).
  - `KEYWORD_SLUG`: Kế thừa giá trị trích xuất gốc. **⚠️ LƯU Ý KỸ THUẬT QUAN TRỌNG:** Toàn bộ thành phần lắp ráp phải được định dạng chuẩn (Slugify - Chuẩn Tiếng Việt không dấu, loại bỏ khoảng trắng dư thừa, chuyển thành kebab-case format). Nguyên tắc lắp ráp:
    - Insight (Tầng 2): `[insight_name]`
    - Concept/Solution (Tầng 3): `[knowledge_name]`
    - Data-point (Tầng 4): `[evidence_keyword]`
    - Story/Case-study (Tầng 4): `[protagonist]-[core_event]`
    - Quote (Tầng 4): `[speaker]-[quote_keyword]`

## 2. Khung Vật Lý Cơ Bản
Định dạng vật lý luôn bao gồm 4 phần tuần tự:
1. YAML Frontmatter (Quản trị Đồ thị DIKW)
2. Nội dung text thô (Raw payload)
3. Giải thích hoặc luận điểm từ LLM rút ra (Insightful explain)
4. Liên kết mở rộng (Nếu có)

👉 *Lưu ý Đặc thù:* Mọi Payload có `content_type` là `story` hoặc `case_study` (Tầng 4) Mặc định GIỮ NGUYÊN và vạch trần các phân khu mốc XML `<situation><problem><turning_point><outcome><lesson>` trong phần ruột văn bản. Chưa cần bóc tách hay làm sạch các thẻ XML này.

## 3. Khuôn Đúc YAML Frontmatter Gốc
Đây là "Mũi tiêm Routing gốc" buộc phải đổ khuôn cho MỌI tập tin:

```yaml
---
type: [Mác_Root_Lớp_1]
# ↑ Giá trị hợp lệ: insight | concept | solution | story | data-point | quote
# ↑ Xem bảng ánh xạ đầy đủ tại: references/dikw-mapping.md
# [Lựa chọn CẤY THÊM 1 trong 4 biến Lớp 2 dưới đây tùy thuộc vào file tham chiếu Mapping]
# insight_type: [giá_trị] 
# knowledge_type: [giá_trị]
# subtype: [giá_trị]
# data_type: [giá_trị]
topics: ["<Kế_thừa_chuỗi_Topic_đã_chốt_ở_Bước_1>"]
status: processed
protagonist: "<Tên_nhân_vật_chính>" # Bắt buộc đính kèm đối với Story (Tầng 4)
source_type: book
source_name: "<Tên Sách> (bởi <Tên Tác Giả, Năm xuất bản>)" # Kế thừa từ META_BOOK. VD: "Atomic Habits (bởi James Clear, 2018)"
confidence: 0.9 # Sách xuất bản độ tin cậy mặc định là cao
# ----- CÁC BIẾN CHẶN MỒ CÔI (Định tuyến Graph) -----
keywords: []                             # Thẻ từ khóa nội suy (Inbox RAG)
belongs_to_audience: [] # Bắt buộc đối với Insight (Tầng 2)
supports_insight: []     # Bắt buộc đối với Solution, Concept (Tầng 3)
supports_knowledge: []  # Bắt buộc đối với Story, Quote, Data-Points (Tầng 4)
# ----- DỮ LIỆU KÝ SINH (Vivid — Script tự động gắn, Agent KHÔNG tự điền) -----
vivid_insights: []                       # Chỉ cho Insight (Tầng 2): mảng canonical, Hard Cap 3
vivid_insights_reserve: []               # Chỉ cho Insight (Tầng 2): mảng dự bị vượt cap
vivid_knowledges: []                     # Chỉ cho Solution, Concept (Tầng 3): mảng canonical, Hard Cap 3
vivid_knowledges_reserve: []             # Chỉ cho Solution, Concept (Tầng 3): mảng dự bị vượt cap
---
```
