---
description: 🔄 Khởi tạo cấu trúc cho một Workspace được clone
---

# WORKFLOW: /start-workspace - Initialize Cloned Workspace

**Mục tiêu:** Workflow này giúp hệ thống tự động dò tìm vị trí thư mục hiện tại để thay đổi các biến số tên "Workspace" và tên "Project Folder" đang bị ghi cứng (hardcode) trong các file cấu hình về đúng với thực tế.

**Yêu cầu trước khi chạy:** 
1. Đã clone (copy) tất cả thư mục hệ thống (ví dụ: `.agent`, `.agents`, `.brain`) sang folder cha (Workspace mới).
2. Đã tạo một folder con chứa mã nguồn bên trong Workspace mới.

---

## Bước 1: Chạy Script Tự Xác Định và Cập Nhật

// turbo-all

1. Chạy đoạn script PowerShell cực kỳ uy lực dưới đây. Script này sẽ lấy tên folder cha và đệ quy tìm folder con để thay lại tên vào `brain.json`, `preferences.json` và bảng luật `GEMINI.md`:

```powershell
$workspacePath = (Get-Item .).FullName
$workspaceName = (Get-Item .).Name

# Tìm thư mục con không bắt đầu bởi dấu chấm (bỏ qua .agent, .brain, .git...) để đính làm project folder
$projectFolder = Get-ChildItem -Directory | Where-Object { $_.Name -notmatch "^\." } | Select-Object -First 1

if (-not $projectFolder) {
    Write-Host "❌ Không tìm thấy thư mục dự án con! Hãy đảm bảo bạn đã tạo 1 folder con chứa source code."
    exit
}

$projectName = $projectFolder.Name
$projectPath = $projectFolder.FullName

Write-Host "🔄 Đang cập nhật cấu hình cho Workspace: [$workspaceName], Project: [$projectName]..."

# 1. Update brain.json
$brainFile = Join-Path $workspacePath ".brain\brain.json"
if (Test-Path $brainFile) {
    $brainData = Get-Content -Raw $brainFile -Encoding UTF8 | ConvertFrom-Json
    $brainData.project.name = $workspaceName
    $brainData | ConvertTo-Json -Depth 10 | Out-File -FilePath $brainFile -Encoding UTF8
    Write-Host "✅ Đã nhúng tên mới vào .brain\brain.json"
}

# 2. Update preferences.json cho các custom_rules
$prefFile = Join-Path $workspacePath ".brain\preferences.json"
if (Test-Path $prefFile) {
    $prefData = Get-Content -Raw $prefFile -Encoding UTF8 | ConvertFrom-Json
    for ($i = 0; $i -lt $prefData.custom_rules.Count; $i++) {
        if ($prefData.custom_rules[$i] -match "CẤU TRÚC LƯU TRỮ BẮT BUỘC:") {
            $prefData.custom_rules[$i] = "CẤU TRÚC LƯU TRỮ BẮT BUỘC: File của AWF (.brain, preferences.json, session.json...) lưu ở gốc $workspaceName."
        }
        if ($prefData.custom_rules[$i] -match "CẤU TRÚC LƯU MÃ NGUỒN:") {
            $prefData.custom_rules[$i] = "CẤU TRÚC LƯU MÃ NGUỒN: File trực tiếp của dự án (code, hình ảnh...) CHỈ ĐƯỢC PHÉP tạo bên trong folder con $projectName."
        }
    }
    
    # Format và unescape character \u0027
    $jsonOutput = ($prefData | ConvertTo-Json -Depth 10) -replace "\\u0027", "'"
    Set-Content -Path $prefFile -Value $jsonOutput -Encoding UTF8
    Write-Host "✅ Đã dập lại khuôn luật trong .brain\preferences.json"
}

# 3. Update lại Hiến pháp GEMINI.md (quét TẤT CẢ vị trí có thể, không dừng ở file đầu tiên)
# ⚡ FIX: Dùng .NET methods thay vì PowerShell cmdlets để kiểm soát encoding chính xác
#    - [System.IO.File]::ReadAllText() → đọc KHÔNG kèm BOM artifacts
#    - [System.IO.File]::WriteAllText() → ghi KHÔNG thêm trailing CRLF dư thừa
#    - Dùng "`r`n" (CRLF) thay vì "`n" (LF) → line endings nhất quán trên Windows
#    - Đảm bảo dòng trắng trước heading ## để markdown parse đúng
$geminiPaths = @(
    (Join-Path $workspacePath ".agent\GEMINI.md"),
    (Join-Path $workspacePath ".agents\GEMINI.md"),
    (Join-Path $workspacePath ".agents\rules\GEMINI.md")
)
$geminiUpdated = $false
foreach ($gf in $geminiPaths) {
    if (Test-Path $gf) {
        # Đọc file bằng .NET (tránh BOM issues của Get-Content)
        $content = [System.IO.File]::ReadAllText($gf, [System.Text.Encoding]::UTF8)

        # Chuẩn hóa TẤT CẢ line endings về CRLF trước khi xử lý
        $content = $content -replace "`r`n", "`n"   # CRLF → LF
        $content = $content -replace "`r", "`n"     # CR → LF  
        $content = $content -replace "`n", "`r`n"   # LF → CRLF (chuẩn Windows)

        # Xây dựng nội dung mới bằng CRLF ("`r`n") nhất quán
        # LƯU Ý: Dùng 2 backtick (``) để tạo 1 backtick literal. KHÔNG dùng 3 backtick vì sẽ escape ký tự $ phía sau
        $newRules = "## Workspace Rules ($workspaceName):" + "`r`n" +
                    "1. **Phân vùng lưu trữ File**:" + "`r`n" +
                    "   - **Các file hệ thống của AWF** (``.agent``, ``.brain``, ``preferences.json``, ``session.json``, v.v.) LUÔN LUÔN được lưu ở thư mục gốc: ``$workspacePath``." + "`r`n" +
                    "   - **Các file dự án code thực tế** (code ứng dụng, tài nguyên dự án, v.v.) LUÔN LUÔN được lưu bên trong thư mục con: ``$projectPath``." + "`r`n" +
                    "2. **Phạm vi Git Commit**: Khi dùng Git commit, thao tác commit cũng CHỈ được thực hiện đối với những thay đổi diễn ra ở trong folder ``$projectName``." + "`r`n" +
                    "3. **Ngoại lệ**: Chỉ chỉnh sửa hoặc thao tác trên khu vực thư mục gốc (``$workspaceName``) NẾU VÀ CHỈ NẾU user có yêu cầu trực tiếp về việc chỉnh sửa / config tại gốc workspace này." + "`r`n"

        # Tìm và thay thế phần Workspace Rules
        $marker = "## Workspace Rules"
        $idx = $content.IndexOf($marker)
        if ($idx -ge 0) {
            $before = $content.Substring(0, $idx)
            # ⚡ FIX: Đảm bảo có dòng trắng trước heading ## (markdown syntax requirement)
            $before = $before.TrimEnd() + "`r`n`r`n"
            $content = $before + $newRules
        }

        # Ghi file bằng .NET: UTF-8 WITHOUT BOM, KHÔNG thêm trailing newline dư
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($gf, $content, $utf8NoBom)
        Write-Host "✅ Đã đúc lại Workspace Rules trong: $gf"
        $geminiUpdated = $true
    }
}
if (-not $geminiUpdated) {
    Write-Host "⚠️ Không tìm thấy file GEMINI.md nào để cập nhật!"
}

Write-Host "🎉 HOÀN TẤT TỰ ĐỘNG CẬP NHẬT! Chúc bạn làm việc vui vẻ với dự án mới!"
```

## Bước 2: Báo cáo
2. Báo với User tiến trình cập nhật đã xong và mô tả sơ cấu trúc Tên Gốc (Workspace) và Tên Con (Project) mà mình vừa nhận diện được.
