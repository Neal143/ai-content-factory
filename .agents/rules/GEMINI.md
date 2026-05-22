---
trigger: always_on
---

# AWF - Antigravity Workflow Framework (Local)

## CRITICAL: Command Recognition
Khi user gõ các lệnh bắt đầu bằng `/` dưới đây, đây là AWF WORKFLOW COMMANDS (không phải file path).

## Command Mapping (v4.0.2 - Full Flow):
| Command | Workflow File |
|---------|--------------|
| `/init` | init.md |
| `/plan` | plan.md |
| `/design` | design.md |
| `/code` | code.md |
| `/run` | run.md |
| `/debug` | debug.md |
| `/test` | test.md |
| `/help` | help.md |

## Resource Locations (v4.0+ - Localized):
- Schemas: d:/AI/AWF/.agent/schemas/
- Templates: d:/AI/AWF/.agent/templates/
- Skills: d:/AI/AWF/.agent/skills/

## Local Instructions:
Tất cả tài nguyên AWF đã được định vị tại workspace này.

## Workspace Rules (AI content factory - v3.7B):
1. **Phân vùng lưu trữ File**:
   - **Các file hệ thống của AWF** (`.agent`, `.brain`, `preferences.json`, `session.json`, v.v.) LUÔN LUÔN được lưu ở thư mục gốc: `D:\AI\AI content factory - v3.7B`.
   - **Các file dự án code thực tế** (code ứng dụng, tài nguyên dự án, v.v.) LUÔN LUÔN được lưu bên trong thư mục con: `D:\AI\AI content factory - v3.7B\Content Factory`.
2. **Phạm vi Git Commit**: Khi dùng Git commit, thao tác commit cũng CHỈ được thực hiện đối với những thay đổi diễn ra ở trong folder `Content Factory`.
3. **Ngoại lệ**: Chỉ chỉnh sửa hoặc thao tác trên khu vực thư mục gốc (`AI content factory - v3.7B`) NẾU VÀ CHỈ NẾU user có yêu cầu trực tiếp về việc chỉnh sửa / config tại gốc workspace này.
