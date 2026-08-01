---
description: "Workflow Antigravity 2.0: Gọi VaultCuratorAgent/AudienceResolverAgent qua subagents, user không cần theo dõi."
---

> **Tên file**: .agents/workflows/vault-curator-anti20.md
> **Last update**: 31/07/2026 23:16 (GMT+7)
> **Vai trò**: Workflow dành cho Antigravity 2.0 — orchestrator gọi VaultCuratorAgent hoặc AudienceResolverAgent qua subagents.
> **Sử dụng khi**: User muốn chạy curation/recalibration pipeline tự động trên Antigravity 2.0 (hỗ trợ define_subagent/invoke_subagent).
> **Output**: Vault đã chuẩn hóa + Summary report.
> **Tóm tắt logic**: Orchestrator phân luồng theo mode → mode curation: đọc AGENT.md routing → spawn subagent per skill. Mode recalibrate-audiences: 3-phase pipeline (calibrate → apply → dedup).

# Workflow: Vault Curation (Antigravity 2.0 – Sub-Agents)

> **LỆNH**: `/vault-curate --mode <mode> [--atoms <list>] [--output-dir <dir>]`
>
> ⚠️ **LUẬT KHÔNG HỎI LẠI (NO PROMPTING RULE)**:
> - Nếu User KHÔNG truyền tham số `--output-dir`, **TUYỆT ĐỐI KHÔNG ĐƯỢC HỎI LẠI**. Tự động lấy giá trị mặc định là: `vault/.curation_temp/`
>
> **Tham chiếu**:
> - Curation modes → đọc [VaultCurator AGENT.md](file:///.agents/agents/vault-curator/AGENT.md)
> - Mode `recalibrate-audiences` → đọc [AudienceResolver AGENT.md](file:///.agents/agents/audience-resolver/AGENT.md)

## Hướng dẫn thực thi

### 1. Phân luồng theo Mode

```text
IF mode == "recalibrate-audiences":
  → Chuyển sang phần "Hướng dẫn thực thi: recalibrate-audiences" bên dưới.
  → KHÔNG thực hiện Bước 2, 3, 4 của luồng curation.
ELSE:
  → Tiếp tục Bước 2 (luồng curation tiêu chuẩn).
```

---

## Luồng A: Curation tiêu chuẩn (tất cả modes trừ recalibrate-audiences)

### 2. Xác định Skill Queue từ não bộ VaultCurator

Bạn (Orchestrator) hãy đọc phần **Kịch bản Routing Logic** trong file `.agents/agents/vault-curator/AGENT.md` để tự xác định danh sách các skill cần gọi cho `<MODE>` tương ứng. 

Ví dụ: Nếu trong AGENT.md ghi là `1. Gọi skill auto-tagger`, `2. Gọi skill atom-dedup`, thì bạn sẽ biết Skill Queue của mình là `[auto-tagger, atom-dedup]`.

### 3. Init + Tạo Pipeline Context

**2a. Tạo pipeline_context.json:**
```python
write_to_file("<OUTPUT_DIR>/pipeline_context.json", {
  "mode": "<MODE>",
  "atoms_file": "<ATOMS_FILE>",
  "root_output_dir": "<OUTPUT_DIR>"
})
```

**2b. Init batches cho từng skill:**
Trước khi chạy subagent cho một skill, bạn (Orchestrator) PHẢI đọc `SKILL.md` của skill đó tại `.agents/skills/<tên_skill>/SKILL.md` để lấy lệnh `--init` (nằm ở Bước 1 của SKILL.md) và chạy nó trên terminal.

*Lưu ý: Bạn là một Agent thông minh. Nếu lệnh `--init` trong SKILL.md yêu cầu truyền đường dẫn persona (VD: `[persona-path]/topic_map.yaml`), hãy dùng lệnh hệ thống để tự động tìm tệp đó và thay thế vào tham số.*

### 4. Skill Loop (Tạo Subagent qua Antigravity 2.0)

Với mỗi skill trong queue đã xác định ở Bước 2:

**3a. Define subagent:**
```
define_subagent(
  name: "VaultCurator_<tên_skill>",
  system_prompt: Đọc và gộp nội dung của AGENT.md + SKILL.md tương ứng,
  enable_write_tools: true
)
```

**3b. Invoke subagent:**
```
invoke_subagent(
  TypeName: "VaultCurator_<tên_skill>",
  Workspace: ".",
  Prompt: """
    Skill: <tên_skill>
    Output dir: <OUTPUT_DIR>/<tên_skill>

    BỎ QUA Bước 1 trong SKILL.md (Orchestrator đã chạy --init). 
    Bắt đầu từ Bước 2: Thực thi vòng lặp get-next → xử lý → submit theo SKILL.md.
    Dừng khi stdout chứa "ALL_DONE" hoặc "SESSION_BREAK".
    Trả về nguyên văn stdout cuối cùng.
  """
)
```

**4c. Parse response:**

| Stdout từ Subagent chứa | Orchestrator hành động |
|---|---|
| `ALL_DONE` | Đọc summary từ stdout. Nếu còn skill tiếp theo → thực hiện Bước 3b và 4a cho skill tiếp theo. Nếu hết → chuyển Bước 5. |
| `SESSION_BREAK` | Extract handoff prompt (nội dung giữa `---` và `---`) → `invoke_subagent` lại với prompt đó → quay lại 4c. |

### 5. Pipeline hoàn tất

Tất cả skills đã ALL_DONE:
1. Tổng hợp summary từ tất cả skills và báo cáo kết quả tổng hợp cho User.
2. Xóa atoms file nếu workflow truyền qua `--atoms-file` (VD: `pending_curation_atoms.txt`, `created_atoms.json`).
3. **Dọn rác thư mục tạm**: Hỏi ý kiến User xem có muốn xóa toàn bộ thư mục lưu các file xử lý `<OUTPUT_DIR>` không (vì chúng không còn giá trị sử dụng). Ví dụ: *"Tiến trình đã hoàn tất. Thư mục tạm `<OUTPUT_DIR>` đang chứa các file log và batch xử lý. Bạn có muốn tôi xóa sạch thư mục này không?"*.
4. Nếu User đồng ý, hãy dùng lệnh hệ thống (VD: `Remove-Item -Recurse -Force "<OUTPUT_DIR>"`) để dọn dẹp.

---

## Luồng B: recalibrate-audiences (Hiệu đính lại JTBD audiences)

> **Tham chiếu**: [AudienceResolver AGENT.md](file:///.agents/agents/audience-resolver/AGENT.md) — Mode RE-CALIBRATE.

### B1. Init — Tạo work_dir và extract dữ liệu

**B1a. Tạo work_dir:**
Tự động tạo thư mục tạm theo timestamp:
```bash
# Format: session_{YYYY-MM-DD_HH-MM}
mkdir -p "vault/recalibrate_runs/session_$(date +%Y-%m-%d_%H-%M)/"
```
> `<WORK_DIR>` = `vault/recalibrate_runs/session_{timestamp}/`

**B1b. Extract audiences hiện tại:**
```bash
python .agents/skills/jtbd-calibrator/scripts/extract_existing_audiences.py \
    --audience-index "vault/01-Atomic/Audiences/_audience_index.yaml" \
    --vault-root "vault/" \
    --output-json "<WORK_DIR>/audiences_parsed.json"
```

**B1c. Phân lô dữ liệu:**
```bash
python .agents/skills/jtbd-calibrator/scripts/prepare_calibration_batches.py \
    --parsed-json "<WORK_DIR>/audiences_parsed.json" \
    --split-dir "<WORK_DIR>/calib_batches" \
    --batch-size 5
```
> Không cần `--source-file` vì mode re-calibrate.

### B2. JTBD Calibration Loop (Subagent)

**B2a. Define subagent:**
```
define_subagent(
  name: "AudienceResolver_jtbd_calibrator",
  system_prompt: Đọc và gộp nội dung của:
    - .agents/agents/audience-resolver/AGENT.md
    - .agents/skills/jtbd-calibrator/SKILL.md
  enable_write_tools: true
)
```

**B2b. Invoke subagent:**
```
invoke_subagent(
  TypeName: "AudienceResolver_jtbd_calibrator",
  Workspace: ".",
  Prompt: """
    Mode: re-calibrate
    Work dir: <WORK_DIR>
    Session dir: <WORK_DIR>/calib_batches

    BỎ QUA Bước 1 và Bước 2 trong SKILL.md (Orchestrator đã chạy extract + phân lô).
    Bắt đầu từ Bước 3: Thực thi vòng lặp get-next → hiệu chỉnh JTBD → submit.
    Lưu ý: Mode re-calibrate — template có pre-fill, đọc giá trị pre-fill và hiệu chỉnh nếu vi phạm tiêu chuẩn.
    Dừng khi stdout chứa "HOÀN THÀNH" hoặc "SESSION_BREAK".
    Trả về nguyên văn stdout cuối cùng.
  """
)
```

**B2c. Parse response:**

| Stdout từ Subagent chứa | Orchestrator hành động |
|---|---|
| `HOÀN THÀNH` (đã sinh `jtbd_recalibrated.json`) | Chuyển sang B3. |
| `SESSION_BREAK` | Extract handoff prompt → `invoke_subagent` lại → quay lại B2c. |

### B3. Apply Recalibration (Orchestrator tự chạy — KHÔNG spawn subagent)

**B3a. Dry-run:**
```bash
python .agents/skills/jtbd-calibrator/scripts/apply_recalibration.py \
    --recalibrated-json "<WORK_DIR>/jtbd_recalibrated.json" \
    --vault-root "vault/" \
    --work-dir "<WORK_DIR>" \
    --dry-run
```

**B3b. Trình bày dry-run report** cho user:
- Số entries cần rename vs chỉ update nội dung
- Backup sẽ lưu tại đâu

**B3c. Hỏi user xác nhận** (ngoại lệ duy nhất được hỏi):
*"Dry-run report: {N} entries hiệu đính, {R} cần rename. Xác nhận để tiếp tục?"*

**B3d. Nếu user xác nhận → chạy thật:**
```bash
python .agents/skills/jtbd-calibrator/scripts/apply_recalibration.py \
    --recalibrated-json "<WORK_DIR>/jtbd_recalibrated.json" \
    --vault-root "vault/" \
    --work-dir "<WORK_DIR>"
```

**B3e. Kiểm tra kết quả:**
- `VERIFICATION PASSED` → chuyển B4.
- `VERIFICATION FAILED` → DỪNG, báo user backup path để rollback.

### B4. Semantic Deduplication (Subagent)

**B4a. Init batches:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill vc-audience-curator \
    --meta-source "vault/01-Atomic/Audiences/_audience_index.yaml" \
    --batch-size 20 \
    --output-dir "<WORK_DIR>/dedup_session"
```

**B4b. Define subagent:**
```
define_subagent(
  name: "AudienceResolver_audience_curator",
  system_prompt: Đọc và gộp nội dung của:
    - .agents/agents/vault-curator/AGENT.md
    - .agents/skills/vc-audience-curator/SKILL.md
  enable_write_tools: true
)
```

**B4c. Invoke subagent:**
```
invoke_subagent(
  TypeName: "AudienceResolver_audience_curator",
  Workspace: ".",
  Prompt: """
    Skill: vc-audience-curator
    Output dir: <WORK_DIR>/dedup_session

    BỎ QUA Bước 1 trong SKILL.md (Orchestrator đã chạy --init).
    Bắt đầu từ Bước 2: Thực thi vòng lặp get-next → đánh giá semantic → submit.
    Dừng khi stdout chứa "ALL_DONE" hoặc "SESSION_BREAK".
    Trả về nguyên văn stdout cuối cùng.
  """
)
```

**B4d. Parse response:**

| Stdout từ Subagent chứa | Orchestrator hành động |
|---|---|
| `ALL_DONE` | Đọc summary. Chuyển sang B5. |
| `SESSION_BREAK` | Extract handoff prompt → `invoke_subagent` lại → quay lại B4d. |

### B5. Pipeline hoàn tất

1. Tổng hợp summary từ cả 3 giai đoạn:
   - **Calibration**: Số batches đã xử lý, số lỗi đã sửa
   - **Apply**: Đọc `<WORK_DIR>/recalibration_report.json` — số entries renamed, content-only, verification status
   - **Dedup**: Số cặp trùng đã merge (nếu có)
2. Báo cáo kết quả tổng hợp cho User.
3. Work_dir (`vault/recalibrate_runs/session_*/`) giữ lại làm audit trail. Không xóa.

## Xử lý lỗi

### Luồng A (Curation)

| Tình huống | Hành động |
|---|---|
| Subagent crash/timeout | Orchestrator gọi `--status --output-dir` → biết batch pending → spawn subagent mới tiếp tục |
| Script lỗi (exit != 0) | Subagent báo orchestrator → DỪNG + BÁO user |
| Validation fail (submit reject) | Subagent tự retry sửa kết quả (max 3 lần). Fail → BÁO orchestrator |

### Luồng B (Recalibrate)

| Tình huống | Hành động |
|---|---|
| Subagent crash/timeout (calibration) | Orchestrator gọi `--get-next --session-dir <WORK_DIR>/calib_batches` → biết batch pending → spawn subagent mới tiếp tục |
| Subagent crash/timeout (dedup) | Orchestrator gọi `--status --output-dir <WORK_DIR>/dedup_session` → spawn subagent mới tiếp tục |
| Script lỗi (exit != 0) | DỪNG + BÁO user |
| apply_recalibration.py VERIFICATION FAILED | DỪNG + báo user backup path để rollback thủ công |
| Validation fail (submit reject) | Subagent tự retry sửa kết quả (max 3 lần). Fail → BÁO orchestrator |
