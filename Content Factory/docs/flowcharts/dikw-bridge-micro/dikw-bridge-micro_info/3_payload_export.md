## IsAudienceArray
### Bước 5: Đóng gói (Export Payload)
Xuất "Gói nguyên liệu DIKW (Atomic Combo)" nạp làm đầu vào trực tiếp cho **Idea Curator** (Bước 2) và **Content-Post** (điều phối cho các Agent khác toàn dây chuyền).

**1b. Audience Resolution (chỉ khi `Target_Audience` là array):**
1. Lấy audience ID từ `belongs_to_audience` của Anchor Insight (strip `[[]]`). Nếu Insight trỏ nhiều audience → chọn audience **nằm trong** `Target_Audience`. Nhiều audience đều nằm trong → đầu tiên.

## ResolveJTBD
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

## GenJSON
**1a. Quy chuẩn Format xuất (Deterministic Combo):**
Combo Tuyến tính duy nhất (đã chọn ở Bước 4):
- `[1 Target Audience]` (Audience của Anchor Insight — xem mục 1b)
- `[1 Insight]` (Anchor cốt lõi)
- `[1 Solution hoặc Concept]` (trỏ `supports_insight` về Insight trên)
- `[1-2 Story]` (trỏ `supports_knowledge` về Solution/Concept trên)
- `[3-5 Data-Points hoặc Quotes]` (trỏ `supports_knowledge` về Solution/Concept)

*Trình bày Output theo bảng*: Atom path | DIKW Layer | Weight | Relevance Score | Node Trỏ

Trong đó `Atom path` = đường dẫn tương đối từ factory root.
Ví dụ: `vault/01-Atomic/Stories/the-whole-brain-child_story-liam-liam-mot-be-muoi-7.md`

**2. Trích xuất Vivid Payload (Minified JSON):**
Quét YAML Frontmatter của các Atom trong Combo, gộp 3 mảng (`vivid_circumstances`, `vivid_insights`, `vivid_knowledges`) thành 1 khối Mini-JSON đính kèm Payload cho `Hook Engineer` và `Voice Writer`.

## WriteOutput
### Bước 6: Persist to Run Folder

1. Ghi toàn bộ output Bước 5 (Bảng Combo + Minified JSON Vivid Payload) vào file `00.5-dikw-combo.md` trong run folder (đường dẫn đã khởi tạo tại Bước 4 workflow).

## ComboFile
2. `resolved_jtbd` đã ghi vào `00-blackboard.yaml` ở Bước 5:
   - IF Target_Audience là array → mục 1b đã ghi.
   - IF Target_Audience là string → Semantic Router đã ghi, DIKW không ghi lại.

⛔ File này là bản sao vật lý của Gói nguyên liệu DIKW, phục vụ resume ở phiên mới. Output trong context memory vẫn được sử dụng bình thường bởi các Phase trong cùng phiên.
