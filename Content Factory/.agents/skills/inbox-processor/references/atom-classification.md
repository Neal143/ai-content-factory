# Atom Classification — Phân loại nguyên liệu

## 5 Atom Types (xu ly boi Inbox Processor)

| # | Type | Thu muc | Dinh nghia | Vi du |
|---|------|---------|-----------|-------|
| 1 | **Insights** | `01-Atomic/Insights/` | Goc nhin sau, phan tich contrarian | "Nguoi ta nghi X nhung thuc ra Y" |
| 2 | **Solutions** | `01-Atomic/Solutions/` | Mo hinh, cong thuc, phuong phap | "DIKW Pyramid", "80/20 Rule" |
| 3 | **Concepts** | `01-Atomic/Concepts/` | Dinh nghia, khai niem nen tang | "Deliberate Practice la gi?" |
| 4 | **Quotes** | `01-Atomic/Quotes/` | Trich dan tu chuyen gia/sach | "Charlie Munger: Invert, always invert" |
| 5 | **Data-Points** | `01-Atomic/Data-Points/` | So lieu, thong ke, research | "73% nguoi dung bo cuoc sau tuan 2" |

> **Luu y:** Stories (`01-Atomic/Stories/`) duoc xu ly boi skill `story-architect`, khong qua skill nay.

## Bang 8 Knowledge Type (cho Solutions & Concepts)

| knowledge_type | Mo ta | -> `type` (Root) | -> Thu muc |
|---|---|---|---|
| `philosophy` | Triet ly, tu tuong chu dao | `concept` | `Concepts/` |
| `concept` | Dinh nghia su vat/hien tuong | `concept` | `Concepts/` |
| `principle` | Quy luat nhan qua "X -> Y" | `solution` | `Solutions/` |
| `framework` | Khung giai phap tuan tu | `solution` | `Solutions/` |
| `mental_model` | Mo hinh tu duy, lang kinh | `solution` | `Solutions/` |
| `actionable_rule` | Quy tac thuc hanh "Hay lam X, tranh Y" | `solution` | `Solutions/` |
| `typology` | Phan loai hoc | `solution` | `Solutions/` |
| `trend` | Du bao, nhan dinh tuong lai | `solution` | `Solutions/` |

> **Quy tac:** Khi tao Solution hoac Concept, PHAI gan `knowledge_type` tu bang tren. `type` (Root) quyet dinh thu muc luu tru.

## Cach phan loai & Gan Topic
1. Doc noi dung file tho.
2. Xac dinh type chinh dua tren bang tren. Neu mo ho, chon type co gia tri DIKW cao hon (W > K > I > D).
3. Neu 1 file chua nhieu loai -> tach thanh nhieu atoms rieng.
4. **Quy tac Topic**: Topic duoc ke thua tu node cha trong graph DIKW (khong tu sinh). Moi Topic PHAI truc thuoc mot Pillar cu cu the dang co trong `pillars.yaml`.

## YAML Template

### Atom file (01-Atomic) — khi tao moi:
```yaml
---
type: quote|concept|insight|solution|data-point
knowledge_type: philosophy|concept|principle|framework|mental_model|actionable_rule|typology|trend  # Chi cho Solutions, Concepts
topics: ["topic1", "topic2"]
belongs_to_audience: "[[Big_Audience]]"            # Chi cho Tang 2 (Insights)
supports_insight: "[[Ten_Insight]]"               # Chi cho Tang 3 (Solutions, Concepts)
supports_knowledge: "[[Ten_Solution_Hoac_Concept]]" # Chi cho Tang 4 (Quotes, Data-Points)
status: processed
source_type: "User"                               # Mac dinh — user tu viet/ke/trai nghiem
source_name: "Inbox Processor"                    # Mac dinh — skill nao tao atom
created: YYYY-MM-DD
confidence: 0.0-1.0
vivid_insights: []                                # Chi cho Insights - Agent tu suy luan dien vao
vivid_knowledges: []                              # Chi cho Solutions, Concepts - Agent tu suy luan dien vao
---
```
Confidence scoring: 1.0 = co nguon ro rang, 0.8 = user tu viet, 0.5 = mo ho/can verify.
