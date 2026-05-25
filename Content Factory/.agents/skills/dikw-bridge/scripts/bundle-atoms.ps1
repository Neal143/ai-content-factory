<#
.SYNOPSIS
Script nối nội dung Atom vào file Combo và tạo khóa xác thực (Poka-Yoke).
.DESCRIPTION
Được sử dụng khi: Gọi từ DIKW Bridge Skill.
Vai trò: Gộp file và chống lười.
Output: Ghi đè (Append) nội dung text của các file Atom + `<!-- BUNDLE_KEY: [Mã] -->` vào đáy file Combo.
Last update: 25/05/2026
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$ComboFile
)

# 1. Kiem tra su ton tai cua file Combo (Dau vao)
if (-not (Test-Path $ComboFile)) {
    Write-Host "[ERROR] Khong tim thay file $ComboFile"
    exit 1
}

$content = Get-Content $ComboFile -Raw -Encoding UTF8

# CHONG LAP DU LIEU (Idempotency Check)
if ($content -match '<!-- BUNDLE_KEY:') {
    Write-Host "[SUCCESS] File da duoc bundle tu truoc. Bo qua viec bundle lai de chong lap ranh."
    exit 0
}

# 2. Quet Regex lay tat ca duong dan Atom (Regex cap do cao, ho tro duong dan co khoang trang)
$matches = [regex]::Matches($content, '(?m)(?<=^|\s|\|)(vault/01-Atomic/[^|\r\n]+?\.md)(?=\s|\||$)')
$rawPaths = @()
foreach ($m in $matches) {
    $rawPaths += $m.Groups[1].Value.Trim()
}

# Loc trung lap (Deduplicate) de giam thieu rác du lieu
$paths = $rawPaths | Select-Object -Unique

$bundleContent = "`n`n## ATOMIC COMBO (APPENDED DATA)`n"
$foundAny = $false

# 3. Lap qua cac duong dan de boc noi dung text vao bien
foreach ($path in $paths) {
    if (Test-Path $path) {
        $atomContent = Get-Content $path -Raw -Encoding UTF8
        $bundleContent += "`n### ATOM: $path`n$atomContent`n---`n"
        $foundAny = $true
    }
}

# 4. Sinh BUNDLE_KEY va Append xuong cuoi file de Sentinel kiem tra
if ($foundAny) {
    # Sinh 8 ky tu Hex ngau nhien an toan bang GUID
    $bundleKey = [guid]::NewGuid().ToString("N").Substring(0, 8).ToUpper()
    
    $bundleContent += "`n<!-- BUNDLE_KEY: $bundleKey -->`n"
    Add-Content -Path $ComboFile -Value $bundleContent -Encoding UTF8
    Write-Host "[SUCCESS] Da append cac Atoms. File san sang cho cac Phase sau."
} else {
    Write-Host "[WARN] Khong the trich xuat bat ky Atom nao tu bang."
}
