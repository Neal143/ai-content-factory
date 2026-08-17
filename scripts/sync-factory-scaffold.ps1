# ------------------------------------------------------------------
# Ten file: sync-factory-scaffold.ps1
# Last update: 17/08/2026 22:30 (GMT+7)
# Vai tro: Dong bo cau truc thu muc va tap tin tu template scaffold sang FactoryRoot:
#          - Du lieu nguoi dung: Creation-only (tuyet doi khong ghi de).
#          - Plugin Obsidian cua Factory: Managed update (chi ghi de file thuoc plugin Factory).
#          - Plugin Obsidian ben thu 3: Giu nguyen 100% (khong dong cham).
#          - Danh sach plugin kich hoat: Auto-merge (bao toan 100% plugin ca nhan).
# Duoc su dung khi: Tu dong goi boi run-migrations.ps1 (khi update) va init_vault.ps1 (khi onboarding).
# Output: Console messages ve so luong item tao moi/cap nhat. Exit 0 = thanh cong, Exit 1 = that bai.
# Tom tat logic hoat dong:
#   1. Xac dinh duong dan template tai .agents/assets/factory-scaffold.
#   2. Quet de quy tat ca thu muc va tap tin trong template.
#   3. Phan vung xu ly theo loai tap tin:
#      - Neu thuoc vault/.obsidian/plugins/*: Chi ghi de cac file dich thuc su co trong template.
#      - Neu la du lieu thong thuong (00-Inbox, 01-Atomic, personas): Chi tao neu chua ton tai.
#   4. Quet danh sach Factory Plugin IDs co trong template scaffold.
#   5. Doc file community-plugins.json cua user, append cac ID con thieu va luu lai format JSON chuan.
# ------------------------------------------------------------------
param(
    [Parameter(Mandatory = $true)]
    [string]$FactoryRoot
)

$ErrorActionPreference = "Stop"

try {
    # --- Nhom 1: Xac dinh duong dan va kiem tra su ton tai cua template scaffold ---
    $templateDir = Join-Path $FactoryRoot ".agents\assets\factory-scaffold"
    if (-not (Test-Path $templateDir)) {
        Write-Host "[FATAL] factory-scaffold template not found at: $templateDir" -ForegroundColor Red
        exit 1
    }

    Write-Host "Syncing factory scaffold from template..."
    $createdCount = 0
    $updatedCount = 0

    # --- Nhom 2: Quet de quy toan bo template va mirror sang FactoryRoot ---
    $items = Get-ChildItem -Path $templateDir -Recurse

    foreach ($item in $items) {
        # Tinh toan duong dan tuong doi va duong dan dich
        $relativePath = $item.FullName.Substring($templateDir.Length).TrimStart('\', '/')
        $destPath = Join-Path $FactoryRoot $relativePath

        if ($item.PSIsContainer) {
            # Tao thu muc neu chua ton tai tren may user
            if (-not (Test-Path $destPath)) {
                New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                Write-Host "  + Created folder: $relativePath"
                $createdCount++
            }
        }
        else {
            # Bo qua file .gitkeep dung de giu thu muc rong tren Git
            if ($item.Name -eq ".gitkeep") { continue }
            
            # Bo qua file community-plugins.json de xu ly bang logic merge rieng o Nhom 3
            if ($relativePath -eq "vault\.obsidian\community-plugins.json") { continue }

            # Dam bao thu muc cha ton tai truoc khi copy file
            $parentDir = Split-Path $destPath -Parent
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }

            # Phan vung A: Factory Obsidian Plugins (Chi ghi de tung file cua Factory Plugin co trong scaffold)
            if ($relativePath -like "vault\.obsidian\plugins\*") {
                if (Test-Path $destPath) {
                    # So sanh byte de chi ghi de khi file thuc su co thay doi
                    $srcBytes = [System.IO.File]::ReadAllBytes($item.FullName)
                    $dstBytes = [System.IO.File]::ReadAllBytes($destPath)
                    $isEqual = ($srcBytes.Length -eq $dstBytes.Length) -and ((Compare-Object $srcBytes $dstBytes) -eq $null)
                    
                    if (-not $isEqual) {
                        Copy-Item -Path $item.FullName -Destination $destPath -Force
                        Write-Host "  ^ Updated factory plugin file: $relativePath"
                        $updatedCount++
                    }
                } else {
                    Copy-Item -Path $item.FullName -Destination $destPath -Force
                    Write-Host "  + Created factory plugin file: $relativePath"
                    $createdCount++
                }
            }
            # Phan vung B: Du lieu va foundation files thong thuong (Creation-only: khong ghi de du lieu user)
            else {
                if (-not (Test-Path $destPath)) {
                    Copy-Item -Path $item.FullName -Destination $destPath -Force
                    Write-Host "  + Created file: $relativePath"
                    $createdCount++
                }
            }
        }
    }

    # --- Nhom 3: Tu dong merge cac Factory Plugins vao community-plugins.json ---
    $scaffoldPluginsDir = Join-Path $templateDir "vault\.obsidian\plugins"
    if (Test-Path $scaffoldPluginsDir) {
        # Lay danh sach tat ca cac plugin duoc quan ly trong scaffold
        $factoryPluginIds = @(Get-ChildItem -Path $scaffoldPluginsDir -Directory | Select-Object -ExpandProperty Name)
        
        if ($factoryPluginIds.Count -gt 0) {
            $obsidianDir = Join-Path $FactoryRoot "vault\.obsidian"
            if (-not (Test-Path $obsidianDir)) {
                New-Item -ItemType Directory -Path $obsidianDir -Force | Out-Null
            }
            
            $pluginsConfigFile = Join-Path $obsidianDir "community-plugins.json"
            $pluginList = @()

            # Doc danh sach plugin hien co cua user neu file da ton tai
            if (Test-Path $pluginsConfigFile) {
                $rawContent = [System.IO.File]::ReadAllText($pluginsConfigFile, [System.Text.Encoding]::UTF8)
                if (-not [string]::IsNullOrWhiteSpace($rawContent)) {
                    try {
                        $parsed = ConvertFrom-Json -InputObject $rawContent
                        $pluginList = @($parsed)
                    } catch {
                        Write-Host "  ! Warning: Invalid community-plugins.json. Rebuilding." -ForegroundColor Yellow
                        $pluginList = @()
                    }
                }
            }

            # Helper format mang JSON 2-space indent chuan Obsidian (chong loi ep kieu PS)
            function Format-JsonArray {
                param([string[]]$Items)
                if ($Items.Count -eq 0) { return "[]" }
                $lines = $Items | ForEach-Object { "  `"$_`"" }
                return "[`r`n" + ($lines -join ",`r`n") + "`r`n]"
            }

            # Loc ra cac plugin cua Factory chua duoc bat trong config cua user
            $missingPlugins = @($factoryPluginIds | Where-Object { -not ($pluginList -contains $_) })
            if ($missingPlugins.Count -gt 0) {
                $combined = @($pluginList) + @($missingPlugins)
                $uniqueList = @($combined | Select-Object -Unique)
                $jsonOutput = Format-JsonArray -Items $uniqueList
                [System.IO.File]::WriteAllText($pluginsConfigFile, $jsonOutput, [System.Text.Encoding]::UTF8)
                Write-Host "  + Enabled factory plugins in community-plugins.json: $($missingPlugins -join ', ')"
                $updatedCount++
            }
        }
    }

    # --- Nhom 4: Bao cao ket qua va ket thuc ---
    Write-Host "[OK] Factory scaffold sync completed. Created: $createdCount, Updated: $updatedCount item(s)."
    exit 0
} catch {
    Write-Host "[FATAL] Factory scaffold sync failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
