param([string]$FactoryRoot)

# Set location to FactoryRoot to make relative paths inside Update-PersonalAtomsQueue.ps1 work correctly
Set-Location -Path $FactoryRoot

$scriptPath = ".agents\scripts\Update-PersonalAtomsQueue.ps1"
if (Test-Path $scriptPath) {
    powershell -ExecutionPolicy Bypass -File $scriptPath -Action "init" 2>$null | Out-Null
}

exit 0
