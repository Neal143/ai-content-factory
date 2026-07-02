# Output Schema — Story Architect
# Version: v19.0

## 1. Mô hình 5 phần Story (S-P-T-O-L)
| # | Phần | Ý nghĩa | Ví dụ |
|---|------|---------|-------|
| S | **Situation** | Bối cảnh, tình huống ban đầu | "Năm 2019, tôi đang làm marketing..." |
| P | **Problem** | Vấn đề phát sinh | "...thì công ty cắt giảm 50% nhân sự" |
| T | **Turning Point** | Điểm xoay chiều | "Một buổi sáng, tôi đọc được cuốn sách..." |
| O | **Outcome** | Kết quả | "6 tháng sau, tôi đã..." |
| L | **Lesson** | Bài học rút ra | "Điều tôi học được là..." |

---

## 2. 5 Story Subtypes

### 2.1. Personal Self — User kể chuyện mình
- `subtype: personal`, `protagonist: "self"`, `confidence: 0.95`
- Có thể gán `outcome_measurable: true` nếu story có kết quả đo bằng số.

### 2.2. Observed — User chứng kiến/nghe kể trực tiếp
- `subtype: observed`, `protagonist: "<Tên>"`, `confidence: 0.8`
- Có thể gán `relationship: friend | colleague | mentor | client`.

### 2.3. Secondhand — User đọc/nghe từ nguồn khác
- `subtype: secondhand`, `protagonist: "<Tên chuyên gia>"`, `confidence: 0.9`
- Ghi chú nguồn gốc câu chuyện vào nội dung thay vì YAML.

### 2.4. Historical — Câu chuyện lịch sử
- `subtype: historical`, `protagonist: "<Nhân vật lịch sử>"`, `confidence: 1.0`
- Ghi chú nguồn gốc câu chuyện vào nội dung thay vì YAML.

### 2.5. Famous World — Người/tổ chức nổi tiếng thế giới (SAS v18.2)
> Dùng khi vault KHÔNG có story liên quan. Chỉ dùng người/tổ chức
> nổi tiếng mà đa số người đọc đã biết. KHÔNG dùng người Việt Nam
> (trừ khi đã có trong vault).

- `subtype: famous_world`, `protagonist: "<Người/tổ chức>"`, `confidence: 1.0`
- Có thể gán `fame_level: global | regional`.

**Ví dụ hợp lệ:**
- Ray Dalio kể trong cuốn Principles...
- Toyota thập niên 50 suýt phá sản, rồi phát minh Toyota Production System...

**Ví dụ KHÔNG hợp lệ:**
- ❌ "Tôi có quen một bạn làm thiết kế..." (bịa, không trong vault)
- ❌ "Chị Hoa, chủ quán cà phê..." (bịa, người Việt không nổi tiếng)

---

## 3. Bảng 8 Knowledge Type & Mapping

| knowledge_type | Mô tả | → `type` (Root) | → Thư mục |
|---|---|---|---|
| `philosophy` | Triết lý, tư tưởng chủ đạo | `concept` | `Concepts/` |
| `concept` | Định nghĩa sự vật/hiện tượng | `concept` | `Concepts/` |
| `principle` | Quy luật nhân quả "X → Y" | `solution` | `Solutions/` |
| `framework` | Khung giải pháp tuần tự | `solution` | `Solutions/` |
| `mental_model` | Mô hình tư duy, lăng kính | `solution` | `Solutions/` |
| `actionable_rule` | Quy tắc thực hành "Hãy làm X, tránh Y" | `solution` | `Solutions/` |
| `typology` | Phân loại học | `solution` | `Solutions/` |
| `trend` | Dự báo, nhận định tương lai | `solution` | `Solutions/` |

> **Quy tắc:** `type` (Root) quyết định thư mục lưu trữ trong `vault/01-Atomic/`. Xem chi tiết tại `dikw-mapping.md`.

---

## 4. Khuôn Đúc YAML Frontmatter

Template thống nhất cho **cả File A (Knowledge) và File B (Story)**. Agent chọn đúng fields theo loại file.

```yaml
---
type: solution | concept | story
# ↑ File A: solution hoặc concept (xem Bảng 8 Knowledge Type)
# ↑ File B: story
# --- BIẾN LỚP 2 (chọn 1 theo loại file) ---
knowledge_type: <1_trong_8_loại>             # CHỈ File A — xem Bảng 8 Knowledge Type
subtype: <1_trong_5_subtypes>                # CHỈ File B — personal | observed | secondhand | historical | famous_world
# --- FIELDS CHUNG ---
topics: ["<resolved_topics>"]                # Cả File A + B — kế thừa biến resolved_topics
status: processed
source_type: "User"                         # Mặc định
source_name: "Story Architect"               # Mặc định
source_id: "story-architect"                 # Mặc định
confidence: <Theo_từng_subtype>              # File B phụ thuộc SubType. File A tuân theo độ chắc chắn của Lesson (thường 0.9)
created: "<Ngày_hôm_nay>"                       # Ngày tạo atom (VD: 2026-06-28)
# --- FIELDS RIÊNG FILE B (Story) ---
protagonist: "<Tên_nhân_vật_chính>"          # BẮT BUỘC File B
# --- ĐỊNH TUYẾN GRAPH (Chặn mồ côi) ---
keywords: []                                 # Khởi tạo mảng trống cho RAG Index
supports_insight: ["[[Link_Insight_Tầng_2]]"]  # CHỈ File A — trỏ lên Insight đã chốt
supports_knowledge: ["[[Link_File_A_Tầng_3]]"] # CHỈ File B — trỏ lên File A vừa tạo
# --- DỮ LIỆU VIVID ---
vivid_knowledges: ["<Câu ẩn dụ>"]            # CHỈ File A — hỏi user ở Bước 3. Hard Cap 3. Bỏ qua nếu rỗng.
# --- TÙY CHỌN THEO SUBTYPE (File B) ---
# outcome_measurable: true | false           # personal/observed — nếu có kết quả đo bằng số
# relationship: friend | colleague | mentor | client  # observed only
# fame_level: global | regional              # famous_world only
---
```

---

## 5. Injection Priority Matrix

Bảng xếp hạng ưu tiên khi inject story vào bài viết:

| Priority | SubType | Protagonist | Weight | Placement | Voice Rule |
|:---|:---|:---|:---|:---|:---|
| 🥇 1 | personal | self | **15** | Hook / Story section | Ngôi 1, chi tiết cảm xúc |
| 🥈 2 | observed | friend/name | **12** | Deep Dive | "Tôi có quen người...", giữ tên + relationship |
| 🥉 3 | secondhand | expert_name | **8** | Anywhere hỗ trợ evidence | "Trong cuốn X, tác giả Y kể rằng..." |
| 4 | famous_world | famous_person/org | **7** | Framework minh họa | Kể lại + nguồn cụ thể |
| 5 | historical | historical_figure | **5** | Anywhere | Ngắn gọn, làm "gia vị" |

> **SAS v18.2**: Priority 1-2 (personal, observed) CHỈ khi có trong vault.
> Nếu vault trống → nhảy xuống Priority 4 (famous_world). TUYỆT ĐỐI KHÔNG BỊA 1-2.

---

## 6. 7 Poka-Yoke Rules (Chống rác vào Vault)
1. **Must have Turning Point**: Không có T → Reject. Đây là linh hồn của story.
2. **Confidence ≥ 0.5**: Nếu story mơ hồ, thiếu chi tiết cụ thể → confidence thấp → Reject.
3. **Verified required**: `verified: false` → Reject (trừ khi subtype = historical).
4. **Timeline required**: Phải có mốc thời gian cụ thể (năm, tháng, hoặc "hồi đại học").
5. **Protagonist required**: Phải xác định rõ nhân vật chính.
6. **Minimum 3 parts**: Tối thiểu phải có S + T + L (3/5 phần).
7. **No fabrication [SAS v18.2]**: Agent TỰ TẠO câu chuyện personal/observed → AUTO-FAIL, BÀI BỊ LOẠI.

## 7. Story Rotation
- Cùng 1 story KHÔNG được dùng trong 2 bài liên tiếp (check `production-log.md`).

## 8. Duplicate Check
Trước khi lưu, quét `vault/01-Atomic/Stories/` xem có story nào cùng protagonist + cùng turning point không. Nếu trùng → Skip.

---

## 9. Naming & Storage Convention

Tất cả các file do Story Architect tạo ra bắt buộc phải tuân thủ chuẩn Tiếng Việt không dấu, viết thường, thay khoảng trắng bằng dấu gạch ngang (`kebab-case`). Tiền tố mặc định là `USER_` do nguồn dữ liệu được khai thác từ cuộc hội thoại với người dùng.

### 9.1. File A (Lesson / Knowledge - Tầng 3)
- **Cấu trúc:** `USER_[knowledge_name].md`
- **Thư mục lưu trữ:** BẮT BUỘC map theo giá trị thẻ `type` trong YAML Frontmatter:
  - Nếu `type: solution` ➔ Lưu vào thư mục `vault/01-Atomic/Solutions/`
  - Nếu `type: concept` ➔ Lưu vào thư mục `vault/01-Atomic/Concepts/`
- **Ví dụ:** `USER_chien-luoc-tiep-thi-du-kich.md`

### 9.2. File B (Story - Tầng 4)
- **Cấu trúc:** `USER_story-[protagonist]-[core_event].md`
- **Thư mục:** `vault/01-Atomic/Stories/`
- **Quy ước `[protagonist]`:**
  - Nếu User tự kể (Personal): Dùng tên của User (Ví dụ: `neal`).
  - Nếu câu chuyện của người khác / danh nhân: Dùng tên nhân vật đó (Ví dụ: `steve-jobs`).
- **Ví dụ:** `USER_story-neal-bi-cat-giam-nhan-su-2019.md`
