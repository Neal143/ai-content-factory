---
description: Pipeline 7 giai đoạn – 1 phiên liên tục qua Sub-Agents.
---

> **Last Update**: 04/06/2026 16:00 (GMT+7)
# Workflow: Viết bài viral (Content Post)
> **LỆNH**: `/content-post [yêu cầu]` | `/content-post tiếp tục`
> PIPELINE_STATUS: SẴN SÀNG

## Output Rules
- Run folder: `vault/.content-pipeline/runs/[YYYY-MM-DD_HHmmss]_[topic-slug]/`
- `00.5-dikw-combo.md` – output Phase 5 DIKW, phục vụ resume (không có nếu `Is_Novel_Angle=True`).
- `gate5-issues.md`, `gate6-issues.md` lưu tại run folder.
- 🚫 KHÔNG ghi ra `output/` root hay `vault/output/`.
- Context mất/truncate – tự mở đọc file trong run folder.

## 🚫 HÀNH VI BỊ CẤM (Vi phạm = HALT, báo User)
1. CẤM tạo file script mới (`.py`, `.js`, `.sh`, `.ps1`).
2. CẤM hardcode bài viết vào biến/code.
3. CẤM hardcode điểm QA vào frontmatter.
4. CẤM padding từ vựng rác.
5. CẤM ghi file vào root `vault/.content-pipeline/` (chỉ được ghi vào sub-folder runs/, posts/, logs/).
6. TRUNCATION GUARD: Context bị `truncated` -> DỪNG + BÁO User.
7. SYSTEM DRIFT GUARD: Script lỗi -> DỪNG + BÁO. KHÔNG tự bóp méo nội dung để lách lỗi.

## Hướng dẫn thực thi

### 1. Gate Check
Kiểm tra cú pháp yêu cầu từ User:
- NẾU lệnh là `/content-post tiếp tục`: Bỏ qua Bước 1, Bước 2. Đi thẳng tới CHECKPOINT & RESUME DỰ PHÒNG.
- NẾU lệnh chứa cấu trúc `/content-post hủy và viết mới:`:
  1. Tự động chạy lệnh `powershell -ep Bypass -f .agents/scripts/generate-phase-key.ps1` để reset hệ thống và sinh bộ key mới.
  2. Chờ thực thi xong, đi thẳng sang Bước 2 để bắt đầu làm việc.
- NẾU lệnh là bắt đầu bài mới thông thường (`/content-post [yêu cầu]`):
  Đọc `PIPELINE_STATUS`. Nếu là `CHƯA SẴN SÀNG`, DỪNG NGAY. In ra mẫu câu sau để User copy:
  > ⚠️ Hệ thống đang kẹt một phiên làm việc dang dở. Copy và gửi lại 1 trong 2 lệnh sau:
  > 1. Để tiếp tục phiên cũ: `/content-post tiếp tục`
  > 2. Để hủy phiên cũ và bắt đầu bài mới này: `/content-post hủy và viết mới: [nội dung yêu cầu bài viết của bạn]`

### 2. Chọn Chế Độ Viết
Đọc `.agents/agents/format-selector/AGENT.md`, gọi tool `define_subagent` (name: "FormatSelector", system_prompt: nội dung AGENT.md). Gọi `invoke_subagent` (TypeName: "FormatSelector", Prompt: "Thực thi").

### 3. Validate Persona (1 Lần)
```powershell
powershell -ep Bypass -f .agents/scripts/validate-persona.ps1
```
- Exit 0: Lưu `PERSONA_PATH` ở dòng cuối output.
- Exit 1: DỪNG.

### 4. Semantic Router
Đọc `.agents/agents/semantic-router/AGENT.md`, gọi tool `define_subagent` (name: "SemanticRouter", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "SemanticRouter", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Thực thi và ghi `00-blackboard.yaml`").
- `Is_Novel_Angle=False`: Chạy Bước 5.
- `Is_Novel_Angle=True`: Chạy Bước 6.
Snapshot: `Copy-Item "formats/active.json" -Destination "[run-folder]/00-format.json"`
Sentinel 0: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 0`

### 5. DIKW Bridge
<!-- NEXT_GUIDANCE: DIKW -->
Đọc `.agents/agents/dikw-bridge/AGENT.md`, gọi tool `define_subagent` (name: "DikwBridge", system_prompt: nội dung AGENT.md). Gọi `invoke_subagent` (TypeName: "DikwBridge", Prompt: "Thực thi"). Xong -> Compile payload Phase 1.
<!-- /NEXT_GUIDANCE: DIKW -->

### 6. Pipeline 7 Phases
> **RULES:** (1) Giữ Blackboard. (2) Chạy Sentinel mỗi phase. (3) Tự check Gate. (4) Agent chính là Orchestrator, BẮT BUỘC dùng tool invoke_subagent để giao việc, KHÔNG tự sinh nội dung. Cấp Workspace cho sub-agent là thư mục run-folder. (5) Ghi `<!-- execution_key: [KEY] -->` cuối output. (6) Sentinel `exit 0`=PASS, `exit 1`=HALT, `exit 2`=RETRY (Truyền file lỗi vào lại sub-agent để sửa, max 3 lần). (7) Các lệnh dưới an toàn.

*(Chạy tuần tự các lệnh JIT sau trước khi gọi Agent)*

<!-- NEXT_GUIDANCE: 1 -->
**Phase 1: Idea Curator** (`01-idea-brief.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -InputMap "blackboard:00-blackboard.yaml, dikw:?00.5-dikw-combo.md, history:?vault/.content-pipeline/logs/idea-history.md|@LAST_7_DAYS"`
2. Phân nhiệm: Đọc `.agents/agents/idea-curator/AGENT.md`, gọi `define_subagent` (name: "IdeaCurator", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "IdeaCurator", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `01-idea-brief.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 1`
<!-- /NEXT_GUIDANCE: 1 -->

<!-- NEXT_GUIDANCE: 2 -->
**Phase 2: Insight Agent** (`02-research-brief.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "01-idea-brief.md" -InputMap "angle:01-idea-brief.md|CONTRARIAN_ANGLE, tension:01-idea-brief.md|CORE_TENSION, belief:01-idea-brief.md|HIDDEN_BELIEF, dikw:?00.5-dikw-combo.md, blackboard:00-blackboard.yaml"`
2. Phân nhiệm: Đọc `.agents/agents/insight-agent/AGENT.md`, gọi `define_subagent` (name: "InsightAgent", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "InsightAgent", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `02-research-brief.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 2`
<!-- /NEXT_GUIDANCE: 2 -->

<!-- NEXT_GUIDANCE: 3 -->
**Phase 3: Hook Engineer** (`03-hook.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "02-research-brief.md" -InputMap "angle:01-idea-brief.md|CONTRARIAN_ANGLE, tension:01-idea-brief.md|CORE_TENSION, evidence:02-research-brief.md|EVIDENCE_LIST, quotes:02-research-brief.md|EXPERT_QUOTES, blackboard:00-blackboard.yaml, dikw:?00.5-dikw-combo.md"`
2. Phân nhiệm: Đọc `.agents/agents/hook-engineer/AGENT.md`, gọi `define_subagent` (name: "HookEngineer", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "HookEngineer", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `03-hook.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 3`
<!-- /NEXT_GUIDANCE: 3 -->

<!-- NEXT_GUIDANCE: 4 -->
**Phase 4: Structure Designer** (`04-outline.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "03-hook.md" -InputMap "hook:03-hook.md|CORE_HOOK, tension:01-idea-brief.md|CORE_TENSION, evidence:02-research-brief.md|EVIDENCE_LIST, stories:02-research-brief.md|STORY_LIST, dikw:?00.5-dikw-combo.md"`
2. Phân nhiệm: Đọc `.agents/agents/structure-designer/AGENT.md`, gọi `define_subagent` (name: "StructureDesigner", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "StructureDesigner", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `04-outline.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 4`
<!-- /NEXT_GUIDANCE: 4 -->

<!-- NEXT_GUIDANCE: 45 -->
**Phase 4.5: Persona Loader** (`04.5-persona-pack.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -InputMap "blackboard:00-blackboard.yaml"`
2. Phân nhiệm: Đọc `.agents/agents/persona-loader/AGENT.md`, gọi `define_subagent` (name: "PersonaLoader", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "PersonaLoader", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `04.5-persona-pack.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 45`
<!-- /NEXT_GUIDANCE: 45 -->

<!-- NEXT_GUIDANCE: 5 -->
**Phase 5: Voice Writer** (`05-draft.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "04.5-persona-pack.md" -InputMap "outline:04-outline.md|OUTLINE_SECTIONS, closing:04-outline.md|CLOSING_COMBO, persona:04.5-persona-pack.md|PERSONA_DNA, evidence:02-research-brief.md|EVIDENCE_LIST, stories:02-research-brief.md|STORY_LIST, dikw:?00.5-dikw-combo.md, connection:?01-idea-brief.md|IDEA_CONNECTION"`
2. Phân nhiệm: Đọc `.agents/agents/voice-writer/AGENT.md`, gọi `define_subagent` (name: "VoiceWriter", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "VoiceWriter", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `05-draft.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 5`
<!-- /NEXT_GUIDANCE: 5 -->

<!-- NEXT_GUIDANCE: 6 -->
**Phase 6: QA Checker** (`06-qa-result.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "05-draft.md" -InputMap "draft:05-draft.md|DRAFT_SECTIONS"`
2. Phân nhiệm: Đọc `.agents/agents/qa-checker/AGENT.md`, gọi `define_subagent` (name: "QAChecker", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "QAChecker", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `06-qa-result.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 6`
<!-- /NEXT_GUIDANCE: 6 -->

<!-- NEXT_GUIDANCE: 7 -->
**Phase 7: Format Agent** (`07-final.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/compile-payload.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -PrevOutput "06-qa-result.md" -InputMap "draft:05-draft.md|DRAFT_SECTIONS, qa:06-qa-result.md|QA_REPORT, blackboard:00-blackboard.yaml"`
2. Phân nhiệm: Đọc `.agents/agents/format-agent/AGENT.md`, gọi `define_subagent` (name: "FormatAgent", system_prompt: nội dung AGENT.md, enable_write_tools: true). Gọi `invoke_subagent` (TypeName: "FormatAgent", Workspace: "vault/.content-pipeline/runs/[run-folder]/", Prompt: "Xử lý dữ liệu payload, xuất kết quả ra `07-final.md`").
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 7`
<!-- /NEXT_GUIDANCE: 7 -->

**Phase 6 REVISE:** Tạo `gate6-issues.md` -> Orchestrator truyền file lỗi gọi lại `invoke_subagent` (TypeName: "VoiceWriter") để sửa, sau đó gọi lại `invoke_subagent` (TypeName: "QAChecker") chấm lại (max 3 lần). FAIL -> Báo User.

### 7. Hoàn thành
Xác nhận có `07-final.md`, bài viết tại `vault/03-Content/Posted/` (đã strip `execution_key`), `production-log.md` & `hook-history.md` đã cập nhật. Báo User hoàn thành. Sentinel tự động chạy `apply-format.ps1 -Action restore`.

## CHECKPOINT & RESUME DỰ PHÒNG
- Tiến độ (State) được lưu tự động & liên tục sau mỗi Phase thành công qua hệ thống Sentinel Tracker. Bất kể đứt gãy ở Phase nào, hệ thống tự động Resume chính xác tại Phase đó.
- Lệnh `/content-post tiếp tục`:
  1. Chạy: `powershell -ep Bypass -f .agents/scripts/resolve-checkpoint.ps1`
  2. Parse output -> Đọc NỘI DUNG ĐẦY ĐỦ các file trong `LOAD_FILES`.
  3. BẮT BUỘC chạy lại Phase 4.5.
  4. Tiếp tục từ phase kế tiếp.

## XỬ LÝ LỖI
1. `exit 2` (RETRY): Truyền file lỗi vào lại invoke_subagent của phase đó để sửa, chạy lại Sentinel (max 3 lần).
2. `exit 1` (HALT): DỪNG NGAY. Báo User.
3. FAIL liên tiếp 3 lần: Báo User.