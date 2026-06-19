# Ten file: export_extraction_runs.ps1
# Last update: 18/06/2026 23:30 (GMT+7)
# Vai tro: Export du lieu Session 1 cua book-extractor sang folder rieng de chuyen sang factory khac.
# Su dung khi nao: Duoc goi boi workflow /transfer-extraction (mode Export) hoac chay truc tiep tu command line.
# Output: Folder vault/.extraction_runs_export/ chua du lieu S1 da normalize + cache files.
# Tom tat logic hoat dong:
#   1. Khoi tao paths, kiem tra output folder.
#   2. Lap qua tung sach: doc blackboard, validate S1, copy S1 data (normalize flat->subfolder),
#      copy pipeline_report.md, tao blackboard moi (reset current_phase=2), copy cache file,
#      sinh file HANDOFF_SESSION2.txt chua prompt san de user copy-paste vao chat moi.
#   3. In summary va huong dan import.

param(
    [Parameter(Mandatory=$true)]
    [string[]]$BookFolders,          # Array ten folder sach, vd: "beyond-the-rainbow-bridge_2026-05-27"

    [string]$SourceType = "books",   # Source type subfolder (books, videos, podcasts)

    [string]$VaultPath = "vault",    # Path tuong doi toi vault (tuong doi voi Content Factory root)

    [string]$OutputPath = "",        # Default: vault/.extraction_runs_export

    [switch]$Force                   # Neu co, xoa output cu khong hoi
)

# â”€â”€ Block 1: Khoi tao paths va output folder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

$BaseDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$VaultDir = Join-Path $BaseDir $VaultPath
$SourceRunsDir = Join-Path (Join-Path $VaultDir ".extraction_runs") $SourceType
$BooksDir = Join-Path (Join-Path $VaultDir "02-sources") "books"

if ([string]::IsNullOrEmpty($OutputPath)) {
    $OutputDir = Join-Path $VaultDir ".extraction_runs_export"
} else {
    $OutputDir = $OutputPath
}

# Xu ly output ton tai
if (Test-Path $OutputDir) {
    if (-not $Force) {
        Write-Host "[WARNING] Output folder da ton tai: $OutputDir"
        Write-Host "Dung -Force de ghi de, hoac xoa thu cong truoc."
        exit 1
    }
    Remove-Item -Path $OutputDir -Recurse -Force
}

# Khoi tao bien dem
$exported = 0
$skipped = 0
$warnings = [System.Collections.ArrayList]::new()

# â”€â”€ Block 2: Lap qua tung sach â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

foreach ($folder in $BookFolders) {
    $srcDir = Join-Path $SourceRunsDir $folder

    # Kiem tra folder ton tai
    if (-not (Test-Path $srcDir)) {
        [void]$warnings.Add("[$folder] Folder khong ton tai trong $SourceType/")
        $skipped++
        continue
    }

    # â”€â”€ Block 2.1: Doc blackboard â”€â”€
    $bbPath = Join-Path $srcDir "00-blackboard.yaml"
    if (-not (Test-Path $bbPath)) {
        [void]$warnings.Add("[$folder] 00-blackboard.yaml khong ton tai")
        $skipped++
        continue
    }

    # Parse YAML don gian (flat key-value)
    $bb = @{}
    foreach ($line in (Get-Content $bbPath -Encoding UTF8)) {
        if ($line -match '^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$') {
            $key = $Matches[1]
            $val = $Matches[2].Trim()
            # Strip surrounding quotes (single or double)
            if (($val.StartsWith('"') -and $val.EndsWith('"')) -or
                ($val.StartsWith("'") -and $val.EndsWith("'"))) {
                $val = $val.Substring(1, $val.Length - 2)
            }
            $bb[$key] = $val
        }
    }

    # Derive truong thieu: cache_file bat buoc
    if (-not $bb['cache_file']) {
        [void]$warnings.Add("[$folder] Blackboard thieu cache_file, skip")
        $skipped++
        continue
    }

    # Derive book_name tu cache_file path neu thieu
    if (-not $bb['book_name']) {
        $bb['book_name'] = [System.IO.Path]::GetFileNameWithoutExtension($bb['cache_file'])
    }

    # Derive slug tu folder name (phan truoc _YYYY-MM-DD)
    if (-not $bb['slug']) {
        if ($folder -match '^(.+)_\d{4}-\d{2}-\d{2}$') {
            $bb['slug'] = $Matches[1]
        } else {
            $bb['slug'] = $folder
        }
    }

    # Derive run_folder (co prefix "vault/")
    if (-not $bb['run_folder']) {
        $bb['run_folder'] = "vault/.extraction_runs/$SourceType/$folder/"
    }

    # notebook_id co the rong
    if (-not $bb['notebook_id']) { $bb['notebook_id'] = "" }

    # â”€â”€ Block 2.2: Validate S1 completeness â”€â”€
    $hasSessionSubfolder = Test-Path (Join-Path $srcDir "session_1")

    $s1SourceDir = if ($hasSessionSubfolder) {
        Join-Path $srcDir "session_1"
    } else {
        $srcDir
    }

    $hasMapper = Test-Path (Join-Path $s1SourceDir "mapper_raw.md")
    $hasMiner  = Test-Path (Join-Path $s1SourceDir "miner_progress.yaml")

    if (-not $hasMapper -or -not $hasMiner) {
        [void]$warnings.Add("[$folder] Session 1 incomplete (mapper_raw.md hoac miner_progress.yaml khong ton tai)")
        $skipped++
        continue
    }

    # â”€â”€ Block 2.3: Tao output folder va copy S1 data â”€â”€
    $dstRunDir = Join-Path (Join-Path $OutputDir $SourceType) $folder
    $dstS1Dir = Join-Path $dstRunDir "session_1"
    New-Item -Path $dstS1Dir -ItemType Directory -Force | Out-Null

    if ($hasSessionSubfolder) {
        # Subfolder structure: copy toan bo session_1/
        Copy-Item -Path (Join-Path $s1SourceDir "*") -Destination $dstS1Dir -Recurse -Force
    } else {
        # Flat structure: copy tung nhom file theo pattern
        $patterns = @(
            "mapper_raw.md",
            "miner_progress.yaml",
            "post_mine_report.txt",
            "chunk_*_raw.txt",
            "chunk_*_gate.json",
            "chunk_*_agent_gate.json"
        )
        foreach ($pat in $patterns) {
            Get-ChildItem -Path $s1SourceDir -Filter $pat -File -ErrorAction SilentlyContinue |
                ForEach-Object { Copy-Item $_.FullName -Destination $dstS1Dir }
        }
    }

    # ── Block 2.4: Export pipeline_report.md (chi giu phan Session 1) ──
    # pipeline_report.md la audit trail xuyen suot pipeline. Cac session append them:
    #   ## 1. book-extractor  -> S1 (audit_cache.py, mode 'w')
    #   ## 1b. generate_baseline -> S2 (generate_baseline.py, append)
    #   ## 2. book-audience-matcher -> S3 (verify_audiences.py, append)
    #   ## 3. book-parser -> S4 (atomizer.py, append)
    # Export chi giu phan S1 de factory moi bat dau sach tu S2.
    $srcReport = Join-Path $srcDir "pipeline_report.md"
    $dstReport = Join-Path $dstRunDir "pipeline_report.md"
    if (Test-Path $srcReport) {
        $reportLines = Get-Content $srcReport -Encoding UTF8
        $s1Lines = [System.Collections.ArrayList]::new()
        foreach ($rl in $reportLines) {
            # Dung lai khi gap heading cua S2 tro di
            if ($rl -match '^## 1b\.' -or $rl -match '^## [2-9]\.') {
                break
            }
            [void]$s1Lines.Add($rl)
        }
        $s1Content = ($s1Lines -join "`r`n").TrimEnd() + "`r`n"
        [System.IO.File]::WriteAllText($dstReport, $s1Content, [System.Text.UTF8Encoding]::new($false))
    }

    # â”€â”€ Block 2.5: Tao blackboard moi (reset current_phase = 2) â”€â”€
    $bbContent = @"
book_name: "$($bb['book_name'])"
notebook_name: ""
notebook_id: "$($bb['notebook_id'])"
run_folder: "vault/.extraction_runs/$SourceType/$folder/"
cache_file: "$($bb['cache_file'])"
slug: "$($bb['slug'])"
current_phase: 2
"@
    # Ghi file voi encoding UTF8 (khong BOM) + trailing newline
    [System.IO.File]::WriteAllText(
        (Join-Path $dstRunDir "00-blackboard.yaml"),
        ($bbContent + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )

    # â”€â”€ Block 2.6: Copy cache file vao run folder â”€â”€
    $cacheRelPath = $bb['cache_file']
    $cacheSrcFull = Join-Path $BaseDir $cacheRelPath

    if (-not (Test-Path $cacheSrcFull)) {
        [void]$warnings.Add("[$folder] Cache file khong ton tai: $cacheRelPath")
        # Van tiep tuc vi S1 data da duoc copy thanh cong
    } else {
        Copy-Item $cacheSrcFull -Destination $dstRunDir
    }

    # â”€â”€ Block 2.7: Sinh file HANDOFF_SESSION2.txt â”€â”€
    # File prompt san de user copy-paste vao chat moi tai factory dich
    $runFolderVal = "vault/.extraction_runs/$SourceType/$folder/"
    $handoffContent = @"
**[He thong] Handoff 1**
Workflow: ``/book-extractor`` (Phase 2)
Sach: $($bb['book_name']) (ID: $($bb['notebook_id'])) | Run: $runFolderVal | Cache: $($bb['cache_file'])
Trang thai: Phase 1 PASS. ``current_phase: 2``.
Yeu cau:
1. Doc ``.agents\workflows\book-extractor.md``.
2. Nap cau hinh tu ``00-blackboard.yaml`` trong $runFolderVal.
3. Kich chay **Buoc 3.5 (Phase 2: Vivid Curation)** ngay lap tuc.
"@
    [System.IO.File]::WriteAllText(
        (Join-Path $dstRunDir "HANDOFF_SESSION2.txt"),
        ($handoffContent + "`n"),
        [System.Text.UTF8Encoding]::new($false)
    )

    # Tinh la exported khi S1 data da copy thanh cong
    $exported++
    Write-Host "[OK] $($bb['book_name']) ($folder)"
}

# â”€â”€ Block 3: Summary va huong dan import â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

Write-Host ""
Write-Host "=== EXPORT COMPLETE ==="
Write-Host "Exported: $exported book(s)"
Write-Host "Skipped:  $skipped book(s)"
Write-Host "Output:   $OutputDir"
Write-Host ""

if ($warnings.Count -gt 0) {
    Write-Host "WARNINGS:"
    foreach ($w in $warnings) {
        Write-Host "  - $w"
    }
    Write-Host ""
}

Write-Host "HOW TO IMPORT:"
Write-Host "  Voi moi folder sach trong $SourceType/:"
Write-Host "  1. Copy folder [book-slug_date]/ vao vault/.extraction_runs/$SourceType/ cua factory moi"
Write-Host "  2. Move file [Ten Sach].md tu trong run folder vao vault/02-sources/books/ cua factory moi"
Write-Host "  3. Xoa file [Ten Sach].md khoi run folder sau khi da move"
Write-Host "  4. Mo file HANDOFF_SESSION2.txt trong run folder, copy noi dung va dan vao chat moi"
