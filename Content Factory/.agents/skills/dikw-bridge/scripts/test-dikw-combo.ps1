<#
Tên file: test-dikw-combo.ps1
Last update: 27/05/2026 01:15 (GMT+7)
Vai trò: Script test unit tự động kiểm thử công cụ Get-DIKWCombo.ps1.
Sử dụng khi nào: Chạy để xác minh logic lọc, tính khả thi (viability) và các trường đầu ra của công cụ Get-DIKWCombo.
Output: In kết quả thực thi 3 test cases quan trọng lên màn hình console.
Tóm tắt logic hoạt động:
  1. Test Case 1: Chạy có TargetSourceIds = @("good-inside"), đảm bảo chỉ lấy atoms từ sách Good Inside.
  2. Test Case 2: Chạy không có TargetSourceIds, kiểm tra khả năng truy xuất rộng.
  3. Test Case 3: Chạy với Audience dạng mảng và in thông tin resolved JTBD.
#>

# ==========================================
# NHÓM 1: CẤU HÌNH THƯ MỤC VÀ ĐƯỜNG DẪN
# ==========================================
$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$comboScript = Join-Path $scriptDir "Get-DIKWCombo.ps1"

if (-not (Test-Path $comboScript)) {
    Write-Error "[ERR] Khong tim thay script Get-DIKWCombo.ps1 tai: $comboScript"
}

# ==========================================
# NHÓM 2: THỰC THI CÁC TEST CASES KIỂM THỬ
# ==========================================
Write-Host "=== BAT DAU TIEN TRINH UNIT TESTING GET-DIKWCOMBO ===" -ForegroundColor Cyan

# ------------------------------------------
# TEST CASE 1: Chạy có bộ lọc TargetSourceIds
# ------------------------------------------
Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
Write-Host "TEST CASE 1: TargetSourceIds = @('good-inside')" -ForegroundColor Yellow
Write-Host "Ky vong: Chi tra ve cac atoms co prefix GI_ thuoc sach Good Inside" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$topic1 = "khung_hoang_cam_xuc"
$audience1 = "cha-me_nguoi-muon-kiem-soat-nhung-hanh-vi-chong_khi-oi-mat-voi-nhung-con-thinh-no-hoac-l"

powershell -ExecutionPolicy Bypass -File $comboScript `
    -Topics $topic1 `
    -Audience $audience1 `
    -TargetSourceIds @("good-inside") `
    -PersonaUser "Neal"

# ------------------------------------------
# TEST CASE 2: Chạy khép kín không có TargetSourceIds
# ------------------------------------------
Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
Write-Host "TEST CASE 2: Khong co TargetSourceIds (Truy van mo rong)" -ForegroundColor Yellow
Write-Host "Ky vong: Co the lay tu bat ky nguon nao khop topic & audience" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$topic2 = "tu_xoa_diu_lo_au"
$audience2 = "cha-me_huong-dan-con-cach-tu-xoa-diu-va-kiem-soat-su-chu-y_khi-con-bi-mac-ket-vao-nhung-suy-nghi-tieu-cuc"

powershell -ExecutionPolicy Bypass -File $comboScript `
    -Topics $topic2 `
    -Audience $audience2 `
    -PersonaUser "Neal"

# ------------------------------------------
# TEST CASE 3: Chạy với Audience dạng mảng nhiều phần tử
# ------------------------------------------
Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
Write-Host "TEST CASE 3: Audience la array + in Resolved JTBD" -ForegroundColor Yellow
Write-Host "Ky vong: Xuat resolved JTBD an toan tu audience.md" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$audienceArr = @(
    "cha-me_nguoi-muon-kiem-soat-nhung-hanh-vi-chong_khi-oi-mat-voi-nhung-con-thinh-no-hoac-l",
    "cap-vo-chong_tim-hieu-ve-nuoi-con_sap-co-con-hoac-dang-co-con-o-do-tuoi-0-7-tuoi"
)

powershell -ExecutionPolicy Bypass -File $comboScript `
    -Topics $topic1 `
    -Audience ($audienceArr -join ",") `
    -PersonaUser "Neal"

Write-Host "`n=== HOAN THANH UNIT TESTING GET-DIKWCOMBO ===" -ForegroundColor Cyan
