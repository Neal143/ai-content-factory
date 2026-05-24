# File       : generate-phase-key.ps1
# Last update: 24/05/2026 13:30 (GMT+7)
# Vai tro    : Tao random key, inject vao 9 SKILL.md + 8 ref files + 5 persona files
#              Sau khi inject xong: set PIPELINE_STATUS = SAN SANG trong content-post.md.
# Dung khi   : (1) User chay thu cong lan dau / sau crash. (2) detect-bypass.ps1 goi tu dong sau Phase 7.
# Output     : Exit 0 = OK | Exit 1 = FAIL
# Logic      : Loop SKILL -> ref -> persona: moi file tao 8-char hex key -> replace placeholder -> set status

param(
    [string]$SkillDir = ".agents/skills",
    [string]$PersonaPath = ""
)

$ErrorActionPreference = "Stop"

# --- Auto-detect khi khong truyen PersonaPath ---
if (-not $PersonaPath) {
    $personaRoot = "personas"
    if (Test-Path $personaRoot) {
        $subdirs = Get-ChildItem -Path $personaRoot -Directory
        if ($subdirs.Count -eq 1) {
            $PersonaPath = Join-Path $personaRoot $subdirs[0].Name
            Write-Host "[AUTO] Detected persona: $PersonaPath"
        }
    }
}

# --- Mapping 7 skill folders ---
$skillFolders = @(
    "semantic-router",
    "idea-curator",
    "insight-agent",
    "hook-engineer",
    "structure-designer",
    "persona-loader",
    "voice-writer",
    "qa-checker",
    "format-agent"
)

$failCount = 0
$pattern = '(?m)^> EXECUTION_KEY: .+$'

foreach ($folder in $skillFolders) {
    $skillPath = Join-Path $SkillDir "$folder/SKILL.md"

    if (-not (Test-Path $skillPath)) {
        Write-Host "[FAIL] SKILL.md not found: $skillPath"
        $failCount++
        continue
    }

    # Tao random key 8 ky tu hex (unique cho moi SKILL)
    $key = -join (('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f') | Get-Random -Count 8)

    $content = Get-Content $skillPath -Raw -Encoding UTF8
    if ($content -match $pattern) {
        $content = $content -replace $pattern, "> EXECUTION_KEY: $key"
        [System.IO.File]::WriteAllText(
            (Resolve-Path $skillPath).Path,
            $content,
            [System.Text.UTF8Encoding]::new($false)
        )
        Write-Host "[OK] $folder key: $key"
    }
    else {
        Write-Host "[FAIL] Missing EXECUTION_KEY placeholder: $skillPath"
        $failCount++
    }
}

# --- Mapping 3 reference files (voice-writer Phase 5) ---
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

$refPattern = '(?m)^> FILE_KEY: .+$'

foreach ($rf in $refFiles) {
    if (-not (Test-Path $rf.Path)) {
        Write-Host "[FAIL] Reference file not found: $($rf.Path)"
        $failCount++
        continue
    }
    $key = -join (('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f') | Get-Random -Count 8)
    $content = Get-Content $rf.Path -Raw -Encoding UTF8
    if ($content -match $refPattern) {
        $content = $content -replace $refPattern, "> FILE_KEY: $key"
        [System.IO.File]::WriteAllText(
            (Resolve-Path $rf.Path).Path,
            $content,
            [System.Text.UTF8Encoding]::new($false)
        )
        Write-Host "[OK] $($rf.Label) file-key: $key"
    }
    else {
        Write-Host "[FAIL] Missing FILE_KEY placeholder: $($rf.Path)"
        $failCount++
    }
}

# --- Mapping 2 persona config files (qa-checker Phase 6) ---
if ($PersonaPath) {
    $personaFiles = @(
        @{ Path = "$PersonaPath/voice-dna.yaml";     Label = "voice-dna"     },
        @{ Path = "$PersonaPath/scoring-rules.yaml";  Label = "scoring-rules" },
        @{ Path = "$PersonaPath/audience.yaml";       Label = "audience"      },
        @{ Path = "$PersonaPath/profile.yaml";        Label = "profile"       },
        @{ Path = "$PersonaPath/authorities.yaml";    Label = "authorities"   }
    )

    $personaPattern = '(?m)^# FILE_KEY: .+$'

    foreach ($pf in $personaFiles) {
        if (-not (Test-Path $pf.Path)) {
            Write-Host "[FAIL] Persona file not found: $($pf.Path)"
            $failCount++
            continue
        }
        $key = -join (('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f') | Get-Random -Count 8)
        $content = Get-Content $pf.Path -Raw -Encoding UTF8
        if ($content -match $personaPattern) {
            $content = $content -replace $personaPattern, "# FILE_KEY: $key"
            [System.IO.File]::WriteAllText(
                (Resolve-Path $pf.Path).Path,
                $content,
                [System.Text.UTF8Encoding]::new($false)
            )
            Write-Host "[OK] $($pf.Label) file-key: $key"
        }
        else {
            Write-Host "[FAIL] Missing FILE_KEY placeholder: $($pf.Path)"
            $failCount++
        }
    }
}

if ($failCount -gt 0) {
    Write-Host "[FAIL] $failCount file(s) failed."
    exit 1
}
$totalKeys = if ($PersonaPath) { 22 } else { 17 }
$detail = if ($PersonaPath) { "9 SKILL + 8 ref + 5 persona" } else { "9 SKILL + 8 ref" }
Write-Host "[OK] All $totalKeys keys injected. ($detail)"

# --- Set PIPELINE_STATUS = SAN SANG ---
$wfPath = ".agents/workflows/content-post.md"
if (Test-Path $wfPath) {
    $wfContent = Get-Content $wfPath -Raw -Encoding UTF8
    if ($wfContent -match '(?m)^> PIPELINE_STATUS: .+$') {
        $sanSang = "S" + [char]0x1EB4 + "N S" + [char]0x00C0 + "NG"
        $wfContent = $wfContent -replace '(?m)^> PIPELINE_STATUS: .+$', "> PIPELINE_STATUS: $sanSang"
        [System.IO.File]::WriteAllText(
            (Resolve-Path $wfPath).Path, $wfContent,
            [System.Text.UTF8Encoding]::new($false)
        )
        Write-Host "[OK] PIPELINE_STATUS set to SAN SANG."
    }
}

exit 0
