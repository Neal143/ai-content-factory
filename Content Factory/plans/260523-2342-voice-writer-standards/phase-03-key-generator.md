# Phase 03: Key Generator Update

> **File:** plans/260523-2342-voice-writer-standards/phase-03-key-generator.md
> **Last update:** 24/05/2026 13:24 (GMT+7)

Status: ✅ Complete
Dependencies: Phase 01 (Task 1.6 bắt buộc phải chạy trước để có placeholder `> FILE_KEY: PENDING`)

## Objective

Cập nhật `generate-phase-key.ps1` để sinh key cho 5 file chuẩn tiếng Việt mới, phục vụ cơ chế chống hallucinate/bypass của hệ thống.

## Target File

`.agents/scripts/generate-phase-key.ps1`

## Tasks

### Task 1: Cập nhật mảng `$refFiles`

**Vị trí:** Dòng 73-77.

**Trước:**
```powershell
$refFiles = @(
    @{ Path = ".agents/skills/voice-writer/references/writing-rules.md";     Label = "writing-rules"    },
    @{ Path = ".agents/skills/voice-writer/references/anti-ai-patterns.md";  Label = "anti-ai-patterns" },
    @{ Path = ".agents/skills/voice-writer/references/english-blacklist.md"; Label = "english-blacklist" }
)
```

**Sau:**
```powershell
$refFiles = @(
    @{ Path = ".agents/skills/voice-writer/references/writing-rules.md";     Label = "writing-rules"    },
    @{ Path = ".agents/skills/voice-writer/references/anti-ai-patterns.md";  Label = "anti-ai-patterns" },
    @{ Path = ".agents/skills/voice-writer/references/english-blacklist.md"; Label = "english-blacklist" },
    @{ Path = ".agents/skills/voice-writer/references/capitalization.md";    Label = "capitalization"   },
    @{ Path = ".agents/skills/voice-writer/references/english-mixing.md";    Label = "english-mixing"   },
    @{ Path = ".agents/skills/voice-writer/references/prose-format.md";      Label = "prose-format"     },
    @{ Path = ".agents/skills/voice-writer/references/punctuation.md";       Label = "punctuation"      },
    @{ Path = ".agents/skills/voice-writer/references/ai-detection.md";      Label = "ai-detection"     }
)
```

### Task 2: Cập nhật Text Report

**Vị trí:** Dòng 144-145.

**Trước:**
```powershell
$totalKeys = if ($PersonaPath) { 17 } else { 12 }
$detail = if ($PersonaPath) { "9 SKILL + 3 ref + 5 persona" } else { "9 SKILL + 3 ref" }
```

**Sau:**
```powershell
$totalKeys = if ($PersonaPath) { 22 } else { 17 }
$detail = if ($PersonaPath) { "9 SKILL + 8 ref + 5 persona" } else { "9 SKILL + 8 ref" }
```

## Verification

- ✅ Chạy `generate-phase-key.ps1`, output report có dòng `[OK] All 17 keys injected` (hoặc 22 nếu có persona parameter).
- ✅ Tất cả 5 file trong `references/` đều đã có mã hex 8 ký tự thay thế cho `PENDING`.

---
Previous Phase: phase-02-script-update.md
