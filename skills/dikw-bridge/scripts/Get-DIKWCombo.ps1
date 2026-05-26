<#
Tên file: Get-DIKWCombo.ps1
Last update: 27/05/2026 00:35 (GMT+7)
Vai trò: Script công cụ thực hiện truy vấn và lắp ghép tổ hợp DIKW Combo tối ưu từ Data Vault.
Sử dụng khi nào: Được gọi bởi dikw-bridge skill thay thế cho Bước 1-4 để tìm kiếm nguyên liệu viết bài đăng.
Output: In ra stdout 3 block dữ liệu: Bảng Combo (Markdown), Vivid Curation Payload (JSON), và Resolved JTBD (Text).
Tóm tắt logic hoạt động:
  1. Rebuild Index: Gọi build-vault-index.ps1 để cập nhật vault_index.json.
  2. Poka-Yoke Filters: Loại bỏ node confidence thấp hoặc bị rejected.
  3. Pre-Filter: Lọc nguồn TargetSourceIds (không áp dụng cho Nguồn 2-4).
  4. Lọc DAG 3 tầng: Tìm Anchor Insights khớp Topic + Audience -> Solutions/Concepts trỏ về -> Stories/Quotes/Data-Points trỏ về.
  5. Anti-Repetition: Loại bỏ các atoms đã dùng trong 3 bài post gần nhất của production-log.md.
  6. Nguồn 2-4 Integration: Quét bài viết thô của user để bổ sung vào stories.
  7. Viability Check & Selection: Tìm Insight tốt nhất thỏa mãn đủ số lượng nguyên tố và xuất kết quả.
#>

param (
    [Parameter(Mandatory = $true)]
    $Topics,

    [Parameter(Mandatory = $true)]
    $Audience,

    [Parameter(Mandatory = $false)]
    [string[]]$TargetSourceIds = @(),

    [Parameter(Mandatory = $true)]
    [string]$PersonaUser,

    [Parameter(Mandatory = $false)]
    [string]$VaultPath = "vault/01-Atomic",

    [Parameter(Mandatory = $false)]
    [string]$ProductionLog = "output/logs/production-log.md"
)

# ==========================================
# NHÓM 1: CẤU HÌNH HỆ THỐNG VÀ KHỞI TẠO CẤP CAO
# ==========================================
$ErrorActionPreference = "Stop"

# Cấu hình trọng số DIKW Layer
$DIKW_Weights = @{
    "story"      = 10
    "insight"    = 7
    "solution"   = 7
    "concept"    = 3
    "quote"      = 1
    "data_point" = 1
}

# Cấu hình trọng số Story Subtype
$Story_Subtype_Weights = @{
    "personal"     = 15
    "observed"     = 12
    "secondhand"   = 8
    "famous_world" = 7
    "historical"   = 5
}

# ==========================================
# NHÓM 2: HÀM TRỢ GIÚP (HELPERS)
# ==========================================
function Clean-Wikilink ([string]$val) {
    if ([string]::IsNullOrEmpty($val)) { return $null }
    $clean = $val.Trim().Trim("'").Trim('"')
    $clean = $clean.Replace("[[", "").Replace("]]", "")
    return $clean.Trim()
}

# ==========================================
# PHASE 0: REBUILD & LOAD VAULT INDEX
# ==========================================
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$buildScript = Join-Path $scriptDir "build-vault-index.ps1"
$indexPath = ".agents/skills/dikw-bridge/assets/vault_index.json"

# Rebuild index tự động
if (Test-Path $buildScript) {
    powershell -ExecutionPolicy Bypass -File $buildScript -VaultPath $VaultPath -OutputPath $indexPath | Out-Null
}

if (-not (Test-Path $indexPath)) {
    Write-Error "[ERR] Khong tim thay file vault_index.json tai: $indexPath"
}

$index = Get-Content -Path $indexPath -Raw -Encoding utf8 | ConvertFrom-Json

# ==========================================
# PHASE 1 & 2: POKA-YOKE & GLOBAL PRE-FILTER
# ==========================================
$validNodes = [ordered]@{ }

foreach ($key in $index.nodes.psobject.properties.name) {
    $node = $index.nodes.$key
    
    # 1. Poka-Yoke: Confidence và Status
    if ($node.confidence -lt 0.5) { continue }
    if ($node.status -in @("rejected", "quarantine")) { continue }
    
    # 2. Smart Pre-Filter: Lọc TargetSourceIds (Không lọc Nguồn 2-4)
    $isSource24 = ($key -like "*Posted*" -or $key -like "*Viral*" -or $key -like "*Reflective*")
    if (-not $isSource24 -and $TargetSourceIds.Count -gt 0) {
        if ($null -eq $node.source_id -or $node.source_id -notin $TargetSourceIds) {
            continue
        }
    }
    
    $validNodes[$key] = $node
}

# ==========================================
# PHASE 5: ANTI-REPETITION (ĐỌC POSTS CŨ)
# ==========================================
$usedAtoms = @()
if (Test-Path $ProductionLog) {
    $logContent = Get-Content -Path $ProductionLog -Raw -Encoding utf8
    
    # Lay 3 bai post gan nhat bang cach split (su dung hoan toan tieng Anh de tranh loi ma hoa)
    $posts = $logContent -split '(?m)^#\s*(Post|Posted|Bai dang)'
    $recentPosts = $posts | Select-Object -Last 3
    
    # Quét tất cả các path .md trong 3 bài viết này
    $matches = [regex]::Matches($recentPosts, 'vault/01-Atomic/[\w\-\/]+\.md')
    foreach ($m in $matches) {
        $usedAtoms += $m.Value
    }
    $usedAtoms = $usedAtoms | Select-Object -Unique
}

# ==========================================
# PHASE 7: NGUỒN 2-4 INTEGRATION (BÀI ĐĂNG THÔ)
# ==========================================
$Source24Nodes = [ordered]@{ }

$viralPath = "vault/$PersonaUser/Viral Posts"
$postedPath = "vault/$PersonaUser/Posted"
$reflectivePath = "vault/Content/Reflective Writing.md"

# Quét Viral Posts
if (Test-Path $viralPath) {
    $files = Get-ChildItem -Path $viralPath -Filter "*.md" -File
    foreach ($f in $files) {
        $relPath = "vault/$PersonaUser/Viral Posts/$($f.Name)"
        $Source24Nodes[$relPath] = [pscustomobject]@{
            "type"                = "story"
            "confidence"          = 0.9
            "topics"              = @()
            "source_id"           = $null
            "belongs_to_audience" = $null
            "status"              = "processed"
            "subtype"             = "personal"
        }
    }
}

# Quét Posted
if (Test-Path $postedPath) {
    $files = Get-ChildItem -Path $postedPath -Filter "*.md" -File
    foreach ($f in $files) {
        $relPath = "vault/$PersonaUser/Posted/$($f.Name)"
        $Source24Nodes[$relPath] = [pscustomobject]@{
            "type"                = "story"
            "confidence"          = 0.8
            "topics"              = @()
            "source_id"           = $null
            "belongs_to_audience" = $null
            "status"              = "processed"
            "subtype"             = "personal"
        }
    }
}

# Quét Reflective Writing
if (Test-Path $reflectivePath) {
    $Source24Nodes[$reflectivePath] = [pscustomobject]@{
        "type"                = "story"
        "confidence"          = 0.6
        "topics"              = @()
        "source_id"           = $null
        "belongs_to_audience" = $null
        "status"              = "processed"
        "subtype"             = "personal"
    }
}

# Gộp Nguồn 2-4 vào danh sách nodes hợp lệ (loại trừ các file đã dùng)
foreach ($key in $Source24Nodes.Keys) {
    if ($key -notin $usedAtoms) {
        $validNodes[$key] = $Source24Nodes[$key]
    }
}

# ==========================================
# PHASE 3: LỌC NHÁNH CHÍNH (ANCHOR INSIGHTS)
# ==========================================
# Chuẩn hóa Topics và Audience sang mảng (hỗ trợ cả Array và chuỗi phân tách bằng dấu phẩy)
$targetTopics = @()
if ($Topics -is [Array]) {
    $targetTopics = $Topics
} elseif ($Topics -is [String]) {
    $targetTopics = $Topics.Split(",").ForEach({ $_.Trim() })
} else {
    $targetTopics = @($Topics)
}

$targetAudienceClean = @()
if ($Audience -is [Array]) {
    foreach ($aud in $Audience) { $targetAudienceClean += Clean-Wikilink $aud }
} elseif ($Audience -is [String]) {
    foreach ($aud in $Audience.Split(",")) { $targetAudienceClean += Clean-Wikilink $aud }
} else {
    $targetAudienceClean = @(Clean-Wikilink $Audience)
}

$Anchors = @() # Danh sách các Insight paths thỏa mãn

foreach ($key in $validNodes.Keys) {
    $node = $validNodes[$key]
    if ($node.type -ne "insight") { continue }
    if ($key -in $usedAtoms) { continue }
    
    # 1. Check Topic Overlap
    $hasTopicOverlap = $false
    foreach ($t in $node.topics) {
        if ($t -in $targetTopics) {
            $hasTopicOverlap = $true
            break
        }
    }
    if (-not $hasTopicOverlap) { continue }
    
    # 2. Check Audience Match
    $audNodeClean = Clean-Wikilink $node.belongs_to_audience
    if ($audNodeClean -notin $targetAudienceClean) { continue }
    
    $Anchors += $key
}

# ==========================================
# PHASE 4: LỌC NHÁNH RỄ (TẦNG 3 VÀ TẦNG 4)
# ==========================================
$T3_Nodes = @() # Solutions/Concepts
$T4_Nodes = @() # Stories/Quotes/Data-Points

# Lọc Tầng 3
foreach ($key in $validNodes.Keys) {
    $node = $validNodes[$key]
    if ($node.type -notin @("solution", "concept")) { continue }
    if ($key -in $usedAtoms) { continue }
    
    # Check edges trỏ về Anchors
    $supportsInsight = $index.edges.supports_insight.$key
    if ($supportsInsight -and $supportsInsight -in $Anchors) {
        $T3_Nodes += $key
    }
}

# Lọc Tầng 4
foreach ($key in $validNodes.Keys) {
    $node = $validNodes[$key]
    if ($node.type -notin @("story", "quote", "data_point")) { continue }
    if ($key -in $usedAtoms) { continue }
    
    # Nếu là Nguồn 2-4 (đã gộp sẵn vào stories ở trên) -> Cho qua không cần link
    $isSource24 = ($key -like "*Posted*" -or $key -like "*Viral*" -or $key -like "*Reflective*")
    if ($isSource24) {
        $T4_Nodes += $key
        continue
    }
    
    # Check edges trỏ về Tầng 3
    $supportsKnowledge = $index.edges.supports_knowledge.$key
    if ($supportsKnowledge -and $supportsKnowledge -in $T3_Nodes) {
        $T4_Nodes += $key
    }
}

# ==========================================
# PHASE 6: ANCHOR-FIRST SELECTION & SCORING
# ==========================================
$Selected_Insight = $null
$Selected_Solution = $null
$Selected_Stories = @()
$Selected_DataQuotes = @()

# Hàm tính Relevance Score cho node
function Get-RelevanceScore ($nodePath, $nodeData) {
    $overlapCount = 0
    foreach ($t in $nodeData.topics) {
        if ($t -in $targetTopics) { $overlapCount++ }
    }
    # Tối thiểu 1 nếu có Nguồn 2-4 (topics trống)
    if ($overlapCount -eq 0) { $overlapCount = 1 }
    
    $weight = 1
    if ($DIKW_Weights.ContainsKey($nodeData.type)) {
        $weight = $DIKW_Weights[$nodeData.type]
    }
    return $overlapCount * $weight
}

# Tính điểm và sort Anchors
$scoredAnchors = @()
foreach ($insPath in $Anchors) {
    $nodeData = $validNodes[$insPath]
    $score = Get-RelevanceScore $insPath $nodeData
    
    # Downstream count (phục vụ tiebreaker)
    $downstreamCount = 0
    foreach ($t3 in $T3_Nodes) {
        if ($index.edges.supports_insight.$t3 -eq $insPath) {
            $downstreamCount++
            foreach ($t4 in $T4_Nodes) {
                if ($index.edges.supports_knowledge.$t4 -eq $t3) { $downstreamCount++ }
            }
        }
    }
    
    $scoredAnchors += [pscustomobject]@{
        Path       = $insPath
        Score      = $score
        Downstream = $downstreamCount
        Filename   = [System.IO.Path]::GetFileNameWithoutExtension($insPath)
    }
}

# Sap xep Anchors: Score DESC -> Downstream DESC -> Filename ASC (su dung cu phap Hashtable chuan cua PowerShell)
$sortedAnchors = $scoredAnchors | Sort-Object @{Expression="Score"; Descending=$true}, @{Expression="Downstream"; Descending=$true}, @{Expression="Filename"; Ascending=$true}

# Loop tìm Combo Viable tốt nhất
foreach ($anchor in $sortedAnchors) {
    $insPath = $anchor.Path
    
    # Lọc Tầng 3 trỏ về Insight này
    $viableT3 = @()
    foreach ($t3 in $T3_Nodes) {
        if ($index.edges.supports_insight.$t3 -eq $insPath) {
            $nodeData = $validNodes[$t3]
            $score = Get-RelevanceScore $t3 $nodeData
            $viableT3 += [pscustomobject]@{ Path = $t3; Data = $nodeData; Score = $score }
        }
    }
    
    # Sắp xếp Solutions/Concepts trỏ về Insight
    $sortedT3 = $viableT3 | Sort-Object @{Expression="Score"; Descending=$true}
    if ($sortedT3.Count -eq 0) { continue }
    
    # Thử từng Solution/Concept
    foreach ($t3Obj in $sortedT3) {
        $solPath = $t3Obj.Path
        
        # Lọc Tầng 4 trỏ về Solution này
        $viableT4 = @()
        foreach ($t4 in $T4_Nodes) {
            $isSource24 = ($t4 -like "*Posted*" -or $t4 -like "*Viral*" -or $t4 -like "*Reflective*")
            
            if ($isSource24 -or $index.edges.supports_knowledge.$t4 -eq $solPath) {
                $nodeData = $validNodes[$t4]
                $score = Get-RelevanceScore $t4 $nodeData
                
                # Tính điểm subtype cho Story
                $subtypeWeight = 0
                if ($nodeData.type -eq "story" -and $nodeData.subtype) {
                    if ($Story_Subtype_Weights.ContainsKey($nodeData.subtype)) {
                        $subtypeWeight = $Story_Subtype_Weights[$nodeData.subtype]
                    }
                }
                
                $viableT4 += [pscustomobject]@{ 
                    Path = $t4; 
                    Data = $nodeData; 
                    Score = $score; 
                    SubtypeWeight = $subtypeWeight 
                }
            }
        }
        
        # Phân loại Tầng 4 thành Stories và Data-Points/Quotes
        $stories = @()
        $dataQuotes = @()
        foreach ($t4Obj in $viableT4) {
            if ($t4Obj.Data.type -eq "story") {
                $stories += $t4Obj
            } else {
                $dataQuotes += $t4Obj
            }
        }
        
        # KIỂM TRA ĐIỀU KIỆN VIABLE (Khả thi)
        # - Có ít nhất 1 Story
        # - Có ít nhất 1 Data-Point hoặc Quote
        if ($stories.Count -ge 1 -and $dataQuotes.Count -ge 1) {
            $Selected_Insight = $insPath
            $Selected_Solution = $solPath
            
            # Chọn top 1-2 Stories: Sắp xếp theo SubtypeWeight DESC -> Score DESC (su dung cu phap Hashtable chuan cua PowerShell)
            $sortedStories = $stories | Sort-Object @{Expression="SubtypeWeight"; Descending=$true}, @{Expression="Score"; Descending=$true}
            $Selected_Stories = $sortedStories | Select-Object -First 2
            
            # Chọn top 3-5 Data/Quotes: Sắp xếp theo Score DESC (su dung cu phap Hashtable chuan cua PowerShell)
            $sortedDataQuotes = $dataQuotes | Sort-Object @{Expression="Score"; Descending=$true}
            $Selected_DataQuotes = $sortedDataQuotes | Select-Object -First 5
            
            break # Tìm thấy combo viable, thoát loop!
        }
    }
    
    if ($Selected_Insight) { break }
}

# ==========================================
# PHASE 8: OUTPUT GENERATOR
# ==========================================
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "PART 1: DIKW COMBO TABLE" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

if (-not $Selected_Insight) {
    Write-Host "[WARN] Khong tim thay Combo hop le nao thoa man dieu kien Viable!" -ForegroundColor Yellow
} else {
    Write-Host "Atom Path | DIKW Layer | Weight | Relevance Score | Node Tro"
    Write-Host "---|---|---|---|---"
    
    # 1. Insight
    $insData = $validNodes[$Selected_Insight]
    $insScore = Get-RelevanceScore $Selected_Insight $insData
    Write-Host "$Selected_Insight | Insight | 7 | $insScore | [Anchor]"
    
    # 2. Solution/Concept
    $solData = $validNodes[$Selected_Solution]
    $solScore = Get-RelevanceScore $Selected_Solution $solData
    Write-Host "$Selected_Solution | $($solData.type.ToUpper()) | $($DIKW_Weights[$solData.type]) | $solScore | $Selected_Insight"
    
    # 3. Stories
    foreach ($st in $Selected_Stories) {
        $stData = $validNodes[$st.Path]
        $isSource24 = ($st.Path -like "*Posted*" -or $st.Path -like "*Viral*" -or $st.Path -like "*Reflective*")
        $targetLink = if ($isSource24) { "[Nguon 2-4]" } else { $Selected_Solution }
        Write-Host "$($st.Path) | Story | 10 | $($st.Score) | $targetLink"
    }
    
    # 4. Data-Points / Quotes
    foreach ($dq in $Selected_DataQuotes) {
        $dqData = $validNodes[$dq.Path]
        Write-Host "$($dq.Path) | $($dqData.type.ToUpper()) | 1 | $($dq.Score) | $Selected_Solution"
    }
}

Write-Host "`n==================================================" -ForegroundColor Magenta
Write-Host "PART 2: VIVID CURATION PAYLOAD JSON" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

if ($Selected_Insight) {
    # Thu thập và gộp vivid data
    $vividPayload = @{
        "vivid_circumstances" = @()
        "vivid_insights"      = @()
        "vivid_knowledges"    = @()
    }
    
    $allComboPaths = @($Selected_Insight, $Selected_Solution)
    foreach ($st in $Selected_Stories) { $allComboPaths += $st.Path }
    foreach ($dq in $Selected_DataQuotes) { $allComboPaths += $dq.Path }
    
    foreach ($path in $allComboPaths) {
        # Đọc trực tiếp file thô để parse vivid data an toàn
        if (Test-Path $path) {
            $rawContent = Get-Content -Path $path -Raw -Encoding utf8
            
            # Trích xuất vivid_circumstances
            if ($rawContent -match 'belongs_to_audience:\s*(.+)') {
                $aud = Clean-Wikilink $Matches[1]
                if ($aud -and $aud -notin $vividPayload.vivid_circumstances) {
                    $vividPayload.vivid_circumstances += $aud
                }
            }
            
            # Trích xuất vivid_insights
            if ($rawContent -match 'vivid_insights:\s*\[([^\]]*)\]') {
                $rawList = $Matches[1]
                if (-not [string]::IsNullOrEmpty($rawList)) {
                    $items = $rawList.Split(",")
                    foreach ($item in $items) {
                        $itemClean = $item.Trim().Trim("'").Trim('"')
                        if ($itemClean -and $itemClean -notin $vividPayload.vivid_insights) {
                            $vividPayload.vivid_insights += $itemClean
                        }
                    }
                }
            }
            # Dự phòng dạng string
            if ($rawContent -match 'vivid_insights:\s*"([^"]+)"') {
                $itemClean = $Matches[1].Trim()
                if ($itemClean -and $itemClean -notin $vividPayload.vivid_insights) {
                    $vividPayload.vivid_insights += $itemClean
                }
            }
            
            # Trích xuất vivid_knowledges (cho solutions/concepts)
            if ($rawContent -match 'vivid_knowledges:\s*\[([^\]]*)\]') {
                $rawList = $Matches[1]
                if (-not [string]::IsNullOrEmpty($rawList)) {
                    $items = $rawList.Split(",")
                    foreach ($item in $items) {
                        $itemClean = $item.Trim().Trim("'").Trim('"')
                        if ($itemClean -and $itemClean -notin $vividPayload.vivid_knowledges) {
                            $vividPayload.vivid_knowledges += $itemClean
                        }
                    }
                }
            }
            # Dự phòng dạng string
            if ($rawContent -match 'vivid_knowledges:\s*"([^"]+)"') {
                $itemClean = $Matches[1].Trim()
                if ($itemClean -and $itemClean -notin $vividPayload.vivid_knowledges) {
                    $vividPayload.vivid_knowledges += $itemClean
                }
            }
        }
    }
    
    # In JSON minified
    Write-Host (ConvertTo-Json -InputObject $vividPayload -Compress)
} else {
    Write-Host "{}"
}

Write-Host "`n==================================================" -ForegroundColor Magenta
Write-Host "PART 3: RESOLVED JTBD DATA" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

if ($Selected_Insight) {
    $insNode = $validNodes[$Selected_Insight]
    $audienceId = Clean-Wikilink $insNode.belongs_to_audience
    $audienceFile = "vault/01-Atomic/Audiences/$audienceId.md"
    
    if (Test-Path $audienceFile) {
        $audContent = Get-Content -Path $audienceFile -Raw -Encoding utf8
        
        $jobPerformer = "unknown"
        $mainJob = "unknown"
        $circumstances = "unknown"
        
        if ($audContent -match 'audience_Job_performer:\s*(.+)') { $jobPerformer = $Matches[1].Trim().Trim("'").Trim('"') }
        if ($audContent -match 'audience_main_job:\s*(.+)') { $mainJob = $Matches[1].Trim().Trim("'").Trim('"') }
        if ($audContent -match 'audience_circumstance:\s*(.+)') { $circumstances = $Matches[1].Trim().Trim("'").Trim('"') }
        
        Write-Host "Audience ID: $audienceId"
        Write-Host "Job Performer: $jobPerformer"
        Write-Host "Main Job: $mainJob"
        Write-Host "Circumstances: $circumstances"
    } else {
        Write-Host "[WARN] Khong tim thay file Audience vat ly tai: $audienceFile"
    }
} else {
    Write-Host "[WARN] Khong co resolved JTBD do khong co Combo."
}
Write-Host "==================================================" -ForegroundColor Magenta
