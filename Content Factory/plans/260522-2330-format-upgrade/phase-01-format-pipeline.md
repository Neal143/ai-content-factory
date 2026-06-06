# Phase 01: Format Pipeline (SKILL.md)

> **File**: phase-01-format-pipeline.md
> **Last update**: 22/05/2026 23:33 (GMT+7)
> **Vai trò**: Chi tiết task sửa format-agent/SKILL.md (3 sửa gộp 1 task)
> **Sử dụng khi**: `/code phase-01`
> **Output**: format-agent/SKILL.md canonical được cập nhật

Status: ⬜ Pending
Dependencies: Prerequisites (restore)

## Objective

Cập nhật format-agent/SKILL.md canonical:
- Reword DATA INTEGRITY cho rõ nghĩa (whitespace changes được phép)
- Reword section separator cho chính xác (mô tả khối 3 dòng)
- Thêm chain separator instruction (dòng mới)

## Task 1.1 — format-agent/SKILL.md: 3 sửa đồng thời

**File**: `.agents/skills/format-agent/SKILL.md` (canonical sau restore, 93 dòng)

> ⚠️ 3 thay đổi trong cùng 1 file → thực hiện trong 1 lần edit duy nhất.

### Sửa A — Dòng 4: cập nhật last_update

BEFORE:
```
last_update: 04/05/2026 16:15 (GMT+7)
```
AFTER:
```
last_update: 23/05/2026 (GMT+7)
```

### Sửa B — Dòng 23-25: reword DATA INTEGRITY

BEFORE:
```
> ⛔ **FATAL RULE — DATA INTEGRITY**: TUYỆT ĐỐI KHÔNG thao tác trên text body.
> Chỉ: nhúng YAML frontmatter, copy file, update logs, ghi execution key.
> Nội dung đã qua QA Phase 6. Mọi thay đổi text = vi phạm Data Integrity.
```
AFTER:
```
> ⛔ **FATAL RULE — DATA INTEGRITY**: TUYỆT ĐỐI CẤM chỉnh sửa từ ngữ, câu chữ trong bài viết.
> Được phép: nhúng YAML frontmatter, strip/replace markers, thay đổi whitespace giữa block cấu trúc theo profile, copy file, update logs, ghi execution key.
> Nội dung đã qua QA Phase 6. Thay đổi từ ngữ = vi phạm Data Integrity.
```

### Sửa C — Dòng 59-60: reword section sep + thêm chain sep

BEFORE (2 dòng):
```
      - Marker `⁂`: Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng 2 dòng trống
      - Giữa các đoạn: cách dòng trên 1 dòng trống, cách dòng dưới 0 dòng trống
```
AFTER (3 dòng — thêm 1 dòng mới, tổng file thành 94):
```
      - Marker `⁂`: Tìm mỗi khối gồm [1 dòng trống + dòng chứa `⁂` + 1 dòng trống], replace TOÀN BỘ khối bằng 2 dòng trống
      - Giữa các đoạn: cách dòng trên 1 dòng trống, cách dòng dưới 0 dòng trống
      - Giữa các chuỗi câu trong cùng 1 đoạn: giữ nguyên 1 xuống dòng, không thêm dòng trống
```

## Atomic Check sau sửa

| Pattern key (patch-patterns.json) | Phải khớp substring trong SKILL.md | Dòng |
|---|---|---|
| `fa_section_sep_find` | `"Tìm mỗi khối gồm [1 dòng trống + dòng chứa `⁂` + 1 dòng trống], replace TOÀN BỘ khối bằng 2 dòng trống"` | 59 |
| `fa_para_sep_find` | `"Giữa các đoạn: cách dòng trên 1 dòng trống, cách dòng dưới 0 dòng trống"` | 60 |
| `fa_chain_sep_find` | `"Giữa các chuỗi câu trong cùng 1 đoạn: giữ nguyên 1 xuống dòng, không thêm dòng trống"` | 61 |

## Test Criteria

- [ ] File SKILL.md có 94 dòng (93 + 1 dòng mới)
- [ ] 3 pattern keys trên đều khớp substring trong file
- [ ] `apply-profile.ps1 -Action patch` không fail pre-flight

---
Next Phase: [phase-02-patch-apply.md](./phase-02-patch-apply.md)
