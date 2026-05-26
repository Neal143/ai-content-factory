# ==============================================================================
# TÊN FILE       : compile-payload.ps1
# LAST UPDATE    : 26/05/2026 16:30 (GMT+7)
# VAI TRÒ        : Data Router & JIT Payload Compiler cho hệ thống Sub-agents.
# SỬ DỤNG KHI    : Chạy TRƯỚC khi gọi mỗi Sub-agent (từ Phase 2 trở đi).
# OUTPUT         : File payload duy nhất tại [RunFolder]/.temp/payload.md.
# TÓM TẮT LOGIC  : 
#   1. Phân tích bản đồ đầu vào (-InputMap).
#   2. Trích xuất Block dữ liệu bằng Regex động.
#   3. Fail-Safe: Thiếu Block bắt buộc -> exit 1.
#   4. Hỗ trợ file tùy chọn (prefix ?) cho nhánh Is_Novel_Angle.
#   5. Backward Extraction: [BLOCK: STRATEGY_UPDATE] -> ghi vào Blackboard.
#   6. Ghi payload sạch vào [RunFolder]/.temp/payload.md.
# ==============================================================================

param(
    [Parameter(Mandatory = $true)][string]$RunFolder,
    [Parameter(Mandatory = $true)][string]$InputMap,
    [string]$PrevOutput = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================================"
Write-Host "  JIT PAYLOAD COMPILER (compile-payload.ps1)"
Write-Host "========================================================================"

# ---- NHÓM 1: Backward Extraction (Strategy Update -> Blackboard) ----
# Nhóm này có nhiệm vụ trích xuất cập nhật chiến lược [BLOCK: STRATEGY_UPDATE] từ phase trước
# và tự động đồng bộ ngược lại vào file 00-blackboard.yaml để các phase sau sử dụng.
if ($PrevOutput) {
    $prevPath = if ([System.IO.Path]::IsPathRooted($PrevOutput)) { $PrevOutput } else { Join-Path $RunFolder $PrevOutput }
    if (Test-Path $prevPath) {
        $prevContent = Get-Content $prevPath -Raw -Encoding UTF8
        $strategyRegex = "(?s)\[BLOCK:\s*STRATEGY_UPDATE\s*\](.*?)\[/BLOCK:\s*STRATEGY_UPDATE\s*\]"
        if ($prevContent -match $strategyRegex) {
            $strategyData = $Matches[1].Trim()
            if ($strategyData.Length -gt 0) {
                $bbPath = Join-Path $RunFolder "00-blackboard.yaml"
                if (Test-Path $bbPath) {
                    $bbLines = Get-Content $bbPath -Encoding UTF8
                    $indented = ($strategyData -split "`r?`n" | ForEach-Object { "  $_" }) -join "`n"
                    $newLines = @()
                    $inserted = $false
                    foreach ($line in $bbLines) {
                        if ($line -match '^#\s*execution_key:' -and -not $inserted) {
                            $newLines += "strategy_updates: |"
                            $newLines += $indented
                            $inserted = $true
                        }
                        $newLines += $line
                    }
                    if (-not $inserted) { $newLines += "strategy_updates: |"; $newLines += $indented }
                    $newLines | Set-Content $bbPath -Encoding UTF8
                    Write-Host "  [OK] STRATEGY_UPDATE -> Blackboard."
                }
            }
        }
    }
}

# ---- NHÓM 2: Tạo thư mục .temp/ và khởi tạo buffer ----
# Nhóm này đảm bảo thư mục tạm .temp/ tồn tại trong thư mục chạy hiện hành
# và khởi tạo bộ đệm lưu trữ nội dung cho payload.md sắp sinh ra.
$tempFolder = Join-Path $RunFolder ".temp"
if (-not (Test-Path $tempFolder)) { New-Item -ItemType Directory -Path $tempFolder -Force | Out-Null }
$payloadPath = Join-Path $tempFolder "payload.md"
$payloadBuffer = @("# JIT PAYLOAD", "> Generated: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')", "---`n")

# ---- NHÓM 3: Phân tích InputMap & Trích xuất dữ liệu ----
# Nhóm này phân tích danh sách InputMap truyền vào, tìm các tệp nguồn tương ứng,
# trích xuất từng khối dữ liệu được chỉ định dạng block (ví dụ: file.md|BLOCK_NAME)
# hoặc nạp toàn bộ nội dung tệp. Hỗ trợ bỏ qua lỗi nếu tệp là tùy chọn (bắt đầu bằng dấu ?).
$items = $InputMap -split ","
foreach ($item in $items) {
    $item = $item.Trim()
    if (-not $item) { continue }

    # Parse nickname:source
    if ($item -match '^([^:]+):(.+)$') {
        $nickname = $Matches[1].Trim()
        $source = $Matches[2].Trim()

        # Kiểm tra prefix ? (file tùy chọn)
        $isOptional = $false
        if ($source.StartsWith("?")) {
            $isOptional = $true
            $source = $source.Substring(1)
        }

        # Tách fileName và blockName
        $fileName = $source
        $blockName = ""
        if ($source.Contains("|")) {
            $parts = $source -split "\|", 2
            $fileName = $parts[0].Trim()
            $blockName = $parts[1].Trim()
        }

        # Xác định đường dẫn tuyệt đối
        $filePath = if ([System.IO.Path]::IsPathRooted($fileName)) { $fileName } else { Join-Path $RunFolder $fileName }

        # Kiểm tra file tồn tại
        if (-not (Test-Path $filePath)) {
            if ($isOptional) {
                Write-Host "  [SKIP] File tuy chon khong ton tai: $fileName"
                continue
            }
            Write-Host "  [CRITICAL] File bat buoc khong ton tai: $filePath" -ForegroundColor Red
            exit 1
        }

        $fileContent = Get-Content $filePath -Raw -Encoding UTF8
        $extractedContent = ""

        if ($blockName) {
            # Gắp block cụ thể bằng Regex
            $blockRegex = "(?s)\[BLOCK:\s*$blockName\s*\](.*?)\[/BLOCK:\s*$blockName\s*\]"
            if ($fileContent -match $blockRegex) {
                $extractedContent = $Matches[1].Trim()
                Write-Host "  [OK] Gap block [$blockName] tu $fileName ($($extractedContent.Length) chars)"
            } else {
                if ($isOptional) {
                    Write-Host "  [SKIP] Block [$blockName] khong tim thay trong $fileName (optional)"
                    continue
                }
                Write-Host "  [CRITICAL] THIEU BLOCK [$blockName] trong $fileName!" -ForegroundColor Red
                exit 1
            }
        } else {
            $extractedContent = $fileContent.Trim()
            Write-Host "  [OK] Nap toan bo $fileName ($($extractedContent.Length) chars)"
        }

        $payloadBuffer += "=== BEGIN: $nickname ==="
        $payloadBuffer += $extractedContent
        $payloadBuffer += "=== END: $nickname ===`n"
    }
}

# ---- NHÓM 4: Ghi payload ----
# Gộp toàn bộ dữ liệu trong bộ đệm và ghi xuống tệp tin payload.md duy nhất bằng chuẩn mã hóa UTF-8.
$payloadBuffer -join "`n" | Set-Content $payloadPath -Encoding UTF8
Write-Host "  [SUCCESS] Payload tai: $payloadPath ($((Get-Item $payloadPath).Length) bytes)"
exit 0
