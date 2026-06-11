# Cẩm Nang Kiến Trúc & Quản Lý Subagents (AWF)

> **Tên file**: subagent_guidelines.md
> **Last update**: 11/06/2026 10:44 (GMT+7)
> **Vai trò**: Bách khoa toàn thư kỹ thuật — Bộ tiêu chuẩn thiết kế, vận hành và gỡ lỗi các Tác nhân con (Subagents) trong hệ thống Antigravity Workflow Framework (AWF).
> **Sử dụng khi nào?**: Tham chiếu trước khi lập trình Workflow mới, khởi tạo Agent mới, gỡ lỗi phân quyền, hoặc truy vết hành vi Subagent qua Log.
> **Output**: Kiến thức tiêu chuẩn hóa cho hệ thống AI Agentic.
> **Tóm tắt logic hoạt động**: Phân tích cú pháp toàn bộ API hệ thống (define, invoke, manage, send_message), sơ đồ phân quyền, vòng đời tác nhân, cơ chế kế thừa ngữ cảnh, cẩm nang phòng chống lỗi (Guardrails), giám sát Log và cung cấp các kịch bản mẫu (Boilerplate).

---

## Mục lục

1. [Tổng quan Kiến trúc](#1-tổng-quan-kiến-trúc)
2. [API 1: define_subagent — Đăng ký Blueprint](#2-api-1-define_subagent--đăng-ký-blueprint)
3. [API 2: invoke_subagent — Triệu hồi Tác nhân](#3-api-2-invoke_subagent--triệu-hồi-tác-nhân)
4. [API 3: manage_subagents — Quản lý Vòng đời](#4-api-3-manage_subagents--quản-lý-vòng-đời)
5. [API 4: send_message — Giao tiếp Liên tác nhân](#5-api-4-send_message--giao-tiếp-liên-tác-nhân)
6. [Subagent Dựng sẵn (Pre-built)](#6-subagent-dựng-sẵn-pre-built)
7. [Phân quyền Công cụ (Tool Permissions)](#7-phân-quyền-công-cụ-tool-permissions)
8. [Cơ chế Kế thừa Ngữ cảnh (Context Inheritance)](#8-cơ-chế-kế-thừa-ngữ-cảnh-context-inheritance)
9. [Cô lập Ngữ cảnh (Context Isolation)](#9-cô-lập-ngữ-cảnh-context-isolation)
10. [Vòng Đời Tác Nhân (Lifecycle)](#10-vòng-đời-tác-nhân-lifecycle)
11. [Thiết kế System Prompt hiệu quả](#11-thiết-kế-system-prompt-hiệu-quả)
12. [Giám sát & Gỡ lỗi qua Transcript Log](#12-giám-sát--gỡ-lỗi-qua-transcript-log)
13. [Best Practices & Chống Lỗi (Poka-Yoke)](#13-best-practices--chống-lỗi-poka-yoke)
14. [Boilerplate (JSON/Prompt Mẫu)](#14-boilerplate-jsonprompt-mẫu)

---

## 1. Tổng quan Kiến trúc

Hệ thống AWF giao tiếp theo mô hình **Phân cấp (Hierarchical Model)**.

```
┌─────────────────────────────────┐
│           USER                  │
│   (Giao tiếp trực tiếp)        │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│     ORCHESTRATOR AGENT          │
│   (Tác nhân Điều phối)         │
│   - Giao tiếp với User         │
│   - Toàn quyền quản lý         │
│   - Cấp quyền & điều hướng     │
└──┬──────────┬──────────┬────────┘
   │          │          │
   ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────┐
│Worker│  │Worker│  │Worker│
│  A   │  │  B   │  │  C   │
└──────┘  └──────┘  └──────┘
  (Subagents — chạy ngầm,
   không giao tiếp với User)
```

**Nguyên tắc cốt lõi:**
- Orchestrator là thực thể DUY NHẤT có quyền giao tiếp với User.
- Subagent chỉ giao tiếp với Orchestrator (hoặc với Subagent khác nếu biết `conversationId`).
- Mỗi Subagent có ngữ cảnh hội thoại (Conversation Context) hoàn toàn riêng biệt.

---

## 2. API 1: `define_subagent` — Đăng ký Blueprint

Công cụ này đăng ký một mẫu Tác nhân (Blueprint/Template) vào bộ nhớ hệ thống. Blueprint tồn tại trong suốt phiên hội thoại hiện tại và có thể được gọi nhiều lần bằng `invoke_subagent`.

### 2.1 Bảng Tham số Đầy đủ

| Tham số | Bắt buộc | Kiểu | Mô tả |
| --- | --- | --- | --- |
| `name` | **Có** | String | Tên định danh duy nhất. Dùng PascalCase, không khoảng trắng. VD: `FormatAgent`, `QAChecker`, `DataAuditor`. |
| `description` | **Có** | String | Mô tả ngắn gọn vai trò và điều kiện kích hoạt. Orchestrator đọc trường này để quyết định "khi nào gọi Agent này". |
| `system_prompt` | **Có** | String | "Não bộ" của tác nhân. Chứa toàn bộ danh tính, luật lệ, định dạng đầu ra, rào cản hành vi. Xem [Mục 11](#11-thiết-kế-system-prompt-hiệu-quả) để biết cách thiết kế. |
| `enable_write_tools` | Không | Boolean | `true`: Cấp quyền Tạo/Sửa/Xóa file (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) và chạy lệnh Terminal (`run_command`, `manage_task`). Mặc định: `false`. |
| `enable_mcp_tools` | Không | Boolean | `true`: Cấp quyền truy cập hệ thống máy chủ vệ tinh MCP (VD: Obsidian Vault qua `call_mcp_tool`, `list_resources`, `read_resource`). Mặc định: `false`. |
| `enable_subagent_tools` | Không | Boolean | `true`: Cấp quyền cho Subagent tự định nghĩa và triệu hồi Subagent cấp thấp hơn nữa (`define_subagent`, `invoke_subagent`, `manage_subagents`). Cẩn thận: có thể tạo vòng lặp vô hạn nếu không kiểm soát. Mặc định: `false`. |

### 2.2 Ví dụ Gọi API

```json
{
  "name": "DataAuditor",
  "description": "Chuyên gia rà soát logic dữ liệu. Gọi khi cần xác thực tính nguyên vẹn của luồng đầu vào.",
  "system_prompt": "Bạn là DataAuditor...",
  "enable_write_tools": false,
  "enable_mcp_tools": false,
  "enable_subagent_tools": false
}
```

### 2.3 Lưu ý Quan trọng
- `define_subagent` chỉ **đăng ký** Blueprint, KHÔNG tạo ra một instance (phiên bản) Subagent nào.
- Có thể gọi `invoke_subagent` nhiều lần với cùng `TypeName` — mỗi lần sẽ sinh ra một instance độc lập với `conversationId` riêng.
- Blueprint chỉ tồn tại trong phạm vi phiên hội thoại hiện tại, không lưu trữ vĩnh viễn.

---

## 3. API 2: `invoke_subagent` — Triệu hồi Tác nhân

Công cụ này tạo ra một instance thực thi từ Blueprint đã đăng ký và giao nhiệm vụ cho nó.

### 3.1 Bảng Tham số Đầy đủ

| Tham số | Bắt buộc | Kiểu | Mô tả |
| --- | --- | --- | --- |
| `Subagents` | **Có** | Array | Mảng JSON chứa danh sách các Subagent cần triệu hồi. Có thể gọi nhiều Subagent cùng lúc trong một lần gọi API. |
| `Subagents[].TypeName` | **Có** | String | Tên Blueprint đã đăng ký bằng `define_subagent`, hoặc tên Subagent dựng sẵn (`research`, `self`). |
| `Subagents[].Role` | **Có** | String | Mô tả vai trò 2-5 từ, tương tự "chức danh công việc". VD: `"Format Agent"`, `"QA Checker"`, `"Data Auditor"`. |
| `Subagents[].Prompt` | **Có** | String | Nhiệm vụ cụ thể, rõ ràng, hành động được (actionable). Đây là chỉ thị TRỰC TIẾP cho instance này, bổ sung cho `system_prompt` đã cấu hình ở Blueprint. |
| `Subagents[].Workspace` | Không | String | Chế độ không gian làm việc. Xem chi tiết ở mục 3.2 bên dưới. Mặc định: `"inherit"`. |

### 3.2 Chế độ Workspace (Không gian Làm việc)

Tham số `Workspace` xác định môi trường file hệ thống mà Subagent thao tác. Có 3 chế độ:

| Chế độ | Hành vi | Khi nào dùng |
| --- | --- | --- |
| `inherit` | Subagent dùng chung workspace với Orchestrator. Mọi thay đổi file đều ảnh hưởng trực tiếp đến hệ thống gốc. | Mặc định. Dùng khi Subagent cần đọc/ghi file vào cùng codebase. Phù hợp với phần lớn các tác vụ pipeline. |
| `branch` | Tạo một bản sao (clone) workspace hoàn toàn tách biệt. Thay đổi file trong branch KHÔNG ảnh hưởng đến workspace gốc. | Dùng khi cần thử nghiệm (experiment) hoặc tạo bản nháp an toàn mà không rủi ro phá vỡ dữ liệu gốc. |
| `share` | Tạo workspace chia sẻ cùng thư mục gốc (tương tự `git worktree`). Cho phép nhánh (branch) độc lập nhưng không nhân đôi dung lượng. | Dùng khi cần làm việc song song trên cùng repository nhưng ở các nhánh khác nhau. |

### 3.3 Giá trị Trả về

Khi gọi thành công, API trả về:

```json
{
  "conversationId": "fe8105a7-8561-4e02-a02b-048a7193b59b",
  "logAbsoluteUri": "file:///C:/Users/Admin/.gemini/antigravity/brain/fe8105a7-.../logs/transcript.jsonl",
  "workspaceUris": ["file:///d:/AI/AI%20content%20factory%20..."]
}
```

- `conversationId`: Mã định danh duy nhất của instance. Dùng để giao tiếp (`send_message`) và quản lý (`manage_subagents`).
- `logAbsoluteUri`: Đường dẫn vật lý đến file Log. Xem [Mục 12](#12-giám-sát--gỡ-lỗi-qua-transcript-log).

### 3.4 Ví dụ Gọi Nhiều Subagent Song Song

```json
{
  "Subagents": [
    {
      "TypeName": "IdeaCurator",
      "Role": "Idea Curator",
      "Prompt": "Đọc payload.md tại run folder X. Xuất kết quả ra 01-idea-brief.md."
    },
    {
      "TypeName": "InsightAgent",
      "Role": "Insight Agent",
      "Prompt": "Đọc payload.md tại run folder X. Xuất kết quả ra 02-research-brief.md."
    }
  ]
}
```

Hai Subagent trên sẽ chạy **đồng thời** (concurrent), mỗi Subagent có `conversationId` riêng.

---

## 4. API 3: `manage_subagents` — Quản lý Vòng đời

Công cụ quản lý trạng thái của các Subagent đang hoạt động.

### 4.1 Bảng Hành động (Actions)

| Hành động | Tham số bổ sung | Mô tả |
| --- | --- | --- |
| `list` | Không | Liệt kê tất cả Subagent đang hoạt động kèm `conversationId`. |
| `kill` | `ConversationIds` (Array of String) | Tiêu diệt các Subagent cụ thể và toàn bộ Subagent con của chúng (descendants). Workspace kiểu `branch` sẽ bị xóa. Log và Artifact được giữ lại. |
| `kill_all` | Không | Tiêu diệt toàn bộ Subagent đang hoạt động và tất cả descendants. |

### 4.2 Ví dụ

```json
// Liệt kê tất cả Subagent
{ "Action": "list" }

// Tiêu diệt 2 Subagent cụ thể
{
  "Action": "kill",
  "ConversationIds": [
    "fe8105a7-8561-4e02-a02b-048a7193b59b",
    "d7163ddd-8cde-4589-951c-eeef59eff9a5"
  ]
}

// Tiêu diệt toàn bộ
{ "Action": "kill_all" }
```

### 4.3 Lưu ý
- Sau khi `kill`, Log Transcript của Subagent vẫn tồn tại vĩnh viễn tại `logAbsoluteUri` — có thể đọc lại bất cứ lúc nào.
- Workspace `branch` bị xóa vật lý, workspace `inherit` và `share` không bị ảnh hưởng.

---

## 5. API 4: `send_message` — Giao tiếp Liên tác nhân

Công cụ gửi tin nhắn giữa các Tác nhân. **TUYỆT ĐỐI CẤM** dùng để giao tiếp với User.

### 5.1 Bảng Tham số

| Tham số | Bắt buộc | Kiểu | Mô tả |
| --- | --- | --- | --- |
| `Recipient` | **Có** | String | `conversationId` của Subagent đích. |
| `Message` | **Có** | String | Nội dung tin nhắn. |

### 5.2 Cơ chế Phản hồi Tự động (Reactive Wakeup)

Hệ thống AWF triển khai cơ chế **Reactive Wakeup** — tức là:
- Orchestrator KHÔNG cần liên tục kiểm tra (polling) xem Subagent đã làm xong chưa.
- Khi Subagent hoàn thành và gửi `send_message`, hệ thống tự động đánh thức (resume) Orchestrator để xử lý tin nhắn.
- Điều này đúng cho cả: tin nhắn từ Subagent, kết quả từ Background Task, và tin nhắn từ User Queue.

**Hệ quả thực tiễn:** Sau khi `invoke_subagent`, Orchestrator có thể tiếp tục làm việc khác hoặc dừng gọi công cụ. Không bao giờ cần viết vòng lặp chờ.

### 5.3 Các Trường hợp Sử dụng

| Trường hợp | Hành vi |
| --- | --- |
| Kiểm tra tiến độ Subagent | Gửi tin nhắn hỏi trạng thái. |
| Gửi chỉ thị bổ sung cho Subagent đang chạy | Gửi tin nhắn chứa nhiệm vụ mới. |
| Giao nhiệm vụ mới cho Subagent đã idle | Gửi tin nhắn chứa chỉ thị mới — Subagent sẽ tự kích hoạt lại. |

---

## 6. Subagent Dựng sẵn (Pre-built)

Hệ thống cung cấp 2 loại Subagent mẫu có thể dùng ngay mà KHÔNG cần gọi `define_subagent`:

| TypeName | Vai trò | Quyền hạn | Khi nào dùng |
| --- | --- | --- | --- |
| `research` | Nghiên cứu viên chỉ-đọc (Read-only Researcher) | Chỉ có công cụ đọc: duyệt codebase, tìm kiếm web, đọc file. Không có quyền ghi. | Khi cần khảo sát codebase hoặc tài liệu mà không muốn rủi ro thay đổi file. Chạy ngầm để không chiếm ngữ cảnh Orchestrator. |
| `self` | Bản sao Orchestrator | Kế thừa 100% cấu hình, công cụ, system prompt và model của Agent cha. | Khi cần chạy một tác vụ với đầy đủ năng lực nhưng trong ngữ cảnh hội thoại (Conversation Context) riêng biệt. |

### Ví dụ Gọi Subagent Dựng sẵn

```json
{
  "Subagents": [
    {
      "TypeName": "research",
      "Role": "Codebase Researcher",
      "Prompt": "Tìm tất cả các file chứa hàm validate trong thư mục .agents/skills/ và liệt kê chức năng của từng file."
    }
  ]
}
```

---

## 7. Phân quyền Công cụ (Tool Permissions)

### 7.1 Công cụ Mặc định (Cấp cho MỌI Subagent)

Bất chấp các cờ (flags), mọi Subagent luôn được trang bị:

| Nhóm | Công cụ |
| --- | --- |
| Khảo sát File | `view_file`, `list_dir`, `grep_search` |
| Tìm kiếm | `search_web`, `read_url_content` |
| Giao tiếp | `send_message` |
| Lịch trình | `schedule` |

### 7.2 Công cụ Mở rộng (Theo cờ)

| Cờ (Flag) | Công cụ được mở khóa |
| --- | --- |
| `enable_write_tools = true` | `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command`, `manage_task` |
| `enable_mcp_tools = true` | `call_mcp_tool`, `list_resources`, `read_resource` |
| `enable_subagent_tools = true` | `define_subagent`, `invoke_subagent`, `manage_subagents` |

### 7.3 Công cụ TUYỆT ĐỐI không khả dụng cho Subagent

Các công cụ sau đây chỉ dành riêng cho Orchestrator vì chúng yêu cầu tương tác trực tiếp với User qua giao diện:

| Công cụ | Lý do loại trừ |
| --- | --- |
| `ask_question` | Hiển thị bảng câu hỏi trắc nghiệm cho User — Subagent không có quyền giao tiếp trực tiếp. |
| `ask_permission` | Yêu cầu User cấp quyền hệ thống — chỉ Orchestrator mới được phép. |
| `generate_image` | Tạo hình ảnh và lưu Artifact — yêu cầu ngữ cảnh UI của phiên chính. |

### 7.4 Cờ `hidden` trong Cấu hình Agent

Khi một Agent được đánh dấu `"hidden": true` trong file cấu hình JSON:
- Agent đó hoạt động hoàn toàn bình thường về mặt kỹ thuật.
- Sự khác biệt duy nhất: Agent sẽ không xuất hiện trên giao diện người dùng (UI Agent List), giữ cho giao diện không bị quá tải bởi các Worker Agent chạy ngầm.
- Cờ này thuần túy là cờ giao diện (UI Flag), không ảnh hưởng đến phân quyền hay hành vi thực thi.

---

## 8. Cơ chế Kế thừa Ngữ cảnh (Context Inheritance)

Khi Orchestrator khởi tạo Subagent, hệ thống tự động "tiêm" (inject) các khối kiến thức chung vào ngữ cảnh của Subagent thông qua cấu hình `systemPromptConfig.includeSections`.

### 8.1 Các Section Khả dụng

| Section | Nội dung được tiêm |
| --- | --- |
| `user_information` | Hệ điều hành, đường dẫn workspace, App Data Directory. |
| `user_rules` | Toàn bộ quy tắc bất khả xâm phạm do User thiết lập (bao gồm cấm tự thực thi, quy tắc encoding, v.v.). |
| `skills` | Danh sách kỹ năng (Skills) hiện có trong hệ thống để Subagent biết cần đọc `SKILL.md` nào. |
| `mcp_servers` | Cấu hình kết nối đến các máy chủ MCP (Obsidian, v.v.). |
| `artifacts` | Thông tin thư mục Artifact của phiên hội thoại hiện tại. |
| `messaging` | Hướng dẫn giao thức nhắn tin (Reactive Wakeup, cách nhận/gửi tin). |
| `subagent_reminder` | Nhắc nhở về cách giao tiếp với các Subagent khác. |

### 8.2 Ý nghĩa Thực tiễn

Nhờ cơ chế này, Subagent tự động "biết" về:
- Quy tắc của User mà không cần Orchestrator sao chép thủ công vào `system_prompt`.
- Cấu trúc thư mục workspace mà không cần hardcode đường dẫn.
- Danh sách Skills hiện có để tự tra cứu tài liệu khi cần.

### 8.3 Cảnh báo

Việc kế thừa ngữ cảnh KHÔNG có nghĩa là Subagent biết mọi thứ Orchestrator biết. Subagent KHÔNG được kế thừa:
- Lịch sử hội thoại (Conversation History) của Orchestrator.
- Nội dung file đã đọc trước đó bởi Orchestrator.
- Các biến ngữ cảnh tạm thời (ví dụ: mã execution_key đã trích xuất từ Log).

---

## 9. Cô lập Ngữ cảnh (Context Isolation)

Mỗi Subagent chạy trong một **Conversation Context hoàn toàn riêng biệt**. Điều này dẫn đến các hệ quả quan trọng:

### 9.1 File Changes Không Hiển thị ở Orchestrator

Khi Subagent tạo hoặc sửa file (bằng `write_to_file`, `replace_file_content`), sự thay đổi này:
- **CÓ** xảy ra trên hệ thống file vật lý (file thực sự được tạo/sửa trên ổ đĩa).
- **KHÔNG** hiển thị trong danh sách "Files Changed" trên giao diện UI của phiên Orchestrator.
- **CHỈ** được ghi nhận trong Transcript Log riêng của Subagent đó.

Lý do: Hệ thống UI chỉ theo dõi các thao tác file được thực hiện trực tiếp bởi Tác nhân trong ngữ cảnh hội thoại hiện tại.

### 9.2 Terminal Side-Effects Không Được Theo dõi

File được tạo gián tiếp qua lệnh Terminal (`run_command` → script PowerShell tạo file) cũng không được hệ thống UI bắt lại, dù file tồn tại vật lý trên ổ đĩa. Hệ thống coi đây là "tác dụng phụ" (Side-effect) của hệ điều hành.

### 9.3 Hệ quả Thực tiễn

- Để xác nhận Subagent đã tạo file đúng, Orchestrator nên chủ động dùng `view_file` hoặc `list_dir` để kiểm tra sau khi nhận báo cáo.
- Không nên dựa vào danh sách "Files Changed" trên UI để đánh giá khối lượng công việc của Subagent.

---

## 10. Vòng Đời Tác Nhân (Lifecycle)

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────────┐
│  DEFINE  │────>│  INVOKE  │────>│  EXECUTING   │────>│ CALLBACK │────>│  IDLE / KILL │
│(Blueprint)│     │(Instance)│     │ (Background) │     │(send_msg)│     │              │
└──────────┘     └──────────┘     └──────────────┘     └──────────┘     └──────────────┘
                       │                                     │                │
                       │          ┌──────────────┐           │                │
                       └────>     │  send_message│ <─────────┘                │
                                  │  (Bổ sung    │                            │
                                  │  chỉ thị)    │──> Tiếp tục thực thi ─────┘
                                  └──────────────┘
```

### Giải thích từng giai đoạn:

| Giai đoạn | Mô tả | API |
| --- | --- | --- |
| **Define** | Đăng ký Blueprint. Chưa tạo instance nào. | `define_subagent` |
| **Invoke** | Tạo instance thực thi, giao nhiệm vụ. Hệ thống sinh `conversationId`. | `invoke_subagent` |
| **Executing** | Subagent chạy ngầm, xử lý tác vụ. Orchestrator tự do làm việc khác. | — |
| **Callback** | Subagent gửi kết quả về. Hệ thống tự đánh thức Orchestrator (Reactive Wakeup). | `send_message` |
| **Idle** | Subagent đã xong nhưng vẫn tồn tại. Có thể gửi nhiệm vụ mới bằng `send_message`. | `send_message` |
| **Kill** | Tiêu diệt instance, giải phóng tài nguyên. Log được giữ lại. | `manage_subagents` |

### Các trường hợp đặc biệt:

- **Subagent bị lỗi (Error):** Subagent sẽ gửi tin nhắn báo lỗi về Orchestrator. Orchestrator cần đọc tin và quyết định: sửa lỗi và gửi lại chỉ thị, hoặc `kill` và tạo instance mới.
- **Subagent bị treo (Hung):** Dùng `manage_subagents` → `list` để kiểm tra trạng thái. Nếu cần, `kill` rồi `invoke` lại.
- **Server Restart:** Tất cả Subagent bị dừng tự động. Orchestrator nhận thông báo hệ thống và phải `invoke` lại nếu cần tiếp tục.

---

## 11. Thiết kế System Prompt hiệu quả

`system_prompt` là tham số có sức ảnh hưởng lớn nhất đến hành vi của Subagent. Dưới đây là cấu trúc chuẩn:

### 11.1 Cấu trúc 4 Khối

```
┌─────────────────────────────────────────┐
│ KHỐI 1: DANH TÍNH (Identity)            │
│ "Bạn là [Tên Agent], chuyên gia về..." │
├─────────────────────────────────────────┤
│ KHỐI 2: CHỈ THỊ CỐT LÕI (Core Rules)  │
│ Liệt kê N bước hành động tuần tự.      │
│ Chỉ ra file nào phải đọc, file nào     │
│ phải ghi, script nào phải chạy.        │
├─────────────────────────────────────────┤
│ KHỐI 3: RÀO CẢN CẤM (Guardrails)      │
│ CẤM: Tự sinh mã xác thực.             │
│ CẤM: Sửa nội dung bài viết.           │
│ CẤM: Giao tiếp trực tiếp với User.    │
├─────────────────────────────────────────┤
│ KHỐI 4: ĐỊNH DẠNG ĐẦU RA (Output Fmt) │
│ Khi hoàn tất, gửi send_message với:    │
│ - Trạng thái: PASS/FAIL                │
│ - Tóm tắt kết quả                      │
│ - Đường dẫn file đã tạo               │
└─────────────────────────────────────────┘
```

### 11.2 Ví dụ System Prompt Chuẩn

```
Bạn là **FormatAgent**, người kiểm soát khâu hoàn thiện cuối cùng.

### Chỉ thị cốt lõi:
1. BẮT BUỘC đọc file `.agents/skills/format-agent/SKILL.md` và làm theo từng bước.
2. Tuyệt đối bảo toàn nội dung bài viết (Data Integrity) — KHÔNG sửa bất kỳ từ ngữ nào.
3. Làm sạch triệt để các markers cấu trúc kỹ thuật.
4. Chạy script `validate-format.ps1` để kiểm định chốt cuối.
5. Cập nhật `production-log.md` và `hook-history.md`.

### RÀO CẢN CẤM:
- CẤM tự sinh hoặc đoán bất kỳ mã xác thực (execution_key, bundle_key) nào.
- CẤM giao tiếp trực tiếp với User. Mọi báo cáo gửi qua send_message cho Orchestrator.

### Định dạng báo cáo:
Khi hoàn tất, gửi send_message với nội dung:
- Trạng thái: [PASS] hoặc [FAIL]
- File đã tạo: [Danh sách đường dẫn]
- Ghi chú: [Nếu có vấn đề cần Orchestrator xử lý]
```

### 11.3 Nguyên tắc Vàng khi Viết System Prompt

| Nguyên tắc | Giải thích |
| --- | --- |
| Chỉ thị phải HÀNH ĐỘNG ĐƯỢC | Viết "Đọc file X" thay vì "Hãy tham khảo file X nếu cần". |
| Liệt kê tuần tự bước 1-2-3 | LLM tuân thủ danh sách đánh số tốt hơn văn xuôi tự do. |
| Đặt Rào Cản CẤM riêng biệt | Tách hẳn thành khối riêng, dùng chữ in hoa "CẤM", "TUYỆT ĐỐI KHÔNG". |
| Quy định rõ định dạng đầu ra | Subagent phải biết chính xác nó cần gửi lại cái gì, ở đâu, theo cấu trúc nào. |
| Không nhồi nhét quá nhiều | Một Agent, một trách nhiệm. Nếu Prompt quá 800 từ, cân nhắc tách Agent. |

---

## 12. Giám sát & Gỡ lỗi qua Transcript Log

Mỗi Subagent sinh ra một file Log riêng tại đường dẫn `logAbsoluteUri` (trả về khi `invoke_subagent`).

### 12.1 Vị trí File Log

```
C:\Users\Admin\.gemini\antigravity\brain\{conversationId}\.system_generated\logs\transcript.jsonl
```

### 12.2 Định dạng File

File sử dụng định dạng JSON Lines (JSONL) — mỗi dòng là một JSON Object đại diện cho một bước (step) trong hội thoại.

Các trường quan trọng:

| Trường | Ý nghĩa |
| --- | --- |
| `step_index` | Thứ tự bước trong luồng thực thi. |
| `source` | Nguồn gốc: `USER_EXPLICIT`, `MODEL`, `SYSTEM`. |
| `type` | Loại bước: `USER_INPUT`, `PLANNER_RESPONSE`, `VIEW_FILE`, `RUN_COMMAND`, v.v. |
| `status` | Trạng thái: `DONE`, `ERROR`. |
| `content` | Nội dung văn bản (tin nhắn, phản hồi, kết quả). |
| `tool_calls` | Mảng các lời gọi công cụ kèm tham số. |

### 12.3 Các Lệnh Gỡ lỗi Thường dùng

```powershell
# Xem 10 bước đầu tiên của Subagent
Get-Content "C:\Users\Admin\.gemini\antigravity\brain\{conversationId}\.system_generated\logs\transcript.jsonl" | Select-Object -First 10

# Tìm tất cả lỗi
Select-String -Path "transcript.jsonl" -Pattern '"status":"ERROR"'

# Tìm tất cả lời gọi write_to_file
Select-String -Path "transcript.jsonl" -Pattern 'write_to_file'

# Tìm tất cả tin nhắn send_message
Select-String -Path "transcript.jsonl" -Pattern 'send_message'
```

### 12.4 Khi nào cần đọc Log?

| Tình huống | Hành động |
| --- | --- |
| Subagent báo PASS nhưng kết quả sai | Đọc Log để xem nó thực sự đã đọc/ghi file nào. |
| Subagent bị treo không phản hồi | Đọc Log để xem nó dừng ở bước nào, có lỗi gì. |
| Cần kiểm tra Subagent có tự sinh dữ liệu giả không | Tìm trong Log xem nó có gọi `view_file` đọc file nguồn trước khi ghi không. |
| Cần truy vết lỗi execution_key | Tìm trong Log xem mã khóa được lấy từ đâu (file vật lý hay tự nội suy). |

---

## 13. Best Practices & Chống Lỗi (Poka-Yoke)

### Nguyên tắc 1: Zero-Hallucination Prompting (Chống ảo giác dữ liệu)

**Case study:** Orchestrator tự đoán mã `execution_key` và nhồi vào Prompt khởi tạo Subagent. Subagent ghi đè mã sai vào file, khiến hệ thống Sentinel phát hiện Bypass và đánh sập pipeline.

**Quy tắc bất khả xâm phạm:**
- CẤM Orchestrator tự sinh/đoán/nội suy bất kỳ chuỗi xác thực nào (Hash, Key, UUID) rồi truyền cho Subagent.
- Mọi dữ liệu xác thực phải được Subagent tự đọc từ file/payload gốc, hoặc do script hệ thống sinh ra tự động.
- Prompt khởi tạo chỉ mang tính điều phối luồng: *"Đọc file X để lấy mã khóa"* — KHÔNG BAO GIỜ là *"Mã khóa là ABC123, hãy ghi vào file Y"*.

### Nguyên tắc 2: Single Responsibility Principle (Đơn Trách Nhiệm)

- Mỗi Subagent giải quyết đúng MỘT tác vụ.
- Nếu cần nghiên cứu VÀ viết bài → Tạo 2 Agent riêng biệt (`Researcher` + `Writer`), KHÔNG tạo 1 `ResearchWriter`.
- Lý do: Agent đơn trách nhiệm dễ gỡ lỗi, dễ thay thế, dễ tái sử dụng.

### Nguyên tắc 3: Principle of Least Privilege (Cấp quyền Tối thiểu)

- Chỉ bật `enable_write_tools = true` cho Agent thực sự cần ghi file.
- Agent chỉ cần phân tích và báo cáo qua Message? → Giữ `false`.
- Agent cần đọc Obsidian Vault? → Bật `enable_mcp_tools`. Không cần? → Giữ `false`.

### Nguyên tắc 4: Explicit Over Implicit (Tường minh hơn Ngầm hiểu)

- Prompt khởi tạo phải chỉ rõ đường dẫn file đầu vào, đường dẫn file đầu ra, tên script cần chạy.
- KHÔNG viết: *"Hãy xử lý dữ liệu"*.
- NÊN viết: *"Đọc file `vault/.content-pipeline/runs/YYYY-MM-DD_HHMMSS_slug/payload.md`. Xuất kết quả ra `01-idea-brief.md` trong cùng thư mục. Chạy script `validate-idea.ps1` để kiểm định."*

### Nguyên tắc 5: Fail-Fast Communication (Báo lỗi sớm)

- System Prompt nên yêu cầu Subagent: *"Nếu gặp bất kỳ lỗi nào (file không tồn tại, script FAIL), DỪNG NGAY và gửi send_message báo cáo lỗi cho Orchestrator. Tuyệt đối không tự sửa chữa hoặc bỏ qua."*
- Điều này giúp Orchestrator phát hiện sự cố sớm thay vì nhận một kết quả sai hoàn chỉnh.

---

## 14. Boilerplate (JSON/Prompt Mẫu)

### 14.1 Mẫu Define — Agent Chỉ-Đọc (Read-Only Auditor)

```json
{
  "name": "DataAuditor",
  "description": "Rà soát và đối chiếu dữ liệu. Gọi khi cần xác thực tính nguyên vẹn của file mà không can thiệp vào dữ liệu gốc.",
  "system_prompt": "Bạn là DataAuditor.\n\n### Chỉ thị:\n1. Đọc file được chỉ định trong Prompt khởi tạo.\n2. Đối chiếu nội dung theo tiêu chí trong SKILL.md.\n3. Gửi send_message báo cáo: [PASS] hoặc [FAIL] kèm chi tiết.\n\n### CẤM:\n- KHÔNG tự sinh dữ liệu.\n- KHÔNG sửa file.\n- KHÔNG giao tiếp với User.",
  "enable_write_tools": false,
  "enable_mcp_tools": false,
  "enable_subagent_tools": false
}
```

### 14.2 Mẫu Define — Agent Ghi File (Writer)

```json
{
  "name": "ContentWriter",
  "description": "Tạo nội dung và ghi file đầu ra. Gọi khi cần sinh ra file mới dựa trên dữ liệu đầu vào.",
  "system_prompt": "Bạn là ContentWriter.\n\n### Chỉ thị:\n1. Đọc file đầu vào từ đường dẫn trong Prompt.\n2. Đọc SKILL.md để nắm quy tắc viết.\n3. Tạo file đầu ra bằng write_to_file.\n4. Chạy script validate bằng run_command.\n5. Gửi send_message báo cáo kết quả.\n\n### CẤM:\n- KHÔNG tự sinh mã xác thực. Đọc từ file gốc.\n- KHÔNG giao tiếp với User.",
  "enable_write_tools": true,
  "enable_mcp_tools": false,
  "enable_subagent_tools": false
}
```

### 14.3 Mẫu Invoke — Prompt Chống Ảo giác

```json
{
  "Subagents": [
    {
      "TypeName": "ContentWriter",
      "Role": "Content Writer",
      "Prompt": "Đọc payload tại `vault/.content-pipeline/runs/2026-06-10_162722_slug/.temp/payload.md`. Xuất kết quả ra `05-draft.md` trong cùng thư mục. Đọc kỹ `.agents/skills/voice-writer/SKILL.md`. Chạy script `validate-draft.ps1`. Mọi mã xác thực (execution_key, bundle_key) phải được lấy từ file hệ thống — TUYỆT ĐỐI KHÔNG tự sinh."
    }
  ]
}
```

### 14.4 Mẫu Invoke — Gọi Song Song

```json
{
  "Subagents": [
    {
      "TypeName": "DataAuditor",
      "Role": "Input Auditor",
      "Prompt": "Kiểm tra file 01-idea-brief.md tại run folder X."
    },
    {
      "TypeName": "DataAuditor",
      "Role": "Output Auditor",
      "Prompt": "Kiểm tra file 02-research-brief.md tại run folder X."
    }
  ]
}
```

Hai instance cùng TypeName, chạy đồng thời, mỗi instance có `conversationId` riêng.

---

> **Ghi chú cuối:** Tài liệu này là tham chiếu sống (Living Document). Cập nhật mỗi khi hệ thống có thay đổi về API, phân quyền, hoặc phát sinh case-study mới về lỗi vận hành.
