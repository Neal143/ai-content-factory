param(
    [string]$Keywords,
    [string]$TypeFilter
)
$ErrorActionPreference = "Stop"

# 1. Update Index (có cooldown 15s) để chống Stale Index & tối ưu hiệu năng
$indexerPath = ".agents/skills/dikw-bridge/scripts/build-vault-index.ps1"
$indexPath = ".agents/skills/dikw-bridge/assets/vault_index.json"
$idxStats = Get-Item $indexPath -ErrorAction SilentlyContinue
if (-not $idxStats -or (Get-Date) -gt $idxStats.LastWriteTime.AddSeconds(15)) {
    if (Test-Path $indexerPath) { & powershell $indexerPath }
}

# 2. Đọc DB
$indexPath = ".agents/skills/dikw-bridge/assets/vault_index.json"
if (-not (Test-Path $indexPath)) { Write-Error "Khong tim thay vault_index.json"; exit }

$index = Get-Content -Path $indexPath -Raw -Encoding utf8 | ConvertFrom-Json
$keywordArray = $Keywords.Split(",").ForEach({$_.Trim().ToLower()}) | Where-Object { $_ }

# 3. Chấm điểm Semantics
$results = @()
foreach ($key in $index.nodes.psobject.properties.name) {
    $node = $index.nodes.$key
    if ($TypeFilter -and $node.type -notmatch "(?i)^($TypeFilter)$") { continue }
    
    $score = 0
    foreach ($kw in $keywordArray) {
        $kwSafe = [regex]::Escape($kw)
        if ($key.ToLower() -match $kwSafe) { $score += 10 }
        
        if ($null -ne $node.topics) {
            foreach ($t in $node.topics) {
                if ($t.ToLower() -match $kwSafe) { $score += 5 }
            }
        }
        if ($null -ne $node.excerpt) {
            $score += [regex]::Matches($node.excerpt.ToLower(), $kwSafe).Count
        }
    }
    if ($score -gt 0) {
        $results += [pscustomobject]@{ Path = $key; Score = $score; Excerpt = $node.excerpt }
    }
}

# 4. Xuất file JSON Tạm (Poka-Yoke chống Agent lười)
$outDir = ".agents/temp"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$outPath = "$outDir/rag_results.json"
$jsonStr = $results | Sort-Object Score -Descending | Select-Object -First 5 | ConvertTo-Json -Compress
[System.IO.File]::WriteAllText((Resolve-Path $outDir).Path + "\rag_results.json", $jsonStr, [System.Text.Encoding]::UTF8)

Write-Host "Success. Agent bat buoc doc file: $outPath de danh gia Semantics."
