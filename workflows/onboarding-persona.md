---
description: Công cụ phỏng vấn để tạo bộ DNA giọng văn mới KHÔNG YÊU CẦU GIẢI THÍCH
---

# 🎨 Workflow: Tạo mới bộ DNA Ký xướng (Onboarding Persona)

> **LỆNH**: `/onboarding-persona`

Quy trình tự động thiết lập Workspace (Persona File, Vault) và kích hoạt Interviewer Skill để thu thập Data.

## Hướng dẫn thực thi

> 🚨 **CRITICAL PROMPT CHO AI ASSISTANT:** Ngay khi User gõ lệnh `/onboarding-persona`, bạn PHẢI LẬP TỨC kích hoạt skill `persona-interviewer` và tiến hành phỏng vấn **Tier 1 (Quick Start)** (Gửi tin nhắn đầu tiên chào mừng và hỏi Tên/Bút danh). KHÔNG giải thích workflow, KHÔNG chờ đợi.

### Tiến trình Thực thi
- Workflow này đóng vai trò như Trigger khởi động. Mọi kịch bản (Khai thác thông tin, chạy Script PowerShell cấu hình hệ thống, tạo Vault) đều đã được GÓI GỌN và điều phối tự động bên trong cấu trúc của System Skill `persona-interviewer`.  
- Bạn CHỈ CẦN mở và làm theo 100% tài liệu `SKILL.md`.

### Kiểm Định Sau Thực Thi (Post-Execution Audit)

> ⛔ **BẮT BUỘC — KHÔNG ĐƯỢC BỎ QUA:** Ngay sau khi hoàn tất toàn bộ quy trình phỏng vấn (Tier 2 kết thúc), AI **PHẢI** tự động chạy lệnh kiểm định dưới đây. Đây là chốt chặn cuối cùng đảm bảo mọi output đã được sinh ra đầy đủ và chính xác.

```powershell
powershell -ExecutionPolicy Bypass -File .agents/skills/persona-interviewer/scripts/validate_outputs.ps1
```

> Sau khi script chạy xong, hiển thị **nguyên văn** kết quả Terminal cho User (không tóm tắt, không diễn giải). Nếu có bất kỳ dòng `[FAIL]` nào, thông báo cho User biết vị trí lỗi cần xử lý.

### Vault Curation — Chuẩn hóa Atoms mới (nếu có)
Nếu quy trình onboarding có sinh Atom mới (Insight/Solution từ data phỏng vấn):
1. Đọc danh sách đường dẫn atom từ file `vault/.tmp/pending_curation_atoms.txt` (do script run_insights.ps1 tự động ghi nhận).
2. Hỏi User chọn cách thực thi:

**Lựa chọn A — Chạy tự động trên Antigravity 2.0 (Khuyến nghị):**
In prompt sau để User copy sang Antigravity 2.0:
```
Đọc workflow `.agents/workflows/vault-curator-anti20.md` và thực thi:
- Mode: atoms-full-pipeline
- Atoms file: vault/.tmp/pending_curation_atoms.txt
- Output dir: vault/.curation_temp/
```

**Lựa chọn B — Chạy tại đây (cần handoff mỗi 5 batch):**
Triệu hồi **VaultCuratorAgent** (đọc `.agents/agents/vault-curator/AGENT.md`):
   - Mode: `atoms-full-pipeline` (cần alignment để gắn `belongs_to_audience` + tìm parent node cho Insight mới)
   - Atoms: Danh sách đường dẫn file Atom.
   - Output-dir: `vault/.curation_temp/`

> Nếu chỉ tạo file Audience (không sinh Atom nội dung), bỏ qua bước này.