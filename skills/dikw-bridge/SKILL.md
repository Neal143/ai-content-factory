---
name: SKILL.md (DIKW Bridge)
last_update: 27/05/2026 00:45 (GMT+7)
role: Skill đóng vai trò cầu nối, gọi tool Get-DIKWCombo để tìm nguyên liệu liên quan đến topic trong Vault và xếp thứ hạng theo mô hình DIKW.
usage: Khi workflow /content-post kích hoạt agent DIKW Bridge để thu thập và sắp xếp combo nguyên liệu cho bài viết.
output: Combo nguyên liệu tối ưu (Anchor Insight, Solution/Concept, Stories, Quotes/Data-Points) được ghi vào Blackboard và lưu trữ tại 00.5-dikw-combo.md.
logic: Phân giải thông tin Blackboard, gọi Tool Get-DIKWCombo.ps1 để thực hiện truy vấn và xếp hạng tối ưu theo DAG in-memory O(1), định dạng payload chuẩn hóa và kích hoạt script đóng gói vật lý bundle-atoms.ps1.
---

# DIKW Bridge Skill

## Hướng dẫn hoạt động

### Bước 1: Tiếp nhận Context & Gọi Combo Engine (Get-DIKWCombo.ps1)
- **Tiếp nhận tham số**: Đọc các cấu hình từ Blackboard (`00-blackboard.yaml`) bao gồm:
  - `mapped_topics` (danh sách topic IDs cần truy vấn)
  - `Target_Audience` (Audience ID hoặc mảng các Audience IDs)
  - `Persona_Path` (đường dẫn đến cấu hình Persona hiện tại)
  - `Target_Source_IDs` (mảng các nguồn dữ liệu cụ thể cần lọc, ví dụ: `["good-inside"]`, nếu có)
- **Phân giải thông tin**:
  - Trích xuất tên người dùng `[User]` từ trường `Persona_Path` (ví dụ: `Persona_Path: personas/Neal` → `[User]` = `Neal`).
- **Thực thi Tool Get-DIKWCombo**: Chạy lệnh PowerShell tích hợp dưới đây để thực hiện tính toán in-memory O(1), tự động áp dụng các màng lọc Smart Global Pre-Filter, bộ lọc đa điều kiện, validate đồ thị DAG liên kết và thuật toán chọn combo tối ưu:
  ```powershell
  powershell -ExecutionPolicy Bypass -File ".agents/skills/dikw-bridge/scripts/Get-DIKWCombo.ps1" -Topics "[mapped_topics]" -Audience "[Target_Audience]" -PersonaUser "[User]" [-TargetSourceIds "[Target_Source_IDs]"]
  ```
  *(Truyền danh sách các topic hoặc audience dưới dạng chuỗi phân tách bằng dấu phẩy nếu có nhiều phần tử. Chỉ truyền `-TargetSourceIds` nếu `Target_Source_IDs` được định nghĩa trong Blackboard).*

- **Xử lý kết quả**: Combo Engine sẽ tự động xuất ra bộ nguyên liệu hoàn chỉnh (1 Anchor Insight, 1 Solution/Concept bổ trợ, 1-2 Stories, và 3-5 Quotes/Data-Points) thỏa mãn 100% các luật Poka-Yoke và cơ chế Anti-Repetition (loại bỏ các nguyên liệu đã dùng trong 3 bài đăng gần nhất từ `production-log.md`). Kết quả này sẽ được chuyển tiếp trực tiếp sang Bước 2 để thực hiện đóng gói payload.

### Bước 2: Đóng gói (Export Payload)
Xuất "Gói nguyên liệu DIKW (Atomic Combo)" nạp làm đầu vào trực tiếp cho **Idea Curator** (Bước 2) và **Content-Post** (điều phối cho các Agent khác toàn dây chuyền).

**1a. Quy chuẩn Format xuất (Deterministic Combo):**
Combo Tuyến tính duy nhất (đã chọn ở Bước 1):
- `[1 Target Audience]` (Audience của Anchor Insight — xem mục 1b)
- `[1 Insight]` (Anchor cốt lõi)
- `[1 Solution hoặc Concept]` (trỏ `supports_insight` về Insight trên)
- `[1-2 Story]` (trỏ `supports_knowledge` về Solution/Concept trên)
- `[3-5 Data-Points hoặc Quotes]` (trỏ `supports_knowledge` về Solution/Concept)

**1b. Audience Resolution (chỉ khi `Target_Audience` là array):**
1. Lấy audience ID từ `belongs_to_audience` của Anchor Insight (strip `[[]]` trước khi so sánh). Nếu Insight trỏ nhiều audience → chọn audience **nằm trong** `Target_Audience`. Nhiều audience đều nằm trong → đầu tiên.
2. `view_file` audience atom tại `vault/01-Atomic/Audiences/[audience-ID].md`.
3. Trích 3 trường: `audience_Job_performer`, `audience_main_job`, `audience_circumstance`.
4. Cập nhật `00-blackboard.yaml` (giữ nguyên `# execution_key:` cuối file):
   - Ghi đè `Target_Audience` thành string (audience ID đã chọn).
   - Append block `resolved_jtbd`:
```yaml
resolved_jtbd:
  audience_Job_performer: "[giá trị]"
  audience_main_job: "[giá trị]"
  audience_circumstance: "[giá trị]"
  source_audience: "[audience atom ID]"
```

*Trình bày Output theo bảng*: Atom path | DIKW Layer | Weight | Relevance Score | Node Trỏ

Trong đó `Atom path` = đường dẫn tương đối từ factory root.
Ví dụ: `vault/01-Atomic/Stories/the-whole-brain-child_story-liam-liam-mot-be-muoi-7.md`

**2. Trích xuất Vivid Payload (Minified JSON):**
Quét YAML Frontmatter của các Atom trong Combo, gộp 3 mảng (`vivid_circumstances`, `vivid_insights`, `vivid_knowledges`) thành 1 khối Mini-JSON đính kèm Payload cho `Hook Engineer` và `Voice Writer`.

### Bước 3: Lưu trữ và gộp vật lý (Persist to Run Folder)

1. Ghi toàn bộ output Bước 2 (Bảng Combo + Minified JSON Vivid Payload) vào file `00.5-dikw-combo.md` trong run folder (đường dẫn đã khởi tạo tại Bước 4 workflow).
2. `resolved_jtbd` đã ghi vào `00-blackboard.yaml` ở Bước 2:
   - IF Target_Audience là array → mục 1b đã ghi.
   - IF Target_Audience là string → Semantic Router đã ghi, DIKW không ghi lại.
3. BẮT BUỘC CHẠY SCRIPT SAU ĐÂY để tự động gộp text nguyên liệu vào file Combo (⚠ **CHÚ Ý:** TUYỆT ĐỐI KHÔNG COPY MÙ. Bạn PHẢI tự thay thế biến `[run-folder]` bằng tên thư mục run folder thực tế của phiên hiện tại):
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/dikw-bridge/scripts/bundle-atoms.ps1" -ComboFile "vault/.content-pipeline/runs/[run-folder]/00.5-dikw-combo.md"
```

⛔ File này là bản sao vật lý của Gói nguyên liệu DIKW, phục vụ resume dự phòng khi pipeline cần khôi phục. Output trong context memory vẫn được sử dụng bình thường bởi các Phase tiếp theo.
