$ErrorActionPreference = "Stop"

# --- Mapping phase -> output filename ---
$phaseFileMap = @{
    1  = "01-idea-brief.md"
    2  = "02-research-brief.md"
    3  = "03-hook.md"
    4  = "04-outline.md"
    5  = "05-draft.md"
    6  = "06-qa-result.md"
    7  = "07-final.md"
    45 = "04.5-persona-pack.md"
}

$runsDir = "output/runs"
if (-not (Test-Path $runsDir)) {
    Write-Host "[FAIL] Thu muc '$runsDir' khong ton tai."
    exit 1
}

# Lay run folder gan nhat
$runFolders = Get-ChildItem -Path $runsDir -Directory | Sort-Object CreationTime -Descending
$foundFolder = $null
$sentinelData = $null

foreach ($folder in $runFolders) {
    $dataPath = Join-Path $folder.FullName ".temp/sentinel-data.json"
    if (Test-Path $dataPath) {
        $foundFolder = $folder
        $raw = Get-Content $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $sentinelData = @{}
        foreach ($prop in $raw.PSObject.Properties) { $sentinelData[$prop.Name] = $prop.Value }
        break
    }
}

if (-not $foundFolder -or -not $sentinelData) {
    Write-Host "[FAIL] Khong tim thay lich su chay (sentinel-data.json) trong tat ca cac thu muc."
    exit 1
}

# Kiem tra da hoan thanh chua
if ($sentinelData.ContainsKey("7") -and $sentinelData["7"].status -eq "PASS") {
    Write-Host "[FAIL] Pipeline gan nhat ($($foundFolder.Name)) da hoan thanh (Phase 7 PASS). Khong co pipeline nao dang do."
    exit 1
}

# Tim Phase cao nhat co status PASS
$validPhases = @(0, 1, 2, 3, 4, 45, 5, 6)
$currentPhase = -1
foreach ($p in $validPhases) {
    $pk = [string]$p
    if ($sentinelData.ContainsKey($pk) -and $sentinelData[$pk].status -eq "PASS") {
        $currentPhase = $p
    }
}

if ($currentPhase -eq -1) {
    Write-Host "[FAIL] Khong tim thay Phase nao PASS trong sentinel-data.json. He thong bi loi ngay tu dau."
    exit 1
}

$runFolderRel = "output/runs/$($foundFolder.Name)"

# Parse blackboard
$bbPath = Join-Path $foundFolder.FullName "00-blackboard.yaml"
if (-not (Test-Path $bbPath)) {
    Write-Host "[FAIL] 00-blackboard.yaml khong ton tai trong $runFolderRel."
    exit 1
}
$bbContent = Get-Content $bbPath -Raw -Encoding UTF8
$personaPath = ""
if ($bbContent -match 'Persona_Path:\s*"?([^"\r\n]+)"?') {
    $personaPath = $Matches[1].Trim()
}

# Build LOAD_FILES
$loadFiles = @("00-blackboard.yaml")
$comboPath = Join-Path $foundFolder.FullName "00.5-dikw-combo.md"
if (Test-Path $comboPath) {
    $loadFiles += "00.5-dikw-combo.md"
}

# Nop cac output theo tien do
foreach ($p in $validPhases) {
    if ($p -le $currentPhase -and $phaseFileMap.ContainsKey($p)) {
        $fileName = $phaseFileMap[$p]
        $filePath = Join-Path $foundFolder.FullName $fileName
        if (Test-Path $filePath) {
            $loadFiles += $fileName
        }
    }
}

Write-Host "RUN_FOLDER=$runFolderRel"
Write-Host "CURRENT_PHASE=$currentPhase"
Write-Host "PERSONA_PATH=$personaPath"
Write-Host "LOAD_FILES=$($loadFiles -join ',')"
exit 0
