# Phase 02: Script Comments Sync

> File: plans/230523-1132-profile-questions/phase-02-comments.md
> Last update: 23/05/2026 21:55 (GMT+7)

## Bối cảnh

Comments R1-R8 trong `apply-profile.ps1` tham chiếu B/A numbers cũ.
Sau renumber, comments sẽ khiến AI/dev hiểu sai validation rule → sửa nhầm → gãy hệ thống.
Logic code KHÔNG đổi, chỉ sửa comments.

## Task 1: Cập nhật comments R1-R8

**File**: `.agents/scripts/apply-profile.ps1`

Chỉ sửa **text trong comments**, KHÔNG sửa code.

| Dòng | Trước | Sau |
|------|-------|-----|
| 98 | `# B6/B7 can be null` | `# B8/B9 can be null` |
| 103 | `# --- R1: B1 != B2 ---` | `# --- R1: B1 != B3 ---` |
| 115 | `# --- R2: B2 != B4 ---` | `# --- R2: B3 != B6 ---` |
| 127 | `# --- R3: B3.max >= B5.max ---` | `# --- R3: B5.max >= B7.max ---` |
| 132 | `# --- R4: B3.max >= B6.max ---` | `# --- R4: B5.max >= B8.max ---` |
| 139 | `# --- R5: B6.min > B5.max ---` | `# --- R5: B8.min > B7.max ---` |
| 146 | `# --- R6, R7, R8: advanced mode only ---` | Giữ nguyên |
| 148 | `# R6: A4.min >= sum(A5.min)` | `# R6: A2.min >= sum(A3.min)` |
| 157 | `# R7: A4.max <= sum(A5.max) * 1.1` | `# R7: A2.max <= sum(A3.max) * 1.1` |
| 167 | `# R8: A6.max <= A4.max` | `# R8: A4.max <= A2.max` |

**Lưu ý**: Biến `$b1`, `$b2`, `$b4` (dòng 104, 116) là tên biến nội bộ PowerShell, KHÔNG sửa.

## Verification

1. ✅ Chỉ sửa comments, 0 dòng code thay đổi
2. ✅ B/A numbers trong comments khớp profile-selector B/A mới
3. ✅ Variable names ($b1, $b2, $b4) giữ nguyên — chỉ là tên biến nội bộ
4. ✅ Đã bao gồm dòng 98 (`B6/B7` → `B8/B9`)
