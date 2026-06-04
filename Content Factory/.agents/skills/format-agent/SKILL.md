---
name: Format Agent
description: Skill Phase 7 — Format bài viết, nhúng metadata, cập nhật log sản xuất và hook history.
last_update: 23/05/2026 (GMT+7)
required_inputs:
  - DRAFT_SECTIONS           # from 05-draft.md (Phase 5)
  - QA_REPORT                # from 06-qa-result.md (Phase 6)
  - blackboard               # 00-blackboard.yaml (topic slug, pillar)
provided_outputs:
  - FINAL_POST
---

# Format Agent (Phase 7)

> EXECUTION_KEY: 3ebad620

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện từ các phase trước đã được biên dịch sẵn. Phase này là một trạm tự động (Automation Node).

## Hướng dẫn thực thi

> ⛔ **CẤM SINH VĂN BẢN:** Bạn KHÔNG ĐƯỢC PHÉP tự sinh yaml, không tự ghi log, không tự format bài viết. Tất cả đã được giao cho script thực hiện để đảm bảo độ chính xác 100%.

1. Chạy lệnh dưới đây để hệ thống tự động bóc tách dữ liệu, format cấu trúc, render spacing và cập nhật file log:
```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/format-agent/scripts/validate-format.ps1 -DraftPath "output/runs/[run-folder]/05-draft.md" -RunFolder "output/runs/[run-folder]/"
```

2. Đọc kết quả Output. 
   - Nếu `[PASS]` toàn bộ và Exit Code `0`, thông báo cho User: "Đã đóng gói và xuất bản bài viết thành công."
   - Nếu Exit Code `1`, báo lỗi cho User để hỗ trợ sửa chữa.
