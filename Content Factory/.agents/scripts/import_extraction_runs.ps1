# Ten file: import_extraction_runs.ps1
# Last update: 19/06/2026 20:55 (GMT+7)
# Vai tro: Import du lieu tu export folder ve dung vi tri trong factory hien tai.
# Su dung khi nao: Duoc goi boi workflow /transfer-extraction (mode Import).
# Output: Cac file duoc di chuyen tu export folder ve vault/.extraction_runs/books/ va vault/02-sources/books/.
# Tom tat logic hoat dong:
#   1. Khoi tao paths, kiem tra export folder ton tai.
#   2. Lap qua tung sach trong export folder:
#      - Doc blackboard de lay cache_file path
#      - Kiem tra conflict (run folder da ton tai hoac cache file da ton tai)
#      - Neu khong conflict: move run folder va move cache file ve dung vi tri
#   3. In summary. Neu co conflict thi bao cho user biet.

param(
    [string[]]$BookFolders,              # (Optional) Chi dinh folder cu the. Neu rong, import tat ca.

    [string]$SourceType = "books",       # Source type subfolder

    [string]$VaultPath = "vault",        # Path tuong doi toi vault

    [string]$ExportPath = ""             # Default: vault/.extraction_runs_export
)

# â”€â”€ Block 1: Khoi tao paths â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

$BaseDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VaultDir = Join-Path $BaseDir $VaultPath

if ([string]::IsNullOrEmpty($ExportPath)) {
    $ExportDir = Join-Path $VaultDir ".extraction_runs_export"
} else {
    $ExportDir = $ExportPath
}

$ExportSourceDir = Join-Path $ExportDir $SourceType
$TargetRunsDir = Join-Path (Join-Path $VaultDir ".extraction_runs") $SourceType
$TargetBooksDir = Join-Path (Join-Path $VaultDir "02-sources") "books"

# Kiem tra export folder ton tai
if (-not (Test-Path $ExportSourceDir)) {
    Write-Host "[ERROR] Export folder khong ton tai: $ExportSourceDir"
    exit 1
}

# Xac dinh danh sach folders can import
if ($BookFolders -and $BookFolders.Count -gt 0) {
    $foldersToImport = $BookFolders
} else {
    # Import tat ca folders trong export
    $foldersToImport = Get-ChildItem -Path $ExportSourceDir -Directory | Select-Object -ExpandProperty Name
}

if ($foldersToImport.Count -eq 0) {
    Write-Host "[WARNING] Khong co folder nao de import trong $ExportSourceDir"
    exit 0
}

# Khoi tao bien dem
$imported = 0
$skipped = 0
$conflicts = [System.Collections.ArrayList]::new()

# â”€â”€ Block 2: Lap qua tung sach â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

foreach ($folder in $foldersToImport) {
    $srcRunDir = Join-Path $ExportSourceDir $folder

    if (-not (Test-Path $srcRunDir)) {
        Write-Host "[SKIP] $folder - khong ton tai trong export folder"
        $skipped++
        continue
    }

    # â”€â”€ Block 2.1: Doc blackboard â”€â”€
    $bbPath = Join-Path $srcRunDir "00-blackboard.yaml"
    if (-not (Test-Path $bbPath)) {
        Write-Host "[SKIP] $folder - 00-blackboard.yaml khong ton tai"
        $skipped++
        continue
    }

    # Parse YAML don gian (flat key-value)
    $bb = @{}
    foreach ($line in (Get-Content $bbPath -Encoding UTF8)) {
        if ($line -match '^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$') {
            $key = $Matches[1]
            $val = $Matches[2].Trim()
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or
                ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            $bb[$key] = $val
        }
    }

    # â”€â”€ Block 2.2: Xac dinh paths dich â”€â”€
    $targetRunDir = Join-Path $TargetRunsDir $folder
    $cacheFileName = if ($bb['cache_file']) {
        [System.IO.Path]::GetFileName($bb['cache_file'])
    } else {
        $null
    }
    $cacheFileSrc = if ($cacheFileName) { Join-Path $srcRunDir $cacheFileName } else { $null }
    $cacheFileDst = if ($cacheFileName) { Join-Path $TargetBooksDir $cacheFileName } else { $null }

    # â”€â”€ Block 2.3: Kiem tra conflict â”€â”€
    $hasConflict = $false

    if (Test-Path $targetRunDir) {
        [void]$conflicts.Add("[$folder] Run folder da ton tai: $targetRunDir")
        $hasConflict = $true
    }

    if ($cacheFileDst -and (Test-Path $cacheFileDst)) {
        [void]$conflicts.Add("[$folder] Cache file da ton tai: $cacheFileDst")
        $hasConflict = $true
    }

    if ($hasConflict) {
        Write-Host "[CONFLICT] $folder - skip (xem chi tiet o cuoi)"
        $skipped++
        continue
    }

    # â”€â”€ Block 2.4: Move cache file truoc, roi move run folder â”€â”€
    # Dam bao target parent dir ton tai
    if (-not (Test-Path $TargetRunsDir)) {
        New-Item -Path $TargetRunsDir -ItemType Directory -Force | Out-Null
    }

    # Move cache file truoc (neu co) de tach ra khoi run folder
    if ($cacheFileSrc -and (Test-Path $cacheFileSrc)) {
        if (-not (Test-Path $TargetBooksDir)) {
            New-Item -Path $TargetBooksDir -ItemType Directory -Force | Out-Null
        }
        Move-Item -Path $cacheFileSrc -Destination $cacheFileDst -Force
    }

    # Move toan bo run folder con lai
    Move-Item -Path $srcRunDir -Destination $targetRunDir -Force

    $bookName = if ($bb['book_name']) { $bb['book_name'] } else { $folder }
    $imported++
    Write-Host "[OK] $bookName ($folder)"
}

# â”€â”€ Block 3: Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Host ""
Write-Host "=== IMPORT COMPLETE ==="
Write-Host "Imported: $imported book(s)"
Write-Host "Skipped:  $skipped book(s)"
Write-Host ""

if ($conflicts.Count -gt 0) {
    Write-Host "CONFLICTS (can user xu ly):"
    foreach ($c in $conflicts) {
        Write-Host "  - $c"
    }
    Write-Host ""
}

# Don dep: xoa export folder neu rong
$remaining = Get-ChildItem -Path $ExportSourceDir -Directory -ErrorAction SilentlyContinue
if ($remaining.Count -eq 0) {
    Remove-Item -Path $ExportDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Export folder da duoc don dep."
}
