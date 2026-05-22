# File       : validate-persona-pack.ps1
# Last update: 06/05/2026 22:00 (GMT+7)
# Vai tro    : Kiem tra 04.5-persona-pack.md hop le + persona_keys khop + rotate voice-dna key
# Dung khi   : detect-bypass.ps1 Check 5 re-run cho Phase 45
# Output     : Exit 0 = PASS | Exit 1 = FAIL
# Logic      : Check exists -> sections -> fields -> keys match -> idempotent rotate

param(
    [Parameter(Mandatory=$true)][string]$PackPath,
    [string]$PersonaPath = ""
)

$ErrorActionPreference = "Stop"
$failed = $false

# --- Check 1: File ton tai va khong rong ---
if (-not (Test-Path $PackPath)) {
    Write-Host "[FAIL] 04.5-persona-pack.md not found: $PackPath"; exit 1
}
$content = Get-Content $PackPath -Raw -Encoding UTF8
if ($content.Trim().Length -eq 0) {
    Write-Host "[FAIL] 04.5-persona-pack.md is empty"; exit 1
}

# --- Check 2: 4 section headers phai co mat ---
$requiredSections = @("[Voice DNA]", "[JTBD Anchor]", "[Profile]", "[Authorities]")
foreach ($section in $requiredSections) {
    if ($content -notmatch [regex]::Escape($section)) {
        Write-Host "[FAIL] Missing section: $section"; $failed = $true
    }
}

# --- Check 3: Fields quan trong khong rong ---
$criticalPatterns = @(
    @{ Name = "Pronouns";      Pattern = 'Pronouns:\s*self=\S+' },
    @{ Name = "Job Performer";  Pattern = 'Job Performer:\s*\S+' },
    @{ Name = "Name";           Pattern = 'Name:\s*\S+' }
)
foreach ($cp in $criticalPatterns) {
    if ($content -notmatch $cp.Pattern) {
        Write-Host "[FAIL] Critical field empty or missing: $($cp.Name)"; $failed = $true
    }
}

# --- Check 4: persona_keys du 3 key va khop file goc ---
if ($content -match 'persona_keys:\s*(.+?)-->') {
    $keysLine = $Matches[1].Trim()
    $keyMap = @{}
    foreach ($pair in ($keysLine -split ',\s*')) {
        if ($pair -match '(\S+)=(\S+)') { $keyMap[$Matches[1]] = $Matches[2] }
    }

    $expectedFiles = @(
        @{ Label = "voice-dna";   File = "voice-dna.yaml" },
        @{ Label = "profile";     File = "profile.yaml" },
        @{ Label = "authorities"; File = "authorities.yaml" }
    )

    # Chi verify keys khi co PersonaPath
    if ($PersonaPath) {
        foreach ($ef in $expectedFiles) {
            $yamlPath = Join-Path $PersonaPath $ef.File
            if (-not (Test-Path $yamlPath)) {
                Write-Host "[FAIL] Persona file not found: $yamlPath"; $failed = $true; continue
            }
            $yamlContent = Get-Content $yamlPath -Raw -Encoding UTF8
            $sourceKey = ""
            if ($yamlContent -match '# FILE_KEY:\s*(\S+)') { $sourceKey = $Matches[1] }

            $packKey = if ($keyMap.ContainsKey($ef.Label)) { $keyMap[$ef.Label] } else { "" }

            if ($sourceKey -eq "" -or $packKey -eq "") {
                Write-Host "[FAIL] Missing key for $($ef.Label): source=$sourceKey pack=$packKey"; $failed = $true
            }
            elseif ($sourceKey -ne $packKey) {
                Write-Host "[FAIL] Key mismatch $($ef.Label): source=$sourceKey pack=$packKey"; $failed = $true
            }
            else { Write-Host "[OK] $($ef.Label) key verified" }
        }
    }
} else {
    Write-Host "[FAIL] Missing persona_keys line in pack"; $failed = $true
}

if ($failed) { exit 1 }

# --- Check 5: Rotate voice-dna.yaml FILE_KEY (Idempotent) ---
# Muc dich: Ep Phase 6 (QA Checker) phai doc lai voice-dna.yaml that su de lay key moi.
# Tu khoa: Chi rotate khi Phase 6 CHUA chay (06-qa-result.md chua ton tai).
# Dong bo: Sau khi rotate source, cap nhat luon vao Pack de Sentinel 45 re-run khong bi mismatch.
if ($PersonaPath) {
    $vdnPath = Join-Path $PersonaPath "voice-dna.yaml"
    $runFolder = Split-Path $PackPath -Parent
    $qaResultPath = Join-Path $runFolder "06-qa-result.md"

    if ((Test-Path $vdnPath) -and (-not (Test-Path $qaResultPath))) {
        $newKey = -join (('0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f') | Get-Random -Count 8)

        # 1. Update source yaml
        $vdnContent = Get-Content $vdnPath -Raw -Encoding UTF8
        if ($vdnContent -match '(?m)^# FILE_KEY: .+$') {
            $vdnContent = $vdnContent -replace '(?m)^# FILE_KEY: .+$', "# FILE_KEY: $newKey"
            [System.IO.File]::WriteAllText(
                (Resolve-Path $vdnPath).Path, $vdnContent, [System.Text.UTF8Encoding]::new($false)
            )

            # 2. Update Pack de giu idempotency cho cac lan re-run Sentinel 45
            $packContent = Get-Content $PackPath -Raw -Encoding UTF8
            $packContent = $packContent -replace 'voice-dna=[^,\s>]+', "voice-dna=$newKey"
            [System.IO.File]::WriteAllText(
                (Resolve-Path $PackPath).Path, $packContent, [System.Text.UTF8Encoding]::new($false)
            )

            Write-Host "[OK] Rotated voice-dna.yaml FILE_KEY -> $newKey"
        }
    } else {
        Write-Host "[INFO] Skip rotation: Phase 6 already started or voice-dna.yaml not found."
    }
}

Write-Host "[PASS] Persona Pack validated."; exit 0
