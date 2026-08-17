# ------------------------------------------------------------------
# Ten file: sync-dev-plugins.ps1
# Last update: 17/08/2026 22:30 (GMT+7)
# Vai tro: Tu dong quet cac plugin chinh thuc cua Factory trong vault/.obsidian/plugins/
#          va sao chep dong bo sang .agents/assets/factory-scaffold/vault/.obsidian/plugins/.
# Duoc su dung khi: Tu dong goi boi workflow /checkpoint truoc khi thuc hien git commit.
# Output: Console messages bao cao so luong plugin da dong bo. Exit 0 = thanh cong, Exit 1 = that bai.
# Tom tat logic hoat dong:
#   1. Kiem tra thu muc live plugins tai vault/.obsidian/plugins/.
#   2. Duyet qua tung folder plugin, doc file manifest.json.
#   3. Kiem tra author (Antigravity) hoac id (factory-sync) de xac dinh Factory Plugin.
#   4. Copy toan bo noi dung folder plugin sang thu muc scaffold tuong ung.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot
)

$ErrorActionPreference = "Stop"

try {
    # --- Nhom 1: Xac dinh duong dan nguon (Live Vault) va dich (Scaffold Template) ---
    $livePluginsDir = Join-Path $FactoryRoot "vault\.obsidian\plugins"
    $scaffoldPluginsDir = Join-Path $FactoryRoot ".agents\assets\factory-scaffold\vault\.obsidian\plugins"

    if (-not (Test-Path $livePluginsDir)) {
        Write-Host "[INFO] No live plugins directory found at: $livePluginsDir"
        exit 0
    }

    if (-not (Test-Path $scaffoldPluginsDir)) {
        New-Item -ItemType Directory -Path $scaffoldPluginsDir -Force | Out-Null
    }

    # --- Nhom 2: Quet cac folder plugin va kiem tra quyen so huu cua Factory ---
    $livePluginFolders = Get-ChildItem -Path $livePluginsDir -Directory
    $syncedCount = 0

    foreach ($folder in $livePluginFolders) {
        $manifestPath = Join-Path $folder.FullName "manifest.json"
        $isFactoryPlugin = $false

        # Kiem tra manifest de chi dong bo cac plugin do Factory phat trien
        if (Test-Path $manifestPath) {
            try {
                $manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
                if ($manifest.author -match "Antigravity" -or $manifest.id -eq "factory-sync") {
                    $isFactoryPlugin = $true
                }
            } catch {}
        }

        # --- Nhom 3: Sao chep ma nguon sang scaffold template ---
        if ($isFactoryPlugin) {
            $destFolder = Join-Path $scaffoldPluginsDir $folder.Name
            if (-not (Test-Path $destFolder)) {
                New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
            }
            
            Copy-Item -Path "$($folder.FullName)\*" -Destination $destFolder -Recurse -Force
            Write-Host "  + Synced Dev Plugin to Scaffold: $($folder.Name)"
            $syncedCount++
        }
    }

    # --- Nhom 4: Bao cao ket qua va ket thuc ---
    Write-Host "[OK] Dev plugins sync to scaffold completed ($syncedCount plugin(s))."
    exit 0
} catch {
    Write-Host "[ERROR] sync-dev-plugins failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
