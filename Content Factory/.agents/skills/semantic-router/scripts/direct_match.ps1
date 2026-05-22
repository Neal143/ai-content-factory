<#
.SYNOPSIS
    Direct Match — Quét nhanh cơ học Input ngắn vào topic_map.yaml
.PARAMETER Topic
    Chuỗi yêu cầu tạo nội dung từ User (ngắn)
.PARAMETER TopicMapPath
    Đường dẫn tới file topic_map.yaml của User
#>
param(
    [string]$Topic,
    [string]$TopicMapPath = "personas/Default/topic_map.yaml",
    [string]$Pillar = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TopicMapPath)) {
    Write-Host "MISS: topic_map.yaml not found at $TopicMapPath"
    exit 1
}

$lines = Get-Content $TopicMapPath -Encoding UTF8

$matchedEntries = @()

# Quét từng entry: id và label
$currentId = $null
$currentLabel = $null
$currentPillar = $null
$currentAudience = $null

foreach ($line in $lines) {
    if ($line -match '^\s*-\s*id:\s*"?([^"#]+)"?') {
        $currentId = $Matches[1].Trim()
    }
    if ($line -match '^\s*label:\s*"?([^"#]+)"?') {
        $currentLabel = $Matches[1].Trim()
    }
    if ($line -match '^\s*pillar_parents:\s*\[?"?([^"\]#]+)"?\]?') {
        $currentPillar = $Matches[1].Trim()
    }
    if ($line -match '^\s*belongs_to_audience:\s*\[?"?([^"\]#]+)"?\]?') {
        $currentAudience = $Matches[1].Trim()
        
        # Lọc theo Pillar nếu có yêu cầu
        if ($Pillar -and $currentPillar -ne $Pillar) {
            $currentId = $null; $currentLabel = $null
            $currentPillar = $null; $currentAudience = $null
            continue
        }
        # Flush entry khi có đủ 4 trường
        if ($currentId -and $currentLabel) {
            $idMatch = $Topic -match [regex]::Escape($currentId.Replace("_"," "))
            $labelMatch = $Topic -match [regex]::Escape($currentLabel)
            if ($idMatch -or $labelMatch) {
                $matchedEntries += [PSCustomObject]@{
                    id = $currentId
                    label = $currentLabel
                    pillar = $currentPillar
                    audience = $currentAudience
                    depth = ($currentId -split "_").Count
                }
            }
            $currentId = $null; $currentLabel = $null
            $currentPillar = $null; $currentAudience = $null
        }
    }
}

if ($matchedEntries.Count -eq 0) {
    Write-Host "MISS"
    exit 1
}

# Cascade: chọn entry sâu nhất (nhiều underscore nhất = cấp hẹp nhất)
$best = $matchedEntries | Sort-Object -Property depth -Descending | Select-Object -First 1

Write-Host "MATCH"
Write-Host "id=$($best.id)"
Write-Host "label=$($best.label)"
Write-Host "pillar=$($best.pillar)"
Write-Host "audience=$($best.audience)"
exit 0
