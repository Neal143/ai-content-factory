# ==============================================================================
# Tên File     : prepare-payload.ps1
# Last Update  : 11/06/2026 17:25 (GMT+7)
# Vai trò      : Bộ định tuyến cấu hình (Configuration Router) cho compile-payload.ps1
# Sử dụng khi  : Được gọi bởi các phase trong workflow để biên dịch payload động.
# ==============================================================================

param (
    [Parameter(Mandatory=$true)]
    [string]$Pipeline,

    [Parameter(Mandatory=$true)]
    [string]$Phase,

    [string]$RunFolder
)

$ErrorActionPreference = "Stop"

# 1. Tự động xác định RunFolder nếu bị bỏ trống hoặc chứa chuỗi thay thế cứng
if ([string]::IsNullOrWhiteSpace($RunFolder) -or $RunFolder -match '\[run-folder\]') {
    $runsDir = Join-Path $PSScriptRoot "../../vault/.content-pipeline/runs"
    if (Test-Path $runsDir) {
        $latest = Get-ChildItem -Path $runsDir -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
            $RunFolder = "vault/.content-pipeline/runs/$($latest.Name)/"
        } else {
            Throw "Lỗi: Không tìm thấy thư mục chạy nào trong $runsDir"
        }
    } else {
        Throw "Lỗi: Không tìm thấy thư mục: $runsDir"
    }
}

# 2. Định nghĩa Hashtable cấu hình cho các Phase
$ConfigMap = @{
    "content-post" = @{
        "1" = @{
            InputMap = "blackboard:00-blackboard.yaml, dikw:?00.5-dikw-combo.md, history:?vault/.content-pipeline/logs/idea-history.md|@LAST_7_DAYS"
        }
        "2" = @{
            PrevOutput = "01-idea-brief.md"
            InputMap = "angle:01-idea-brief.md|CONTRARIAN_ANGLE, tension:01-idea-brief.md|CORE_TENSION, belief:01-idea-brief.md|HIDDEN_BELIEF, dikw:?00.5-dikw-combo.md, blackboard:00-blackboard.yaml"
        }
        "3" = @{
            PrevOutput = "02-research-brief.md"
            InputMap = "angle:01-idea-brief.md|CONTRARIAN_ANGLE, tension:01-idea-brief.md|CORE_TENSION, evidence:02-research-brief.md|EVIDENCE_LIST, quotes:02-research-brief.md|EXPERT_QUOTES, blackboard:00-blackboard.yaml, dikw:?00.5-dikw-combo.md"
        }
        "4" = @{
            PrevOutput = "03-hook.md"
            InputMap = "hook:03-hook.md|CORE_HOOK, tension:01-idea-brief.md|CORE_TENSION, evidence:02-research-brief.md|EVIDENCE_LIST, stories:02-research-brief.md|STORY_LIST, dikw:?00.5-dikw-combo.md"
        }
        "4.5" = @{
            InputMap = "blackboard:00-blackboard.yaml"
        }
        "45" = @{
            InputMap = "blackboard:00-blackboard.yaml"
        }
        "5" = @{
            PrevOutput = "04.5-persona-pack.md"
            InputMap = "outline:04-outline.md|OUTLINE_SECTIONS, closing:04-outline.md|CLOSING_COMBO, persona:04.5-persona-pack.md|PERSONA_DNA, evidence:02-research-brief.md|EVIDENCE_LIST, stories:02-research-brief.md|STORY_LIST, dikw:?00.5-dikw-combo.md, connection:?01-idea-brief.md|IDEA_CONNECTION"
        }
        "6" = @{
            PrevOutput = "05-draft.md"
            InputMap = "draft:05-draft.md|DRAFT_SECTIONS"
        }
        "7" = @{
            PrevOutput = "06-qa-result.md"
            InputMap = "draft:05-draft.md|DRAFT_SECTIONS, qa:06-qa-result.md|QA_REPORT, blackboard:00-blackboard.yaml"
        }
    }
}

# 3. Trích xuất cấu hình của pipeline mục tiêu
if (-not $ConfigMap.ContainsKey($Pipeline)) {
    Throw "Lỗi: Pipeline '$Pipeline' chưa được cấu hình trong prepare-payload.ps1"
}

$PipelineConfig = $ConfigMap[$Pipeline]
$PhaseKey = [string]$Phase

if (-not $PipelineConfig.ContainsKey($PhaseKey)) {
    Throw "Lỗi: Phase '$PhaseKey' chưa được cấu hình cho pipeline '$Pipeline'"
}

$PhaseConfig = $PipelineConfig[$PhaseKey]

# 4. Lắp ráp tham số bằng Hashtable splatting và chuyển tiếp sang compile-payload.ps1
$compileArgs = @{
    RunFolder = $RunFolder
    InputMap  = $PhaseConfig["InputMap"]
}

if ($PhaseConfig.ContainsKey("PrevOutput")) {
    $compileArgs["PrevOutput"] = $PhaseConfig["PrevOutput"]
}

# Thực thi script compile đích
$compileScript = Join-Path $PSScriptRoot "compile-payload.ps1"
& $compileScript @compileArgs
