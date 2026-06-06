---
name: BRIEF-DIKW-Index.md
last_update: 26/05/2026 23:48 (GMT+7)
role: Tài liệu tóm tắt ý tưởng thiết kế (Brief)
usage: Dùng làm input cho /plan để lên kiến trúc chi tiết và task list
output: Kế hoạch giải quyết technical debt + schema mismatch
logic: Chuyển đổi thuật toán duyệt đồ thị O(N^3) sang In-memory Indexing, cung cấp Tool chuẩn cho Agent, và đồng nhất schema Atom giữa 2 nguồn (Book Parser vs Persona Interviewer)
---

# 💡 BRIEF: Xử lý Nợ Kỹ Thuật trong Truy vấn Graph DIKW + Đồng nhất Schema Atom

**Ngày tạo:** 26/05/2026
**Brainstorm cùng:** User

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT

### Nhóm A — Performance & Architecture (DIKW Index Tool)
- Thuật toán truy vấn đồ thị DIKW sử dụng 3 vòng lặp lồng nhau O(N³) kết hợp Disk I/O (`Get-Content`) để quét file Markdown.
- Agent tự sinh script tạm bợ (`scratch/find_combos.ps1`) → sinh rác, phân mảnh luồng chạy.
- Rủi ro: Vault phình to → timeout, crash, lãng phí token.

### Nhóm B — Schema Mismatch (Insight Schema B thiếu `topics`)
Vault hiện có **2 schema Insight** hoàn toàn khác nhau:

| | Schema A (Book Parser) | Schema B (Persona Interviewer) |
|---|---|---|
| Nguồn | Sách → `book-parser` | Phỏng vấn User → `persona-interviewer` |
| `topics` | ✅ Có (kế thừa từ Book/Chunk) | ❌ **KHÔNG CÓ** |
| `source_id` | ✅ Có | ❌ Không có trong template (chỉ có trong file thực tế) |
| `insight_name` | ❌ Không có | ✅ Có (nhưng không phục vụ routing) |

**Hệ lụy:**
- `dikw-bridge` Bước 2 lọc Insight theo `topics` + `audience` → Schema B bị loại 100%.
- Mọi Atom con (Tầng 3, 4) trỏ `supports_insight` về Schema B cũng bị orphan theo.
- 8 file Insight Schema B hiện có trong Vault đều bị ảnh hưởng.

**Nguyên nhân gốc:**
- Template `insight.md` có `insight_name: "{{name}}"` nhưng không có `topics`.
- Script `generate_insights.py` chỉ inject 4 biến: `headline`, `insight_type`, `raw_payload`, `llm_explain` — không có `topics`.
- `persona-interviewer/SKILL.md` L146 (Bước 2 Câu 11) mapping Insight→Pillar nhưng không resolve topics dù dữ liệu đã tồn tại trong `topic_map.yaml` (mỗi topic đã có `pillar_parents`).

---

## 2. GIẢI PHÁP ĐỀ XUẤT

### Nhóm A — In-Memory Indexing & Standardized Tool

**A1. File `vault_index.json`** (Flat Nodes + Relational Edges):
```json
{
  "metadata": { "last_updated": "..." },
  "nodes": {
    "vault/01-Atomic/Insights/GI_example.md": {
      "type": "insight", "topics": ["dieu_hoa_cam_xuc"], "source_id": "good-inside",
      "belongs_to_audience": "cha-me_...", "confidence": 0.9, "status": "processed",
      "insight_type": "pain_point", "subtype": null, "knowledge_type": null
    }
  },
  "edges": {
    "supports_insight": {
      "vault/01-Atomic/Solutions/GI_sol.md": "vault/01-Atomic/Insights/GI_example.md"
    },
    "supports_knowledge": {
      "vault/01-Atomic/Stories/GI_story.md": "vault/01-Atomic/Solutions/GI_sol.md"
    }
  }
}
```

**A2. Script `build-vault-index.ps1`:**
- Quét **đúng 6 thư mục**: `Insights/`, `Solutions/`, `Concepts/`, `Stories/`, `Quotes/`, `Data-Points/`.
- **Exclude:** `Audiences/`, `_DLQ/`, file `.gitkeep`, file/thư mục prefix `_` (VD: `_audience_index.yaml`).
- Parse YAML frontmatter: **CHỈ đọc block đầu tiên** (dòng 1 phải là `---`, đọc đến dòng `---` tiếp theo, dừng). ⚠ Schema B files chứa fake YAML trong comment block HTML — parser phải bỏ qua hoàn toàn phần body.
- Strip `[[` `]]` từ Wikilinks để tạo ID thuần.
- Xuất `vault_index.json`.
- ⚠ **CWD Constraint:** Script phải chạy với working directory = `Content Factory/` (root dự án code) để mọi path tương đối (`vault/01-Atomic/...`) resolve đúng.

**A3. Tool `Get-DIKWCombo`:**
- Input: `$Topics` (chấp nhận cả single string lẫn array), `$Audience` (string hoặc array), `$TargetSourceIds`, `$PersonaUser` (từ Blackboard).
- Luôn rebuild index khi gọi (Vault ~260 file, <1s). Khi Vault >1000 file → chuyển sang so sánh `max(LastWriteTime)` của từng thư mục con.
- **Poka-Yoke Filters** (áp dụng trước mọi logic lọc): Loại atom có `confidence < 0.5` hoặc `status = "rejected"/"quarantine"`.
- Thực hiện logic Bước 1→4 của `dikw-bridge/SKILL.md`:
  - Smart Global Pre-Filter: Khi `Target_Source_IDs` có phần tử → loại atom không khớp `source_id`. Khi rỗng → bỏ qua.
  - Lọc Nhánh Chính (Bước 2): `topic match AND audience match`. Lưu ý: `source_id match` **CHỈ** được dùng trong Pre-Filter (khi `Target_Source_IDs` có ràng buộc), KHÔNG dùng trong Bước 2.
  - Lọc Nhánh Rễ (validate `supports_insight`, `supports_knowledge`).
  - Orphan Purge.
  - Anti-Repetition: Đọc trực tiếp `output/logs/production-log.md` tại runtime (không nằm trong index).
  - Anchor-First Selection (Phase A, B, C): Score theo `injection-rules.md` (W=10, K=7, I=3, D=1 + Story Subtype Priority), Viability check, chọn Combo.
- Nguồn 2-4 (`vault/[User]/Viral Posts/`, `vault/[User]/Posted/`): Quét trực tiếp khi có file `.md` (hiện đều rỗng, nhưng phải dự phòng). Không áp dụng `Target_Source_IDs` filter (Zero-breakage Rule).
- Output 3 phần (⚠ path phải dùng format tương đối `vault/01-Atomic/...` để tương thích regex của `bundle-atoms.ps1`):
  1. Bảng Combo tuyến tính (Audience, Insight, Solution/Concept, Stories, Data/Quotes) + Relevance Score.
  2. Vivid Payload JSON (gộp `vivid_circumstances`, `vivid_insights`, `vivid_knowledges` từ frontmatter).
  3. `resolved_jtbd` (nếu `Target_Audience` là array → resolve audience, trích 3 trường JTBD).

**A4. Cập nhật `dikw-bridge/SKILL.md`:**
- Bước 1-4 cũ → thay bằng lệnh gọi `Get-DIKWCombo` duy nhất.
- Bước 5 chỉ còn format output + ghi Blackboard.
- Bước 6 giữ nguyên (persist + gọi `bundle-atoms.ps1`).

### Nhóm B — Đồng nhất Schema Insight

**B1. Sửa template `insight.md`:**
- Bỏ trường `insight_name: "{{name}}"`.
- Thêm trường `topics: {{topics}}`.
- Thêm trường `source_id: "persona-interview"`.
- Giữ nguyên `{{name}}` trong phần body heading (`# {{type}}: {{name}}`).

**B2. Sửa `generate_insights.py`:**
- Đọc thêm trường `topics` từ payload item.
- Format thành chuỗi YAML array bằng `json.dumps(topics, ensure_ascii=False)`.
- Thêm `.replace("{{topics}}", topics_yaml)` vào chuỗi template replacement.

**B3. Sửa `persona-interviewer/SKILL.md`:**
- L146 Bước 2 Câu 11: Khi mapping Insight→Pillar, **đồng thời resolve topics**: Tra cứu `topic_map.yaml` → tìm tất cả topic có `pillar_parents` chứa Pillar vừa map → gán danh sách `id` làm giá trị `topics`.
- L149-153 Payload format: Thêm trường thứ 5 `topics` (mảng id topic đã resolve).

**B4. Backfill 8 file Insight Schema B hiện có:**
- Bỏ `insight_name` khỏi frontmatter.
- Thêm `topics: [...]` (xác định Pillar phù hợp → resolve topics từ `topic_map.yaml`).
- `source_id: "persona-interview"` — đã tồn tại trong cả 8 file (no-op, chỉ cần xác nhận).

8 file cần backfill:
- `cam-giac-dang-lam-dung-di-dung-huong.md`
- `khong-chac-lam-dung-khong-co-thoi-gian-sua-sai.md`
- `man-hinh-ap-luc-hoc-som-lam-hai-con.md`
- `muon-con-hanh-phuc-y-nghia-du-the-gioi-thay-doi.md`
- `muon-lam-cha-me-du-tot-khong-bo-lo-giai-doan-vang.md`
- `qua-ban-qua-met-khong-du-hien-dien-cho-con.md`
- `so-ai-thay-the-con-thieu-ky-nang.md`
- `so-lang-phi-giai-doan-vang-cua-con.md`

Tất cả đều có `belongs_to_audience: "[[cap-vo-chong_tim-hieu-ve-nuoi-con_sap-co-con-hoac-dang-co-con-o-do-tuoi-0-7-tuoi]]"` → Reverse-lookup `topic_map.yaml` cho audience này sẽ trả về danh sách topics. Tuy nhiên audience Big này trỏ tới rất nhiều topics nên cần **lọc thêm theo Pillar** (xem ghi chú bên dưới).

> **Ghi chú Backfill:** 8 file này không có thông tin Pillar nào đã được map (vì chúng được tạo trước Câu 11 của persona-interviewer, lúc chưa có bảng mapping). Cần xác định Pillar phù hợp cho từng file dựa trên nội dung `insight_type` + `raw_payload` → rồi mới resolve topics từ Pillar đó. Thực hiện thủ công (8 file, lượng nhỏ).

### Nhóm C — Backfill Good-Inside Atoms (Topic ID không đồng nhất)

**Vấn đề:** `good-inside` atoms có topic IDs tiếng Anh (`"parenting"`, `"child-psychology"`, `"child-behavior"`, `"emotional-regulation"`) không khớp `topic_map.yaml` IDs. Khi `Target_Source_IDs` rỗng (viết tự do) → Bước 2 chỉ dùng topic match → toàn bộ good-inside atoms biến mất.

**Bằng chứng:** `atomizer_context.json` cho thấy 30 chunks đều có cùng 2 topics `["child-behavior", "emotional-regulation"]` (bất thường — 30 chương khác nhau không thể cùng topics). File `resolved_topics.json` KHÔNG tồn tại trong run folder → Bước 1.5 Semantic Dedup bị skip.

**Nguyên nhân gốc:** Agent thực thi `book-parser` cho good-inside đã **skip Bước 1.5** (Semantic Dedup via `topic_manager.md`) → `resolved_topics.json` không được tạo → `atomizer_context.json` được tạo từ working memory thay vì từ `resolved_topics.json` (vi phạm SKILL.md L59-61, L96) → `atomizer.py` nhận input sai → ghi topics sai vào toàn bộ atoms. Hệ thống `topic_manager` hoạt động đúng (bằng chứng: `the-whole-brain-child` atoms có đúng topic_map.yaml IDs).

**C1. Fix:** Backfill topics cho toàn bộ GI_ atoms:
- Chạy lại Bước 1.2-1.5 của `book-parser` SKILL.md cho good-inside (sinh topics đúng + qua Semantic Dedup) → tạo `resolved_topics.json`.
- **Viết script backfill** đọc `resolved_topics.json` mới → update **chỉ trường `topics`** trong frontmatter từng file GI_ (giữ nguyên mọi trường khác).
- ⚠ **KHÔNG re-run `atomizer.py`**: `curate_vivids.py` đã gắn vivid data (`vivid_insights`, `vivid_knowledges`) vào frontmatter sau lần parse đầu. Re-atomize sẽ reset vivid về `[]`, mất dữ liệu.

---

## 3. ĐỐI TƯỢNG SỬ DỤNG
- **Primary:** DIKW Bridge Agent (Skill: `dikw-bridge`).
- **Secondary:** Persona Interviewer (Skill: `persona-interviewer`) — cải tiến chất lượng Atom đầu ra.

## 4. TÍNH NĂNG

### 🚀 MVP (Bắt buộc có):

**Nhóm A:**
- [ ] Script `build-vault-index.ps1`
- [ ] Script `Get-DIKWCombo` (bao gồm Anti-Repetition runtime, Nguồn 2-4 dự phòng, Vivid Payload, Audience Resolution)
- [ ] Cập nhật `dikw-bridge/SKILL.md`

**Nhóm B:**
- [ ] Sửa template `insight.md`
- [ ] Sửa `generate_insights.py`
- [ ] Sửa `persona-interviewer/SKILL.md` (L146 + L149-153)
- [ ] Backfill 8 file Insight Schema B

**Nhóm C:**
- [ ] Backfill `topics` cho toàn bộ good-inside atoms (`GI_*`) với đúng topic_map.yaml IDs

### 🎁 Phase 2 (Làm sau):
- [ ] Xuất sơ đồ DOT/Mermaid từ Index.
- [ ] Chuyển Pre-flight Check sang `max(LastWriteTime)` khi Vault >1000 file.

## 5. ƯỚC TÍNH & RỦI RO

| Hạng mục | Độ phức tạp | Rủi ro |
|---|---|---|
| `build-vault-index.ps1` | Trung bình | Parse YAML phải chỉ đọc block frontmatter đầu tiên (Schema B files chứa fake YAML trong comment block) |
| `Get-DIKWCombo` | Cao | Logic Anchor-First Selection + Scoring phải khớp 1:1 với SKILL.md |
| `dikw-bridge/SKILL.md` refactor | Thấp | Phải giữ nguyên Bước 5, 6 không bị ảnh hưởng |
| Schema B fix | Thấp | Backfill 8 file cần xác định Pillar chính xác |
| Good-inside backfill | Trung bình | Cần Semantic Dedup thủ công cho từng topic. Không match → thêm mới vào `topic_map.yaml` |
| `bundle-atoms.ps1` | Không sửa | Regex quét path trong combo file → không bị ảnh hưởng |

## 6. BƯỚC TIẾP THEO
→ Chạy `/plan` để lên Implementation Plan chi tiết (kiến trúc file, hàm, task list).
