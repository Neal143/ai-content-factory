param([string]$FactoryRoot)

$workspaceRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location -Path $workspaceRoot

# 1. Quét thay đổi trong file structure-manifest.txt
$manifestDiff = git diff HEAD~1 -- .agents/migrations/structure-manifest.txt
$newManifestLines = @()
if ($manifestDiff) {
    $newManifestLines = $manifestDiff | Where-Object { $_ -match '^\+(?!\+)' -and $_ -notmatch '^\+\s*#' -and $_ -match '\S' }
}

# 2. Quét các dòng code tạo/đổi tên folder trong toàn bộ commit CHỈ trên file .ps1
$fullDiff = git diff HEAD~1 -- '*.ps1'
$codeMatches = @()
if ($fullDiff) {
    $codeMatches = $fullDiff | Where-Object { 
        $_ -match '^\+' -and 
        $_ -notmatch '^\+\+\+' -and 
        ($_ -match 'New-Item.*Directory' -or $_ -match 'mkdir' -or $_ -match 'CreateDirectory' -or $_ -match 'Rename-Item' -or $_ -match 'Move-Item')
    }
}

if ($newManifestLines.Count -gt 0 -or $codeMatches.Count -gt 0) {
    Write-Host "[WARNING] Structural change detected in commit HEAD~1" -ForegroundColor Yellow
    
    if ($newManifestLines.Count -gt 0) {
        Write-Host "`n[+] New folders added to structure-manifest.txt:" -ForegroundColor Cyan
        $newManifestLines | ForEach-Object { Write-Host ("  " + $_) }
    }
    
    if ($codeMatches.Count -gt 0) {
        Write-Host "`n[+] Folder manipulation code detected in diff:" -ForegroundColor Cyan
        $codeMatches | ForEach-Object { Write-Host ("  " + $_.Trim()) }
    }
    
    Write-Host "`nAction required: Ask user if migration script is needed." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "[OK] No structural folder changes detected in the recent commit." -ForegroundColor Green
    exit 0
}