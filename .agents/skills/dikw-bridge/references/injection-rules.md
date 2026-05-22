# DIKW Injection Rules

## 1. Trọng số DIKW

| Layer | Thư mục | Weight |
|-------|---------|--------|
| W (Wisdom) | Stories | 10 |
| K (Knowledge) | Insights, Solutions | 7 |
| I (Information) | Concepts | 3 |
| D (Data) | Quotes, Data-Points | 1 |

## 2. Story Subtype Priority

| Priority | SubType | Weight | Điều kiện |
|----------|---------|--------|-----------|
| 1 | personal (self) | 15 | Phải có trong vault |
| 2 | observed (friend) | 12 | Phải có trong vault |
| 3 | secondhand (expert) | 8 | Phải có trong vault |
| 4 | famous_world | 7 | Khi vault trống |
| 5 | historical | 5 | Khi vault trống |

> **SAS v18.2**: Personal + Observed CHỈ khi CÓ trong vault. Vault trống → nhảy xuống famous_world. TUYỆT ĐỐI KHÔNG BỊA.

## 3. Poka-Yoke Rules
- ⛔ Không có atom liên quan? → BỎ QUA. KHÔNG BỊA.
- ⛔ Atom confidence < 0.5 → KHÔNG dùng.
- ⛔ Atom status = "rejected" → KHÔNG dùng.
- ⛔ Agent tự tạo story personal/observed → AUTO-FAIL.
- ✅ Solution/Concept PHẢI có KCS credibility intro.
