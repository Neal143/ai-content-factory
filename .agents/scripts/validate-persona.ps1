# File       : validate-persona.ps1
# Last update: 07/05/2026 21:44 (GMT+7)
# Vai tro    : Kiem tra 6 file persona YAML ton tai va khong rong.
#              Khi khong truyen PersonaPath, tu dong quet thu muc personas/ de phat hien.
#              Sau validation OK: set PIPELINE_STATUS = CHUA SAN SANG trong content-post.md.
# Dung khi   : content-post.md Buoc 3 goi 1 LAN truoc pipeline
# Output     : Exit 0 = OK (dong cuoi: PERSONA_PATH=...) | Exit 1 = FAIL
# Logic      : Auto-detect persona → Loop 6 files → check exists → check non-empty

param([string]$PersonaPath = "")

$ErrorActionPreference = "Stop"

# --- Auto-detect khi khong truyen PersonaPath ---
if (-not $PersonaPath) {
    $personaRoot = "personas"
    if (-not (Test-Path $personaRoot)) {
        Write-Host "[FAIL] Thu muc '$personaRoot' khong ton tai."
        exit 1
    }
    $subdirs = Get-ChildItem -Path $personaRoot -Directory
    if ($subdirs.Count -eq 0) {
        Write-Host "[FAIL] Khong tim thay persona nao trong '$personaRoot'. Chay /onboarding-persona truoc."
        exit 1
    }
    if ($subdirs.Count -gt 1) {
        Write-Host "[FAIL] Tim thay $($subdirs.Count) persona. Truyen -PersonaPath de chon:"
        foreach ($d in $subdirs) { Write-Host "  - personas/$($d.Name)" }
        exit 1
    }
    $PersonaPath = Join-Path $personaRoot $subdirs[0].Name
    $PersonaPath = $PersonaPath -replace '\\', '/'
    Write-Host "[AUTO] Detected persona: $PersonaPath"
}

# --- Validate 6 files (logic giu nguyen tu phien ban cu) ---
$requiredFiles = @("profile.yaml","voice-dna.yaml","pillars.yaml","audience.yaml","authorities.yaml","scoring-rules.yaml")
$failCount = 0

foreach ($file in $requiredFiles) {
    $filePath = Join-Path $PersonaPath $file
    if (-not (Test-Path $filePath)) {
        Write-Host "[FAIL] File not found: $filePath"; $failCount++; continue
    }

    # Doc file va kiem tra co it nhat 1 top-level field khong rong
    $content = Get-Content $filePath -Encoding UTF8
    $hasNonEmptyField = $false
    for ($i = 0; $i -lt $content.Count; $i++) {
        $line = $content[$i]
        # Bo qua comment, dong trong, dong co indent (child field)
        if ($line -match '^\s*#' -or $line -match '^\s*$' -or $line -match '^\s') { continue }
        # Case A: inline value (vd: "name: Neal")
        if ($line -match '^[a-zA-Z_]\w*\s*:\s*\S') { $hasNonEmptyField = $true; break }
        # Case B: block scalar (vd: "voice:" + dong sau co indent)
        if ($line -match '^[a-zA-Z_]\w*\s*:\s*$') {
            for ($j = $i + 1; $j -lt $content.Count; $j++) {
                if ($content[$j] -match '^\s*#' -or $content[$j] -match '^\s*$') { continue }
                if ($content[$j] -match '^\s+\S') { $hasNonEmptyField = $true }
                break
            }
            if ($hasNonEmptyField) { break }
        }
    }

    if (-not $hasNonEmptyField) { Write-Host "[FAIL] All fields empty: $filePath"; $failCount++ }
    else { Write-Host "[OK] $file" }
}

if ($failCount -gt 0) {
    Write-Host "[FAIL] $failCount file(s) failed. Persona chua du du lieu. Vui long chay /onboarding-persona de hoan thanh Tier 2 truoc."
    exit 1
}
Write-Host "[OK] All 6 persona files validated."

# --- Set PIPELINE_STATUS = CHUA SAN SANG (danh dau pipeline dang chay) ---
$wfPath = ".agents/workflows/content-post.md"
if (Test-Path $wfPath) {
    $wfContent = Get-Content $wfPath -Raw -Encoding UTF8
    $chuaSanSang = "CH" + [char]0x01AF + "A S" + [char]0x1EB4 + "N S" + [char]0x00C0 + "NG"
    $wfContent = $wfContent -replace '(?m)^> PIPELINE_STATUS: .+$', "> PIPELINE_STATUS: $chuaSanSang"
    [System.IO.File]::WriteAllText(
        (Resolve-Path $wfPath).Path, $wfContent,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "[OK] PIPELINE_STATUS set to CHUA SAN SANG."
}

# Dong cuoi cung: Agent parse dong nay de lay PersonaPath
Write-Host "PERSONA_PATH=$PersonaPath"
exit 0
