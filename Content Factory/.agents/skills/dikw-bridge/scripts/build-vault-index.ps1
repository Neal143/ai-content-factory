<#
Tên file: build-vault-index.ps1
Last update: 27/05/2026 00:35 (GMT+7)
Vai trò: Script PowerShell quét toàn bộ Data Vault nguyên tố DIKW và xây dựng Index dạng JSON (nodes và edges).
Sử dụng khi nào: Được gọi tự động trước mỗi truy vấn DIKW Combo để cung cấp cơ sở dữ liệu in-memory tốc độ cao O(1).
Output: File vault_index.json chứa toàn bộ thông tin metadata của các atoms và các liên kết DAG.
Tóm tắt logic hoạt động:
  1. Quét qua 6 thư mục nguyên tố DIKW trong vault/01-Atomic/.
  2. Với mỗi file, parse YAML frontmatter đầu tiên một cách an toàn bằng regex (bỏ qua các fake YAML trong comment block HTML).
  3. Strip wikilinks [[...]] khỏi các liên kết nguyên tố.
  4. Chuẩn hóa dữ liệu (mảng inline, số thực confidence).
  5. Xây dựng bảng tra cứu nhanh filename -> full path.
  6. Ánh xạ các liên kết edges (supports_insight, supports_knowledge) từ filename sang full path tương đối chuẩn.
  7. Xuất cấu trúc JSON hoàn chỉnh ra OutputPath.
#>

param (
    [Parameter(Mandatory = $false)]
    [string]$VaultPath = "vault/01-Atomic",

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ".agents/skills/dikw-bridge/assets/vault_index.json"
)

# ==========================================
# NHÓM 1: KHỞI TẠO CẤU HÌNH VÀ BIẾN TOÀN CỤC
# ==========================================
$ErrorActionPreference = "Stop"

# Định nghĩa 6 thư mục DIKW và loại tương ứng
$DIKW_Folders = @{
    "Insights"    = "insight"
    "Solutions"   = "solution"
    "Concepts"    = "concept"
    "Stories"     = "story"
    "Quotes"      = "quote"
    "Data-Points" = "data_point"
}

# Khởi tạo cấu trúc lưu trữ index
$Nodes = [ordered]@{ }
$Edges_SupportsInsight = [ordered]@{ }
$Edges_SupportsKnowledge = [ordered]@{ }
$FilenameLookup = @{ } # Tra cứu nhanh: "GI_filename" -> "vault/01-Atomic/Insights/GI_filename.md"
$RawEdges = New-Object System.Collections.Generic.List[System.Object] # Lưu tạm: @{ Source = "path"; Type = "insight/knowledge"; Target = "filename" }

# ==========================================
# NHÓM 2: HÀM TRỢ GIÚP (HELPERS)
# ==========================================
function Clean-Wikilink ([string]$val) {
    <#
    Loại bỏ cặp dấu ngoặc vuông kép [[ ]] và dấu nháy đơn/kép bao quanh giá trị liên kết bằng so khớp literal.
    #>
    if ([string]::IsNullOrEmpty($val)) { return $null }
    $clean = $val.Trim().Trim("'").Trim('"')
    $clean = $clean.Replace("[[", "").Replace("]]", "")
    return $clean.Trim()
}

function Parse-YAMLValue ([string]$key, [string]$val) {
    <#
    Parse giá trị YAML thô sang kiểu dữ liệu phù hợp trong PowerShell.
    #>
    $val = $val.Trim()
    
    # 1. Xử lý null/empty
    if ($val -eq "null" -or $val -eq "~" -or $val -eq "") {
        return $null
    }
    
    # 2. Xử lý trường hợp Array Inline: [item1, item2] hoặc ["item1", "item2"]
    if ($val.StartsWith("[") -and $val.EndsWith("]")) {
        try {
            # Normalize array để convert qua JSON an toàn
            $jsonVal = $val -replace "'", '"'
            $arr = ConvertFrom-Json $jsonVal -ErrorAction SilentlyContinue
            if ($arr -is [Array]) {
                $cleanArr = New-Object System.Collections.ArrayList
                foreach ($item in $arr) {
                    [void]$cleanArr.Add((Clean-Wikilink $item))
                }
                return $cleanArr.ToArray()
            }
        } catch {}
        
        # Fallback nếu JSON parse fail
        $items = $val.Trim("[", "]").Split(",")
        $cleanArr = New-Object System.Collections.ArrayList
        foreach ($item in $items) {
            $itemClean = Clean-Wikilink $item
            if (![string]::IsNullOrEmpty($itemClean)) {
                [void]$cleanArr.Add($itemClean)
            }
        }
        return $cleanArr.ToArray()
    }
    
    # 3. Xử lý trường confidence sang kiểu Double
    if ($key -eq "confidence") {
        [double]$num = 0.0
        if ([double]::TryParse($val, [System.Globalization.NumberStyles]::Any, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$num)) {
            return $num
        }
    }
    
    # 4. Xử lý các liên kết wikilink thông thường
    if ($val.Contains("[[")) {
        return Clean-Wikilink $val
    }
    
    # Mặc định trả về chuỗi đã strip nháy bao quanh
    return $val.Trim("'").Trim('"')
}

# ==========================================
# NHÓM 3: LOGIC QUÉT VAULT VÀ PARSE FRONTMATTER
# ==========================================
Write-Host ">>> Bat dau quet vault tai: $VaultPath" -ForegroundColor Cyan

foreach ($folderName in $DIKW_Folders.Keys) {
    $folderPath = Join-Path $VaultPath $folderName
    if (-not (Test-Path $folderPath)) {
        Write-Host "[WARN] Thu muc khong ton tai: $folderPath (Bo qua)" -ForegroundColor Yellow
        continue
    }
    
    $atomType = $DIKW_Folders[$folderName]
    $files = Get-ChildItem -Path $folderPath -Filter "*.md" -File
    
    foreach ($file in $files) {
        # Loại bỏ các file hệ thống ẩn, .gitkeep hoặc file bắt đầu bằng "_"
        if ($file.Name.StartsWith("_") -or $file.Name -eq ".gitkeep") {
            continue
        }
        
        $relativeCwdPath = "vault/01-Atomic/$folderName/$($file.Name)"
        $fileContent = Get-Content -Path $file.FullName -Raw -Encoding utf8
        
        # Đọc frontmatter an toàn: Chỉ lấy block nằm giữa cặp '---' đầu tiên của file
        $lines = $fileContent -split '\r?\n'
        if ($lines.Count -lt 2 -or $lines[0].Trim() -ne "---") {
            Write-Host "[ERR] File khong co frontmatter hop le: $relativeCwdPath" -ForegroundColor Red
            continue
        }
        
        $frontmatterData = @{
            "type"                = $atomType
            "topics"              = @()
            "source_id"           = $null
            "belongs_to_audience" = $null
            "confidence"          = 1.0
            "status"              = $null
            "insight_type"        = $null
            "subtype"             = $null
            "knowledge_type"      = $null
        }
        
        $inFrontmatter = $true
        # Lặp qua từng dòng của frontmatter (bắt đầu từ dòng thứ 2)
        for ($i = 1; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ($line.Trim() -eq "---") {
                $inFrontmatter = $false
                break
            }
            
            # Parse YAML key-value bằng regex
            if ($line -match '^\s*(\w+):\s*(.+)$') {
                $key = $Matches[1].ToLower()
                $valRaw = $Matches[2]
                
                $parsedVal = Parse-YAMLValue $key $valRaw
                $frontmatterData[$key] = $parsedVal
            }
        }
        
        if ($inFrontmatter) {
            Write-Host "[ERR] Frontmatter khong khep kin trong file: $relativeCwdPath" -ForegroundColor Red
            continue
        }
        
        # Đưa node vào danh sách Nodes chính thức
        $Nodes[$relativeCwdPath] = $frontmatterData
        
        # Cập nhật Lookup Table: "GI_tên-file" -> "vault/01-Atomic/..."
        $filenameKey = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $FilenameLookup[$filenameKey] = $relativeCwdPath
        
        # Lưu các raw edges để resolve sau bằng Generic List Add
        $remainingLines = $lines | Select-Object -Skip ($i + 1)
        if (($remainingLines -join "`n") -match 'supports_insight:\s*(.+)') {
            $target = Clean-Wikilink $Matches[1]
            if (-not [string]::IsNullOrEmpty($target)) {
                $RawEdges.Add(@{ Source = $relativeCwdPath; Type = "insight"; Target = $target })
            }
        }
        # Nếu đã parse được trong YAML properties
        if ($frontmatterData.ContainsKey("supports_insight") -and $frontmatterData["supports_insight"]) {
            $RawEdges.Add(@{ Source = $relativeCwdPath; Type = "insight"; Target = $frontmatterData["supports_insight"] })
        }
        if ($frontmatterData.ContainsKey("supports_knowledge") -and $frontmatterData["supports_knowledge"]) {
            $RawEdges.Add(@{ Source = $relativeCwdPath; Type = "knowledge"; Target = $frontmatterData["supports_knowledge"] })
        }
    }
}

# ==========================================
# NHÓM 4: LOGIC RESOLVE EDGES (DỰA TRÊN LOOKUP TABLE)
# ==========================================
Write-Host ">>> Bat dau resolve edges..." -ForegroundColor Cyan

foreach ($edge in $RawEdges) {
    $source = $edge.Source
    $targetName = $edge.Target
    
    # Tìm kiếm target full path từ bảng tra cứu lookup
    $targetPath = $null
    if ($FilenameLookup.ContainsKey($targetName)) {
        $targetPath = $FilenameLookup[$targetName]
    } else {
        # Dự phòng trường hợp user chèn trực tiếp đuôi .md trong wikilink
        $cleanTargetName = $targetName -replace '\.md$', ''
        if ($FilenameLookup.ContainsKey($cleanTargetName)) {
            $targetPath = $FilenameLookup[$cleanTargetName]
        }
    }
    
    if ($targetPath) {
        if ($edge.Type -eq "insight") {
            $Edges_SupportsInsight[$source] = $targetPath
        } else {
            $Edges_SupportsKnowledge[$source] = $targetPath
        }
    } else {
        Write-Host "[WARN] Orphan link! Khong tim thay path cho atom: '$targetName' (tu file: $source)" -ForegroundColor Yellow
    }
}

# ==========================================
# NHÓM 5: TỔNG HỢP VÀ XUẤT FILE JSON CẤU TRÚC
# ==========================================
$IndexData = [ordered]@{
    "metadata" = @{
        "last_updated" = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        "node_count"   = $Nodes.Count
        "edge_count"   = $Edges_SupportsInsight.Count + $Edges_SupportsKnowledge.Count
    }
    "nodes"    = $Nodes
    "edges"    = @{
        "supports_insight"   = $Edges_SupportsInsight
        "supports_knowledge" = $Edges_SupportsKnowledge
    }
}

# Tạo thư mục đầu ra nếu chưa có
$outputDir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Xuất ra file JSON dưới định dạng UTF-8 no BOM
$jsonString = ConvertTo-Json -InputObject $IndexData -Depth 100
[System.IO.File]::WriteAllText($OutputPath, $jsonString, [System.Text.Encoding]::UTF8)

Write-Host "[SUCCESS] Da build thanh cong index voi $($Nodes.Count) nodes va $($IndexData.metadata.edge_count) edges!" -ForegroundColor Green
Write-Host "[SUCCESS] File index duoc ghi tai: $OutputPath" -ForegroundColor Green
