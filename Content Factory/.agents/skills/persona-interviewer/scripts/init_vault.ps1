param (
    [Parameter(Mandatory = $true)]
    [string]$UserName
)

$ErrorActionPreference = "Stop"

# Xác định workspace root (Cách scripts folder 4 cấp: .agents/skills/persona-interviewer/scripts)
$workspaceRoot = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$personaDir = Join-Path $workspaceRoot "personas"
$userPersonaDir = Join-Path $personaDir $UserName
$templateDir = Join-Path $workspaceRoot ".agents\skills\persona-interviewer\assets\persona-template"
$vaultDir = Join-Path $workspaceRoot "vault"

Write-Host ">>> Bắt đầu khởi tạo hệ sinh thái Persona và Vault cho: $UserName"

# 1. Khởi tạo thư mục Persona và sao chép template
if (-Not (Test-Path $userPersonaDir)) {
    New-Item -ItemType Directory -Path $userPersonaDir -Force | Out-Null
    Write-Host "[OK] Đã tạo thư mục Persona: personas/$UserName"
}

if (Test-Path $templateDir) {
    Copy-Item -Path "$templateDir\*" -Destination $userPersonaDir -Recurse -Force
    Write-Host "[OK] Đã sao chép thành công bộ 7 file YAML mẫu"
}
else {
    Write-Host "[FATAL] Không tìm thấy thư mục template tại $templateDir" -ForegroundColor Red
    exit 1
}

# 2. Xây dựng cấu trúc hệ thống Vault
$vaultFolders = @(
    "00-Inbox",
    "01-Atomic\Stories",
    "01-Atomic\Insights",
    "01-Atomic\Solutions",
    "01-Atomic\Concepts",
    "01-Atomic\Quotes",
    "01-Atomic\Data-Points",
    "01-Atomic\Audiences",
    "$UserName\Posted",
    "$UserName\Viral Posts",
    "Content",
    "output\logs",
    "output\posts"
)

Write-Host ">>> Đang thiết lập cấu trúc Vault..."
foreach ($folder in $vaultFolders) {
    $fullPath = Join-Path $vaultDir $folder
    if (-Not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        # Tạo file .gitkeep để hỗ trợ version control
        New-Item -ItemType File -Path (Join-Path $fullPath ".gitkeep") -Force | Out-Null
        Write-Host "  + Tạo folder chuyên biệt: $folder (/w .gitkeep)"
    }
}

Write-Host ">>> HOÀN TẤT TẠO LẬP HỆ THỐNG!" -ForegroundColor Green
