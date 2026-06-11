---
name: Insight Agent
description: Skill Phase 2 — Thu thập dẫn chứng, studies, expert quotes. Áp dụng SAS chống bịa và KCS cho framework.
last_update: 05/05/2026 13:13 (GMT+7)
required_inputs:
  - CONTRARIAN_ANGLE         # from 01-idea-brief.md (Phase 1)
  - CORE_TENSION             # from 01-idea-brief.md (Phase 1)
  - HIDDEN_BELIEF            # from 01-idea-brief.md (Phase 1)
  - blackboard               # 00-blackboard.yaml
  - dikw_combo               # 00.5-dikw-combo.md
  - persona_authorities      # [Persona_Path]/authorities.yaml
provided_outputs:
  - EVIDENCE_LIST
  - EXPERT_QUOTES
  - STORY_LIST
---

# Insight Agent Skill (Phase 2)

> EXECUTION_KEY:

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện từ các phase trước đã được biên dịch sẵn trong `.temp/payload.md` (run folder). Đọc file này để lấy input từ phase trước. Các file khác (persona, references, logs) vẫn đọc trực tiếp theo hướng dẫn bên dưới.

Từ Bảng đen (Global Context), TUYỆT ĐỐI CHỈ truy xuất 2 khối:
1. **`Idea Brief`** (Phase 1 Idea Curator).
2. **`[3-5 Data-Points hoặc Quotes]`** (từ Gói nguyên liệu DIKW).

## SAS v18.2 — Hệ thống chống bịa chuyện

**Chỉ 3 nguồn story hợp lệ:**
1. **Vault verified**: Story/data trong `vault/01-Atomic/` với `verified: true` → tag `source: vault`.
2. **Famous World**: Nhân vật/sự kiện nổi tiếng thế giới (Ray Dalio, Steve Jobs, Daniel Kahneman...) → tag `source: famous`.
3. **Published Book**: Câu chuyện từ sách đã xuất bản, ghi rõ tác giả + tên sách → tag `source: book`.

**AUTO-FAIL:**
- Bịa story: "Tôi có một người bạn tên A..."
- Số liệu không nguồn: "Theo nghiên cứu gần đây, 87% người..."
- Trích dẫn giả: Gán lời cho chuyên gia chưa từng nói.
- ⛔ Người Việt KHÔNG có trong vault → KHÔNG dùng.

Vault trống story → dùng famous world / published book / hoặc viết bằng data-research. TUYỆT ĐỐI KHÔNG BỊA.

## KCS — Knowledge Credibility System

Mỗi khi nhắc Solution/Concept/Framework trong bài, BẮT BUỘC có ≥ 1 Credibility Intro:

| Loại | Fuzzy Definition | Ví dụ |
|------|-----------------|-------|
| **Origin** | Ai/tổ chức nào tạo ra? Bối cảnh uy tín nào đúc kết ra? | "Mô hình DIKW được Kenneth Boulding đề xuất từ 1955..." |
| **Achievement** | Giải quyết bài toán cụ thể nào? Tác động thực tế? | "OKR mà Google dùng quản trị suốt 20 năm qua..." |
| **Scale** | Phổ biến bao nhiêu người/tổ chức? Ảnh hưởng bao nhiêu %? | "Pomodoro được hơn 2 triệu người trên thế giới sử dụng..." |

## Hướng dẫn hoạt động

### Bước 1: Nhận input
Trích xuất Idea Brief + Gói nguyên liệu DIKW từ Bảng đen (Global Context).
**BẮT BUỘC**: Dùng tool `view_file` đọc file `00.5-dikw-combo.md` trong run folder để lấy dữ liệu thô của các Atoms và trích xuất mã `BUNDLE_KEY` ở cuối file.

### Bước 2: Thu thập dẫn chứng
1. Đọc `[Persona_Path]/authorities.yaml` → tìm experts phù hợp topic.
2. Thu thập tối thiểu: **2 studies/data points**, **1 expert authority**, **5 con số cụ thể**.
3. Áp dụng **SAS v18.2** (xem section trên) cho mọi dẫn chứng.
4. Áp dụng **KCS** (xem section trên) cho mỗi framework/concept.
5. Lấy **Atom path** từ cột 1 bảng Gói DIKW — dùng cho `view_file` ở Bước 3.

### Bước 3: Xuất Research Brief

> ⛔ **FATAL RULE:** BẮT BUỘC dùng dữ liệu thô của các Atoms đã đọc từ file `00.5-dikw-combo.md` để điền vào phần dưới (Cấm tóm tắt từ memory hoặc tự bịa dẫn chứng).

Output file `02-research-brief.md` — mỗi phần BẮT BUỘC bọc trong thẻ `[BLOCK: TÊN]...[/BLOCK: TÊN]`:
- `[BLOCK: EVIDENCE_LIST]` — Bao bọc toàn bộ section Evidence List + Số liệu cụ thể
- `[BLOCK: EXPERT_QUOTES]` — Bao bọc toàn bộ section Expert Quotes
- `[BLOCK: STORY_LIST]` — Bao bọc toàn bộ section Story List

Theo format:

#### Evidence List (Studies & Numbers)

Với mỗi data-point atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]**
[Paste TOÀN BỘ body text của atom, NGUYÊN VĂN]

Không có atom từ vault → `[Atom: none]` + ghi fact với nguồn rõ ràng.

**Số liệu cụ thể (≥5):**
- [số + đơn vị]: [mô tả ngắn] `[Atom: [path — PHẢI TRÙNG với path trong Evidence List]]`
- [số + đơn vị]: [mô tả ngắn] `[Atom: none]`  ← nếu từ nguồn ngoài vault

#### Expert Quotes

Với mỗi quote atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]**
[Paste TOÀN BỘ body text của atom, NGUYÊN VĂN]
— [Tên tác giả], [Credential ngắn]

Không có atom từ vault → trích dẫn từ sách/nguồn đã xuất bản, ghi rõ nguồn.

#### Story List

Với mỗi story atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]** | source: [vault/famous/book]
**[Situation]** [Nội dung <situation> từ atom, nguyên văn]
**[Problem]** [Nội dung <problem> từ atom, nguyên văn]
**[Turning Point]** [Nội dung <turning_point> từ atom, nguyên văn]
**[Outcome]** [Nội dung <outcome> từ atom, nguyên văn]
**[Lesson]** [Nội dung <lesson> từ atom, nguyên văn]

Không có atom từ vault → dùng famous world/published book, ghi rõ nguồn, `[Atom: none]`.

Dòng cuối cùng của file 02-research-brief.md: `<!-- bundle_key: [Mã trích xuất từ 00.5-dikw-combo.md] -->`

#### SAS & KCS Status
- SAS status: PASS / FAIL
- KCS status: PASS / FAIL

#### Knowledge Credibility System (KCS)
[Framework + Origin/Achievement/Scale đủ theo chuẩn KCS]

### Bước 4: Validation + Gate

**Chạy script:**
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/insight-agent/scripts/validate-research.ps1" -ResearchPath "[Đường dẫn file Research Brief]"
```

**Verdict** (dựa trên script exit code):
- Exit code = 0 → **PASS** → Chuyển Phase 3.
- Exit code > 0 → **REVISE** → Quay bước 2, bổ sung dẫn chứng. Tối đa 2 lần retry.
- FAIL 2 lần → Dừng pipeline, escalate cho User.

**Ghi log:** `[Phase 2 Gate] Verdict: PASS/REVISE | Attempt: N/2`
