---
name: Voice Writer
description: Skill Phase 5 — Viết bài hoàn chỉnh dựa trên Voice DNA, tiêm atoms theo DIKW, áp dụng Anti-AI scan.
last_update: 24/05/2026 14:30 (GMT+7)
required_inputs:
  - OUTLINE_SECTIONS         # from 04-outline.md (Phase 4)
  - CLOSING_COMBO            # from 04-outline.md (Phase 4)
  - PERSONA_DNA              # from 04.5-persona-pack.md (Phase 4.5)
  - EVIDENCE_LIST            # from 02-research-brief.md (Phase 2)
  - STORY_LIST               # from 02-research-brief.md (Phase 2)
  - dikw_combo               # 00.5-dikw-combo.md
provided_outputs:
  - DRAFT_SECTIONS
---

# Voice Writer (Phase 5)

> EXECUTION_KEY:

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện từ các phase trước đã được biên dịch sẵn trong `.temp/payload.md` (run folder). Đọc file này để lấy input từ phase trước. Các file khác (persona, references, logs) vẫn đọc trực tiếp theo hướng dẫn bên dưới.

1. **`Outline 5 phần`** (Phase 4)
2. **`Persona Pack`** (Phase 4.5 — đã có trong context)
3. **`Atomic Combo`** (Stories, Insight, Solutions, Concepts... từ Bước 5 của workflow)
4. **`Minified JSON Vivid Payload`** (từ Bước 5 của workflow)

## Hướng dẫn hoạt động

### Bước 1: Đọc tham chiếu BẮT BUỘC
Dùng tool `view_file` đọc lần lượt 5 file:
- `.agents/skills/voice-writer/references/writing-rules.md`
- `.agents/skills/voice-writer/references/anti-ai-rules.md`
- `.agents/skills/voice-writer/references/english-rules.md`
- `.agents/skills/voice-writer/references/typography-and-format.md`
- `.agents/skills/voice-writer/references/metaphor.md`

> ⛔ **FATAL RULE:** PHẢI dùng tool đọc thành công toàn bộ 5 file. File Not Found → DỪNG, BÁO USER. Cấm hallucinate nội dung.

Sau khi đọc mỗi file, ghi nhận giá trị `FILE_KEY` ở dòng cuối file đó.

Sau khi hoàn thành toàn bộ nội dung `05-draft.md`, append vào **cuối file** dòng:
```
<!-- ref_keys: writing-rules=[key1], anti-ai-rules=[key2], english-rules=[key3], typography-and-format=[key4], metaphor=[key5] -->
```
Thay [key1]...[key5] bằng đúng giá trị FILE_KEY đã đọc từ mỗi file.

### Bước 2: Nhận input
Trích xuất dữ liệu từ Global Context theo Điều kiện Đầu vào.
- Nếu Payload có khối `connection` (`IDEA_CONNECTION`) mang thông tin liên kết, hãy ĐỌC HIỂU Bản chất Mối nối Logic và sử dụng thông tin này linh hoạt ở phần Mở bài hoặc Chuyển ý để nhắc nhớ độc giả về bài trước đó, tạo mạch liền mạch cho kênh. Nếu có nhiều báo cáo liên kết, hãy tự do lựa chọn 1 mối nối phù hợp nhất.
**BẮT BUỘC**: Dùng tool `view_file` đọc file `00.5-dikw-combo.md` trong run folder để lấy dữ liệu thô của các Atoms và trích xuất mã `BUNDLE_KEY` ở cuối file.

### Bước 3: Viết bài section-by-section

> ⛔ **TUYỆT ĐỐI KHÔNG viết toàn bộ 1300-1800 từ trong 1 lượt.**

**3.0 — Word Budget:**
Đọc word count từ Outline (Phase 4). Nếu không có, dùng mặc định:

| Section | Từ |
|---------|-----|
| Hook | 100 |
| Story | 250 |
| Deep Dive | 800 |
| Pivot | 250 |
| Closing | 150 |

**3.0.1 — Hook Adaptation:**
Core Hook trong outline là nguyên liệu thô từ Hook Engineer — KHÔNG phải text cuối cùng. Khi viết section Hook, PHẢI:
1. Đọc `Hook Intent` và `Core Hook` từ outline
2. Viết lại câu hook bằng Voice DNA (pronoun, filler, tone, sentence rhythm), giữ nguyên Hook Intent và Formula
3. CẤM copy nguyên văn Core Hook vào draft

**3.1 — Viết từng section:**
Viết lần lượt 5 sections. TOÀN BỘ nội dung bài viết (từ dòng `<!-- TITLE: ... -->` đến hết Closing) BẮT BUỘC bọc trong `<!-- [BLOCK: DRAFT_SECTIONS] -->...<!-- [/BLOCK: DRAFT_SECTIONS] -->`. Mỗi section:
- Bám sát outline, nằm trong word budget
- Ghi vào `05-draft.md` trong run folder (section 1: overwrite, section 2-5: append). LUÔN viết đầy đủ structural markers (dạng HTML comment). Tất cả marker KHÔNG được đếm vào word count.

**Markers bắt buộc:**
- Dòng đầu tiên: `<!-- TITLE: [Tiêu đề bài viết] -->`
- Dòng cuối cùng của file 05-draft.md (sau khi kết thúc Closing và ghi các ref_keys): `<!-- bundle_key: [Mã trích xuất từ 00.5-dikw-combo.md] -->`
- Trước mỗi section: `<!-- SECTION: [Tên section] -->` (Hook/Story/Deep Dive/Pivot/Closing)
- Sau SECTION marker: `<!-- SECTION_HEADING: [Heading section — AI tự đặt] -->`
- Trước mỗi đoạn: `<!-- PARAGRAPH: [Số thứ tự đoạn — đánh số liên tục 1→N trên toàn bài] -->`
- Sau PARAGRAPH marker: `<!-- PARAGRAPH_HEADING: [Heading đoạn — AI tự đặt] -->`
- Kết thúc mỗi section (trừ section cuối): marker `⁂` trên 1 dòng riêng, cách dòng trên 1 dòng trống, cách dòng dưới 1 dòng trống
- Trước khi viết section tiếp, đọc lại section vừa viết để đảm bảo transition tự nhiên

**3.2 — Kiểm tra toàn bài:**
Đọc lại `05-draft.md` → kiểm tra transitions + tổng word count (mục tiêu: 1300-1800 từ, ưu tiên ngữ nghĩa hơn con số tuyệt đối).

**Constraints áp dụng cho MỖI section:**

| Constraint | Quy tắc |
|------------|---------|
| **Voice DNA** (AUTO-FAIL) | Đúng pronoun từ `voice-dna.yaml`. Rải fillers 3-5 lần/bài. Không dùng `banned_words`. Áp dụng `sentence_rhythm`, `analogy_style`, `closing_style`, `humor_style` |
| **JTBD Phân Rã** (AUTO-FAIL) | Không ghép chuỗi tĩnh 3 tham số JTBD — xem bảng biến thiên bên dưới. Vi phạm → REVISE toàn đoạn |
| **Atom Injection** | Story → viết lại theo subtype (xem writing-rules.md Section 3). Solution/Concept → KCS credibility intro. Không có atom → bỏ qua, KHÔNG BỊA |
| **VTS v19.0** | Mỗi đoạn PHẢI có value signal. Phân bổ theo section — xem writing-rules.md Section 4. Gap > 5 câu = bị QA phạt |
| **SAS v18.2** (AUTO-FAIL) | CHỈ dùng stories từ Vault (verified) HOẶC người/tổ chức nổi tiếng thế giới. Vault trống → famous world stories + ghi nguồn. Không story phù hợp → viết bằng data/research. KHÔNG BỊA |
| **KCS** | Mọi Solution/Concept PHẢI có ≥1: Ai tạo + credential / Ai dùng thành công + kết quả / Bao nhiêu người áp dụng |
| **Authority Citation** | Áp dụng Credential Cascade theo writing-rules.md Section 7. Đa dạng cách giới thiệu expert |
| **Vivid Extrapolation** | Tuân thủ 2 kịch bản tại writing-rules.md Section 6. BẮT BUỘC áp dụng 1 trong 3 cấu trúc ẩn dụ (Extended, Compounding, Loop) từ metaphor.md nếu có yếu tố ẩn dụ. Cấm ẩn dụ sáo rỗng |
| **Anti-AI** | Quét 10 patterns + blacklist + AI detection. Đặc biệt: Cấm AI Labels (Key, Note, Summary). Cấm lạm dụng từ nối (>3 lần/bài). Cấm trộn tiếng Anh. |
| **Killer Statements** | ≥ 2 câu khẳng định mạnh, đáng nhớ mỗi bài |
| **Paragraph** | 8-10 câu/paragraph. Không viết paragraph 1 câu (trừ Hook câu đầu tiên). Không viết paragraph > 10 câu. LƯU Ý: Đoạn mới CHỈ bắt đầu khi có marker `<!-- PARAGRAPH: N -->`. |
| **Chain** | BẮT BUỘC bấm ENTER (xuống dòng) để ngắt câu thành các chuỗi 1-2 câu/dòng. Có 3-5 chuỗi dài (3-5 câu/dòng) toàn bài. Xem writing-rules.md Section 9 |
| **Prose & Punc** (AUTO-FAIL) | Không dùng Title Case (H2+ viết hoa chữ đầu). Không dấu hai chấm trong tiêu đề. Dấu câu sát từ trước, cách từ sau. Cấm em-dash `—` (đổi sang từ nối hoặc ` - `). Cấm Oxford comma `, và`. Cấm Bullet trong thân văn xuôi. Độ dài đoạn văn phải biến thiên, tránh các đoạn liên tiếp có số câu bằng nhau. |

**Bảng biến thiên JTBD (Deconstructed):**

| Biến | Cấm | Phải |
|------|-----|------|
| `audience_Job_performer` | Ghép nguyên chuỗi | Biến thiên: "bố mẹ", "phụ huynh", "chúng ta"... |
| `audience_main_job` | Ghép nguyên chuỗi | Biến thiên động từ: "thiết lập nếp", "tập tự ngủ"... |
| `audience_circumstance` | Ghép nguyên chuỗi | Biến thiên trạng từ: "giai đoạn này", "đối với độ tuổi sơ sinh"... |

### Bước 4: Scripted Validation
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/voice-writer/scripts/validate-draft.ps1" -DraftPath "[Đường dẫn file Draft]"
```
Script kiểm tra 10 chỉ số objective. Nếu FAIL → **sửa ngay** trước khi tiếp tục.

### Bước 5: Self-Check Gate

> ⛔ **KHÔNG ĐƯỢC BỎ QUA.** Kiểm soát chất lượng cuối cùng trước Phase 6.

**Điều kiện tiên quyết:** Script validation Bước 4 PHẢI đạt `ALL OBJECTIVE CHECKS PASSED`.

**Tiêu chí kiểm tra:**

| Check | Tiêu chí | Rollback |
|-------|----------|----------|
| Voice DNA | 100% pronoun/filler/tone compliance | → REVISE, quay Bước 3 |
| Anti-AI | Zero AI signatures (10 patterns) | → REVISE, quay Bước 3 |
| Vivid | Neo chặt JSON Vivid gốc hoặc phóng tác 5 giác quan. Tuân thủ 3 cấu trúc ẩn dụ từ metaphor.md (Extended, Compounding, Loop). Cấm ẩn dụ sáo rỗng | → REVISE, quay Bước 3 |
| Engagement | Không gap > 5 câu liên tiếp không value signal | → REVISE, quay Bước 3 |
| Killer Statements | ≥ 2 câu mạnh, đáng nhớ | → REVISE, quay Bước 3 |
| Atom Integrity | No fabricated atoms, all verified | → REVISE, quay Bước 3 |
| SAS v18.2 | Mọi story trace back: ① vault, ② famous person/org + nguồn, ③ published book + tác giả. Bịa = AUTO-FAIL | → FAIL, escalate User |
| KCS v18.2 | Mọi Solution/Concept có credibility intro (origin/achievement/scale) | → REVISE, quay Bước 3 thêm credibility intro |
| JTBD | Không chứa chuỗi tĩnh JTBD | → REVISE, quay Bước 3 |
| VN Standards | Đúng chuẩn viết hoa (H2+), không trộn tiếng Anh, Prose format (không bullet), Punctuation chuẩn | → REVISE, quay Bước 3 |

**Verdict:**
- **PASS** → Chuyển Phase 6.
- **REVISE** → Ghi issues vào `output/runs/[run-folder]/gate5-issues.md` → Revision Mode. Max 3 retry.
- **FAIL** (SAS violation) → Dừng pipeline, escalate User.

**Ghi log:** `[Phase 5 Self-Check] Verdict: PASS/REVISE/FAIL | Attempt: N/3`

### Bước 6: Issue Tracking (khi REVISE)
Ghi vào `output/runs/[run-folder]/gate5-issues.md`:
```yaml
## Round N
- id: ISSUE_NAME
  location: "paragraph X, câu Y-Z"
  criteria: "Tiêu chí vi phạm"
  severity: HIGH/MEDIUM
  status: OPEN
```

### Bước 7: Revision Mode (khi có issues OPEN)
1. Đọc `gate5-issues.md` → lọc `status: OPEN`.
2. Với mỗi issue: đọc location → tìm vị trí trong `05-draft.md` → sửa theo criteria.
3. Ghi đè `05-draft.md`. **KHÔNG viết lại toàn bộ draft** — chỉ sửa đúng vị trí issue.
4. Chạy lại `validate-draft.ps1`.
5. Quay Bước 5 verify: Fix → `VERIFIED` ✅ / Chưa fix → `OPEN` ❌
6. Tất cả VERIFIED → PASS. Còn OPEN → thêm round (max 3).
