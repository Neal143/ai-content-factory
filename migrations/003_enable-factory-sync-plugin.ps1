# ------------------------------------------------------------------
# 003_enable-factory-sync-plugin.ps1
# Last update: 16/08/2026 00:26 (GMT+7)
# Role: Enable factory-sync plugin in Obsidian community-plugins.json
#       and ensure plugin files are copied to user's vault.
# When: Called by run-migrations.ps1 during /update-agents workflow.
# Output: Console messages. Exit 0 = success, Exit 1 = failure.
# Logic: Ensure vault/.obsidian/ exists ->
#        Copy plugin files from scaffold if missing ->
#        Create or update community-plugins.json to include "factory-sync".
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot
)

$ErrorActionPreference = "Stop"

try {
    $obsidianDir = Join-Path $FactoryRoot "vault\.obsidian"
    $pluginsConfigFile = Join-Path $obsidianDir "community-plugins.json"
    $targetPluginId = "factory-sync"

    # --- Nhom 1: Dam bao thu muc vault/.obsidian ton tai ---
    if (-not (Test-Path $obsidianDir)) {
        New-Item -ItemType Directory -Path $obsidianDir -Force | Out-Null
        Write-Host "  + Created directory: vault/.obsidian"
    }

    # --- Nhom 2: Fallback kiem tra va copy plugin files tu scaffold neu thieu ---
    $scaffoldPluginDir = Join-Path $FactoryRoot ".agents\assets\factory-scaffold\vault\.obsidian\plugins\$targetPluginId"
    $destPluginDir = Join-Path $obsidianDir "plugins\$targetPluginId"
    if ((Test-Path $scaffoldPluginDir) -and (-not (Test-Path $destPluginDir))) {
        New-Item -ItemType Directory -Path $destPluginDir -Force | Out-Null
        Copy-Item -Path "$scaffoldPluginDir\*" -Destination $destPluginDir -Recurse -Force
        Write-Host "  + Copied plugin files to vault/.obsidian/plugins/$targetPluginId"
    }

    # --- Nhom 3: Helper dinh dang JSON array voi 2-space indent ---
    function Format-JsonArray {
        param([string[]]$Items)
        if ($Items.Count -eq 0) { return "[]" }
        $lines = $Items | ForEach-Object { "  `"$_`"" }
        return "[`r`n" + ($lines -join ",`r`n") + "`r`n]"
    }

    # --- Nhom 4: Tao moi hoac cap nhat community-plugins.json ---
    if (-not (Test-Path $pluginsConfigFile)) {
        # File chua ton tai: tao moi voi targetPluginId
        $jsonContent = Format-JsonArray -Items @($targetPluginId)
        [System.IO.File]::WriteAllText($pluginsConfigFile, $jsonContent, [System.Text.Encoding]::UTF8)
        Write-Host "  + Created community-plugins.json with [$targetPluginId]"
    } else {
        # File da ton tai: parse, kiem tra, append neu thieu
        $rawContent = [System.IO.File]::ReadAllText($pluginsConfigFile, [System.Text.Encoding]::UTF8)
        $pluginList = @()

        if (-not [string]::IsNullOrWhiteSpace($rawContent)) {
            try {
                $parsed = ConvertFrom-Json -InputObject $rawContent
                $pluginList = @($parsed)
            } catch {
                Write-Host "  ! Warning: community-plugins.json contains invalid JSON. Rebuilding." -ForegroundColor Yellow
                $pluginList = @()
            }
        }

        if (-not ($pluginList -contains $targetPluginId)) {
            $pluginList = @($pluginList) + @($targetPluginId)
            $uniqueList = @($pluginList | Select-Object -Unique)
            $jsonContent = Format-JsonArray -Items $uniqueList
            [System.IO.File]::WriteAllText($pluginsConfigFile, $jsonContent, [System.Text.Encoding]::UTF8)
            Write-Host "  + Enabled [$targetPluginId] in existing community-plugins.json"
        } else {
            Write-Host "  = Plugin [$targetPluginId] is already enabled in community-plugins.json"
        }
    }

    exit 0
} catch {
    Write-Host "ERROR in migration 003: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
