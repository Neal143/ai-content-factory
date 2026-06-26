<#
.SYNOPSIS
Ten file: run_insights.ps1
Last update: 26/06/2026 15:16 (GMT+7)
Vai tro: Wrapper PowerShell goi script Python generate_insights.py
Khi nao dung: Duoc goi tu SKILL.md sau khi user xac nhan mapping Insight-Pillar
Output: Cac file Markdown Insight trong vault/01-Atomic/Insights + cap nhat pillars.yaml
Logic:
  1. Nhan tham so UserName va Audience tu SKILL.md
  2. Truyen cac duong dan tinh (payload, template, output) den Python
  3. Python tao file .md va tu dong cap nhat file_ref/file_link trong pillars.yaml
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$UserName,
    [Parameter(Mandatory = $true)]
    [string]$Audience
)

# Duong dan vat ly tinh ky thuat (Architecture Routing)
$OutputPath = "vault/01-Atomic/Insights"
$TemplatePath = ".agents/skills/persona-interviewer/assets/insight.md"
$PayloadPath = ".agents/skills/persona-interviewer/scripts/insights_payload.json"

Write-Host "Processing Batch Insights..."

# Goi Backend an (Tranh lam rac Prompt)
python .agents/skills/persona-interviewer/scripts/generate_insights.py --payload $PayloadPath --template $TemplatePath --output $OutputPath --audience $Audience --username $UserName

Write-Host "Du lieu Payload da duoc nap xong. File Buffer rong san sang cho luot tiep theo."
