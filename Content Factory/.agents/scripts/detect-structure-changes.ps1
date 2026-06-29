# ------------------------------------------------------------------
# detect-structure-changes.ps1
# Last update: 30/06/2026 00:55 (GMT+7)
# Role: Quet git diff HEAD~1 phat hien thay doi trong factory-scaffold
#       template hoac code tao folder/file trong *.ps1.
# When: Goi boi /checkpoint workflow (Giai doan 2.5).
# Output: [OK] hoac [WARNING] + chi tiet. Exit 0 = clean, Exit 1 = detected.
# Logic: Scan git diff cho .agents/assets/factory-scaffold/ ->
#        scan git diff cho folder/file creation code in *.ps1 ->
#        report findings.
# ------------------------------------------------------------------
param([string]$FactoryRoot)

$workspaceRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location -Path $workspaceRoot

# 1. Quet thay doi trong factory-scaffold template
$structureDiff = git diff HEAD~1 --name-only -- .agents/assets/factory-scaffold/
$structureChanges = @()
if ($structureDiff) {
    $structureChanges = @($structureDiff | Where-Object { $_ -match '\S' })
}

# 2. Quet code tao/doi ten folder HOAC file trong toan bo commit CHI tren file .ps1
$fullDiff = git diff HEAD~1 -- '*.ps1'
$codeMatches = @()
if ($fullDiff) {
    $codeMatches = $fullDiff | Where-Object {
        $_ -match '^\+' -and
        $_ -notmatch '^\+\+\+' -and
        ($_ -match 'New-Item.*Directory' -or $_ -match 'New-Item.*File' -or
         $_ -match 'mkdir' -or $_ -match 'CreateDirectory' -or
         $_ -match 'Copy-Item' -or $_ -match 'Rename-Item' -or $_ -match 'Move-Item')
    }
}

if ($structureChanges.Count -gt 0 -or $codeMatches.Count -gt 0) {
    Write-Host "[WARNING] Structural change detected in commit HEAD~1" -ForegroundColor Yellow

    if ($structureChanges.Count -gt 0) {
        Write-Host "`n[+] Changed files in .agents/assets/factory-scaffold/:" -ForegroundColor Cyan
        $structureChanges | ForEach-Object { Write-Host ("  " + $_) }
    }

    if ($codeMatches.Count -gt 0) {
        Write-Host "`n[+] Folder/file manipulation code detected in .ps1 diff:" -ForegroundColor Cyan
        $codeMatches | ForEach-Object { Write-Host ("  " + $_.Trim()) }
    }

    Write-Host "`nAction required: Check if migration script is needed for rename/move operations." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "[OK] No structural changes detected in the recent commit." -ForegroundColor Green
    exit 0
}