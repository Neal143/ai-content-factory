param([string]$FactoryRoot)

if (-not $FactoryRoot) {
    $FactoryRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
}

$manifestPath = Join-Path $FactoryRoot ".agents\migrations\structure-manifest.txt"

if (-not (Test-Path $manifestPath)) {
    Write-Host "[FATAL] structure-manifest.txt not found at $manifestPath" -ForegroundColor Red
    exit 1
}

# Đọc cấu trúc chuẩn
$lines = Get-Content $manifestPath | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' }

$missing = @()
foreach ($line in $lines) {
    $folderPath = $line.Trim()
    $fullPath = Join-Path $FactoryRoot $folderPath
    if (-not (Test-Path $fullPath)) {
        $missing += $folderPath
        Write-Host "[MISSING] $folderPath" -ForegroundColor Yellow
    }
}

if ($missing.Count -eq 0) {
    Write-Host "[OK] All $( $lines.Count ) system folders exist." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[WARNING] $( $missing.Count ) system folder(s) missing. Structural change detected." -ForegroundColor Yellow
    exit 1
}