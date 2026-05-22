# Story Schema — Cấu trúc 5 phần (S-P-T-O-L)
# Version: v18.2 (synced with Thông Phan engine)

## Mô hình 5 phần
| # | Phần | Ý nghĩa | Ví dụ |
|---|------|---------|-------|
| S | **Situation** | Bối cảnh, tình huống ban đầu | "Năm 2019, tôi đang làm marketing..." |
| P | **Problem** | Vấn đề phát sinh | "...thì công ty cắt giảm 50% nhân sự" |
| T | **Turning Point** | Điểm xoay chiều | "Một buổi sáng, tôi đọc được cuốn sách..." |
| O | **Outcome** | Kết quả | "6 tháng sau, tôi đã..." |
| L | **Lesson** | Bài học rút ra | "Điều tôi học được là..." |

---

## 5 Story Subtypes

### 1. Personal Self — Tác giả kể chuyện mình
```yaml
---
type: story
subtype: personal
protagonist: "self"
topics: [career, focus]
verified: true               # TÁC GIẢ tự xác nhận
confidence: 0.95
timeline: "11 tháng"
outcome_measurable: true     # Có kết quả đo được bằng số?
source: user_told
created: 2026-03-03
---
```

### 2. Observed — Tác giả chứng kiến/nghe kể
```yaml
---
type: story
subtype: observed
protagonist: "Anh Minh"     # Tên thật hoặc bút danh
topics: [business, risk]
verified: true               # Tác giả xác nhận đã gặp/chứng kiến
relationship: "friend"       # friend | colleague | mentor | client
confidence: 0.8
timeline: "2023"
outcome_measurable: false
source: user_told
created: 2026-03-03
---
```

### 3. Secondhand — Tác giả đọc/nghe từ nguồn khác
```yaml
---
type: story
subtype: secondhand
protagonist: "Cal Newport"
topics: [productivity]
verified: true
source: "Deep Work, Chapter 3"   # Nguồn cụ thể (sách, bài báo)
confidence: 0.9
timeline: "2016"
created: 2026-03-03
---
```

### 4. Historical — Câu chuyện lịch sử/nổi tiếng
```yaml
---
type: story
subtype: historical
protagonist: "Steve Jobs"
topics: [innovation, leadership]
verified: true
source: "Walter Isaacson biography"
confidence: 1.0
timeline: "1985"
created: 2026-03-03
---
```

### 5. Famous World — Người/tổ chức nổi tiếng thế giới (SAS v18.2)

> Dùng khi vault KHÔNG có story liên quan. Chỉ dùng người/tổ chức
> nổi tiếng mà đa số người đọc đã biết. KHÔNG dùng người Việt Nam
> (trừ khi đã có trong vault).

```yaml
---
type: story
subtype: famous_world
protagonist: "Ray Dalio"
topics: [investment, principles]
verified: true                  # Đã public, có sách/bài báo
source: "Principles, Chapter 2" # PHẢI có nguồn cụ thể
fame_level: "global"            # global | regional (NO local)
confidence: 1.0
timeline: "2008"
created: 2026-03-03
---
```

**Ví dụ hợp lệ:**
- Ray Dalio kể trong cuốn Principles...
- Toyota thập niên 50 suýt phá sản, rồi phát minh Toyota Production System...
- Jeff Bezos từ garage đến đế chế nghìn tỷ đô...

**Ví dụ KHÔNG hợp lệ:**
- ❌ "Tôi có quen một bạn làm thiết kế..." (bịa, không trong vault)
- ❌ "Có anh Minh ở công ty cũ tôi..." (bịa, không trong vault)
- ❌ "Chị Hoa, chủ quán cà phê..." (bịa, người Việt không nổi tiếng)

---

## Injection Priority Matrix

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

## YAML Frontmatter — Tóm tắt tất cả fields

```yaml
---
title: "Tên câu chuyện"
subtype: personal | observed | secondhand | historical | famous_world
protagonist: "Tên nhân vật chính"
topics: [topic1, topic2]
verified: true | false
confidence: 0.0-1.0
timeline: "YYYY hoặc mô tả thời gian"
source: user_told | extracted_from_post | vault | "Tên sách/bài báo"
created: YYYY-MM-DD
# --- Optional (theo subtype) ---
outcome_measurable: true | false     # personal/observed
relationship: friend | colleague | mentor | client  # observed only
fame_level: global | regional        # famous_world only
---
```

---

## 7 Poka-Yoke Rules (Chống rác vào Vault)
1. **Must have Turning Point**: Không có T → Reject. Đây là linh hồn của story.
2. **Confidence ≥ 0.5**: Nếu story mơ hồ, thiếu chi tiết cụ thể → confidence thấp → Reject.
3. **Verified required**: `verified: false` → Reject (trừ khi subtype = historical).
4. **Timeline required**: Phải có mốc thời gian cụ thể (năm, tháng, hoặc "hồi đại học").
5. **Protagonist required**: Phải xác định rõ nhân vật chính.
6. **Minimum 3 parts**: Tối thiểu phải có S + T + L (3/5 phần).
7. **No fabrication [SAS v18.2]**: Agent TỰ TẠO câu chuyện personal/observed → AUTO-FAIL, BÀI BỊ LOẠI.

## Story Rotation
- Cùng 1 story KHÔNG được dùng trong 2 bài liên tiếp (check `production-log.md`).

## Duplicate Check
Trước khi lưu, quét `vault/01-Atomic/Stories/` xem có story nào cùng protagonist + cùng turning point không. Nếu trùng → Skip.
