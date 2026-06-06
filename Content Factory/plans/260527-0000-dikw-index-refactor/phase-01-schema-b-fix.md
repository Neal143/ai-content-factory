---
name: phase-01-schema-b-fix.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Phase
usage: Hướng dẫn thực thi chi tiết Phase 1 — sửa Schema B cho persona-interviewer
output: Template insight.md có trường topics, script inject topics, SKILL.md resolve topics, 8 file backfill
logic: Sửa 3 file hệ thống (template, script, SKILL.md) + backfill 8 file data
---

# Phase 01: Schema B Fix (Persona Interviewer)

**Trạng thái:** ⬜ Pending
**Nhóm BRIEF:** B
**Dependencies:** Không (phase độc lập)

---

## Task 1.1: Sửa template `insight.md`

**File:** `.agents/skills/persona-interviewer/assets/insight.md`

**Thay đổi:**
- Dòng 4: **Bỏ** `insight_name: "{{name}}"`
- Thêm dòng mới tại vị trí dòng 4: `topics: {{topics}}`
- Thêm dòng mới ngay sau `topics`: `source_id: "persona-interview"`

**TRƯỚC (dòng 1-13):**
```yaml
---
type: insight
insight_type: "{{type}}"
insight_name: "{{name}}"
belongs_to_audience: "[[{{target_audience}}]]"
status: processed
created: "{{date}}"
source_type: "User"
source_name: "Persona Interview"
confidence: 1.0
vivid_insights: []
vivid_insights_reserve: []
---
```

**SAU (dòng 1-14):**
```yaml
---
type: insight
insight_type: "{{type}}"
topics: {{topics}}
source_id: "persona-interview"
belongs_to_audience: "[[{{target_audience}}]]"
status: processed
created: "{{date}}"
source_type: "User"
source_name: "Persona Interview"
confidence: 1.0
vivid_insights: []
vivid_insights_reserve: []
---
```

**Lưu ý:**
- `{{topics}}` sẽ được inject dưới dạng JSON array string (VD: `["dieu_hoa_cam_xuc", "gan_ket_an_toan"]`). Đây là cú pháp YAML inline array hợp lệ.
- `# {{type}}: {{name}}` ở dòng 15 (body heading) **giữ nguyên** — `{{name}}` vẫn dùng cho tiêu đề hiển thị.
- Comment block ví dụ minh họa (dòng 26-52) **giữ nguyên** — không cần sửa vì nó chỉ là tài liệu tham khảo.

**Kiểm tra:** Mở file trong Obsidian → YAML frontmatter hiển thị đúng cấu trúc, không lỗi parse.

---

## Task 1.2: Sửa `generate_insights.py`

**File:** `.agents/skills/persona-interviewer/scripts/generate_insights.py`

**Thay đổi 1 — Đọc `topics` từ payload (dòng 33, sau `llm_explain`):**

**TRƯỚC:**
```python
        llm_explain = item.get("llm_explain", "")
```

**SAU:**
```python
        llm_explain = item.get("llm_explain", "")
        topics = item.get("topics", [])
```

**Thay đổi 2 — Format topics thành YAML-compatible string và inject vào template (dòng 47-53):**

**TRƯỚC:**
```python
        # Replace variables
        file_content = template.replace("{{type}}", str(insight_type).upper())\
                               .replace("{{date}}", today)\
                               .replace("{{name}}", headline)\
                               .replace("{{target_audience}}", target_audience)\
                               .replace("{{raw_payload}}", raw_payload)\
                               .replace("{{llm_explain}}", llm_explain)
```

**SAU:**
```python
        # Format topics thành JSON array string (VD: ["topic_a", "topic_b"])
        topics_yaml = json.dumps(topics, ensure_ascii=False)
        
        # Replace variables
        file_content = template.replace("{{type}}", str(insight_type).upper())\
                               .replace("{{date}}", today)\
                               .replace("{{name}}", headline)\
                               .replace("{{topics}}", topics_yaml)\
                               .replace("{{target_audience}}", target_audience)\
                               .replace("{{raw_payload}}", raw_payload)\
                               .replace("{{llm_explain}}", llm_explain)
```

**Lưu ý:**
- `json.dumps` đã import sẵn ở dòng 2 (`import json`).
- Nếu payload không có trường `topics` → default `[]` → output `topics: []` trong frontmatter (mảng rỗng, không gãy).
- CLI interface (`argparse` dòng 60-69) **không thay đổi** — topics đến từ JSON payload, không từ CLI args.

**Kiểm tra:** Chạy script với payload test có trường `topics` → file output có `topics: ["id1", "id2"]` trong frontmatter.

---

## Task 1.3: Sửa `persona-interviewer/SKILL.md`

**File:** `.agents/skills/persona-interviewer/SKILL.md`

**Thay đổi 1 — Dòng 146 (Bước 2 Xác nhận Mapping), thêm logic resolve topics:**

**TRƯỚC (dòng 146):**
```markdown
    - **Bước 2 (Xác nhận Mapping)**: Tự động phân bổ danh sách Seed Insights (từ Câu 10) vào các Pillars tương ứng (nhưng CHƯA ghi file). Hiển thị bảng Mapping ra Chatbox và yêu cầu: *"Vui lòng xem lại bảng phân bổ Insight vào Pillar và gõ (Y) để xác nhận."*
```

**SAU (dòng 146):**
```markdown
    - **Bước 2 (Xác nhận Mapping)**: Tự động phân bổ danh sách Seed Insights (từ Câu 10) vào các Pillars tương ứng. **Đồng thời resolve topics**: Với mỗi Insight được map vào Pillar P, tra cứu `topic_map.yaml` → lấy tất cả topic có `pillar_parents` chứa P → gán danh sách `id` làm giá trị `topics` cho Insight đó. Hiển thị bảng Mapping (bao gồm cột Topics) ra Chatbox và yêu cầu: *"Vui lòng xem lại bảng phân bổ Insight vào Pillar và gõ (Y) để xác nhận."*
```

**Thay đổi 2 — Dòng 149-153 (Payload format), thêm trường `topics`:**

**TRƯỚC (dòng 149):**
```markdown
    - **Hành động Hệ thống (Phát tín hiệu Script)**: CHỈ SAU KHI nhận lệnh `(Y)` từ User, tiến trình mới được phép ghi nối dữ liệu Pillars vào `pillars.yaml`. Đồng thời AI dùng Tool In Đè (Overwrite) toàn bộ array JSON tổng hợp Insight vào file tĩnh có sẵn: `.agent/skills/persona-interviewer/scripts/insights_payload.json`, bắt buộc chứa 4 biến chính xác sau:
      + `headline`: Đặt tên tối giản, loại bỏ stop words, chỉ lấy cụm danh từ/động từ chính. Script sẽ tự chuyển thành **Slug Naming** chuẩn: `[slug-keyword-tieng-viet-khong-dau].md` (chữ thường, không dấu, nối bằng gạch ngang).
      + `insight_type`: Phân loại nhóm Insight (ví dụ: desire, pain_point...).
      + `raw_payload`: Nguyên văn phần text thô do User gợi mở.
      + `llm_explain`: Phân tích chuyên sâu đúc rút từ AI (Insightful explain).
```

**SAU (dòng 149):**
```markdown
    - **Hành động Hệ thống (Phát tín hiệu Script)**: CHỈ SAU KHI nhận lệnh `(Y)` từ User, tiến trình mới được phép ghi nối dữ liệu Pillars vào `pillars.yaml`. Đồng thời AI dùng Tool In Đè (Overwrite) toàn bộ array JSON tổng hợp Insight vào file tĩnh có sẵn: `.agent/skills/persona-interviewer/scripts/insights_payload.json`, bắt buộc chứa 5 biến chính xác sau:
      + `headline`: Đặt tên tối giản, loại bỏ stop words, chỉ lấy cụm danh từ/động từ chính. Script sẽ tự chuyển thành **Slug Naming** chuẩn: `[slug-keyword-tieng-viet-khong-dau].md` (chữ thường, không dấu, nối bằng gạch ngang).
      + `insight_type`: Phân loại nhóm Insight (ví dụ: desire, pain_point...).
      + `raw_payload`: Nguyên văn phần text thô do User gợi mở.
      + `llm_explain`: Phân tích chuyên sâu đúc rút từ AI (Insightful explain).
      + `topics`: Mảng `id` topics đã resolve ở Bước 2 (VD: `["dieu_hoa_cam_xuc", "gan_ket_an_toan"]`).
```

**Kiểm tra:** Đọc lại SKILL.md → flow Câu 11 Bước 2 phải mô tả rõ cách resolve topics từ `topic_map.yaml`.

---

## Task 1.4: Backfill 8 file Insight Schema B

**Vị trí:** `vault/01-Atomic/Insights/` (8 file không có prefix)

**Thao tác cho MỖI file:**
1. Bỏ dòng `insight_name: "..."` khỏi frontmatter.
2. Thêm dòng `topics: [...]` (giá trị resolve từ bước 3 bên dưới).
3. Xác nhận `source_id: "persona-interview"` đã tồn tại (no-op nếu có).

**Cách resolve topics cho từng file:**
- Đọc nội dung `insight_type` + body text.
- Xác định Pillar phù hợp nhất (1 Pillar duy nhất).
- Tra `topic_map.yaml` → lấy tất cả topic có `pillar_parents` chứa Pillar đó → gán danh sách `id`.

**Danh sách 8 file:**

| File | `insight_type` | Pillar gợi ý (cần xác nhận) |
|---|---|---|
| `cam-giac-dang-lam-dung-di-dung-huong.md` | cần kiểm tra | cần xác nhận |
| `khong-chac-lam-dung-khong-co-thoi-gian-sua-sai.md` | cần kiểm tra | cần xác nhận |
| `man-hinh-ap-luc-hoc-som-lam-hai-con.md` | cần kiểm tra | cần xác nhận |
| `muon-con-hanh-phuc-y-nghia-du-the-gioi-thay-doi.md` | cần kiểm tra | cần xác nhận |
| `muon-lam-cha-me-du-tot-khong-bo-lo-giai-doan-vang.md` | cần kiểm tra | cần xác nhận |
| `qua-ban-qua-met-khong-du-hien-dien-cho-con.md` | cần kiểm tra | cần xác nhận |
| `so-ai-thay-the-con-thieu-ky-nang.md` | cần kiểm tra | cần xác nhận |
| `so-lang-phi-giai-doan-vang-cua-con.md` | cần kiểm tra | cần xác nhận |

> ⚠️ Pillar cho từng file cần AI đọc nội dung thực tế rồi quyết định tại thời điểm thực thi. Không hardcode sẵn vì có thể sai nếu dựa trên tên file.

**TRƯỚC (ví dụ 1 file):**
```yaml
---
type: insight
insight_type: "DESIRE"
insight_name: "Muốn con hạnh phúc ý nghĩa dù thế giới thay đổi"
belongs_to_audience: "[[cap-vo-chong_tim-hieu-ve-nuoi-con_sap-co-con-hoac-dang-co-con-o-do-tuoi-0-7-tuoi]]"
status: processed
created: "2026-05-22"
source_type: "User"
source_name: "Persona Interview"
source_id: "persona-interview"
confidence: 1.0
vivid_insights: []
vivid_insights_reserve: []
---
```

**SAU (ví dụ — giả sử Pillar = "Cửa sổ vàng phát triển trẻ 0-7 tuổi"):**
```yaml
---
type: insight
insight_type: "DESIRE"
topics: ["nao_bo_tre_em", "gan_ket_an_toan", "trai_nghiem_giac_quan", "ngon_ngu_som", "phat_trien_tam_ly_tre", "dieu_hoa_cam_xuc", "khoa_hoc_than_kinh_ung_dung", "khung_hoang_cam_xuc", "ket_noi_truoc_khi_dieu_huong", "goi_ten_cam_xuc", "kich_hoat_nao_tang_tren", "tu_duy_logic_cho_tre", "dieu_hoa_qua_the_chat", "ung_pho_ky_uc_buon", "ren_luyen_tri_nho", "tinh_tam_thoi_cua_cam_xuc", "nhan_dien_the_gioi_noi_tam", "ky_nang_sift", "tu_xoa_diu_lo_au", "niem_vui_gia_dinh", "ky_nang_giai_quyet_xung_dot"]
belongs_to_audience: "[[cap-vo-chong_tim-hieu-ve-nuoi-con_sap-co-con-hoac-dang-co-con-o-do-tuoi-0-7-tuoi]]"
status: processed
created: "2026-05-22"
source_type: "User"
source_name: "Persona Interview"
source_id: "persona-interview"
confidence: 1.0
vivid_insights: []
vivid_insights_reserve: []
---
```

**Kiểm tra:** Mở file trong Obsidian → frontmatter không lỗi, không còn `insight_name`, có `topics` array.

---

**Hoàn thành Phase 1 → Chuyển sang Phase 2.**
