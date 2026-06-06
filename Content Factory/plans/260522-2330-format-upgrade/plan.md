# Plan: Upgrade Format Pipeline + AGENT.md Single Source of Truth

> **File**: plan.md
> **Last update**: 22/05/2026 23:33 (GMT+7)
> **Vai trò**: Tổng quan kế hoạch, theo dõi tiến độ
> **Sử dụng khi**: Bắt đầu `/code` — đọc file này trước để biết cần làm gì
> **Output**: Cập nhật cột Status/Progress khi hoàn thành mỗi phase

Created: 22/05/2026 23:33 (GMT+7)
Status: ✅ Complete

## Overview

Upgrade hệ thống format bài viết trong pipeline `content-post`:
- Bổ sung chain separator vào FormatAgent pipeline
- Làm rõ section separator logic + mở rộng DATA INTEGRITY
- Dọn dead code trong validate-draft.ps1
- Loại bỏ 26 mục duplicate/hardcode/xung đột trong 9 AGENT.md → single source of truth

## Prerequisites

> ⚠️ **BẮT BUỘC** chạy trước khi thực thi Phase 1-3:

```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
```

**Verify**: `format-agent/SKILL.md` dòng 60 = `"Giữa các đoạn: cách dòng trên 1 dòng trống, cách dòng dưới 0 dòng trống"`.

## Phases

| Phase | Name | Status | Progress | Tasks | Files |
|-------|------|--------|----------|-------|-------|
| 01 | Format Pipeline (SKILL.md) | ✅ Complete | 100% | 1 | 1 |
| 02 | Patch Patterns + Apply Profile | ✅ Complete | 100% | 2 | 2 |
| 03 | Dead Code Cleanup | ✅ Complete | 100% | 1 | 1 |
| 04 | AGENT.md Single Source of Truth | ✅ Complete | 100% | 9 | 9 |

**Tổng:** 13 tasks | 13 files | Ước tính: 1 session

## Verification

Sau Phase 1-3:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action patch
# Kỳ vọng: PATCH COMPLETE

powershell -ExecutionPolicy Bypass -File ".agents/skills/voice-writer/scripts/validate-draft.ps1" -DraftPath "output/runs/2026-05-21_nao_bo_tre_em/05-draft.md"
# Kỳ vọng: Không lỗi biến đã xóa
```

Sau Phase 4: Spot check từng AGENT.md — không còn con số cụ thể, không liệt kê execution steps.

## Quick Commands

- Start Phase 1: `/code phase-01`
- Check progress: `/next`
- Save context: `/checkpoint`
