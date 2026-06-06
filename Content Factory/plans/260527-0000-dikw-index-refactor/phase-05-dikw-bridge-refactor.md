---
name: phase-05-dikw-bridge-refactor.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Phase
usage: Hướng dẫn thực thi Phase 5 — Refactor dikw-bridge/SKILL.md để dùng Get-DIKWCombo
output: SKILL.md mới với Bước 1-4 thay bằng tool call, Bước 5-6 giữ nguyên
logic: Thay thế nội dung Bước 1-4 bằng lệnh gọi script, giữ nguyên Bước 5-6
---

# Phase 05: DIKW Bridge SKILL.md Refactor

**Trạng thái:** ✅ Complete
**Nhóm BRIEF:** A (A4)
**Dependencies:** Phase 4 (cần Get-DIKWCombo.ps1 tồn tại và hoạt động)

---

## Task 5.1: Refactor Bước 1-4 trong `dikw-bridge/SKILL.md`

**File:** `.agents/skills/dikw-bridge/SKILL.md`

**Nguyên tắc:**
- Bước 1-4 (dòng 11-87) → thay bằng lệnh gọi `Get-DIKWCombo` duy nhất
- Bước 5 (dòng 88-121) → giữ nguyên, chỉ đổi context ("nhận output từ tool" thay vì "từ bước trước")
- Bước 6 (dòng 122-135) → giữ nguyên 100%

**NỘI DUNG MỚI cho Bước 1-4 (thay thế toàn bộ từ dòng 11 đến dòng 87):**

```markdown
### Bước 1: Tiếp nhận Context & Gọi Tool

1. Đọc `00-blackboard.yaml`:
   - `mapped_topics` (topic IDs — có thể là string hoặc array)
   - `Target_Audience` (Audience ID hoặc array Audience IDs)
   - `Target_Source_IDs` (mảng source_id, có thể rỗng)
   - `Persona_Path` → trích `[User]` (VD: `personas/Neal` → `Neal`)

2. Đọc kĩ `.agents/skills/dikw-bridge/references/injection-rules.md`.

3. **Gọi Tool Get-DIKWCombo** — lệnh duy nhất thay thế toàn bộ logic duyệt graph:

```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/dikw-bridge/scripts/Get-DIKWCombo.ps1" `
  -Topics "[mapped_topics]" `
  -Audience "[Target_Audience]" `
  -PersonaUser "[User]" `
  [-TargetSourceIds @("source1", "source2")]
```

> ⚠️ **TUYỆT ĐỐI KHÔNG** tự quét file, tự duyệt graph, tự viết script ad-hoc. Toàn bộ logic Pre-Filter, Lọc Nhánh, Scoring, Anti-Repetition đã được đóng gói trong tool.

4. Đọc output từ tool (stdout). Output gồm 3 phần:
   - **Bảng Combo**: Atom path | DIKW Layer | Weight | Relevance Score | Node Trỏ
   - **Vivid Payload JSON**: Minified JSON gộp vivid data
   - **resolved_jtbd** (nếu Target_Audience là array): audience_Job_performer, audience_main_job, audience_circumstance
```

**GIỚI HẠN THAY THẾ:** Chỉ thay nội dung từ `### Bước 1` đến hết `### Bước 4` (kể cả Thủ tục phụ Smart Global Pre-Filter). Giữ nguyên:
- Frontmatter YAML (dòng 1-5)
- `# DIKW Bridge Skill` (dòng 7)
- `## Hướng dẫn hoạt động` (dòng 9)
- `### Bước 5` trở đi (dòng 88+)

**Kiểm tra:**
- Đọc SKILL.md mới → flow rõ ràng: đọc blackboard → gọi tool → nhận output → Bước 5 format → Bước 6 persist.
- Bước 5, 6 không bị thay đổi bất kỳ dòng nào.
- Không còn reference đến "Quét 6 thư mục", "Parse frontmatter", "Get-Content" trong Bước 1-4.

---

## Task 5.2: Cập nhật `last_update` trong frontmatter

**File:** `.agents/skills/dikw-bridge/SKILL.md`

**Thay đổi dòng 4:**

**TRƯỚC:**
```yaml
last_update: 24/05/2026 16:55 (GMT+7)
```

**SAU:**
```yaml
last_update: [ngày thực thi]/05/2026 [giờ thực thi] (GMT+7)
```

**Thay đổi dòng 3 — cập nhật description:**

**TRƯỚC:**
```yaml
description: Skill đóng vai trò cầu nối, quét kho dữ liệu Obsidian (Vault) để tìm nguyên liệu liên quan đến topic và xếp thứ hạng theo mô hình DIKW.
```

**SAU:**
```yaml
description: Skill đóng vai trò cầu nối, gọi tool Get-DIKWCombo để tìm nguyên liệu liên quan đến topic trong Vault và xếp thứ hạng theo mô hình DIKW.
```

---

**Hoàn thành Phase 5 → Plan hoàn tất.**

## Checklist tổng kết sau khi hoàn thành tất cả Phases

- [ ] Template `insight.md` có `topics` + `source_id`, không còn `insight_name`
- [ ] `generate_insights.py` inject `topics` từ payload
- [ ] `persona-interviewer/SKILL.md` resolve topics tại Bước 2 Câu 11
- [ ] 8 file Schema B có `topics` đúng, không còn `insight_name`
- [ ] GI_ atoms có topics = topic_map.yaml IDs (không còn English IDs)
- [ ] `build-vault-index.ps1` chạy đúng, output `vault_index.json`
- [ ] `Get-DIKWCombo.ps1` chạy đúng 3 test cases
- [ ] `dikw-bridge/SKILL.md` Bước 1-4 thay bằng tool call, Bước 5-6 nguyên vẹn
- [ ] `bundle-atoms.ps1` vẫn hoạt động bình thường (test regex với path mới)
- [ ] Chạy `/content-post` end-to-end → DIKW Bridge tìm thấy atoms đúng
