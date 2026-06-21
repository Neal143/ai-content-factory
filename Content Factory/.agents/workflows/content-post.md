---
description: Pipeline 7 giai đoạn – 1 phiên liên tục qua Sub-Agents.
---

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
Gọi **FormatSelectorAgent** (Đọc AGENT.md tại `.agents/agents/format-selector/`).

### 3. Validate Persona (1 Lần)
```powershell
powershell -ep Bypass -f .agents/scripts/validate-persona.ps1
```
- Exit 0: Lưu `PERSONA_PATH` ở dòng cuối output.
- Exit 1: DỪNG.

### 4. Semantic Router
Gọi **SemanticRouterAgent**. Ghi `00-blackboard.yaml`.
- `Is_Novel_Angle=False`: Chạy Bước 5.
- `Is_Novel_Angle=True`: Chạy Bước 6.
Snapshot: `Copy-Item ".agents/formats/active.json" -Destination "[run-folder]/00-format.json"`
Sentinel 0: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 0`

### 5. DIKW Bridge
<!-- NEXT_GUIDANCE: DIKW -->
Gọi **DikwBridgeAgent**. Xong -> Compile payload Phase 1.
<!-- /NEXT_GUIDANCE: DIKW -->

### 6. Pipeline 7 Phases
> **RULES:** (1) Giữ Blackboard. (2) Chạy Sentinel mỗi phase. (3) Tự check Gate. (4) Tự đọc payload `.temp/payload.md`. (5) Ghi `<!-- execution_key: [KEY] -->` cuối output. (6) Sentinel `exit 0`=PASS (xem NEXT_GUIDANCE), `exit 1`=HALT, `exit 2`=RETRY (sửa + chạy lại max 3 lần). (7) Các lệnh dưới an toàn (`SafeToAutoRun = true`).

*(Chạy tuần tự các lệnh JIT sau trước khi gọi Agent)*

<!-- NEXT_GUIDANCE: 1 -->
**Phase 1: Idea Curator** (`01-idea-brief.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 1`
2. Gọi Agent: Đọc AGENT.md tại `.agents/agents/idea-curator/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 1`
<!-- /NEXT_GUIDANCE: 1 -->

<!-- NEXT_GUIDANCE: 2 -->
**Phase 2: Insight Agent** (`02-research-brief.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 2`
2. Gọi Agent: `.agents/agents/insight-agent/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 2`
<!-- /NEXT_GUIDANCE: 2 -->

<!-- NEXT_GUIDANCE: 3 -->
**Phase 3: Hook Engineer** (`03-hook.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 3`
2. Gọi Agent: `.agents/agents/hook-engineer/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 3`
<!-- /NEXT_GUIDANCE: 3 -->

<!-- NEXT_GUIDANCE: 4 -->
**Phase 4: Structure Designer** (`04-outline.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 4`
2. Gọi Agent: `.agents/agents/structure-designer/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 4`
<!-- /NEXT_GUIDANCE: 4 -->

<!-- NEXT_GUIDANCE: 45 -->
**Phase 4.5: Persona Loader** (`04.5-persona-pack.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 45`
2. Gọi Agent: `.agents/agents/persona-loader/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 45`
<!-- /NEXT_GUIDANCE: 45 -->

<!-- NEXT_GUIDANCE: 5 -->
**Phase 5: Voice Writer** (`05-draft.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 5`
2. Gọi Agent: `.agents/agents/voice-writer/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 5`
<!-- /NEXT_GUIDANCE: 5 -->

<!-- NEXT_GUIDANCE: 6 -->
**Phase 6: QA Checker** (`06-qa-result.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 6`
2. Gọi Agent: `.agents/agents/qa-checker/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 6`
<!-- /NEXT_GUIDANCE: 6 -->

<!-- NEXT_GUIDANCE: 7 -->
**Phase 7: Format Agent** (`07-final.md`)
1. Payload: `powershell -ep Bypass -f .agents/scripts/prepare-payload.ps1 -Pipeline "content-post" -Phase 7`
2. Gọi Agent: `.agents/agents/format-agent/`
3. Sentinel: `powershell -ep Bypass -f .agents/scripts/detect-bypass.ps1 -RunFolder "vault/.content-pipeline/runs/[run-folder]/" -Phase 7`
<!-- /NEXT_GUIDANCE: 7 -->

**Phase 6 REVISE:** Tạo `gate6-issues.md` -> VoiceWriter sửa, QA chấm lại (max 3 lần). FAIL -> Báo User.

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
1. `exit 2` (RETRY): Tự sửa output, chạy Sentinel lại (max 3 lần).
2. `exit 1` (HALT): DỪNG NGAY. Báo User.
3. FAIL liên tiếp 3 lần: Báo User.