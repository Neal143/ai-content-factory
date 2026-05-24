---
name: DIKW Bridge
description: Skill đóng vai trò cầu nối, quét kho dữ liệu Obsidian (Vault) để tìm nguyên liệu liên quan đến topic và xếp thứ hạng theo mô hình DIKW.
last_update: 24/05/2026 16:55 (GMT+7)
---

# DIKW Bridge Skill

## Hướng dẫn hoạt động

### Bước 1: Tiếp nhận Context & Khai báo Nguồn
- Tiếp nhận từ Workflow `/content-post`: `mapped_topics` (topic IDs) và `Target_Audience` (Audience ID hoặc array Audience IDs).
- Đọc kĩ `.agents/skills/dikw-bridge/references/injection-rules.md`.
- **Phân giải User ID**: Trích xuất `[User]` từ phần cuối của `Persona_Path` trong Bảng đen (ví dụ: `Persona_Path: personas/Neal` → `[User]` = `Neal`).

**Nguồn 1 — Vault Atoms (Ưu tiên cao nhất):**
- Path: `vault/01-Atomic/`
- Quét 6 thư mục vật lý (Direct Read, TUYỆT ĐỐI không dùng LLM extraction):
  1. `Stories/` → Wisdom (W)
  2. `Solutions/` → Knowledge (K)
  3. `Insights/` → Knowledge (K)
  4. `Concepts/` → Information (I)
  5. `Quotes/` → Data (D)
  6. `Data-Points/` → Data (D)

**Nguồn 2-4 — Extract Stories bổ sung (chỉ phục vụ Wisdom layer):**

| Nguồn | Path | Confidence |
|-------|------|------------|
| Viral Posts | `vault/[User]/Viral Posts/` | 0.9 |
| Posted | `vault/[User]/Posted/` | 0.8 |
| Reflective Writing | `vault/Content/Reflective Writing.md` | 0.6 |

**Exclude**: `.obsidian`, `.git`, `.gitkeep`, `Template`, `_Templates`, `_System`

---

### Thủ tục phụ: Smart Global Pre-Filter (Màng Lọc Nguồn Toàn Cục)
Trước khi thực hiện các phép lọc chuyên sâu ở Bước 2, hãy đọc `Target_Source_IDs` từ Blackboard (`00-blackboard.yaml`).

1. **Nếu `Target_Source_IDs` CÓ RÀNG BUỘC (mảng có phần tử, ví dụ: `["good-inside"]`):**
   - Quét tất cả các file MD trong **Nguồn 1** (`vault/01-Atomic/` gồm 6 thư mục con: `Stories`, `Solutions`, `Insights`, `Concepts`, `Quotes`, `Data-Points`).
   - Đọc trường `source_id` trong frontmatter của từng file.
   - **LOẠI BỎ NGAY LẬP TỨC** các file thuộc `vault/01-Atomic/` ra khỏi danh sách ứng viên đưa vào Rổ nguyên liệu nếu file đó không chứa thuộc tính `source_id` hoặc giá trị `source_id` không nằm trong mảng `Target_Source_IDs`.
   - ⛔ **QUY TẮC BẢO TOÀN (Zero-breakage Rule):** Màng lọc này TUYỆT ĐỐI KHÔNG ÁP DỤNG cho các file quét từ các **Nguồn 2-4** (như `Viral Posts/`, `Posted/`, `Reflective Writing.md`). Những file này không có `source_id` và thuộc về tài nguyên dùng chung của Persona, phải được giữ nguyên vẹn để đi tiếp vào vòng chấm điểm như bình thường.

2. **Nếu `Target_Source_IDs` TRỐNG (mảng rỗng hoặc null, tức viết tự do):**
   - Bỏ qua màng lọc này, giữ nguyên toàn bộ các file ứng viên và đi tiếp vào Bước 2.

---

### Bước 2: Lọc Nhánh Chính (Bộ lọc O(1) Đa Điều Kiện)
- Tầng 2: **Insights** = Anchors. Quét các file `Insights` thoả mãn ĐỒNG THỜI:
  - Có ít nhất một topic thuộc mảng `mapped_topics` HOẶC có thuộc tính `source_id` nằm trong mảng `Target_Source_IDs` (nếu mảng này tồn tại và có phần tử).
  - Có `belongs_to_audience` khớp với `Target_Audience` (strip `[[]]` trước khi so sánh):
    - `Target_Audience` là string → so sánh trực tiếp.
    - `Target_Audience` là array → khớp nếu trùng **bất kỳ** phần tử nào.
- Các file Insight thỏa mãn sẽ là Mỏ neo gốc (Anchors) đưa vào Rổ nguyên liệu.

### Bước 3: Lọc Nhánh Rễ (Validate Graph Links & Purge)
- **Tầng 3 (Validate `supports_insight`):** Scan `Solutions`, `Concepts`. Chỉ lấy các Atom nào có Node Link `supports_insight` trỏ VÀO MỘT TRONG CÁC file Insight (Tầng 2) đang có trong Rổ.
- **Tầng 4 (Validate `supports_knowledge`):** Scan `Stories`, `Quotes`, `Data-Points`. Chỉ lấy các Atom nào có Node Link `supports_knowledge` trỏ VÀO MỘT TRONG CÁC file Solution/Concept (Tầng 3) đang có trong Rổ.
- **⛔ Orphan Purge:** Drop hoàn toàn các Atom thiếu Link Graph, hoặc Link trỏ ra ngoài Rổ nguyên liệu. Không đưa rác vào quy trình.
- **Anti-Repetition:** Đọc `production-log.md` để tự động loại bỏ các Atoms đã được sử dụng trong 3 bài post gần nhất.

### Bước 4: Anchor-First Selection (Chọn Combo Deterministic)

> Relevance = `topic_overlap_count` × `dikw_weight` (từ `injection-rules.md`).
> Loại atom có confidence < 0.5 hoặc status = "rejected"/"quarantine".

**Phase A — Chọn Anchor Insight:**
1. Score từng Insight trong Rổ. Sort DESC.
2. Tiebreaker ngang điểm: Insight có nhiều downstream atoms (Solutions/Concepts trỏ về) thắng. Vẫn ngang → alphabet filename.

**Phase B — Kiểm tra Viability (top-down):**
3. FOR each Insight (score cao → thấp):
   a. Tìm Solutions/Concepts có `supports_insight` → Insight này. Không có → **skip**.
   b. Score Solutions/Concepts → chọn top 1.
   c. Tìm Stories có `supports_knowledge` → Solution/Concept đã chọn.
   d. Tìm Data-Points/Quotes có `supports_knowledge` → Solution/Concept đã chọn.
   e. Nếu (Data-Points + Quotes) < 1 → **skip**, thử Insight tiếp.
   f. **VIABLE** → chốt Anchor. BREAK.

**Phase C — Lấp slot Combo:**
5. Stories: top 1-2 (score DESC, ưu tiên subtype theo `injection-rules.md`).
6. Data-Points/Quotes: top 3-5 (score DESC).

### Bước 5: Đóng gói (Export Payload)
Xuất "Gói nguyên liệu DIKW (Atomic Combo)" nạp làm đầu vào trực tiếp cho **Idea Curator** (Bước 2) và **Content-Post** (điều phối cho các Agent khác toàn dây chuyền).

**1a. Quy chuẩn Format xuất (Deterministic Combo):**
Combo Tuyến tính duy nhất (đã chọn ở Bước 4):
- `[1 Target Audience]` (Audience của Anchor Insight — xem mục 1b)
- `[1 Insight]` (Anchor cốt lõi)
- `[1 Solution hoặc Concept]` (trỏ `supports_insight` về Insight trên)
- `[1-2 Story]` (trỏ `supports_knowledge` về Solution/Concept trên)
- `[3-5 Data-Points hoặc Quotes]` (trỏ `supports_knowledge` về Solution/Concept)

**1b. Audience Resolution (chỉ khi `Target_Audience` là array):**
1. Lấy audience ID từ `belongs_to_audience` của Anchor Insight (strip `[[]]`). Nếu Insight trỏ nhiều audience → chọn audience **nằm trong** `Target_Audience`. Nhiều audience đều nằm trong → đầu tiên.
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

### Bước 6: Persist to Run Folder

1. Ghi toàn bộ output Bước 5 (Bảng Combo + Minified JSON Vivid Payload) vào file `00.5-dikw-combo.md` trong run folder (đường dẫn đã khởi tạo tại Bước 4 workflow).
2. `resolved_jtbd` đã ghi vào `00-blackboard.yaml` ở Bước 5:
   - IF Target_Audience là array → mục 1b đã ghi.
   - IF Target_Audience là string → Semantic Router đã ghi, DIKW không ghi lại.

⛔ File này là bản sao vật lý của Gói nguyên liệu DIKW, phục vụ resume dự phòng khi pipeline cần khôi phục. Output trong context memory vẫn được sử dụng bình thường bởi các Phase tiếp theo.

