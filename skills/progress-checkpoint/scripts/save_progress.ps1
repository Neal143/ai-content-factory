# ============================================================
# File: .agents/skills/progress-checkpoint/scripts/save_progress.ps1
# Last update: 11/08/2026 00:00 (GMT+7)
# Role: Manage data snapshots for Content Factory using a separate git repository (.save-data/)
# Usage: Called by agent via SKILL.md instructions.
# Output: Git commits/tags in .save-data/, entries in progress-checkpoints.md
# Logic: Uses git --git-dir=.save-data --work-tree=<FactoryRoot> to isolate snapshot git
#        from any parent git. 3 actions: save (commit+tag+log), list, rollback (checkout+clean)
# ============================================================

param(
    [Parameter(Mandatory)]
    [ValidateSet("save", "list", "rollback")]
    [string]$Action,

    [string]$Label,
    [string]$Description
)

# --- Resolve Factory Root (4 levels up from scripts/) ---
$FactoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\.." )).Path
$GitDir = Join-Path $FactoryRoot ".save-data"
$SaveProgressFile = Join-Path $FactoryRoot "progress-checkpoints.md"

# --- Helper: Run git with custom --git-dir and --work-tree ---
# NOTE: Does NOT redirect stderr. Callers use 2>$null where needed.
function Invoke-SaveGit {
    param([Parameter(ValueFromRemainingArguments)][string[]]$GitArgs)
    & git --git-dir="$GitDir" --work-tree="$FactoryRoot" @GitArgs
}

# --- Helper: Get current timestamp in GMT+7 ---
function Get-VNTimestamp {
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("SE Asia Standard Time")
    return [System.TimeZoneInfo]::ConvertTime([System.DateTimeOffset]::Now, $tz)
}

# --- Helper: Initialize .save-data/ git repo if not exists ---
function Initialize-SaveRepo {
    if (Test-Path $GitDir) { return }

    Write-Host "[INIT] Creating .save-data/ repository..."

    # Init git repo with custom git-dir
    Invoke-SaveGit init 2>$null | Out-Null

    # Set local git config (prevents commit failure on systems without global git config)
    Invoke-SaveGit config user.email "factory@local" 2>$null | Out-Null
    Invoke-SaveGit config user.name "Content Factory" 2>$null | Out-Null

    # Set up info/exclude (only affects this git repo, not parent git)
    $excludePath = Join-Path (Join-Path $GitDir "info") "exclude"
    $excludeContent = @(
        "# Excluded from progress-checkpoint snapshots",
        ".agents/",
        ".save-data/",
        "progress-checkpoints.md"
    )
    $excludeContent | Set-Content -Path $excludePath -Encoding UTF8

    Write-Host "[INIT] Repository initialized."
}

# ============================================================
# ACTION: SAVE
# ============================================================
function Save-State {
    if (-not $Label) {
        Write-Host "[ERROR] -Label is required for save action."
        exit 1
    }

    # Auto-init if first run
    Initialize-SaveRepo

    Push-Location $FactoryRoot

    # Check for duplicate tag BEFORE staging/committing
    $tagName = "snap/$Label"
    $existingTag = Invoke-SaveGit tag -l $tagName 2>$null
    if ($existingTag) {
        Write-Host "[ERROR] Tag '$tagName' already exists. Use a unique label."
        Pop-Location
        exit 1
    }

    # Stage all data changes (info/exclude handles .agents/, .save-data/, progress-checkpoints.md)
    Invoke-SaveGit add --all . 2>$null | Out-Null

    # Commit snapshot (allow-empty ensures a commit is always created even without file changes)
    Invoke-SaveGit commit --allow-empty -m "save: $Label" 2>$null | Out-Null

    # Create annotated tag
    $tagMsg = if ($Description) { $Description } else { $Label }
    Invoke-SaveGit tag -a $tagName -m $tagMsg 2>$null | Out-Null

    # Get commit hash for logging (2>$null prevents stderr from mixing into output)
    $hash = (Invoke-SaveGit rev-parse --short HEAD 2>$null) | Out-String
    $hash = $hash.Trim()

    # --- Update progress-checkpoints.md ---
    $ts = Get-VNTimestamp
    $dateStr = $ts.ToString("dd/MM/yyyy HH:mm")

    $newEntry = @"

### $dateStr (GMT+7)
#### $Label
- **Tag:** ``snap/$Label``
- **Hash:** ``$hash``
- **Description:** $tagMsg
"@

    # Create file with header if not exists
    if (-not (Test-Path $SaveProgressFile)) {
        $header = "# Progress Checkpoints"
        [System.IO.File]::WriteAllText($SaveProgressFile, $header, [System.Text.Encoding]::UTF8)
    }

    # Read current content, insert new entry after first line (header)
    $lines = [System.IO.File]::ReadAllLines($SaveProgressFile, [System.Text.Encoding]::UTF8)
    $headerLine = $lines[0]
    $restLines = if ($lines.Length -gt 1) { $lines[1..($lines.Length - 1)] } else { @() }
    $allContent = @($headerLine) + $newEntry.Split("`n") + $restLines
    [System.IO.File]::WriteAllLines($SaveProgressFile, $allContent, [System.Text.Encoding]::UTF8)

    Pop-Location
    Write-Host "[OK] Saved: snap/$Label (hash: $hash)"
}

# ============================================================
# ACTION: LIST
# ============================================================
function Get-SaveList {
    if (-not (Test-Path $GitDir)) {
        Write-Host "[INFO] No save points yet. Run with -Action save first."
        return
    }

    # Prefer reading progress-checkpoints.md (user-friendly format)
    if (Test-Path $SaveProgressFile) {
        Get-Content $SaveProgressFile -Encoding UTF8
    }
    else {
        # Fallback: list git tags directly
        Write-Host "=== Save Points ==="
        Invoke-SaveGit tag -l "snap/*" --sort=-creatordate -n1 2>$null
    }
}

# ============================================================
# ACTION: ROLLBACK
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

    Push-Location $FactoryRoot
    $tagName = "snap/$Label"

    # Verify tag exists
    $tagCheck = Invoke-SaveGit tag -l $tagName 2>$null
    if (-not $tagCheck) {
        Write-Host "[ERROR] Tag '$tagName' not found. Available save points:"
        Invoke-SaveGit tag -l "snap/*" --sort=-creatordate 2>$null
        Pop-Location
        exit 1
    }

    # --- Safety net: auto-save current state before rollback ---
    $ts = Get-VNTimestamp
    $autoLabel = "before-rollback-" + $ts.ToString("yyyyMMdd-HHmmss")

    Invoke-SaveGit add --all . 2>$null | Out-Null
    $status = Invoke-SaveGit status --porcelain 2>$null
    if ($status) {
        Write-Host "[INFO] Auto-saving current state as snap/$autoLabel..."
        Invoke-SaveGit commit -m "auto-save before rollback to $Label" 2>$null | Out-Null
        Invoke-SaveGit tag -a "snap/$autoLabel" -m "Auto-save before rolling back to $Label" 2>$null | Out-Null
    }

    # --- Rollback: checkout files from snapshot ---
    Write-Host "[INFO] Rolling back data to snap/$Label..."
    Invoke-SaveGit checkout $tagName -- . 2>$null | Out-Null

    # --- Clean up files created after the snapshot ---
    # git clean -fd removes untracked files not in the snapshot
    # Ignored files (.agents/, .save-data/, progress-checkpoints.md) are NOT removed
    Invoke-SaveGit clean -fd 2>$null | Out-Null

    Pop-Location
    Write-Host "[OK] Rolled back to snap/$Label."
    if ($status) {
        Write-Host "[OK] Auto-save created at snap/$autoLabel (use this to undo rollback if needed)."
    }
}

# ============================================================
# MAIN: Route to action
# ============================================================
switch ($Action) {
    "save"    { Save-State }
    "list"    { Get-SaveList }
    "rollback" { Invoke-Rollback }
}
