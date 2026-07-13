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

> **LỆNH**: `/vault-curate --mode <mode> --atoms <list> --output-dir <dir>`
>
> **Tham chiếu**: Toàn bộ routing logic, input/output specs, cleanup logic → đọc [AGENT.md](file:///.agents/agents/vault-curator/AGENT.md).

## Hướng dẫn thực thi

### 1. Xác định Skill Queue

Từ `MODE` trong prompt, xác định skill queue:

| Mode | Skill Queue (theo thứ tự) |
|---|---|
| `full-pipeline` | tag → dedup → align |
| `tag-and-dedup` | tag → dedup |
| `tag-only` | tag |
| `dedup-incremental` | dedup |
| `dedup-full` | dedup |
| `align-only` | align |

Skill map (tên skill → SKILL.md path):
- `tag` → `.agents/skills/auto-tagger/SKILL.md`
- `dedup` → `.agents/skills/atom-dedup/SKILL.md`
- `align` → `.agents/skills/atom-linker/SKILL.md`

### 2. Init + Tạo Pipeline Context

**2a. Tạo pipeline_context.json:**
```python
write_to_file("<OUTPUT_DIR>/pipeline_context.json", {
  "mode": "<MODE>",
  "atoms_file": "<ATOMS_FILE>",
  "root_output_dir": "<OUTPUT_DIR>"
})
```

**2b. Init batches cho skill đầu tiên:**
```powershell
# Nếu có atoms file:
python .agents/scripts/prepare_curation_batches.py --init --skill <skill> --batch-size 10 --atoms-file "<ATOMS_FILE>" --output-dir "<OUTPUT_DIR>/<skill>"

# Nếu mode dedup-full (không cần atoms file):
python .agents/scripts/prepare_curation_batches.py --init --skill dedup --batch-size 10 --scope full --layer <insight|solution|evidence> --output-dir "<OUTPUT_DIR>/dedup"
```

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

    BỎ QUA Bước 1 trong SKILL.md (--init đã được orchestrator chạy). 
    Bắt đầu từ Bước 2: Thực thi vòng lặp get-next → xử lý → submit theo SKILL.md.
    Dừng khi stdout chứa "ALL_DONE" hoặc "SESSION_BREAK".
    Trả về nguyên văn stdout cuối cùng.
  """
)
```

**3c. Parse response:**

| Stdout chứa | Orchestrator hành động |
|---|---|
| `ALL_DONE` | Đọc summary từ stdout. Nếu còn skill tiếp theo → chạy `--init` cho skill tiếp theo → quay lại 3a. Nếu hết → chuyển Bước 4. |
| `SESSION_BREAK` | Extract handoff prompt (nội dung giữa `---` và `---`) → `invoke_subagent` lại với prompt đó → quay lại 3c. |

Chi tiết ALL_DONE cho skill tiếp theo:
```powershell
python .agents/scripts/prepare_curation_batches.py --init --skill <next_skill> --batch-size 10 --atoms-file "<ATOMS_FILE>" --output-dir "<OUTPUT_DIR>/<next_skill>"
```

> ⚠️ **QUAN TRỌNG — Tránh double-init**: SKILL.md mỗi skill đều có "Bước 1: Khởi tạo Batch (--init)". Nhưng trong Anti 2.0, orchestrator đã chạy `--init` trước khi spawn subagent. Vì vậy, invoke prompt (Section 3b) PHẢI ghi rõ:
> ```
> BỎ QUA Bước 1 trong SKILL.md (--init đã chạy). Bắt đầu từ Bước 2 (get-next loop).
> ```
> Nếu thiếu chỉ dẫn này → subagent đọc SKILL.md → chạy lại --init → xóa sạch batches đã tạo → mất dữ liệu.

### 4. Pipeline hoàn tất

Tất cả skills đã ALL_DONE:
1. Tổng hợp summary từ tất cả skills
2. Cleanup: Xóa atoms file nếu workflow truyền qua `--atoms-file` (VD: `pending_curation_atoms.txt`, `created_atoms.json`)
3. Báo user kết quả tổng hợp.

## Xử lý lỗi

| Tình huống | Hành động |
|---|---|
| Subagent crash/timeout | Orchestrator gọi `--status --output-dir` → biết batch pending → spawn subagent mới tiếp tục |
| Script lỗi (exit != 0) | Subagent báo orchestrator → DỪNG + BÁO user |
| Validation fail (submit reject) | Subagent tự retry sửa kết quả (max 3 lần). Fail → BÁO orchestrator |
