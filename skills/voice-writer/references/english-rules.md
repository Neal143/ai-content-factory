<!--
Tên file: english-rules.md
Last update: 09/06/2026 15:30 (GMT+7)
Vai trò: Hướng dẫn xử lý tiếng Anh, cấm trộn từ và danh sách blacklist.
Được sử dụng khi nào: Khi AI thực hiện viết bài nháp (draft).
Output là gì: Bài viết thuần Việt, thuật ngữ chuẩn hóa.
Tóm tắt logic hoạt động: Quy định cấm trộn tiếng Anh trong câu; cung cấp danh sách từ vựng tiếng Anh bị cấm (blacklist) kèm từ thay thế chuẩn; định dạng hiển thị thuật ngữ Việt-Anh lần đầu và lần sau; liệt kê các grep pattern tự động quét lỗi.
-->

# English Rules & Localization
**Module:** check/english-rules

## 1. Cấm trộn tiếng Anh trong câu
Tuyệt đối không trộn tiếng Anh kiểu lóng vào giữa câu tiếng Việt.
```
❌ "Performance của team đạt target trong quarter này"
✅ "Hiệu suất của đội ngũ đạt mục tiêu trong quý này"
```

## 2. English Blacklist — Danh sách từ tiếng Anh bị cấm
Tuyệt đối KHÔNG được dùng các từ tiếng Anh sau trong bài viết tiếng Việt. Phải thay bằng tiếng Việt thuần.

| # | Từ cấm ❌ | Thay bằng ✅ |
|---|----------|------------|
| 1 | mindset | tư duy |
| 2 | team | nhóm / đội |
| 3 | level up | nâng cấp |
| 4 | focus | tập trung |
| 5 | passion | đam mê |
| 6 | content | nội dung |
| 7 | hustle | cày cuốc |
| 8 | skill | kỹ năng |
| 9 | trend | xu hướng |
| 10 | insight | góc nhìn sâu |
| 11 | networking | kết nối |

**Ngoại lệ chung**: Tên riêng (Facebook, Google) và thuật ngữ chuyên ngành (marketing, branding, startup, freelancer, CEO, AI, KPI, ROI) được phép giữ nguyên.

## 3. Chuẩn thuật ngữ Việt-Anh
| Tình huống | Format | Ví dụ |
|-----------|--------|-------|
| Giới thiệu lần đầu | Tiếng Việt (*English*) | Kiến thức (*Knowledge*) |
| Các lần sau | Tiếng Việt hoặc acronym | Kiến thức, hoặc KB |
| Ngoại lệ phổ biến | Giữ nguyên | AI, CEO, KPI, ROI |

**KHÔNG BAO GIỜ:** English trước, Việt sau. Cấm "Knowledge (Kiến thức)".
**NHẤT QUÁN:** Đã chọn từ Việt nào → dùng xuyên suốt, không đổi.

## Grep Patterns
| Pattern | Search | Quy tắc |
|---------|--------|---------|
| English in sentence | `\b(performance|target|quarter|deliver|team|improve|reduce|adapt|training|insight|subscribe|embrace)\b` | Cấm trộn, dịch sang Việt |
| English-first term | Pattern: `English (Tiếng Việt)` | Cấm. Phải Việt trước |

## Checklist
- [ ] Không trộn tiếng Anh không cần thiết
- [ ] Không sử dụng từ trong Blacklist
- [ ] Thuật ngữ lần đầu: Việt (*English*)
- [ ] Thuật ngữ các lần sau: nhất quán dùng Việt

> FILE_KEY:
