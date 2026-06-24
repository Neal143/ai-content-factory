# Atom Classification — Phân loại 7 loại nguyên liệu

## 7 Atom Types

| # | Type | Thư mục | Định nghĩa | Ví dụ |
|---|------|---------|-----------|-------|
| 1 | **Stories** | `01-Atomic/Stories/` | Câu chuyện cá nhân có turning point | "Năm 2019 tôi mất sạch tiền..." |
| 2 | **Insights** | `01-Atomic/Insights/` | Góc nhìn sâu, phân tích contrarian | "Người ta nghĩ X nhưng thực ra Y" |
| 3 | **Solutions** | `01-Atomic/Solutions/` | Mô hình, công thức, phương pháp | "DIKW Pyramid", "80/20 Rule" |
| 5 | **Concepts** | `01-Atomic/Concepts/` | Định nghĩa, khái niệm nền tảng | "Deliberate Practice là gì?" |
| 6 | **Quotes** | `01-Atomic/Quotes/` | Trích dẫn từ chuyên gia/sách | "Charlie Munger: Invert, always invert" |
| 7 | **Data-Points** | `01-Atomic/Data-Points/` | Số liệu, thống kê, research | "73% người dùng bỏ cuộc sau tuần 2" |

## Cách phân loại & Gán Topic
1. Đọc nội dung file thô.
2. Xác định type chính dựa trên bảng trên. Nếu mơ hồ, chọn type có giá trị DIKW cao hơn (W > K > I > D).
3. Nếu 1 file chứa nhiều loại → tách thành nhiều atoms riêng.
4. **Quy tắc sinh Topic**: Mọi Topic gán vào mảng `topics` PHẢI trực thuộc một Pillar cụ thể đang có trong `pillars.yaml`. Không được tự bịa Topic vĩ cuồng, lan man không liên quan đến trục nội dung của Persona.

## Status Tracking

### File gốc (00-Inbox) — trước khi xử lý:
```yaml
---
status: pending
created: YYYY-MM-DD
---
```

### File gốc — sau khi xử lý:
```yaml
---
status: processed
created: YYYY-MM-DD
processed_at: YYYY-MM-DD
atoms_created: 3
---
```

### Atom file (01-Atomic) — khi tạo mới:
```yaml
---
type: quote|concept|insight|story|solution|data-point
topics: ["topic1", "topic2"]
belongs_to_audience: "[JTBD_Name]" # Chỉ cho Tầng 2 (Insights)
supports_insight: "[Tên_Insight]"  # Chỉ cho Tầng 3 (Solutions, Concepts)
supports_knowledge: "[Tên_Solution_Hoặc_Concept]" # Chỉ cho Tầng 4 (Stories, Quotes, Data-Points)
status: processed
source_type: "User" | "book"    # User = user tu viet/ke/trai nghiem, book = trich tu sach/bao
created: YYYY-MM-DD
source_file: "tên-file-gốc-trong-inbox.md"
confidence: 0.0-1.0
vivid_insights: []           # Chỉ cho Insights — Script tự gắn, không tự điền
vivid_insights_reserve: []   # Mảng dự bị vượt cap
vivid_knowledges: []         # Chỉ cho Solutions, Concepts — Script tự gắn, không tự điền
vivid_knowledges_reserve: [] # Mảng dự bị vượt cap
---
```
Confidence scoring: 1.0 = có nguồn rõ ràng, 0.8 = user tự viết, 0.5 = mơ hồ/cần verify.
