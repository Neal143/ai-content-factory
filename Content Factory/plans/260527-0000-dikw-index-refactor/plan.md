---
name: plan.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Plan Overview
usage: Tổng quan tiến độ và danh sách phases cho BRIEF-DIKW-Index
output: Tracker trạng thái từng phase
logic: Chia 3 nhóm BRIEF (A, B, C) thành 5 phases theo thứ tự dependency
---

# Plan: DIKW Index Refactor + Schema Fix

**BRIEF nguồn:** `docs/BRIEF-DIKW-Index.md`
**Ngày tạo:** 27/05/2026
**Trạng thái:** ✅ Complete

## Thứ tự thực thi (Dependency Chain)

```
Phase 1 (Nhóm B) ──→ Phase 2 (Nhóm C) ──→ Phase 3 (Nhóm A) ──→ Phase 4 (Nhóm A) ──→ Phase 5 (Nhóm A)
Schema B fix         GI backfill           Build Index           Get-DIKWCombo         SKILL.md refactor
(độc lập)            (cần topic_map        (cần data đúng)       (cần index)           (cần tool)
                      đã cập nhật)
```

**Lý do thứ tự:**
- Phase 1 (B) sửa template + script → future atoms đúng từ đầu
- Phase 2 (C) sửa data GI_ hiện có → vault có topics đúng
- Phase 3-5 (A) build tool trên nền data đã clean

## Phases

| Phase | Nhóm | Tên | Trạng thái | Tasks |
|-------|------|-----|------------|-------|
| 01 | B | Schema B Fix (Template + Script + SKILL.md + Backfill 8 files) | ✅ Complete | 4 |
| 02 | C | Good-Inside Topic Backfill | ✅ Complete | 3 |
| 03 | A | Build Vault Index (`build-vault-index.ps1` + `vault_index.json`) | ✅ Complete | 2 |
| 04 | A | Get-DIKWCombo Tool | ✅ Complete | 3 |
| 05 | A | DIKW Bridge SKILL.md Refactor | ✅ Complete | 2 |

**Tổng:** 14 tasks

## Quick Commands
- Bắt đầu Phase 1: `/code phase-01`
- Kiểm tra tiến độ: xem file này
- Lưu context: `/save_brain`
