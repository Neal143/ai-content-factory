param(
    [Parameter(Mandatory = $true)]
    [string]$Audience
)

# Đường dẫn vật lý tĩnh kỹ thuật (Architecture Routing)
$OutputPath = "vault/01-Atomic/Insights"
$TemplatePath = ".agents/skills/persona-interviewer/assets/insight.md"
$PayloadPath = ".agents/skills/persona-interviewer/scripts/insights_payload.json"

Write-Host "🔄 Processing Batch Insights..."

# Gọi Backend ẩn (Tránh làm rác Prompt)
python .agents/skills/persona-interviewer/scripts/generate_insights.py --payload $PayloadPath --template $TemplatePath --output $OutputPath --audience $Audience

Write-Host "✅ Dữ liệu Payload đã được nạp xong. File Buffer rỗng sẵn sàng cho lượt tiếp theo."

