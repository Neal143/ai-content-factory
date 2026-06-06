# Plan: Content-Post — Chế Độ Auto & Thử Nghiệm

**Tên file:** plan.md
**Last update:** 18/05/2026 22:20 (GMT+7)
**Vai trò:** Tổng quan kế hoạch triển khai, theo dõi tiến độ.
**Được sử dụng khi nào?:** Trong suốt quá trình triển khai tính năng.
**Output:** Tham chiếu nhanh trạng thái các phase.
**Tóm tắt logic hoạt động:** Chia nhỏ công việc thành 5 phase, mỗi phase có file chi tiết riêng.

Created: 17/05/2026 23:01 (GMT+7)
Status: 🟡 In Progress
Source: `docs/BRIEF.md`

---

## Overview

Bổ sung chế độ Thử nghiệm (Basic/Nâng cao) cho pipeline `content-post`, cho phép user tùy chỉnh các tham số cấu trúc bài viết (separator, số câu, số từ, heading) trước khi pipeline chạy. Voice-writer LUÔN viết đầy đủ structural markers (TITLE, SECTION, PARAGRAPH, HEADING) + `⁂` delimiter. Format-agent strip/giữ theo profile.

## Kiến trúc tổng quan

```
User chọn chế độ (Agent hỏi trong chat)
       │
       ├── Auto → Agent copy default.json → active.json
       │
       └── Thử nghiệm → Agent hỏi tham số qua chat
                                │
                                ▼
                  Agent tạo profiles/active.json
                                │
                                ▼
                  apply-profile.ps1 -Action validate
                  (script kiểm tra ràng buộc R1–R8)
                                │
                                ▼
                  apply-profile.ps1 -Action patch
                  (patch prompt files từ active.json)
                                │
                                ▼
             validate-*.ps1 đọc trực tiếp profiles/active.json
             (không cần patch — đã được refactor đọc JSON)
                                │
                                ▼
                  Pipeline content-post chạy bình thường
                                │
                                ▼
                  apply-profile.ps1 -Action restore
                  (restore prompt files về bản gốc)
```

**Nguyên tắc thiết kế:**
- **Agent** xử lý tương tác: hỏi user qua chat, thu thập câu trả lời, tạo `profiles/active.json`.
- **Script** xử lý kỹ thuật: validate JSON, patch prompt files, restore. KHÔNG interactive (`Read-Host`).
- **Script validation (.ps1):** Refactor VĨNH VIỄN để đọc threshold từ `profiles/active.json`. Không cần patch/restore.
- **Prompt files (.md):** Patch tạm thời bằng `apply-profile.ps1`, restore sau khi pipeline xong.
- **Structural Markers:** Voice-writer LUÔN viết `<!-- TITLE -->`, `<!-- SECTION -->`, `<!-- SECTION_HEADING -->`, `<!-- PARAGRAPH: N -->`, `<!-- PARAGRAPH_HEADING -->`, `⁂`. Validator kiểm tra cấu trúc. Format-agent strip/giữ theo profile (`output_elements`).
- **Mode-aware severity:** Chế độ Auto → chain checks là WARN. Thử nghiệm → FAIL.
- **Auto-restore:** Đầu mỗi pipeline run, luôn chạy restore để dọn patch thừa từ lần crash trước.
- **Encoding rule:** File `.ps1` = 100% ASCII. Mọi nội dung non-ASCII (patterns tiếng Việt, messages) lưu trong `.json`, đọc runtime bằng `-Encoding UTF8`. Lý do: PowerShell 5 cần BOM cho UTF-8 nhưng AI tools không đảm bảo giữ BOM khi edit.

## Phases

| Phase | Name | File | Status | Progress |
|-------|------|------|--------|----------|
| 01 | Profile System | `phase-01-profile-system.md` | ✅ Complete | 100% |
| 02 | Validator Overhaul | `phase-02-validator-overhaul.md` | ✅ Complete | 100% |
| 03 | Prompt Patching | `phase-03-prompt-patching.md` | ✅ Complete | 100% |
| 04 | Format Agent & Structural Markers | `phase-04-format-agent.md` | ✅ Complete | 100% |
| 05 | Pipeline Integration & Test | `phase-05-integration.md` | ✅ Complete | 100% |

## Quick Commands
- Start Phase 1: `/code phase-01`
- Check progress: `/next`
