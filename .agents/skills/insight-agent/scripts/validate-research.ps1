# Last Update: 28/04/2026 15:24 (GMT+7)
<#
.SYNOPSIS
    Tên file: validate-research.ps1
    Vai trò: Làm "người gác cổng" (Quality Gate) cho Phase 2 (Insight Agent).
    Được sử dụng khi nào: Chạy tự động ngay sau khi Insight Agent tạo xong file research-brief.md.
    Input: Đường dẫn file research-brief.md.
    Output: Trả về PASS/FAIL cho 3 tiêu chí (Số lượng data, Nguồn câu chuyện, KCS status) và log ra màn hình. Nếu có lỗi, exit code > 0.
.DESCRIPTION
    Tóm tắt logic hoạt động:
    1. Kiểm tra tối thiểu 5 con số/data cụ thể.
    2. Nếu có story thì phải có source tags (vault / famous / book / none).
    3. Đảm bảo KCS status là PASS.
.PARAMETER ResearchPath
    Đường dẫn tới research-brief.md
.NOTES
    Last Update: 05/05/2026 10:00 (GMT+7)
#>

param(
    [Parameter(Mandatory=$true)][string]$ResearchPath
)

$ErrorActionPreference = "Stop"
$results = @()
$passCount = 0
$failCount = 0

function Add-Result($check, $status, $detail) {
    $script:results += [PSCustomObject]@{ Check = $check; Status = $status; Detail = $detail }
    if ($status -eq "PASS") { $script:passCount++ } else { $script:failCount++ }
}

# Kiểm tra vật lý: Nếu file research-brief.md không tồn tại thì báo lỗi và dừng toàn bộ (exit 1)
if (-not (Test-Path $ResearchPath)) {
    Write-Host "ERROR: Research brief not found at $ResearchPath"; exit 1
}
# Đọc toàn bộ nội dung text của file vào biến $research
$research = Get-Content $ResearchPath -Raw -Encoding UTF8

# ============================================================
# CHECK 1: KIỂM TRA ĐỘ CHI TIẾT CỦA DỮ LIỆU (Specific Numbers Count)
# - Mục đích: Ép Insight Agent phải đưa ra dẫn chứng bằng con số cụ thể, tránh việc viết chung chung sáo rỗng.
# - Dấu hiệu tìm kiếm: Dùng Regex quét tìm các con số (có thể chứa dấu phẩy/chấm) đứng kèm các từ khóa như: %, phần trăm, năm, tháng, triệu, tỷ, nghìn...
# - Điều kiện PASS: Bắt buộc phải quét ra từ 5 cụm số liệu trở lên.
# ============================================================
# Match patterns: digits with %, year-like numbers, decimal numbers, percentages
# Thực thi quét bằng Regex: Đếm các số liệu đi kèm % hoặc đơn vị đo lường
$numberMatches = [regex]::Matches($research, '\b\d+[.,]?\d*\s*(%|phần trăm|năm|tháng|tuần|ngày|lần|triệu|tỷ|nghìn|k\b|hours?|times?)?')
# Gán tổng số lượng quét được vào biến $numberCount
$numberCount = $numberMatches.Count
# Kiểm tra: Nếu biến đếm >= 5 thì cho PASS, ngược lại FAIL
if ($numberCount -ge 5) {
    Add-Result "Specific Numbers" "PASS" "$numberCount numbers found (min 5)"
}
else {
    Add-Result "Specific Numbers" "FAIL" "$numberCount numbers found (min 5)"
}

# ============================================================
# CHECK 2: KIỂM TRA NGUỒN GỐC CÂU CHUYỆN (Story Source Tags)
# - Mục đích: Nếu bài có nhắc đến "câu chuyện", hệ thống ép buộc phải khai báo nguồn gốc (vault, famous, book, none) để chống bịa đặt (fabrication).
# - Dấu hiệu tìm kiếm: Quét tìm chữ "story, stories, cau chuyen" và thẻ "source: vault/famous/book/none".
# - Điều kiện PASS: 
#   + Nếu nhắc đến story (>0) thì bắt buộc phải có thẻ source (>0).
#   + Nếu không nhắc đến story (chỉ có data) thì tự động PASS.
# ============================================================
# Thực thi quét 1: Tìm xem có bao nhiêu thẻ khai báo nguồn gốc (vault/famous/book/none)
$sourceTagCount = ([regex]::Matches($research, '(?i)source\s*[:：]\s*(vault|famous|book|none)')).Count
# Thực thi quét 2: Tìm xem có bao nhiêu lần nhắc đến từ khóa "story", "câu chuyện"
$storyMentions = ([regex]::Matches($research, '(?i)(story|stories|cau\s*chuyen)')).Count

# Kiểm tra trường hợp 1: Có kể chuyện NHƯNG không khai báo nguồn -> FAIL
if ($storyMentions -gt 0 -and $sourceTagCount -eq 0) {
    Add-Result "Story Source Tags" "FAIL" "Stories mentioned but no source tags (vault/famous/none)"
}
elseif ($storyMentions -gt 0 -and $sourceTagCount -gt 0) {
    Add-Result "Story Source Tags" "PASS" "$sourceTagCount tag(s) found for $storyMentions story mention(s)"
}
else {
    Add-Result "Story Source Tags" "PASS" "No stories mentioned (data/research-only approach)"
}

# ============================================================
# CHECK 3: KIỂM TRA TỰ ĐÁNH GIÁ (KCS Status)
# - Mục đích: Ép Insight Agent phải tự audit bài làm của chính nó theo chuẩn Knowledge-Centered Service (KCS) trước khi nộp.
# - Dấu hiệu tìm kiếm: Quét tìm cụm "KCS status: PASS" hoặc "KCS check: PASS".
# - Điều kiện PASS: Chỉ PASS khi tìm thấy chính xác chữ PASS. Nếu khai báo FAIL hoặc quên khai báo đều bị đánh trượt.
# ============================================================
# Thực thi quét Regex: Tìm cụm "KCS status: [Gì đó]" (không phân biệt hoa thường)
if ($research -match '(?i)KCS\s*(status|check)?\s*[:：]\s*(PASS|FAIL)') {
    # Lấy ra đúng chữ PASS hoặc FAIL và in hoa lên (đề phòng AI viết pass/Fail)
    $kcsStatus = $Matches[2].ToUpper()
    # Kiểm tra: Nếu đúng là chữ PASS thì cho qua
    if ($kcsStatus -eq "PASS") {
        Add-Result "KCS Status" "PASS" "KCS: PASS declared"
    }
    else {
        Add-Result "KCS Status" "FAIL" "KCS: FAIL declared in research brief"
    }
}
else {
    Add-Result "KCS Status" "FAIL" "No explicit KCS status found in research brief"
}

# ============================================================
# OUTPUT
# ============================================================
Write-Host ""
Write-Host "========================================="
Write-Host "  RESEARCH VALIDATION REPORT (Phase 2)"
Write-Host "========================================="
# Duyệt qua từng kết quả lưu trong mảng $results để in ra màn hình
foreach ($r in $results) {
    # Gán icon hiển thị dựa trên trạng thái (PASS/WARN/FAIL)
    $icon = if ($r.Status -eq "PASS") { "[PASS]" } elseif ($r.Status -eq "WARN") { "[WARN]" } else { "[FAIL]" }
    Write-Host "  $icon $($r.Check): $($r.Detail)"
}
Write-Host "-----------------------------------------"
Write-Host "  Total: $passCount PASS / $failCount FAIL"
Write-Host "========================================="

exit $failCount
