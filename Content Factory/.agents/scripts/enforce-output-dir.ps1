# File       : enforce-output-dir.ps1
# Last update: 05/06/2026 00:40 (GMT+7)
# Vai tro    : Hook PreToolUse chan ghi file ngoai thu muc cho phep khi workflow dang chay
# Dung khi   : Tu dong kich hoat boi IDE platform truoc moi lenh write_to_file
# Output     : JSON stdout: {} (cho phep) hoac {"decision":"force_ask","reason":"..."} (chan)
# Logic      : Doc payload stdin -> trich xuat va sanitize TargetFile -> doc transcript (non-locking)
#              -> xac dinh workflow gan nhat -> kiem tra thu muc -> tra quyet dinh JSON

try {
    # --- Nhom 1: Doc va parse payload stdin ---
    $rawInput = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($rawInput)) {
        [Console]::Error.WriteLine("[HOOK] Empty stdin, allowing.")
        [Console]::Out.Write("{}")
        exit 0
    }

    $payload = $rawInput | ConvertFrom-Json

    # --- Nhom 2: Trich xuat TargetFile voi fallback da cau truc ---
    # Platform co the gui TargetFile trong toolCall.args hoac tool_input
    $targetFile = $null
    if ($payload.toolCall -and $payload.toolCall.args) {
        $targetFile = $payload.toolCall.args.TargetFile
    }
    if (-not $targetFile -and $payload.tool_input) {
        $targetFile = $payload.tool_input.TargetFile
    }
    if (-not $targetFile) {
        [Console]::Error.WriteLine("[HOOK] No TargetFile in payload, allowing.")
        [Console]::Out.Write("{}")
        exit 0
    }

    # --- Nhom 3: Lam sach duong dan (FIX lo hong 1) ---
    # Loai bo dau nhay kep/don bao quanh do platform hoac Agent truyen vao
    $targetFile = $targetFile.Trim().Trim('"').Trim("'").Trim()
    if ([string]::IsNullOrWhiteSpace($targetFile)) {
        [Console]::Out.Write("{}")
        exit 0
    }

    # --- Nhom 4: Chuan hoa duong dan ---
    # Tinh workspace base tu vi tri script (portable, khong hardcode)
    $agentsDir = Split-Path -Parent $PSScriptRoot        # .agents/scripts -> .agents
    $workspaceBase = Split-Path -Parent $agentsDir        # .agents -> Content Factory root

    $normalizedTarget = [System.IO.Path]::GetFullPath($targetFile).Replace('/', '\').ToLowerInvariant()
    $normalizedBase = [System.IO.Path]::GetFullPath($workspaceBase).Replace('/', '\').ToLowerInvariant()

    [Console]::Error.WriteLine("[HOOK] Target: $normalizedTarget")
    [Console]::Error.WriteLine("[HOOK] Base: $normalizedBase")

    # --- Nhom 5: Doc transcript de xac dinh workflow dang chay ---
    # Thu nhieu ten truong co the co (FIX lo hong 2)
    $transcriptPath = $null
    if ($payload.transcriptPath) { $transcriptPath = $payload.transcriptPath }
    elseif ($payload.transcript_path) { $transcriptPath = $payload.transcript_path }

    $activeWorkflow = $null

    if ($transcriptPath -and (Test-Path $transcriptPath -ErrorAction SilentlyContinue)) {
        # Doc file bang FileStream voi ReadWrite sharing (FIX lo hong 3)
        $recentText = ""
        try {
            $fs = [System.IO.FileStream]::new(
                $transcriptPath,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite
            )
            $reader = [System.IO.StreamReader]::new($fs)
            $fullText = $reader.ReadToEnd()
            $reader.Close()
            $fs.Close()

            # Lay toi da 200 dong cuoi cung de giam tai
            $allLines = $fullText -split "`r?`n"
            $start = [Math]::Max(0, $allLines.Length - 200)
            $recentText = ($allLines[$start..($allLines.Length - 1)]) -join "`n"
        } catch {
            [Console]::Error.WriteLine("[HOOK] FileStream failed: $($_.Exception.Message). Trying Get-Content fallback.")
            # Fallback: Get-Content co the doc duoc neu lock chi la ReadWrite
            try {
                $recentText = Get-Content $transcriptPath -Tail 200 -ErrorAction Stop | Out-String
            } catch {
                [Console]::Error.WriteLine("[HOOK] Fallback also failed: $($_.Exception.Message)")
                $recentText = ""
            }
        }

        # Tim ten workflow gan nhat trong transcript
        if ($recentText) {
            $regexMatches = [regex]::Matches($recentText, "(content-post|book-extractor)")
            if ($regexMatches.Count -gt 0) {
                $activeWorkflow = $regexMatches[$regexMatches.Count - 1].Value
            }
        }
    } else {
        [Console]::Error.WriteLine("[HOOK] No valid transcriptPath found, allowing.")
    }

    # Khong phat hien workflow nao dang chay -> cho phep (fail-open an toan)
    if (-not $activeWorkflow) {
        [Console]::Error.WriteLine("[HOOK] No monitored workflow detected, allowing.")
        [Console]::Out.Write("{}")
        exit 0
    }

    [Console]::Error.WriteLine("[HOOK] Active workflow: $activeWorkflow")

    # --- Nhom 6: Xac dinh thu muc hop le cho workflow ---
    $allowedRelative = switch ($activeWorkflow) {
        "content-post"   { "output" }
        "book-extractor" { ".extraction_runs" }
        default          { $null }
    }

    if (-not $allowedRelative) {
        [Console]::Out.Write("{}")
        exit 0
    }

    $allowedBase = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::Combine($workspaceBase, $allowedRelative)
    ).Replace('/', '\').ToLowerInvariant()

    [Console]::Error.WriteLine("[HOOK] Allowed base: $allowedBase")

    # --- Nhom 7: So sanh duong dan dich voi vung cho phep ---
    if ($normalizedTarget.StartsWith($allowedBase + "\") -or $normalizedTarget -eq $allowedBase) {
        [Console]::Error.WriteLine("[HOOK] PASS - target within allowed directory.")
        [Console]::Out.Write("{}")
        exit 0
    }

    # --- Nhom 8: VI PHAM - tra quyet dinh chan ---
    $errorMessage = "❌ [LỖI NGHIÊM TRỌNG - HOOK BLOCKED] Agent đang chạy quy trình [$activeWorkflow] NHƯNG lại cố gắng ghi đè/tạo file bên ngoài thư mục cho phép [$allowedRelative/]. Đường dẫn vi phạm: $targetFile."
    [Console]::Error.WriteLine($errorMessage)
    exit 1
} catch {
    # Failsafe: Log loi va cho phep de khong chan cac thao tac hop le
    [Console]::Error.WriteLine("[HOOK-FATAL] $($_.Exception.Message)")
    exit 0
}
