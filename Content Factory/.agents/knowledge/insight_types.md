<!--
Tên file: insight_types.md
Last update: 30/06/2026 15:35 (GMT+7)
Vai trò: Single Source of Truth cho danh sách mã insight_type chuẩn.
Được sử dụng khi nào: (1) validate_outputs.ps1 đọc để kiểm định enum. (2) Tương lai: workflow inject vào SKILL.md trước khi agent thực thi.
Output: Bảng Markdown chứa mã và mô tả insight_type.
Tóm tắt logic hoạt động: File tĩnh chứa enum. Script đọc cột đầu bảng bằng regex.
-->

# Bảng Mã Insight Type

| Mã (insight_type) | Mô tả |
|---|---|
| `desire` | Tham vọng, khao khát, động lực tiến tới |
| `fear` | Nỗi sợ hãi |
| `pain_point` | Nỗi đau, bế tắc hiện tại |
| `barrier` | Rào cản (Tâm lý, vật lý, thời gian...) |
| `belief` | Niềm tin cốt lõi |
| `likes` | Sở thích, điều ưa chuộng |
| `dislikes` | Điều ghét, muốn tránh xa |
| `pitfall` | Cạm bẫy, cách làm sai lầm/độc hại |
| `myth` | Lầm tưởng, huyền thoại sáo rỗng/sai lệch |
