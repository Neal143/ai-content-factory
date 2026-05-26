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

## 4. Tool Interface

Toàn bộ logic Bước 1-4 được đóng gói trong script:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/dikw-bridge/scripts/Get-DIKWCombo.ps1" -Topics "[topic]" -Audience "[audience]" -PersonaUser "[user]" [-TargetSourceIds @("source1")]
```

<!--
Tên file: injection-rules.md
Last update: 27/05/2026 01:20 (GMT+7)
Vai trò: Tài liệu hướng dẫn quy chuẩn tiêm DIKW và giao diện gọi Tool Get-DIKWCombo.
Được sử dụng khi nào: Khi Agent thực thi Bước 1-4 của dikw-bridge hoặc tham chiếu trọng số và thứ tự ưu tiên viết bài.
Output: Quy chuẩn trọng số các lớp DIKW, thứ tự ưu tiên câu chuyện, luật Poka-Yoke và cú pháp dòng lệnh gọi Combo Engine.
Tóm tắt logic hoạt động: Định nghĩa chính xác trọng số các tầng DIKW (Wisdom=10, Knowledge=7, etc.), thứ tự ưu tiên các câu chuyện cá nhân/quan sát, các bộ lọc an toàn Poka-Yoke và giao diện dòng lệnh của Get-DIKWCombo.ps1 để tối ưu hóa hiệu suất truy vấn DAG O(1).
-->
