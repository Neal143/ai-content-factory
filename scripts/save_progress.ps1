# ============================================================
# Ten file: .agents/scripts/save_progress.ps1
# Last update: 30/10/2026 00:20 (GMT+7)
# Vai tro: Quan ly snapshot du lieu cho Content Factory bang kho Git doc lap (.save-data/).
# Duoc su dung khi: Goi boi Agent (SKILL.md hoac /checkpoint), hoac goi tu dong tu auto_checkpoint.py.
# Output: Git commits/tags trong .save-data/ va cap nhat lich su trong progress-checkpoints.md.
# Tom tat logic hoat dong:
#   1. Thiet lap Console OutputEncoding UTF-8 de doc stdout cua Git khong bi loi font (CodePage 437).
#   2. Dung git --git-dir=.save-data --work-tree=<FactoryRoot> de cach ly kho du lieu khoi Git goc.
#   3. Dong bo danh sach info/exclude va go bo khoi index cac file tam/backup/workspace.
#   4. Ho tro 3 hanh dong: save (tu dong xu ly trung nhan, phuc hoi log neu mat, commit+tag+log),
#      list (xem hoac tai tao log tu Git tags), rollback (auto-save kem ghi log, bao toan workspace.json
#      trong RAM qua reset --hard, goi lai Sync-SaveExclude va sync-factory-scaffold.ps1).
# ============================================================

param(
    [Parameter(Mandatory)]
    [ValidateSet("save", "list", "rollback")]
    [string]$Action,

    [string]$Label,
    [string]$Description
)

# --- Nhom 1: Thiet lap UTF-8 Encoding va xac dinh duong dan goc Content Factory ---
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$FactoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$GitDir = Join-Path $FactoryRoot ".save-data"
$SaveProgressFile = Join-Path $FactoryRoot "progress-checkpoints.md"

# --- Nhom 2: Helper chay Git voi --git-dir va --work-tree rieng biet ---
function Invoke-SaveGit {
    param([Parameter(ValueFromRemainingArguments)][string[]]$GitArgs)
    & git --git-dir="$GitDir" --work-tree="$FactoryRoot" @GitArgs
}

# --- Nhom 3: Helper lay thoi gian hien tai theo mui gio GMT+7 ---
function Get-VNTimestamp {
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("SE Asia Standard Time")
    return [System.TimeZoneInfo]::ConvertTime([System.DateTimeOffset]::Now, $tz)
}

# --- Nhom 4: Helper dong bo info/exclude va go cache cac file tam da lo bi track ---
function Sync-SaveExclude {
    if (-not (Test-Path $GitDir)) { return }

    $excludePath = Join-Path (Join-Path $GitDir "info") "exclude"
    $excludeContent = @(
        "# Excluded from progress-checkpoint snapshots"
        ".agents/"
        ".agents_update_temp/"
        ".update_backups/"
        ".save-data/"
        ".gitignore"
        "progress-checkpoints.md"
        "__pycache__/"
        "*.pyc"
        "vault/.tmp/"
        "vault/.curation_temp/"
        "vault/.obsidian/workspace.json"
        "vault/.obsidian/workspace-mobile.json"
        "vault/.content-pipeline/fb_cache/"
        "vault/.content-pipeline/fb-tracker-state.json"
    )
    [System.IO.File]::WriteAllLines($excludePath, $excludeContent, [System.Text.Encoding]::UTF8)

    # Go khoi Git index cac file tam/workspace neu truoc day hoac sau reset --hard bi track lai
    $cachedPathsToUntrack = @(
        "vault/.obsidian/workspace.json",
        "vault/.obsidian/workspace-mobile.json",
        "vault/.curation_temp",
        "vault/.tmp",
        ".update_backups",
        ".agents_update_temp",
        "vault/.content-pipeline/fb_cache",
        "vault/.content-pipeline/fb-tracker-state.json"
    )
    Invoke-SaveGit rm -r --cached --ignore-unmatch @cachedPathsToUntrack 2>$null | Out-Null
}

# --- Nhom 5: Helper phuc hoi file progress-checkpoints.md tu annotated tags ---
function Restore-ProgressLog {
    if (-not (Test-Path $GitDir)) { return }

    $tagLines = @(Invoke-SaveGit for-each-ref --sort=-creatordate "refs/tags/snap/*" --format="%(refname:short)|%(creatordate:format:%d/%m/%Y %H:%M)|%(*objectname:short)|%(contents:subject)" 2>$null)
    if (-not $tagLines -or $tagLines.Count -eq 0) {
        Write-Host "[INFO] No tags found in .save-data. Nothing to rebuild."
        return
    }

    $header = "# Progress Checkpoints"
    $entries = @()

    foreach ($line in $tagLines) {
        if (-not $line) { continue }
        $parts = $line -split '\|', 4
        if ($parts.Count -lt 4) { continue }
        $tagName = $parts[0]
        $dateStr = $parts[1]
        $hash    = $parts[2]
        $desc    = $parts[3]
        $label   = $tagName -replace '^snap/', ''

        $entryBlock = @(
            "",
            "### $dateStr (GMT+7)",
            "#### $label",
            "- **Tag:** ``$tagName``",
            "- **Hash:** ``$hash``",
            "- **Description:** $desc"
        ) -join "`r`n"
        $entries += $entryBlock
    }

    $content = (@($header) + $entries) -join "`r`n"
    [System.IO.File]::WriteAllText($SaveProgressFile, $content + "`r`n", [System.Text.Encoding]::UTF8)
    Write-Host "[OK] Rebuilt progress-checkpoints.md from $($entries.Count) tags."
}

# --- Nhom 6: Helper chen 1 ban ghi moi len dau file progress-checkpoints.md (chong loi CRLF) ---
function Add-ProgressLogEntry {
    param(
        [string]$EntryLabel,
        [string]$EntryHash,
        [string]$EntryDesc,
        [System.DateTimeOffset]$EntryTime
    )

    $dateStr = $EntryTime.ToString("dd/MM/yyyy HH:mm")
    $newLines = @(
        "",
        "### $dateStr (GMT+7)",
        "#### $EntryLabel",
        "- **Tag:** ``snap/$EntryLabel``",
        "- **Hash:** ``$EntryHash``",
        "- **Description:** $EntryDesc"
    )

    if (-not (Test-Path $SaveProgressFile) -or (Get-Item $SaveProgressFile).Length -eq 0) {
        $header = "# Progress Checkpoints"
        [System.IO.File]::WriteAllText($SaveProgressFile, $header, [System.Text.Encoding]::UTF8)
    }

    $lines = [System.IO.File]::ReadAllLines($SaveProgressFile, [System.Text.Encoding]::UTF8)
    $headerLine = if ($lines.Length -gt 0) { $lines[0] } else { "# Progress Checkpoints" }
    $restLines = if ($lines.Length -gt 1) { $lines[1..($lines.Length - 1)] } else { @() }
    $allContent = @($headerLine) + $newLines + $restLines
    [System.IO.File]::WriteAllLines($SaveProgressFile, $allContent, [System.Text.Encoding]::UTF8)
}

# --- Nhom 7: Helper khoi tao kho .save-data neu chua ton tai ---
function Initialize-SaveRepo {
    if (-not (Test-Path $GitDir)) {
        Write-Host "[INIT] Creating .save-data/ repository..."
        Invoke-SaveGit init 2>$null | Out-Null
        Invoke-SaveGit config --unset core.worktree 2>$null | Out-Null
        Invoke-SaveGit config user.email "factory@local" 2>$null | Out-Null
        Invoke-SaveGit config user.name "Content Factory" 2>$null | Out-Null
        Invoke-SaveGit config core.longpaths true 2>$null | Out-Null
        Write-Host "[INIT] Repository initialized."
    }
    Sync-SaveExclude
}

# ============================================================
# NHOM 8: ACTION SAVE — Luu trang thai du lieu hien tai
# ============================================================
function Save-State {
    if (-not $Label) {
        Write-Host "[ERROR] -Label is required for save action."
        exit 1
    }

    Initialize-SaveRepo
    Push-Location $FactoryRoot

    # Neu file progress-checkpoints.md bi xoa/rong truoc khi save, phuc hoi lich su cu tu tags truoc
    if (-not (Test-Path $SaveProgressFile) -or (Get-Item $SaveProgressFile).Length -eq 0) {
        Restore-ProgressLog
    }

    $ts = Get-VNTimestamp

    # Tu dong gan hau to thoi gian neu nhan snap/$Label da ton tai de khong bao gio gay luong
    $tagName = "snap/$Label"
    $existingTag = Invoke-SaveGit tag -l $tagName 2>$null
    if ($existingTag) {
        $Label = "$Label-" + $ts.ToString("yyyyMMdd-HHmmss")
        $tagName = "snap/$Label"
        Write-Host "[INFO] Tag already exists. Auto-appended timestamp: $tagName"
    }

    Invoke-SaveGit add --all . 2>$null | Out-Null
    Invoke-SaveGit commit --allow-empty -m "save: $Label" 2>$null | Out-Null

    $tagMsg = if ($Description) { $Description } else { $Label }
    Invoke-SaveGit tag -a $tagName -m $tagMsg 2>$null | Out-Null

    $hash = (Invoke-SaveGit rev-parse --short HEAD 2>$null) | Out-String
    $hash = $hash.Trim()

    Add-ProgressLogEntry -EntryLabel $Label -EntryHash $hash -EntryDesc $tagMsg -EntryTime $ts

    Pop-Location
    Write-Host "[OK] Saved: snap/$Label (hash: $hash)"
}

# ============================================================
# NHOM 9: ACTION LIST — Xem danh sach cac moc save points
# ============================================================
function Get-SaveList {
    if (-not (Test-Path $GitDir)) {
        Write-Host "[INFO] No save points yet. Run with -Action save first."
        return
    }

    if (-not (Test-Path $SaveProgressFile) -or (Get-Item $SaveProgressFile).Length -eq 0) {
        Write-Host "[INFO] progress-checkpoints.md missing or empty. Rebuilding from tags..."
        Restore-ProgressLog
    }

    if (Test-Path $SaveProgressFile) {
        Get-Content $SaveProgressFile -Encoding UTF8
    }
    else {
        Write-Host "[INFO] No save points found."
    }
}

# ============================================================
# NHOM 10: ACTION ROLLBACK — Khoi phuc du lieu, bao toan UI state & dong bo plugin he thong
# ============================================================
function Invoke-Rollback {
    if (-not $Label) {
        Write-Host "[ERROR] -Label is required for rollback action."
        exit 1
    }

    if (-not (Test-Path $GitDir)) {
        Write-Host "[ERROR] No .save-data/ repository found. Nothing to rollback."
        exit 1
    }

    Sync-SaveExclude
    Push-Location $FactoryRoot
    $tagName = "snap/$Label"

    $tagCheck = Invoke-SaveGit tag -l $tagName 2>$null
    if (-not $tagCheck) {
        Write-Host "[ERROR] Tag '$tagName' not found. Available save points:"
        Invoke-SaveGit tag -l "snap/*" --sort=-creatordate 2>$null
        Pop-Location
        exit 1
    }

    # --- Chot chan an toan: Auto-save trang thai hien tai va ghi vao progress-checkpoints.md ---
    $ts = Get-VNTimestamp
    $autoLabel = "before-rollback-" + $ts.ToString("yyyyMMdd-HHmmss")

    Invoke-SaveGit add --all . 2>$null | Out-Null
    $status = Invoke-SaveGit status --porcelain 2>$null
    if ($status) {
        Write-Host "[INFO] Auto-saving current state as snap/$autoLabel..."
        $autoMsg = "Auto-save before rolling back to $Label"
        Invoke-SaveGit commit -m "auto-save before rollback to $Label" 2>$null | Out-Null
        Invoke-SaveGit tag -a "snap/$autoLabel" -m $autoMsg 2>$null | Out-Null
        $autoHash = (Invoke-SaveGit rev-parse --short HEAD 2>$null) | Out-String
        $autoHash = $autoHash.Trim()
        Add-ProgressLogEntry -EntryLabel $autoLabel -EntryHash $autoHash -EntryDesc $autoMsg -EntryTime $ts
    }

    # --- Sao luu workspace.json trong RAM truoc khi reset --hard ve cac tag cu co chua workspace.json ---
    $wsPath = Join-Path $FactoryRoot "vault\.obsidian\workspace.json"
    $wsBytes = if (Test-Path $wsPath) { [System.IO.File]::ReadAllBytes($wsPath) } else { $null }
    $wsMobilePath = Join-Path $FactoryRoot "vault\.obsidian\workspace-mobile.json"
    $wsMobileBytes = if (Test-Path $wsMobilePath) { [System.IO.File]::ReadAllBytes($wsMobilePath) } else { $null }

    # --- Khoi phuc du lieu ve trang thai snapshot ---
    Write-Host "[INFO] Rolling back data to snap/$Label..."
    Invoke-SaveGit reset --hard $tagName 2>$null | Out-Null

    # --- Khoi phuc ngay trang thai giao dien Obsidian tu RAM va go lai cache cac file tam ---
    if ($null -ne $wsBytes) {
        [System.IO.File]::WriteAllBytes($wsPath, $wsBytes)
    }
    if ($null -ne $wsMobileBytes) {
        [System.IO.File]::WriteAllBytes($wsMobilePath, $wsMobileBytes)
    }
    Sync-SaveExclude

    # --- Dong bo lai Factory Scaffold & Obsidian Plugins de khong bi downgrade plugin he thong ---
    $syncScaffoldScript = Join-Path $FactoryRoot ".agents\scripts\sync-factory-scaffold.ps1"
    if (Test-Path $syncScaffoldScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $syncScaffoldScript -FactoryRoot $FactoryRoot 2>$null | Out-Null
    }

    Pop-Location
    Write-Host "[OK] Rolled back to snap/$Label."
    if ($status) {
        Write-Host "[OK] Auto-save created at snap/$autoLabel (use this to undo rollback if needed)."
    }
}

# ============================================================
# NHOM 11: MAIN — Dieu huong hanh dong
# ============================================================
switch ($Action) {
    "save"     { Save-State }
    "list"     { Get-SaveList }
    "rollback" { Invoke-Rollback }
}
