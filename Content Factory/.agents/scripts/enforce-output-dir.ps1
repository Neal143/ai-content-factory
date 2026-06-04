try {
    # Đọc luồng dữ liệu chuẩn từ stdin
    $rawInput = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($rawInput)) { Write-Output "{}"; exit 0 }
    
    # Chuyển đổi JSON thành Object PowerShell
    $payload = $rawInput | ConvertFrom-Json
    
    # Rút trích đường dẫn file đích từ payload tool call
    $targetFile = $payload.toolCall.args.TargetFile
    if (-not $targetFile) { Write-Output "{}"; exit 0 }
    
    # Chuẩn hóa đường dẫn đích
    $normalizedTarget = [System.IO.Path]::GetFullPath($targetFile).ToLowerInvariant()
    $workspaceBase = "d:\AI\AI content factory - v3.7B\Content Factory"
    
    # Truy tìm Context bằng Regex quét ngược từ transcript
    $transcriptPath = $payload.transcriptPath
    if (-not (Test-Path $transcriptPath)) { Write-Output "{}"; exit 0 }
    
    # Đọc 200 dòng cuối cùng (Bỏ qua lỗi khóa file nếu có)
    $recentLines = Get-Content $transcriptPath -Tail 200 -ErrorAction SilentlyContinue | Out-String
    
    # Tìm kiếm các workflow mục tiêu
    $matches = [regex]::Matches($recentLines, "(content-post|book-extractor)")
    
    if ($matches.Count -eq 0) {
        # Không tìm thấy workflow bị kiểm duyệt -> Bỏ qua
        Write-Output "{}"
        exit 0
    }
    
    # Xác định Workflow gần nhất được gọi (Phần tử cuối cùng)
    $activeWorkflow = $matches[$matches.Count - 1].Value
    
    # Phân luồng thư mục hợp lệ theo Workflow
    $allowedRelative = ""
    if ($activeWorkflow -eq "content-post") {
        $allowedRelative = "output"
    } elseif ($activeWorkflow -eq "book-extractor") {
        $allowedRelative = ".extraction_runs"
    }
    
    # Chuẩn hóa đường dẫn thư mục bắt buộc
    $allowedBase = [System.IO.Path]::GetFullPath("$workspaceBase\$allowedRelative").ToLowerInvariant()
    
    # So sánh an toàn (đúng bằng thư mục đích hoặc nằm trong thư mục đích)
    if ($normalizedTarget -eq $allowedBase -or $normalizedTarget.StartsWith($allowedBase + "\")) {
        # Hợp lệ -> Bỏ qua
        Write-Output "{}"
        exit 0
    }
    
    # Nếu vi phạm, trả về thông báo lỗi dạng JSON buộc Platform phải chặn và hiển thị
    $response = @{
        decision = "force_ask"
        reason = "🚨 Cảnh báo hệ thống: Agent đang thực thi quy trình [$activeWorkflow] nhưng cố ghi file ngoài thư mục bắt buộc ([$allowedRelative]).`nĐường dẫn vi phạm: [$targetFile](file:///$targetFile).`nTiến trình đã bị chặn. Vui lòng bấm Deny."
    }
    
    # Nén chuỗi JSON in ra một dòng duy nhất cho stdout
    $response | ConvertTo-Json -Compress | Write-Output
} catch {
    # Failsafe: Trả về Object rỗng để bỏ qua hook nếu có lỗi bất ngờ
    Write-Output "{}"
}
