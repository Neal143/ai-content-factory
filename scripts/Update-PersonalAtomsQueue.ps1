<#
Ten file: Update-PersonalAtomsQueue.ps1
Last update: 27/06/2026 17:16 (GMT+7)
Vai tro: Quan ly file trang thai personal-atoms-queue.md — theo doi atoms ca nhan chua duoc su dung.
Su dung khi nao:
  - init: Chay 1 lan de bootstrap tu vault scan (hoac re-sync). Idempotent.
  - append: Goi boi story-architect/inbox-processor sau khi tao atom moi co source_type=User.
  - remove: Goi boi validate-format.ps1 sau khi ghi production-log.
Output: Cap nhat file vault/03-Content/Content Plan/personal-atoms-queue.md
Tom tat logic hoat dong:
  init: Rebuild vault index -> loc source_type=User -> loai atoms da dung (production-log) -> cross-ref topic_map -> ghi de file.
  append: Doc frontmatter atom moi -> check source_type=User -> cross-ref topic_map -> append dong vao file.
  remove: Doc file, xoa dong chua atom path khop (match bang substring 01-Atomic/...), re-number, ghi lai.
#>

param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("init", "append", "remove")]
    [string]$Action,

    # Comma-separated atom paths (khong dung [string[]] vi powershell -File khong ho tro array)
    [Parameter(Mandatory = $false)]
    [string]$AtomPathsRaw = "",

    [Parameter(Mandatory = $false)]
    [string]$QueueFile = "vault/03-Content/Content Plan/personal-atoms-queue.md",

    [Parameter(Mandatory = $false)]
    [string]$ProductionLog = "vault/.content-pipeline/logs/production-log.md"
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# Parse AtomPathsRaw thanh mang
$AtomPaths = @()
if ($AtomPathsRaw -ne "") {
    $AtomPaths = $AtomPathsRaw -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
}

# ==========================================
# NHOM 1: HAM TRO GIUP
# ==========================================

# Auto-detect PersonaUser tu thu muc personas/
function Get-PersonaUser {
    $personaDirs = Get-ChildItem -Path "personas" -Directory -ErrorAction SilentlyContinue
    if ($personaDirs.Count -gt 0) { return $personaDirs[0].Name }
    return $null
}

# Parse frontmatter tu 1 atom file, tra ve hashtable
function Get-AtomFrontmatter ([string]$filePath) {
    if (-not (Test-Path $filePath)) { return $null }
    $lines = Get-Content -Path $filePath -Encoding utf8
    if ($lines.Count -lt 2 -or $lines[0].Trim() -ne "---") { return $null }

    $data = @{}
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].Trim() -eq "---") { break }
        if ($lines[$i] -match '^\s*(\w+):\s*(.+)$') {
            $key = $Matches[1].ToLower()
            $val = $Matches[2].Trim().Trim("'").Trim('"')
            # Parse inline array: ["a","b"]
            if ($val.StartsWith("[") -and $val.EndsWith("]")) {
                $inner = $val.Substring(1, $val.Length - 2)
                $arr = @($inner.Split(",") | ForEach-Object { $_.Trim().Trim("'").Trim('"') } | Where-Object { $_ -ne "" })
                $data[$key] = $arr
            }
            else {
                $data[$key] = $val
            }
        }
    }
    return $data
}

# Build topic lookup tu topic_map.yaml: topic_id -> { label, pillar }
function New-TopicLookup ([string]$personaUser) {
    $topicMapPath = "personas/$personaUser/topic_map.yaml"
    $lookup = @{}
    if (-not (Test-Path $topicMapPath)) { return $lookup }

    $tmLines = Get-Content -Path $topicMapPath -Encoding utf8
    $currentId = $null; $currentLabel = $null; $currentPillar = $null; $readingPillars = $false

    foreach ($line in $tmLines) {
        if ($line -match '^\s*-\s*id:\s*(.+)$') {
            if ($currentId -and -not $lookup.ContainsKey($currentId)) {
                $lookup[$currentId] = @{ label = $currentLabel; pillar = $currentPillar }
            }
            $currentId = $Matches[1].Trim()
            $currentLabel = $currentId; $currentPillar = "N/A"; $readingPillars = $false
        }
        elseif ($line -match '^\s+label:\s*(.+)$') { $currentLabel = $Matches[1].Trim(); $readingPillars = $false }
        elseif ($line -match '^\s+pillar_parents:') { $readingPillars = $true }
        elseif ($line -match '^\s+belongs_to_audience:') { $readingPillars = $false }
        elseif ($readingPillars -and $line -match '^\s+-\s+(.+)$') {
            $currentPillar = $Matches[1].Trim().Trim("'").Trim('"'); $readingPillars = $false
        }
    }
    if ($currentId -and -not $lookup.ContainsKey($currentId)) {
        $lookup[$currentId] = @{ label = $currentLabel; pillar = $currentPillar }
    }
    return $lookup
}

# Tim topic trong lookup (ho tro prefix matching pN_xxx -> xxx)
function Resolve-TopicInfo ([string]$topicId, [hashtable]$lookup) {
    if ($lookup.ContainsKey($topicId)) { return $lookup[$topicId] }
    foreach ($mapKey in $lookup.Keys) {
        $clean = $mapKey -replace '^p\d+_', ''
        if ($clean -eq $topicId) { return $lookup[$mapKey] }
    }
    return $null
}

# Sinh header cua file queue
function Get-QueueHeader {
    $ts = Get-Date -Format "dd/MM/yyyy HH:mm"
    return @"
# Personal Atoms Queue
<!-- Last updated: $ts (GMT+7) -->
<!-- Auto-managed by Update-PersonalAtomsQueue.ps1. Do not edit manually. -->

> File nay liet ke cac atoms ca nhan (source_type=User) chua duoc su dung trong bat ky bai dang nao.
> Chon 1 Topic tu cot "Topic kha dung" va chay /content-post voi topic do.

"@ + "`r`n`r`n"
}

# Table header constant
$TABLE_HEADER = "| # | Atom | Type | Sub/Insight | Topic kha dung | Pillar | Created |`r`n|---|------|------|-------------|----------------|--------|---------|"
$PLACEHOLDER_MARKER = "Khong co atom personal nao dang cho"

# Sinh 1 dong bang markdown cho 1 atom
function Format-AtomRow ([int]$index, [string]$atomPath, [hashtable]$fm, [hashtable]$topicLookup) {
    $filename = [System.IO.Path]::GetFileNameWithoutExtension($atomPath)
    $atomType = if ($fm["type"]) { $fm["type"] } else { "unknown" }
    $subInsight = if ($fm["insight_type"]) { $fm["insight_type"] } else { if ($fm["subtype"]) { $fm["subtype"] } else { "-" } }
    $created = if ($fm["created"]) { $fm["created"] } else { "N/A" }

    # Tim topic kha dung (co trong topic_map) - lay toi da 3
    $mappedTopics = @()
    $topicsRaw = $fm["topics"]
    $topicsArray = @()
    if ($null -ne $topicsRaw) {
        if ($topicsRaw -is [Array]) { $topicsArray = $topicsRaw }
        elseif ($topicsRaw -is [String]) { $topicsArray = @($topicsRaw) }
    }

    foreach ($t in $topicsArray) {
        $info = Resolve-TopicInfo $t $topicLookup
        if ($info) {
            $mappedTopics += "$t ($($info.label))"
            if ($mappedTopics.Count -ge 3) { break }
        }
    }
    
    $topicDisplay = if ($mappedTopics.Count -gt 0) { $mappedTopics -join ", " } else { "Chua co topic trong map" }

    # Tim pillar tu topic dau tien khop
    $pillar = "N/A"
    foreach ($t in $topicsArray) {
        $info = Resolve-TopicInfo $t $topicLookup
        if ($info -and $info.pillar -ne "N/A") { $pillar = $info.pillar; break }
    }

    # Relative link: queue tai vault/03-Content/Content Plan/ -> atom tai vault/01-Atomic/...
    # Tu Content Plan/ can di len 2 cap (../../) de ve vault/
    $relPath = $atomPath -replace '^vault/', '../../'
    $link = "[$filename]($relPath)"

    return "| $index | $link | $atomType | $subInsight | $topicDisplay | $pillar | $created |"
}

# ==========================================
# NHOM 2: ACTION - INIT (idempotent)
# ==========================================
if ($Action -eq "init") {
    $personaUser = Get-PersonaUser
    if (-not $personaUser) { Write-Error "[ERR] Khong tim thay persona trong thu muc personas/"; exit 1 }

    # Rebuild vault index
    $buildScript = ".agents/skills/dikw-bridge/scripts/build-vault-index.ps1"
    $indexPath = ".agents/skills/dikw-bridge/assets/vault_index.json"
    if (Test-Path $buildScript) {
        powershell -ExecutionPolicy Bypass -File $buildScript -VaultPath "vault/01-Atomic" -OutputPath $indexPath | Out-Null
    }
    if (-not (Test-Path $indexPath)) { Write-Error "[ERR] vault_index.json khong ton tai"; exit 1 }

    $index = Get-Content -Path $indexPath -Raw -Encoding utf8 | ConvertFrom-Json
    $topicLookup = New-TopicLookup $personaUser

    # Lay tat ca atoms da dung tu production-log (TOAN BO log, khong gioi han)
    $usedAtoms = @()
    if (Test-Path $ProductionLog) {
        $logContent = Get-Content -Path $ProductionLog -Raw -Encoding utf8
        $regexMatches = [regex]::Matches($logContent, 'vault/01-Atomic/[\w\-\/]+\.md')
        foreach ($m in $regexMatches) { $usedAtoms += $m.Value }
        $usedAtoms = $usedAtoms | Select-Object -Unique
    }

    # Loc personal atoms chua dung
    $rows = @()
    $counter = 1
    foreach ($prop in $index.nodes.psobject.properties) {
        if ($prop.Value.source_type -ne "User") { continue }
        if ($prop.Name -in $usedAtoms) { continue }
        $fm = @{}
        foreach ($p in $prop.Value.psobject.properties) { $fm[$p.Name] = $p.Value }
        $rows += Format-AtomRow $counter $prop.Name $fm $topicLookup
        $counter++
    }

    # Tao thu muc neu chua co
    $queueDir = Split-Path $QueueFile
    if (-not (Test-Path $queueDir)) { New-Item -ItemType Directory -Path $queueDir -Force | Out-Null }

    # Ghi file (ghi de)
    $header = Get-QueueHeader
    $content = $header + $TABLE_HEADER
    if ($rows.Count -gt 0) {
        $content += "`r`n" + ($rows -join "`r`n")
    }
    else {
        $content += "`r`n| - | *$PLACEHOLDER_MARKER* | - | - | - | - | - |"
    }
    $content += "`r`n"

    [System.IO.File]::WriteAllText($QueueFile, $content, $utf8NoBom)
    Write-Host "[SUCCESS] Init queue: $($rows.Count) atoms personal chua dung." -ForegroundColor Green
}

# ==========================================
# NHOM 3: ACTION - APPEND
# ==========================================
elseif ($Action -eq "append") {
    if ($AtomPaths.Count -eq 0) { Write-Host "[SKIP] Khong co atom path nao."; exit 0 }

    $personaUser = Get-PersonaUser
    $topicLookup = if ($personaUser) { New-TopicLookup $personaUser } else { @{} }

    # Dam bao file + thu muc ton tai
    if (-not (Test-Path $QueueFile)) {
        $queueDir = Split-Path $QueueFile
        if (-not (Test-Path $queueDir)) { New-Item -ItemType Directory -Path $queueDir -Force | Out-Null }
        $header = Get-QueueHeader
        [System.IO.File]::WriteAllText($QueueFile, ($header + $TABLE_HEADER + "`r`n"), $utf8NoBom)
    }

    $existingContent = Get-Content -Path $QueueFile -Raw -Encoding utf8

    # Xoa placeholder row neu co
    if ($existingContent -match [regex]::Escape($PLACEHOLDER_MARKER)) {
        $lines = $existingContent -split '\r?\n'
        $filteredLines = $lines | Where-Object { $_ -notmatch [regex]::Escape($PLACEHOLDER_MARKER) }
        $existingContent = ($filteredLines -join "`r`n")
        [System.IO.File]::WriteAllText($QueueFile, ($existingContent + "`r`n"), $utf8NoBom)
    }

    # Tim so thu tu hien tai cao nhat
    $maxIndex = 0
    $indexMatches = [regex]::Matches($existingContent, '^\|\s*(\d+)\s*\|', [System.Text.RegularExpressions.RegexOptions]::Multiline)
    foreach ($m in $indexMatches) {
        $num = [int]$m.Groups[1].Value
        if ($num -gt $maxIndex) { $maxIndex = $num }
    }

    $appendedCount = 0
    $newRows = ""
    foreach ($path in $AtomPaths) {
        # Check trung lap: strip vault/ prefix de match voi noi dung file (dang ../../01-Atomic/...)
        $searchKey = $path -replace '^vault/', ''
        if ($existingContent -match [regex]::Escape($searchKey)) { continue }

        $fm = Get-AtomFrontmatter $path
        if (-not $fm) { continue }
        if ($fm["source_type"] -ne "User") { continue }

        $maxIndex++
        $row = Format-AtomRow $maxIndex $path $fm $topicLookup
        $newRows += "`r`n$row"
        $appendedCount++
    }

    if ($appendedCount -gt 0) {
        [System.IO.File]::AppendAllText($QueueFile, $newRows, $utf8NoBom)
        # Cap nhat timestamp
        $ts = Get-Date -Format "dd/MM/yyyy HH:mm"
        $updatedContent = Get-Content -Path $QueueFile -Raw -Encoding utf8
        $updatedContent = $updatedContent -replace 'Last updated: .+?\)', "Last updated: $ts (GMT+7)"
        [System.IO.File]::WriteAllText($QueueFile, $updatedContent, $utf8NoBom)
    }
    Write-Host "[SUCCESS] Appended $appendedCount atom(s) vao queue." -ForegroundColor Green
}

# ==========================================
# NHOM 4: ACTION - REMOVE
# ==========================================
elseif ($Action -eq "remove") {
    if ($AtomPaths.Count -eq 0) { Write-Host "[SKIP] Khong co atom path nao."; exit 0 }
    if (-not (Test-Path $QueueFile)) { Write-Host "[SKIP] Queue file khong ton tai."; exit 0 }

    $lines = Get-Content -Path $QueueFile -Encoding utf8
    $filteredLines = @()
    $removedCount = 0

    foreach ($line in $lines) {
        $shouldRemove = $false
        foreach ($atomPath in $AtomPaths) {
            # Strip vault/ prefix de match voi noi dung file (dang ../../01-Atomic/...)
            $searchKey = $atomPath -replace '^vault/', ''
            if ($line -match [regex]::Escape($searchKey)) {
                $shouldRemove = $true
                $removedCount++
                break
            }
        }
        if (-not $shouldRemove) { $filteredLines += $line }
    }

    if ($removedCount -gt 0) {
        # Re-number cac dong bang
        $counter = 1
        $renumbered = @()
        foreach ($line in $filteredLines) {
            if ($line -match '^\|\s*\d+\s*\|') {
                $line = $line -replace '^\|\s*\d+\s*\|', "| $counter |"
                $counter++
            }
            $renumbered += $line
        }

        # Cap nhat timestamp
        $ts = Get-Date -Format "dd/MM/yyyy HH:mm"
        $content = ($renumbered -join "`r`n") -replace 'Last updated: .+?\)', "Last updated: $ts (GMT+7)"
        $content += "`r`n"
        [System.IO.File]::WriteAllText($QueueFile, $content, $utf8NoBom)
    }
    Write-Host "[SUCCESS] Removed $removedCount atom(s) tu queue." -ForegroundColor Green
}
