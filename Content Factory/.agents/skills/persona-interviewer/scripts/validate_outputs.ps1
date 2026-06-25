<#
.SYNOPSIS
Tên file: validate_outputs.ps1
Last update: 26/06/2026 01:03 (GMT+7)
Vai trò: Kiểm định Output BẮT BUỘC do SKILL.md quy định (không kiểm tra trường tùy chọn/placeholder).
Khi nào dùng: Cuối vòng đời persona-interviewer hoặc User chạy thủ công.
Output: Log Terminal (Xanh = OK, Đỏ = FAIL, Vàng = WARN).
Logic:
- Kiểm tra 7 file YAML tồn tại (init_vault.ps1).
- Nội soi CHỈ Tier 1 (name, pronouns, tone) + Tier 2 Nhóm C (JTBD, Pillars, Insights, Topics, Authorities).
- Bỏ qua Nhóm A, B (user có quyền skip) và template placeholders.
- Xác thực file vật lý Insight và Audience (chống Link Mồ côi).
#>

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " PERSONA INTERVIEWER - OUTPUT VALIDATOR (V6) " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# ==============================================================================
# KHỐI 1: MỎ NEO THƯ MỤC GỐC (Absolute Anchor)
# Ý nghĩa: Luôn chạy đúng bất chấp thư mục User mở Terminal.
# ==============================================================================
$RootPath = (Get-Item $PSScriptRoot).Parent.Parent.Parent.Parent.FullName
Write-Host "[*] Root: $RootPath" -ForegroundColor DarkGray

$personasDir = Join-Path $RootPath "personas"
if (-not (Test-Path $personasDir)) { Write-Host "[FAIL] Không tìm thấy: $personasDir" -ForegroundColor Red; exit }
$userFolders = Get-ChildItem -Path $personasDir -Directory
if ($userFolders.Count -eq 0) { Write-Host "[FAIL] Không có Persona nào." -ForegroundColor Red; exit }

# ==============================================================================
# KHỐI 2: HÀM KIỂM TRA UNIFIED REGEX
# Ý nghĩa: Xác thực 1 key YAML có giá trị thực (không null, không rỗng, không mảng rỗng).
# Xử lý đúng: gạch đầu dòng (- key:), Block Scalar (>), inline comments (# ...).
# ==============================================================================
function Test-RequiredField {
    param([string]$Content, [string]$Key)
    # Negative lookahead chặn: null, "", '', [], và dòng chỉ có whitespace/comment
    return ($Content -match "(?m)^\s*(?:-\s+)?${Key}:\s*(?!null\b)(?!""""\s*(#.*)?$)(?!''\s*(#.*)?$)(?!\[\s*\]\s*(#.*)?$)(?!\s*(#.*)?$)")
}

# ==============================================================================
# KHỐI 3: QUÉT TỪNG PERSONA
# ==============================================================================
foreach ($userFolder in $userFolders) {
    $userName = $userFolder.Name
    Write-Host "`n>>> PERSONA: [$userName] <<<" -ForegroundColor Yellow

    # --- CHECK 1: 7 file YAML tồn tại (do init_vault.ps1 tạo) ---
    Write-Host "--- 1. FILE TỒN TẠI (init_vault.ps1) ---" -ForegroundColor Cyan
    $requiredFiles = @("voice-dna.yaml","profile.yaml","audience.yaml","topic_map.yaml","pillars.yaml","authorities.yaml","scoring-rules.yaml")
    foreach ($f in $requiredFiles) {
        $fp = Join-Path $userFolder.FullName $f
        if (Test-Path $fp) { Write-Host "[OK] $f" -ForegroundColor Green }
        else { Write-Host "[FAIL] $f (THIẾU)" -ForegroundColor Red }
    }

    # --- CHECK 2: Tier 1 — Danh tính cốt lõi (Câu 1-3, KHÔNG có Bỏ qua) ---
    Write-Host "`n--- 2. TIER 1: DANH TÍNH (BẮT BUỘC) ---" -ForegroundColor Cyan
    $profilePath = Join-Path $userFolder.FullName "profile.yaml"
    if (Test-Path $profilePath) {
        $c = Get-Content $profilePath -Raw
        if (Test-RequiredField $c "name") { Write-Host "[OK] profile.yaml -> name" -ForegroundColor Green }
        else { Write-Host "[FAIL] profile.yaml -> name (RỖNG)" -ForegroundColor Red }
    }
    $voicePath = Join-Path $userFolder.FullName "voice-dna.yaml"
    if (Test-Path $voicePath) {
        $c = Get-Content $voicePath -Raw
        foreach ($key in @("self","audience","primary")) {
            if (Test-RequiredField $c $key) { Write-Host "[OK] voice-dna.yaml -> $key" -ForegroundColor Green }
            else { Write-Host "[FAIL] voice-dna.yaml -> $key (RỖNG)" -ForegroundColor Red }
        }
    }

    # --- CHECK 3: Tier 2 Nhóm C — JTBD (Câu 10, BẮT BUỘC) ---
    Write-Host "`n--- 3. TIER 2: JTBD (BẮT BUỘC) ---" -ForegroundColor Cyan
    $audiencePath = Join-Path $userFolder.FullName "audience.yaml"
    if (Test-Path $audiencePath) {
        $c = Get-Content $audiencePath -Raw
        foreach ($key in @("audience_Job_performer","audience_main_job","audience_circumstance")) {
            if (Test-RequiredField $c $key) { Write-Host "[OK] audience.yaml -> $key" -ForegroundColor Green }
            else { Write-Host "[FAIL] audience.yaml -> $key (RỖNG)" -ForegroundColor Red }
        }
    }

    # --- CHECK 4: Pillars & Insights (Câu 11, BẮT BUỘC) ---
    Write-Host "`n--- 4. PILLARS & INSIGHTS (BẮT BUỘC) ---" -ForegroundColor Cyan
    $pillarsPath = Join-Path $userFolder.FullName "pillars.yaml"
    if (Test-Path $pillarsPath) {
        $c = Get-Content $pillarsPath -Raw
        foreach ($key in @("name","description","target_emotion")) {
            if (Test-RequiredField $c $key) { Write-Host "[OK] pillars -> $key" -ForegroundColor Green }
            else { Write-Host "[FAIL] pillars -> $key (RỖNG)" -ForegroundColor Red }
        }
        foreach ($key in @("type","raw","file_ref","llm_explain")) {
            if (Test-RequiredField $c $key) { Write-Host "[OK] pillars -> insight.$key" -ForegroundColor Green }
            else { Write-Host "[FAIL] pillars -> insight.$key (RỖNG)" -ForegroundColor Red }
        }
    }

    # --- CHECK 5: File vật lý Insight (run_insights.ps1 tạo) ---
    Write-Host "`n--- 5. INSIGHT FILES (BẮT BUỘC) ---" -ForegroundColor Cyan
    if (Test-Path $pillarsPath) {
        $lines = Get-Content $pillarsPath -Encoding UTF8
        $count = 0
        foreach ($line in $lines) {
            if ($line -match "^\s*file_ref:\s*['""]?\[\[(.*?)\]\]['""]?") {
                $count++
                $fn = $matches[1] + ".md"
                $pp = Join-Path $RootPath "vault\01-Atomic\Insights\$fn"
                if (Test-Path $pp) { Write-Host "  [OK] $fn" -ForegroundColor Green }
                else { Write-Host "  [FAIL] $fn (THIẾU FILE VẬT LÝ)" -ForegroundColor Red }
            }
        }
        if ($count -eq 0) { Write-Host "  [WARN] Chưa có insight." -ForegroundColor Yellow }
    }

    # --- CHECK 6: Topic Map (Câu 11 Bước 1, BẮT BUỘC) ---
    Write-Host "`n--- 6. TOPIC MAP (BẮT BUỘC) ---" -ForegroundColor Cyan
    $topicPath = Join-Path $userFolder.FullName "topic_map.yaml"
    if (Test-Path $topicPath) {
        $c = Get-Content $topicPath -Raw
        if (Test-RequiredField $c "id") { Write-Host "[OK] topic_map.yaml có topic entries" -ForegroundColor Green }
        else { Write-Host "[FAIL] topic_map.yaml không có topic nào" -ForegroundColor Red }
    }

    # --- CHECK 7: Authorities (Câu 12, BẮT BUỘC) ---
    Write-Host "`n--- 7. AUTHORITIES (BẮT BUỘC) ---" -ForegroundColor Cyan
    $authPath = Join-Path $userFolder.FullName "authorities.yaml"
    if (Test-Path $authPath) {
        $authSize = (Get-Item $authPath).Length
        if ($authSize -gt 0) { Write-Host "[OK] authorities.yaml ($authSize bytes)" -ForegroundColor Green }
        else { Write-Host "[FAIL] authorities.yaml (RỖNG)" -ForegroundColor Red }
    }
}

# ==============================================================================
# KHỐI 4: QUÉT VAULT — AUDIENCE INDEX & FILES (Câu 10 Hành động 2-3)
# ==============================================================================
Write-Host "`n>>> VAULT <<<" -ForegroundColor Yellow
Write-Host "--- 8. AUDIENCE INDEX & FILES ---" -ForegroundColor Cyan
$indexPath = Join-Path $RootPath "vault\01-Atomic\Audiences\_audience_index.yaml"
if (Test-Path $indexPath) {
    Write-Host "[OK] _audience_index.yaml" -ForegroundColor Green
    $lines = Get-Content $indexPath -Encoding UTF8
    $count = 0
    foreach ($line in $lines) {
        if ($line -match "^\s*file_ref:\s*['""]?\[\[(.*?)\]\]['""]?") {
            $count++
            $fn = $matches[1] + ".md"
            $pp = Join-Path $RootPath "vault\01-Atomic\Audiences\$fn"
            if (-not (Test-Path $pp)) { Write-Host "  [FAIL] MỒ CÔI: $fn" -ForegroundColor Red }
        }
    }
    Write-Host "  Tổng: $count Audience(s)." -ForegroundColor Green
} else {
    Write-Host "[FAIL] _audience_index.yaml không tồn tại" -ForegroundColor Red
}

# ==============================================================================
# KHỐI 5: BUFFER PAYLOAD (Câu 11 — insights_payload.json)
# Ý nghĩa: File này là sản phẩm trung gian. Chỉ kiểm tra NẾU file tồn tại.
# ==============================================================================
Write-Host "`n--- 9. BUFFER PAYLOAD ---" -ForegroundColor Cyan
$payloadPath = Join-Path $PSScriptRoot "insights_payload.json"
if (Test-Path $payloadPath) {
    $jc = Get-Content $payloadPath -Raw
    $miss = @()
    foreach ($k in @("headline","insight_type","raw_payload","llm_explain","topics")) {
        if (-not ($jc -match "(?m)^\s*""${k}""\s*:\s*(?!null\b)(?!""""\s*(#.*)?$)(?!\[\s*\]\s*(#.*)?$)(?!\s*$).+")) { $miss += $k }
    }
    if ($miss.Count -eq 0) { Write-Host "[OK] Payload đủ 5/5 trường." -ForegroundColor Green }
    else { Write-Host "[FAIL] Payload THIẾU/RỖNG: $($miss -join ', ')" -ForegroundColor Red }
} else {
    Write-Host "[INFO] Chưa có insights_payload.json (bình thường nếu chưa chạy Câu 11)." -ForegroundColor DarkGray
}

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "             HOÀN TẤT KIỂM TRA               " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
