# ------------------------------------------------------------------
# Ten file: detect-structure-changes.ps1
# Last update: 30/10/2026 00:20 (GMT+7)
# Vai tro: Quet git diff HEAD~1 phat hien thay doi trong factory-scaffold
#          template hoac code tao/di chuyen folder/file trong *.ps1.
# Duoc su dung khi: Goi boi workflow /checkpoint (Giai doan 2.5).
# Output: In ra stdout [OK] (Exit 0) hoac [WARNING] kem chi tiet (Exit 1).
# Tom tat logic hoat dong:
#   1. Thiet lap Console OutputEncoding UTF-8 va xac dinh thu muc Content Factory.
#   2. Quet git diff HEAD~1 tren .agents/assets/factory-scaffold/.
#   3. Quet git diff HEAD~1 tren cac file .ps1 trong .agents/ de tim lenh thao tac file/folder.
#   4. Xuat bao cao va tra ve ma thoat tuong ung.
# ------------------------------------------------------------------
param([string]$FactoryRoot = "")

# --- Nhom 1: Dam bao UTF-8 Encoding va xac dinh duong dan goc Content Factory ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

if ($FactoryRoot -and (Test-Path $FactoryRoot)) {
    $workspaceRoot = (Resolve-Path $FactoryRoot).Path
} else {
    $workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
Set-Location -Path $workspaceRoot

# --- Nhom 2: Quet thay doi trong factory-scaffold template ---
$structureDiff = git diff HEAD~1 HEAD --name-only -- ".agents/assets/factory-scaffold/"
$structureChanges = @()
if ($structureDiff) {
    $structureChanges = @($structureDiff | Where-Object { $_ -match '\S' })
}

# --- Nhom 3: Quet code tao/doi ten folder hoac file trong cac script .ps1 cua .agents ---
$fullDiff = git diff HEAD~1 HEAD -- ".agents/*.ps1"
$codeMatches = @()
if ($fullDiff) {
    $codeMatches = @($fullDiff | Where-Object {
        $_ -match '^\+' -and
        $_ -notmatch '^\+\+\+' -and
        ($_ -match 'New-Item.*Directory' -or $_ -match 'New-Item.*File' -or
         $_ -match 'mkdir' -or $_ -match 'CreateDirectory' -or
         $_ -match 'Copy-Item' -or $_ -match 'Rename-Item' -or $_ -match 'Move-Item')
    })
}

# --- Nhom 4: Xuat ket qua kiem tra ---
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
