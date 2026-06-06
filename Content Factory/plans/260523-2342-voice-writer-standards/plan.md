# Plan: Nâng Cấp Tiêu Chuẩn Tiếng Việt Cho Voice Writer

> **Tên file:** plans/260523-2342-voice-writer-standards/plan.md
> **Last update:** 24/05/2026 13:06 (GMT+7)
> **Vai trò:** Tổng quan tiến độ và theo dõi kế hoạch tích hợp 5 bộ chuẩn tiếng Việt vào Voice Writer skill.
> **Output:** Cập nhật cột Status/Progress khi hoàn thành mỗi phase.

Created: 23/05/2026 23:42 (GMT+7)
Status: ✅ Complete

## Overview

Tích hợp 5 tài liệu chuẩn tiếng Việt (`capitalization.md`, `english-mixing.md`, `prose-format.md`, `punctuation.md`, `ai-detection.md`) vào Voice Writer skill thông qua 2 lớp:
1. **Prompt layer** — Cập nhật `SKILL.md` để AI đọc và tuân thủ chuẩn khi viết.
2. **Hard-gate layer** — Thêm CHECK 15/16/17 vào `validate-draft.ps1` để kiểm tra tự động.

## Rủi ro hệ thống đã xử lý

| Rủi ro | Giải pháp | Phase |
|--------|-----------|-------|
| `apply-profile.ps1` patch vỡ nếu đụng dòng Paragraph/Chain | Giữ nguyên 100% nội dung dòng Paragraph và Chain. Thêm constraint mới ở cuối bảng. | 01 |
| PS5 đọc file `.ps1` không BOM → ký tự có dấu bị hỏng | Dùng `[char]0xXXXX` cho string, regex `\uXXXX` cho pattern. Messages tiếng Anh. | 02 |
| FATAL RULE "cả 3" lỗi thời | Đổi thành "toàn bộ" | 01 |
| Đường dẫn `../../viet-chuyen-nghiep/` sai | Dùng `../viet-chuyen-nghiep/` (1 cấp từ Content Factory root) | 01 |

## Phases

| Phase | Name | Status | Progress | Tasks | Files |
|-------|------|--------|----------|-------|-------|
| 01 | Copy Refs & SKILL Update | ✅ Complete | 100% | 7 | 6 |
| 02 | Script Hard-Gate | ✅ Complete | 100% | 3 | 1 |
| 03 | Key Generator Update | ✅ Complete | 100% | 2 | 1 |

**Tổng:** 12 tasks | 8 files | Ước tính: < 20 phút
