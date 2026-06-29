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

# 2. Xây dựng cấu trúc hệ thống từ manifest
$manifestPath = Join-Path $workspaceRoot ".agents\migrations\structure-manifest.txt"
if (-not (Test-Path $manifestPath)) {
    Write-Host "[FATAL] Không tìm thấy structure-manifest.txt tại $manifestPath" -ForegroundColor Red
    exit 1
}

$systemFolders = Get-Content $manifestPath | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '\S' } | ForEach-Object { $_.Trim() }

Write-Host ">>> Đang thiết lập cấu trúc hệ thống (Vault/Docs/Plans/Personas)..."
foreach ($folder in $systemFolders) {
    $fullPath = Join-Path $workspaceRoot $folder
    if (-Not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        # Tạo file .gitkeep để hỗ trợ version control (chỉ áp dụng cho subfolders của vault, docs, plans)
        if ($folder -match "/") {
            New-Item -ItemType File -Path (Join-Path $fullPath ".gitkeep") -Force | Out-Null
        }
        Write-Host "  + Tạo folder: $folder (/w .gitkeep)"
    }
}

# 3. Tao 7 file gio nap lieu + 7 file log + file huong dan trong 00-Inbox
$inboxDir = Join-Path $workspaceRoot "vault\00-Inbox"
$processedDir = Join-Path $inboxDir "Processed"
$inboxFiles = @("Concepts.md", "Data-Points.md", "Insights.md", "Quotes.md", "Solutions.md", "Stories.md", "Uncategorized.md")

New-Item -ItemType Directory -Path $processedDir -Force | Out-Null
foreach ($f in $inboxFiles) {
    $gioPath = Join-Path $inboxDir $f
    $logPath = Join-Path $processedDir $f
    if (-not (Test-Path $gioPath)) { New-Item -ItemType File -Path $gioPath -Force | Out-Null }
    if (-not (Test-Path $logPath)) { New-Item -ItemType File -Path $logPath -Force | Out-Null }
}
# Copy file huong dan vao Inbox
$guideSource = Join-Path $workspaceRoot ".agents\skills\persona-interviewer\assets\_Huong-dan.md"
$guideDest = Join-Path $inboxDir "_Huong-dan.md"
if ((Test-Path $guideSource) -and (-not (Test-Path $guideDest))) {
    Copy-Item -Path $guideSource -Destination $guideDest -Force
}
# Xoa .gitkeep neu ton tai
$gitkeep = Join-Path $inboxDir ".gitkeep"
if (Test-Path $gitkeep) { Remove-Item $gitkeep -Force }

Write-Host ">>> HOAN TAT TAO LAP HE THONG!" -ForegroundColor Green