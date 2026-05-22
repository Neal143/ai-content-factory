# File       : resolve-checkpoint.ps1
# Last update: 08/05/2026 06:13 (GMT+7)
# Vai tro    : Tim run folder dang do (in_progress), parse checkpoint + blackboard,
#              tra ve danh sach file can view_file cho agent resume.
# Dung khi   : content-post.md Resume goi 1 LAN khi `/content-post tiep tuc`
# Output     : Exit 0 = OK (key=value) | Exit 1 = FAIL (error message)
# Logic      : Quet output/runs/ -> parse checkpoint.yaml -> parse blackboard -> map phases -> output

$ErrorActionPreference = "Stop"

# --- Mapping phase -> output filename (dong bo voi detect-bypass.ps1 L87-91) ---
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

# --- Quet output/runs/ tim folder co checkpoint.yaml status: in_progress ---
$runsDir = "output/runs"
if (-not (Test-Path $runsDir)) {
    Write-Host "[FAIL] Thu muc '$runsDir' khong ton tai."
    exit 1
}

$runFolders = Get-ChildItem -Path $runsDir -Directory | Sort-Object Name -Descending
$foundFolder = $null
$checkpointData = $null

foreach ($folder in $runFolders) {
    $cpPath = Join-Path $folder.FullName "checkpoint.yaml"
    if (Test-Path $cpPath) {
        $cpContent = Get-Content $cpPath -Raw -Encoding UTF8
        if ($cpContent -match 'status:\s*in_progress') {
            $foundFolder = $folder
            $checkpointData = $cpContent
            break
        }
    }
}

if (-not $foundFolder) {
    Write-Host "[FAIL] Khong tim thay pipeline dang do (checkpoint.yaml voi status: in_progress)."
    exit 1
}

$runFolderRel = "output/runs/$($foundFolder.Name)"

# --- Parse current_phase ---
$currentPhase = ""
if ($checkpointData -match 'current_phase:\s*(\S+)') {
    $currentPhase = $Matches[1]
}

# --- Parse completed_phases ---
$completedPhases = @()
if ($checkpointData -match 'completed_phases:\s*\[([^\]]+)\]') {
    $completedPhases = $Matches[1] -split ',\s*' | ForEach-Object { $_.Trim() }
}

# --- Parse blackboard ---
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

# --- Build LOAD_FILES ---
$loadFiles = @("00-blackboard.yaml")

# Them 00.5-dikw-combo.md neu ton tai
$comboPath = Join-Path $foundFolder.FullName "00.5-dikw-combo.md"
if (Test-Path $comboPath) {
    $loadFiles += "00.5-dikw-combo.md"
}

# Map completed_phases -> filenames (FAIL neu file thieu = corrupted state)
$missingCount = 0
foreach ($phase in $completedPhases) {
    $phaseInt = [int]$phase
    if ($phaseFileMap.ContainsKey($phaseInt)) {
        $fileName = $phaseFileMap[$phaseInt]
        $filePath = Join-Path $foundFolder.FullName $fileName
        if (Test-Path $filePath) {
            $loadFiles += $fileName
        } else {
            Write-Host "[FAIL] File khong ton tai: $runFolderRel/$fileName (checkpoint ghi completed nhung file mat)"
            $missingCount++
        }
    }
}

# --- Check corrupted state ---
if ($missingCount -gt 0) {
    Write-Host "[FAIL] $missingCount file(s) trong completed_phases khong ton tai. State bi corrupted."
    exit 1
}

# --- Output ---
Write-Host "RUN_FOLDER=$runFolderRel"
Write-Host "CURRENT_PHASE=$currentPhase"
Write-Host "PERSONA_PATH=$personaPath"
Write-Host "LOAD_FILES=$($loadFiles -join ',')"
exit 0
