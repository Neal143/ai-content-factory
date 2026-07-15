<#
.SYNOPSIS
Search-SemanticAtom.ps1
Last update: 13/07/2026 10:44 (GMT+7)

.DESCRIPTION
Vai tro: Script PowerShell da che do (alignment/dedup) de tim kiem cac Atom trong Vault, chay Local Zero-API.
Khi nao su dung: Goi tu cac skill nhu atom-dedup, atom-linker, inbox-processor.
Output: rag_results.json (danh sach candidates) hoac dedup_pairs.json (danh sach cac cap trung lap).
Tom tat logic: 
 - Luong A (alignment/dedup incremental): Loc theo Scope -> Cham diem Keyword -> Loc nguong -> Lay Top-K.
 - Luong B (dedup full): Gom nhom theo (Audience x Type) -> So sanh tung cap (Pairwise) -> Loc nguong -> Xuat ra danh sach.
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("alignment", "dedup")]
    [string]$Mode,

    [Parameter(Mandatory = $false)]
    [ValidateSet("incremental", "full")]
    [string]$Scope = "incremental",

    [Parameter(Mandatory = $false)]
    [string]$SourceAtomPath,

    [Parameter(Mandatory = $false)]
    [string[]]$NewAtoms,

    [Parameter(Mandatory = $false)]
    [ValidateSet("insight", "solution", "evidence", "")]
    [string]$Layer = "",

    [Parameter(Mandatory = $false)]
    [string]$IndexPath = ".agents/assets/vault_index.json"
)

$THRESHOLD_ALIGNMENT = 4
$THRESHOLD_DEDUP = 6
$TOPK_ALIGNMENT = 15
$TOPK_DEDUP = 10

$DAG_PARENT_MAP = @{
    "solution" = @("insight", "knowledge")
    "concept" = @("insight", "knowledge")
    "story" = @("solution", "concept", "insight", "knowledge")
    "quote" = @("solution", "concept", "insight", "knowledge")
    "data_point" = @("solution", "concept", "insight", "knowledge")
    "data-point" = @("solution", "concept", "insight", "knowledge")
}

$TempDir = "vault/.curation_temp"
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}

if (-not (Test-Path $IndexPath)) {
    Write-Host "[ERR] Khong tim thay vault_index.json tai $IndexPath" -ForegroundColor Red
    exit 1
}

$IndexContent = Get-Content $IndexPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Nodes = $IndexContent.nodes

function Get-OverlapScore($kw1, $kw2) {
    if (-not $kw1 -or -not $kw2) { return 0 }
    $set1 = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($k in $kw1) { $set1.Add($k.Trim()) | Out-Null }
    
    $score = 0
    foreach ($k in $kw2) {
        if ($set1.Contains($k.Trim())) { $score++ }
    }
    return $score
}

function Get-TypeGroup($type) {
    if ($type -eq "insight") { return "insight" }
    if ($type -match "^(solution|concept)$") { return "solution" }
    if ($type -match "^(story|quote|data_point)$") { return "evidence" }
    return ""
}

if (($Mode -eq "alignment") -or ($Mode -eq "dedup" -and $Scope -eq "incremental")) {
    if (-not $SourceAtomPath) {
        Write-Host "[ERR] Yeu cau SourceAtomPath" -ForegroundColor Red
        exit 1
    }
    if (-not $Nodes.psobject.properties.match($SourceAtomPath)) {
        Write-Host "[ERR] Source atom khong co trong index: $SourceAtomPath" -ForegroundColor Red
        exit 1
    }
    
    $sourceNode = $Nodes.$SourceAtomPath
    $sourceType = $sourceNode.type
    $sourceAudience = $sourceNode.resolved_audience
    $sourceKeywords = $sourceNode.keywords
    
    $candidates = @()
    
    foreach ($prop in $Nodes.psobject.properties) {
        $path = $prop.Name
        if ($path -eq $SourceAtomPath) { continue }
        
        $node = $prop.Value
        
        # Scope Filter
        if ($Mode -eq "alignment") {
            $allowedParents = $DAG_PARENT_MAP[$sourceType]
            if (-not $allowedParents -or $node.type -notin $allowedParents) { continue }
        } else {
            # Dedup incremental
            if ($node.type -ne $sourceType) { continue }
            if ($sourceAudience -eq "CONFLICT" -or $node.resolved_audience -eq "CONFLICT") { continue }
            if ($sourceAudience) {
                if (-not $node.resolved_audience -or $node.resolved_audience.id -ne $sourceAudience.id) { continue }
            } else {
                if ($node.resolved_audience) { continue }
            }
        }
        
        $score = Get-OverlapScore $sourceKeywords $node.keywords
        $threshold = if ($Mode -eq "alignment") { $THRESHOLD_ALIGNMENT } else { $THRESHOLD_DEDUP }
        
        if ($score -ge $threshold) {
            $candidates += @{
                "path" = $path
                "score" = $score
                "description" = $node.description
                "resolved_audience" = $node.resolved_audience
                "keywords" = $node.keywords
            }
        }
    }
    
    $topK = if ($Mode -eq "alignment") { $TOPK_ALIGNMENT } else { $TOPK_DEDUP }
    $sorted = $candidates | Sort-Object -Property @{Expression="score"; Descending=$true} | Select-Object -First $topK
    
    $outFile = "$TempDir/rag_results.json"
    $sorted | ConvertTo-Json -Depth 5 | Out-File $outFile -Encoding UTF8
    Write-Host "Da ghi ket qua vao $outFile ($($sorted.Count) candidates)"
    
} elseif ($Mode -eq "dedup" -and $Scope -eq "full") {
    if (-not $Layer) {
        Write-Host "[ERR] Dedup full yeu cau -Layer" -ForegroundColor Red
        exit 1
    }
    
    $groups = @{} # "audienceId_type" -> @(paths)
    
    foreach ($prop in $Nodes.psobject.properties) {
        $path = $prop.Name
        $node = $prop.Value
        
        if ((Get-TypeGroup $node.type) -ne $Layer) { continue }
        if ($node.resolved_audience -eq "CONFLICT") { continue }
        
        $audId = if ($node.resolved_audience) { $node.resolved_audience.id } else { "NONE" }
        $groupKey = "${audId}_$($node.type)"
        
        if (-not $groups.ContainsKey($groupKey)) {
            $groups[$groupKey] = @()
        }
        $groups[$groupKey] += $path
    }
    
    $pairs = @()
    
    foreach ($group in $groups.Values) {
        for ($i = 0; $i -lt $group.Count; $i++) {
            for ($j = $i + 1; $j -lt $group.Count; $j++) {
                $path1 = $group[$i]
                $path2 = $group[$j]
                $node1 = $Nodes.$path1
                $node2 = $Nodes.$path2
                
                $score = Get-OverlapScore $node1.keywords $node2.keywords
                if ($score -ge $THRESHOLD_DEDUP) {
                    $pairs += @{
                        "score" = $score
                        "resolved_audience" = $node1.resolved_audience
                        "atom1" = @{
                            "path" = $path1
                            "description" = $node1.description
                            "keywords" = $node1.keywords
                        }
                        "atom2" = @{
                            "path" = $path2
                            "description" = $node2.description
                            "keywords" = $node2.keywords
                        }
                    }
                }
            }
        }
    }
    
    $sortedPairs = $pairs | Sort-Object -Property @{Expression="score"; Descending=$true}
    $outFile = "$TempDir/dedup_pairs.json"
    $sortedPairs | ConvertTo-Json -Depth 6 | Out-File $outFile -Encoding UTF8
    Write-Host "Da ghi ket qua vao $outFile ($($sortedPairs.Count) pairs)"
}
