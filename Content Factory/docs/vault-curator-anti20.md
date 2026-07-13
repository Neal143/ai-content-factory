---
description: "Workflow Antigravity 2.0: Gọi VaultCuratorAgent qua subagents, user không cần theo dõi."
---

> **Tên file**: docs/vault-curator-anti20.md
> **Last update**: 13/07/2026 11:00 (GMT+7)
> **Vai trò**: Workflow dành cho Antigravity 2.0 — orchestrator gọi VaultCuratorAgent qua subagents.
> **Sử dụng khi**: User muốn chạy curation pipeline tự động trên Antigravity 2.0 (hỗ trợ define_subagent/invoke_subagent).
> **Output**: Vault đã chuẩn hóa + Summary report.
> **Tóm tắt logic**: Orchestrator đọc AGENT.md để biết routing → spawn subagent cho từng skill → SESSION_BREAK thì tự respawn → ALL_DONE thì chuyển skill → Báo user.

# Workflow: Vault Curation (Antigravity 2.0 – Sub-Agents)

> **LỆNH**: `/vault-curate --mode <mode> --atoms <list> --output-dir <dir>`
>
> **Tham chiếu**: Toàn bộ routing logic, input/output specs, cleanup logic → đọc [AGENT.md](file:///.agents/agents/vault-curator/AGENT.md).

## Hướng dẫn thực thi

### 1. Đọc AGENT.md + Xác định Skill Queue

Đọc `.agents/agents/vault-curator/AGENT.md` Section 2 (Routing Modes) và Section 5 (Routing Logic).
Từ `MODE` user truyền vào → xác định danh sách skills cần chạy theo thứ tự.

### 2. Init + Tạo Pipeline Context

Thực hiện theo AGENT.md Section 5: tạo `pipeline_context.json`, sau đó init batches cho skill đầu tiên.

### 3. Skill Loop (Subagent)

Với mỗi skill trong queue:

**3a. Define subagent:**
```
Đọc AGENT.md + SKILL.md tương ứng (auto-tagger | atom-dedup | atom-linker).

define_subagent(
  name: "VaultCurator",
  system_prompt: nội dung AGENT.md + SKILL.md,
  enable_write_tools: true
)
```

**3b. Invoke subagent:**
```
invoke_subagent(
  TypeName: "VaultCurator",
  Workspace: ".",
  Prompt: """
    Skill: <skill_name>
    Output dir: <OUTPUT_DIR>/<skill>

    Thực thi vòng lặp get-next → xử lý → submit theo SKILL.md.
    Dừng khi stdout chứa "ALL_DONE" hoặc "SESSION_BREAK".
    Trả về nguyên văn stdout cuối cùng.
  """
)
```

**3c. Parse response:**

| Stdout chứa | Orchestrator hành động |
|---|---|
| `ALL_DONE` | Lưu summary. Init batches cho skill tiếp theo → quay lại 3a. |
| `SESSION_BREAK` | Extract handoff prompt (nội dung giữa `---` và `---`) → `invoke_subagent` lại với prompt đó → quay lại 3c. |

### 4. Pipeline hoàn tất

Tất cả skills đã ALL_DONE → Tổng hợp summary → Cleanup (AGENT.md Section 6) → Báo user.

## Xử lý lỗi

| Tình huống | Hành động |
|---|---|
| Subagent crash/timeout | Orchestrator gọi `--status --output-dir` → biết batch pending → spawn subagent mới tiếp tục |
| Script lỗi (exit != 0) | Subagent báo orchestrator → DỪNG + BÁO user |
| Validation fail (submit reject) | Subagent tự retry sửa kết quả (max 3 lần). Fail → BÁO orchestrator |
