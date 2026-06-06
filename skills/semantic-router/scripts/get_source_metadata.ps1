# Tên file: get_source_metadata.ps1
# Last update: 05/06/2026 11:30 (GMT+7)
# Vai trò: Trích xuất metadata nguồn siêu tốc (Zero-Inference) phục vụ định tuyến ngữ nghĩa.
# Sử dụng khi nào: Được gọi ở Phase 0 bởi semantic-router agent để phân tích thông tin file nguồn.
# Output: Trả về chuỗi JSON chứa topic_ids, Target_Audience, Target_Source_Type, Target_Source_IDs.
# Tóm tắt logic hoạt động:
#   1. Tìm kiếm file markdown nguồn khớp với SearchTerm trong vault/02-sources.
#   2. Đọc và phân tích nội dung file để trích xuất source_id và metadata của các chunk.
#   3. Kiểm tra trùng lặp trong production-log.md để đảm bảo không tái sử dụng các tổ hợp chủ đề + độc giả đã xuất bản.
#   4. Xuất thông tin dưới định dạng JSON nén để trả về cho Agent.

param (
    [Parameter(Mandatory=$true)]
    [string]$SearchTerm,
    
    [string]$CHUNK_index = ""
)

# 1. Dựng đường dẫn và tìm file
$files = Get-ChildItem -Path "vault/02-sources" -Recurse | Where-Object { $_.Name -match $SearchTerm -and $_.Extension -eq ".md" }
if (-not $files) {
    throw "Khong tim thay file nguon nao khop voi tu khoa: $SearchTerm"
}
$file = $files[0]
$Target_Source_Type = $file.Directory.Name.TrimEnd('s')

# 2. Đọc nội dung
$content = Get-Content -Path $file.FullName -Raw

$source_id = ""
$topics = @()
$audience = ""
$topics_str = ""

# Đọc production-log.md để lấy danh sách (Topic, Audience) đã sử dụng
$usedCombos = @()
$logPath = "vault/.content-pipeline/logs/production-log.md"
if (Test-Path $logPath) {
    $logContent = Get-Content $logPath -Raw
    $logBlocks = $logContent -split "## "
    foreach ($block in $logBlocks) {
        if ([string]::IsNullOrWhiteSpace($block)) { continue }
        $topicMatch = [regex]::Match($block, "- \*\*Topic\*\*: `?`"([^`"]+)`"`?")
        $audMatch = [regex]::Match($block, "- \*\*Target_Audience\*\*: (.*?)(?:\r|\n|$)")
        $postTitleMatch = [regex]::Match($block, "^.*?(?:\-|\u2013|\u2014)\s*(.*?)(?:\r|\n)")
        
        if ($topicMatch.Success -and $audMatch.Success) {
            $t = $topicMatch.Groups[1].Value.Trim()
            $a = $audMatch.Groups[1].Value.Trim()
            $title = ""
            if ($postTitleMatch.Success) { $title = $postTitleMatch.Groups[1].Value.Trim() }
            $usedCombos += [PSCustomObject]@{ Topic = $t; Audience = $a; Title = $title }
        }
    }
}

# 3. Phân nhánh Regex
if ([string]::IsNullOrWhiteSpace($CHUNK_index)) {
    # Cấp Sách
    if ($content -match "RESOLVED_BOOK_META: source_id=\[(.*?)\]") {
        $source_id = $matches[1]
    }
    
    # Tìm tất cả các RESOLVED_CHUNK_META
    $chunkMatches = [regex]::Matches($content, "RESOLVED_CHUNK_META: source_id=\[.*?\] \| topic_ids=\[(.*?)\] \| audience_filename=(.*?)(\r|\n|$)")
    
    $foundChunk = $false
    $conflictTitle = ""
    
    foreach ($match in $chunkMatches) {
        $c_topics_str = $match.Groups[1].Value
        $c_audience = $match.Groups[2].Value.Trim()
        
        $c_topics = @()
        if (-not [string]::IsNullOrWhiteSpace($c_topics_str)) {
            $temp_str = $c_topics_str -replace '"', ''
            if ($temp_str.Contains(",")) {
                $c_topics = $temp_str -split "," | ForEach-Object { $_.Trim() }
            } elseif ($temp_str.Length -gt 0) {
                $c_topics = @($temp_str.Trim())
            }
        }
        
        # Check xem chunk này có hợp lệ không (chưa được sử dụng)
        $isUsed = $false
        foreach ($t in $c_topics) {
            foreach ($used in $usedCombos) {
                if ($used.Topic -eq $t -and $used.Audience -eq $c_audience) {
                    $isUsed = $true
                    $conflictTitle = $used.Title
                    break
                }
            }
            if ($isUsed) { break }
        }
        
        if (-not $isUsed) {
            $topics_str = $c_topics_str
            $audience = $c_audience
            $foundChunk = $true
            break
        }
    }
    
    if (-not $foundChunk) {
        if ($conflictTitle -ne "") {
            throw "Co ve nhu toan bo cac phan cua tai lieu nay da duoc su dung. Vui long kiem tra lai bai: $conflictTitle"
        } else {
            throw "Khong tim thay chunk nao kha dung cho tai lieu nay."
        }
    }
} else {
    # Cấp Chunk
    $pattern = "CHUNK_index=$CHUNK_index\b.*?[\r\n]+RESOLVED_CHUNK_META: source_id=\[(.*?)\] \| topic_ids=\[(.*?)\] \| audience_filename=(.*?)(\r|\n|$)"
    if ($content -match $pattern) {
        $source_id = $matches[1]
        $topics_str = $matches[2]
        $audience = $matches[3].Trim()
        
        # Parse topics
        $c_topics = @()
        if (-not [string]::IsNullOrWhiteSpace($topics_str)) {
            $temp_str = $topics_str -replace '"', ''
            if ($temp_str.Contains(",")) {
                $c_topics = $temp_str -split "," | ForEach-Object { $_.Trim() }
            } elseif ($temp_str.Length -gt 0) {
                $c_topics = @($temp_str.Trim())
            }
        }
        
        # Check xem chunk đích danh này đã được sử dụng chưa
        $isUsed = $false
        $conflictTitle = ""
        foreach ($t in $c_topics) {
            foreach ($used in $usedCombos) {
                if ($used.Topic -eq $t -and $used.Audience -eq $audience) {
                    $isUsed = $true
                    $conflictTitle = $used.Title
                    break
                }
            }
            if ($isUsed) { break }
        }
        
        if ($isUsed) {
            throw "Canh bao: Chunk dich danh ($CHUNK_index) ban yeu cau da duoc su dung trong bai: $conflictTitle. Vui long chon 1 phan khac."
        }
    } else {
        throw "Khong tim thay CHUNK_index=$CHUNK_index trong tai lieu."
    }
}

# Xử lý Topics String (JSON array format)
if (-not [string]::IsNullOrWhiteSpace($topics_str)) {
    $topics_str = $topics_str -replace '"', ''
    if ($topics_str.Contains(",")) {
        $topics = $topics_str -split "," | ForEach-Object { $_.Trim() }
    } elseif ($topics_str.Length -gt 0) {
        $topics = @($topics_str.Trim())
    }
}

# 4. Trả về JSON
$result = @{
    topic_ids = $topics
    Target_Audience = $audience
    Target_Source_Type = $Target_Source_Type
    Target_Source_IDs = @($source_id)
}

$result | ConvertTo-Json -Depth 5 -Compress
