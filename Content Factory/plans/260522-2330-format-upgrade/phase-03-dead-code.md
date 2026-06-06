# Phase 03: Dead Code Cleanup

> **File**: phase-03-dead-code.md
> **Last update**: 22/05/2026 23:33 (GMT+7)
> **Vai trò**: Xóa 3 biến thừa trong validate-draft.ps1
> **Sử dụng khi**: `/code phase-03`
> **Output**: validate-draft.ps1 sạch dead code

Status: ⬜ Pending
Dependencies: Không (độc lập)

## Objective

Xóa 3 biến `$cfgSection*` trong validate-draft.ps1 — đã verify không dùng ở bất kỳ đâu trong file (Select-String confirmed).

## Task 3.1 — validate-draft.ps1: xóa 3 biến thừa

**File**: `.agents/skills/voice-writer/scripts/validate-draft.ps1`

**XÓA dòng 49-51** (3 dòng liên tiếp):
```powershell
$cfgSectionMarker = if ($profile) { $profile.section_separator.marker } else { [string][char]0x2042 }
$cfgSectionBlankAbove = if ($profile) { $profile.section_separator.blank_lines_above } else { 1 }
$cfgSectionBlankBelow = if ($profile) { $profile.section_separator.blank_lines_below } else { 1 }
```

**GIỮ NGUYÊN dòng 52-56** — trong đó `$cfgVeryShortThreshold` đang dùng ở dòng 445, 454.

## Test Criteria

- [ ] File chạy không lỗi: `validate-draft.ps1 -DraftPath "output/runs/2026-05-21_nao_bo_tre_em/05-draft.md"`
- [ ] Không còn chuỗi `$cfgSection` trong file (grep verify)

---
Next Phase: [phase-04-agent-cleanup.md](./phase-04-agent-cleanup.md)
