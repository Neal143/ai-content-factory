---
description: "Workflow Antigravity 2.0: Gọi VaultCuratorAgent qua subagents, user không cần theo dõi."
---

> **Tên file**: .agents/workflows/vault-curator-anti20.md
> **Last update**: 13/07/2026 11:00 (GMT+7)
> **Vai trò**: Workflow dành cho Antigravity 2.0 — orchestrator gọi VaultCuratorAgent qua subagents.
> **Sử dụng khi**: User muốn chạy curation pipeline tự động trên Antigravity 2.0 (hỗ trợ define_subagent/invoke_subagent).
> **Output**: Vault đã chuẩn hóa + Summary report.
> **Tóm tắt logic**: Orchestrator đọc AGENT.md để biết routing → spawn subagent cho từng skill → SESSION_BREAK thì tự respawn → ALL_DONE thì chuyển skill → Báo user.

# Workflow: Vault Curation (Antigravity 2.0 – Sub-Agents)

> **LỆNH**: `/vault-curate --mode <mode> [--atoms <list>] [--output-dir <dir>]`
>
> ⚠️ **LUẬT KHÔNG HỎI LẠI (NO PROMPTING RULE)**:
> - Nếu User KHÔNG truyền tham số `--output-dir`, **TUYỆT ĐỐI KHÔNG ĐƯỢC HỎI LẠI**. Tự động lấy giá trị mặc định là: `vault/.curation_temp/`
>
> **Tham chiếu**: Toàn bộ routing logic, input/output specs, cleanup logic → đọc [AGENT.md](file:///.agents/agents/vault-curator/AGENT.md).

## Hướng dẫn thực thi

### 1. Xác định Skill Queue từ não bộ VaultCurator

Bạn (Orchestrator) hãy đọc phần **Kịch bản Routing Logic** trong file `.agents/agents/vault-curator/AGENT.md` để tự xác định danh sách các skill cần gọi cho `<MODE>` tương ứng. 

Ví dụ: Nếu trong AGENT.md ghi là `1. Gọi skill auto-tagger`, `2. Gọi skill atom-dedup`, thì bạn sẽ biết Skill Queue của mình là `[auto-tagger, atom-dedup]`.

### 2. Init + Tạo Pipeline Context

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

### 3. Skill Loop (Tạo Subagent qua Antigravity 2.0)

Với mỗi skill trong queue đã xác định ở Bước 1:

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

**3c. Parse response:**

| Stdout từ Subagent chứa | Orchestrator hành động |
|---|---|
| `ALL_DONE` | Đọc summary từ stdout. Nếu còn skill tiếp theo → thực hiện Bước 2b và 3a cho skill tiếp theo. Nếu hết → chuyển Bước 4. |
| `SESSION_BREAK` | Extract handoff prompt (nội dung giữa `---` và `---`) → `invoke_subagent` lại với prompt đó → quay lại 3c. |

### 4. Pipeline hoàn tất

Tất cả skills đã ALL_DONE:
1. Tổng hợp summary từ tất cả skills và báo cáo kết quả tổng hợp cho User.
2. Xóa atoms file nếu workflow truyền qua `--atoms-file` (VD: `pending_curation_atoms.txt`, `created_atoms.json`).
3. **Dọn rác thư mục tạm**: Hỏi ý kiến User xem có muốn xóa toàn bộ thư mục lưu các file xử lý `<OUTPUT_DIR>` không (vì chúng không còn giá trị sử dụng). Ví dụ: *"Tiến trình đã hoàn tất. Thư mục tạm `<OUTPUT_DIR>` đang chứa các file log và batch xử lý. Bạn có muốn tôi xóa sạch thư mục này không?"*.
4. Nếu User đồng ý, hãy dùng lệnh hệ thống (VD: `Remove-Item -Recurse -Force "<OUTPUT_DIR>"`) để dọn dẹp.

## Xử lý lỗi

| Tình huống | Hành động |
|---|---|
| Subagent crash/timeout | Orchestrator gọi `--status --output-dir` → biết batch pending → spawn subagent mới tiếp tục |
| Script lỗi (exit != 0) | Subagent báo orchestrator → DỪNG + BÁO user |
| Validation fail (submit reject) | Subagent tự retry sửa kết quả (max 3 lần). Fail → BÁO orchestrator |
