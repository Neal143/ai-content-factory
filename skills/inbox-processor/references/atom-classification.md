# Atom Classification — Phân loại nguyên liệu

## 5 Atom Types (xử lý bởi Inbox Processor)

| # | Type | Thư mục | Định nghĩa | Ví dụ |
|---|------|---------|-----------|-------|
| 1 | **Insights** | `01-Atomic/Insights/` | Góc nhìn sâu, phân tích contrarian | "Người ta nghĩ X nhưng thực ra Y" |
| 2 | **Solutions** | `01-Atomic/Solutions/` | Mô hình, công thức, phương pháp | "DIKW Pyramid", "80/20 Rule" |
| 3 | **Concepts** | `01-Atomic/Concepts/` | Định nghĩa, khái niệm nền tảng | "Deliberate Practice là gì?" |
| 4 | **Quotes** | `01-Atomic/Quotes/` | Trích dẫn từ chuyên gia/sách | "Charlie Munger: Invert, always invert" |
| 5 | **Data-Points** | `01-Atomic/Data-Points/` | Số liệu, thống kê, research | "73% người dùng bỏ cuộc sau tuần 2" |

> **Lưu ý:** Stories (`01-Atomic/Stories/`) được xử lý bởi skill `story-architect`, không qua skill này.

## Bảng 8 Knowledge Type (cho Solutions & Concepts)

| knowledge_type | Mô tả | -> `type` (Root) | -> Thư mục |
|---|---|---|---|
| `philosophy` | Triết lý, tư tưởng chủ đạo | `concept` | `Concepts/` |
| `concept` | Định nghĩa sự vật/hiện tượng | `concept` | `Concepts/` |
| `principle` | Quy luật nhân quả "X -> Y" | `solution` | `Solutions/` |
| `framework` | Khung giải pháp tuần tự | `solution` | `Solutions/` |
| `mental_model` | Mô hình tư duy, lăng kính | `solution` | `Solutions/` |
| `actionable_rule` | Quy tắc thực hành "Hãy làm X, tránh Y" | `solution` | `Solutions/` |
| `typology` | Phân loại học | `solution` | `Solutions/` |
| `trend` | Dự báo, nhận định tương lai | `solution` | `Solutions/` |

> **Quy tắc:** Khi tạo Solution hoặc Concept, PHẢI gán `knowledge_type` từ bảng trên. `type` (Root) quyết định thư mục lưu trữ.

## Cách phân loại & Gán Topic
1. Đọc nội dung file thô.
2. Xác định type chính dựa trên bảng trên. Nếu mơ hồ, chọn type có giá trị DIKW cao hơn (W > K > I > D).
3. Nếu 1 file chứa nhiều loại -> tách thành nhiều atoms riêng.
4. **Quy tắc Topic**: Topic được kế thừa từ node cha trong graph DIKW (không tự sinh). Mỗi Topic PHẢI trực thuộc một Pillar cụ thể đang có trong `pillars.yaml`.

## YAML Template

### Atom file (01-Atomic) — khi tạo mới:
```yaml
---
type: quote|concept|insight|solution|data-point
knowledge_type: philosophy|concept|principle|framework|mental_model|actionable_rule|typology|trend  # Chỉ cho Solutions, Concepts
topics: ["topic1", "topic2"]
belongs_to_audience: "[[Big_Audience]]"            # Chỉ cho Tầng 2 (Insights)
supports_insight: "[[Ten_Insight]]"               # Chỉ cho Tầng 3 (Solutions, Concepts)
supports_knowledge: "[[Ten_Solution_Hoac_Concept]]" # Chỉ cho Tầng 4 (Quotes, Data-Points)
status: processed
source_type: "User"                               # Mặc định — user tự viết/kể/trải nghiệm
source_name: "Inbox Processor"                    # Mặc định — skill nào tạo atom
created: YYYY-MM-DD
confidence: 0.0-1.0
vivid_insights: []                                # Chỉ cho Insights - Agent tự suy luận điền vào
vivid_knowledges: []                              # Chỉ cho Solutions, Concepts - Agent tự suy luận điền vào
---
```
Confidence scoring: 1.0 = có nguồn rõ ràng, 0.8 = user tự viết, 0.5 = mơ hồ/cần verify.
