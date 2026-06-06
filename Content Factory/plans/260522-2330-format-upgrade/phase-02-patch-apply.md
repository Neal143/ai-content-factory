# Phase 02: Patch Patterns + Apply Profile

> **File**: phase-02-patch-apply.md
> **Last update**: 22/05/2026 23:33 (GMT+7)
> **Vai trò**: Chi tiết task sửa patch-patterns.json + apply-profile.ps1
> **Sử dụng khi**: `/code phase-02`
> **Output**: patch-patterns.json có chain sep patterns, apply-profile.ps1 có chain sep logic

Status: ⬜ Pending
Dependencies: Phase 01

## Objective

- Đồng bộ patch-patterns.json với SKILL.md đã sửa (section sep reword + thêm chain sep patterns)
- Thêm chain separator logic vào apply-profile.ps1 (pre-flight check + patch execution)

---

## Task 2.1 — patch-patterns.json: update section sep + thêm chain sep

**File**: `profiles/patch-patterns.json`

> ⚠️ 4 sửa trong cùng 1 file → thực hiện 1 lần edit duy nhất.

### Sửa A — Dòng 28: reword section sep find

BEFORE:
```json
    "fa_section_sep_find": "Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng 2 dòng trống",
```
AFTER:
```json
    "fa_section_sep_find": "Tìm mỗi khối gồm [1 dòng trống + dòng chứa `⁂` + 1 dòng trống], replace TOÀN BỘ khối bằng 2 dòng trống",
```

### Sửa B — Dòng 30: reword section sep replace_marker

BEFORE:
```json
    "fa_section_sep_replace_marker": "Thay mỗi dòng chứa `⁂` bằng marker {marker} cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống",
```
AFTER:
```json
    "fa_section_sep_replace_marker": "Tìm mỗi khối gồm [1 dòng trống + dòng chứa `⁂` + 1 dòng trống], replace TOÀN BỘ khối bằng [{above} dòng trống + marker {marker} + {below} dòng trống]",
```

### Sửa C — Dòng 31: reword section sep replace_blank

BEFORE:
```json
    "fa_section_sep_replace_blank": "Thay mỗi dòng chứa `⁂` (và dòng trống bao quanh) bằng {total} dòng trống",
```
AFTER:
```json
    "fa_section_sep_replace_blank": "Tìm mỗi khối gồm [1 dòng trống + dòng chứa `⁂` + 1 dòng trống], replace TOÀN BỘ khối bằng {total} dòng trống",
```

### Sửa D — Dòng 44: thêm comma + 4 dòng chain sep patterns

BEFORE (dòng 43-45):
```json
    "fa_para_sep_replace_marker": "Giữa các đoạn: chèn marker {marker} cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống",
    "fa_para_sep_replace_blank": "Giữa các đoạn: cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống"
  },
```
AFTER (dòng 43-49):
```json
    "fa_para_sep_replace_marker": "Giữa các đoạn: chèn marker {marker} cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống",
    "fa_para_sep_replace_blank": "Giữa các đoạn: cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống",
    "fa_chain_sep_find": "Giữa các chuỗi câu trong cùng 1 đoạn: giữ nguyên 1 xuống dòng, không thêm dòng trống",
    "_desc_fa_chain_sep": "Đổi khoảng cách giữa các chuỗi câu trong cùng 1 đoạn",
    "fa_chain_sep_replace_marker": "Giữa các chuỗi câu trong cùng 1 đoạn: chèn marker {marker} cách dòng trên {above} dòng trống, cách dòng dưới {below} dòng trống",
    "fa_chain_sep_replace_blank": "Giữa các chuỗi câu trong cùng 1 đoạn: giữa mỗi chuỗi cách {total} dòng trống"
  },
```

---

## Task 2.2 — apply-profile.ps1: thêm chain sep logic

**File**: `.agents/scripts/apply-profile.ps1`

### Sửa A — Pre-flight (thêm sau dòng 214, trước dòng 216)

Anchor BEFORE (dòng 212-216):
```powershell
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_chain_find },
        @{ File = ".agents/skills/voice-writer/references/writing-rules.md"; Pattern = $pat.writing_rules.wr_chain_find }
    )

    if ($p.mode -eq "advanced") {
```
Anchor AFTER (dòng 212-222):
```powershell
        @{ File = ".agents/skills/voice-writer/SKILL.md"; Pattern = $pat.voice_writer.vw_chain_find },
        @{ File = ".agents/skills/voice-writer/references/writing-rules.md"; Pattern = $pat.writing_rules.wr_chain_find }
    )

    # Chain separator (format-agent) - only check when non-default
    $chainTotal = $p.chain_separator.blank_lines_above + $p.chain_separator.blank_lines_below
    if ($p.chain_separator.marker -or $chainTotal -gt 0) {
        $checks += @{ File = ".agents/skills/format-agent/SKILL.md"; Pattern = $pat.format_agent.fa_chain_sep_find }
    }

    if ($p.mode -eq "advanced") {
```

### Sửa B — Patch execution (thêm sau dòng 291, trước dòng 293)

Anchor BEFORE (dòng 290-294):
```powershell
        }
    }

    # Chain instructions (find/replace in SKILL.md)
    Invoke-Patch $vwPath $pat.voice_writer.vw_chain_find ($pat.voice_writer.vw_chain_replace -replace '{n_min}', $p.sentences_per_normal_chain.min -replace '{n_max}', $p.sentences_per_normal_chain.max -replace '{lc_min}', $p.long_chains_per_article.min -replace '{lc_max}', $p.long_chains_per_article.max -replace '{l_min}', $p.sentences_per_long_chain.min -replace '{l_max}', $p.sentences_per_long_chain.max)
```
Anchor AFTER (dòng 290-303):
```powershell
        }
    }

    # Chain separator (format-agent)
    $chainTotal = $p.chain_separator.blank_lines_above + $p.chain_separator.blank_lines_below
    if ($p.chain_separator.marker) {
        Invoke-Patch $faPath $pat.format_agent.fa_chain_sep_find ($pat.format_agent.fa_chain_sep_replace_marker -replace '{marker}', $p.chain_separator.marker -replace '{above}', $p.chain_separator.blank_lines_above -replace '{below}', $p.chain_separator.blank_lines_below)
    } elseif ($chainTotal -gt 0) {
        Invoke-Patch $faPath $pat.format_agent.fa_chain_sep_find ($pat.format_agent.fa_chain_sep_replace_blank -replace '{total}', $chainTotal)
    }

    # Chain instructions (find/replace in SKILL.md)
    Invoke-Patch $vwPath $pat.voice_writer.vw_chain_find ($pat.voice_writer.vw_chain_replace -replace '{n_min}', $p.sentences_per_normal_chain.min -replace '{n_max}', $p.sentences_per_normal_chain.max -replace '{lc_min}', $p.long_chains_per_article.min -replace '{lc_max}', $p.long_chains_per_article.max -replace '{l_min}', $p.sentences_per_long_chain.min -replace '{l_max}', $p.sentences_per_long_chain.max)
```

## Test Criteria

- [ ] `apply-profile.ps1 -Action restore` → "Nothing to restore" hoặc thành công
- [ ] `apply-profile.ps1 -Action patch` → "PATCH COMPLETE"
- [ ] Không lỗi pre-flight liên quan chain_sep

---
Next Phase: [phase-03-dead-code.md](./phase-03-dead-code.md)
