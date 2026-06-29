param([string]$FactoryRoot)

$inboxDir = Join-Path $FactoryRoot "vault\00-Inbox"
$processedDir = Join-Path $inboxDir "Processed"
$inboxFiles = @("Concepts.md", "Data-Points.md", "Insights.md", "Quotes.md", "Solutions.md", "Stories.md", "Uncategorized.md")

if (-not (Test-Path $processedDir)) { New-Item -ItemType Directory -Path $processedDir -Force | Out-Null }

foreach ($f in $inboxFiles) {
    $gioPath = Join-Path $inboxDir $f
    $logPath = Join-Path $processedDir $f
    if (-not (Test-Path $gioPath)) { New-Item -ItemType File -Path $gioPath -Force | Out-Null }
    if (-not (Test-Path $logPath)) { New-Item -ItemType File -Path $logPath -Force | Out-Null }
}

$guideSource = Join-Path $FactoryRoot ".agents\skills\persona-interviewer\assets\_Huong-dan.md"
$guideDest = Join-Path $inboxDir "_Huong-dan.md"
if ((Test-Path $guideSource) -and (-not (Test-Path $guideDest))) {
    Copy-Item -Path $guideSource -Destination $guideDest -Force
}

$gitkeep = Join-Path $inboxDir ".gitkeep"
if (Test-Path $gitkeep) { Remove-Item $gitkeep -Force }

exit 0
