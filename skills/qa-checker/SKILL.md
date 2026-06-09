---
name: QA Checker
description: Skill Phase 6 — Chấm điểm bài viết theo 4 sections, tổng 130 điểm. Quyết định PASS/REVISE/FAIL.
last_update: 05/05/2026 18:11 (GMT+7)
required_inputs:
  - DRAFT_SECTIONS           # from 05-draft.md (Phase 5)
  - persona_voice_dna        # [Persona_Path]/voice-dna.yaml (WR-03 verification)
  - persona_scoring_rules    # [Persona_Path]/scoring-rules.yaml (pass_threshold)
provided_outputs:
  - QA_REPORT
---

# QA Checker (Phase 6)

> EXECUTION_KEY: e5f6d9a1

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện từ các phase trước đã được biên dịch sẵn trong `.temp/payload.md` (run folder). Đọc file này để lấy input từ phase trước. Các file khác (persona, references, logs) vẫn đọc trực tiếp theo hướng dẫn bên dưới.

> ⛔ **DEFAULT DENY:** Để chấm điểm khách quan, CẤM đọc các file sau trong Run Folder:
> `01-idea-brief.md`, `03-hook.md`, `04-outline.md`, `gate5-issues.md`, `gate6-issues.md`.
> Lưu ý: TUYỆT ĐỐI KHÔNG dùng nội dung `02-research-brief.md` để thiên vị đánh giá (ngoại trừ việc đọc `02-research-brief.md` trực tiếp để thực hiện Atom Attribution Check CT-05).

## Quy trình

1. Trích xuất Draft từ Bảng đen.
2. Chấm từng rule theo bảng dưới đây.
3. Cộng tổng (/130), xác định verdict.
4. Thực hiện Atom Attribution Check (xem CT-05 bên dưới).
5. Liệt kê chi tiết lỗi cần sửa (nếu REVISE).

**Ghi log:** `[Phase 6 Self-Check] Score: X/130 | Verdict: PASS/REVISE/FAIL | Attempt: N of 3`

**Output:** `06-qa-result.md` — TOÀN BỘ nội dung chấm điểm BẮT BUỘC bọc trong `[BLOCK: QA_REPORT]...[/BLOCK: QA_REPORT]`. Cuối file BẮT BUỘC append: `<!-- persona_keys: voice-dna=[key], scoring-rules=[key] -->` (lấy giá trị `# FILE_KEY:` đã ghi nhận ở WR-03 và Verdict).

---

## Bảng chấm điểm (130đ)

### Voice DNA (30đ)

| Rule | Điểm | Kiểm tra |
|------|------|----------|
| WR-01 | 10đ | Pronoun đúng xuyên suốt |
| WR-02 | 5đ | Fillers xuất hiện 3-5 lần tự nhiên |
| WR-03 | 5đ | Core tone đủ phổ — xem **WR-03 Protocol** bên dưới |
| WR-04 | 5đ | Engagement phrases (hỏi reader) ≥ 2 |
| WR-05 | 5đ | Không dùng banned words |

**Auto-fail:** Sai pronoun, thiếu filler.

#### WR-03 Verification Protocol

1. Đọc `[Persona_Path]/voice-dna.yaml` (lấy `Persona_Path` từ Bảng đen). Trích xuất `tone.primary` để xác định các trụ tone. Ghi nhận giá trị `# FILE_KEY:` trong file.
2. **Bằng chứng ngôn ngữ:** Trích dẫn nguyên văn 1 câu hoàn chỉnh từ draft thể hiện MỖI trụ:
   - `[trụ-tone]: "câu trích dẫn"`
   - Nếu draft thực sự thiếu tone đó → khai báo `[trụ-tone]: KHÔNG TÌM THẤY` (không cần chạy tool).
3. **Scripted Verification:** Từ mỗi câu ở bước 2, bóc ra **cụm từ liên tục 7-12 từ, nằm trọn 1 dòng, không chứa format**. Chạy:
   ```
   grep_search(query="cụm từ trích xuất", file="vault/.content-pipeline/runs/[run-folder]/05-draft.md")
   ```
   - Có kết quả → Pass trụ đó.
   - Không tìm thấy → Fail trụ đó (bịa đặt).
4. **Tính điểm:**
   - Pass tất cả: 5đ
   - Fail 1 trụ: Trừ 2đ
   - Fail ≥2 trụ hoặc bịa trích dẫn: 0đ toàn WR-03

### Anti-AI (20đ)

| Rule | Điểm | Kiểm tra |
|------|------|----------|
| AI-01 | 5đ | Không dash connector |
| AI-02 | 5đ | Không Micro-staccato |
| AI-03 | 5đ | Không anaphora |
| AI-05 | 5đ | Language purity (không English lóng) |

**Auto-fail:** Bất kỳ pattern AI nào (5 items trên).

### Content (60đ)

| Rule | Điểm | Kiểm tra |
|------|------|----------|
| CT-01 | 10đ | Hook score ≥ 8 (từ Phase 3) |
| CT-02 | 10đ | Authority citations ≥ 2 |
| CT-03 | 10đ | Killer Statements & Punchline từ 2-3 |
| CT-04 | 10đ | Cross-check Vector Vivid (Fail nếu lạm dụng Extrapolate lệch chuẩn so với Constraint-based Improvise) |
| CT-05 | 10đ | Story verified (SAS pass) — xem **Atom Attribution Check** bên dưới |
| CT-06 | 10đ | Số lượng Vivid ≥ 3 |

**Auto-fail:** Engagement gap, fabricated story.

#### Atom Attribution Check (CT-05)

> ⛔ **FATAL RULE:** Đọc content atom từ `02-research-brief.md` (đã có trong Điều kiện Đầu vào).
> TUYỆT ĐỐI KHÔNG đọc file atom vật lý — brief đã chứa full body text nguyên văn.

> **Poka-Yoke:** Số "Block đối chất" trong `06-qa-result.md` PHẢI BẰNG CHÍNH XÁC số UNIQUE path `[Atom: ...]`
> (trừ `[Atom: none]`) trong Research Brief. Thiếu 1 block = FAIL CT-05 (0đ).

Với mỗi UNIQUE `[Atom: đường-dẫn]` path trong `02-research-brief.md` (trừ `none`):
(Nếu cùng path xuất hiện nhiều lần — e.g., cả trong Evidence List lẫn Số liệu — chỉ xuất ĐÚNG 1 Block,
dùng body content ở lần xuất hiện đầu tiên có full text, thường là trong Evidence List / Story List.)
1. Đọc phần body content ngay sau tag đó trong brief.
2. Xuất Block đối chất:
   - **Draft Claim:** [Tóm tắt sự kiện như viết trong draft]
   - **Vault Fact:** [Trích dẫn nguyên văn 1-2 câu từ body content trong brief]
   - **Discrepancy Analysis:** [Phóng đại/bịa đặt/sai lệch so với brief?]
   - **CT-05 Score:** [KHÔNG sai lệch → điểm tối đa | CÓ sai lệch → 0đ, trigger REVISE]

### Poetic (20đ)

| Rule | Điểm | Kiểm tra |
|------|------|----------|
| PM-01 | 5đ | Emotional adjectives đa dạng |
| PM-02 | 5đ | Sting test: ≥ 1 câu gây "nhói" |
| PM-03 | 5đ | Verb diversity (không lặp động từ) |
| PM-04 | 5đ | Redefinition: ≥ 1 câu tái định nghĩa khái niệm |

---

## Verdict

Đọc `pass_threshold` từ `[Persona_Path]/scoring-rules.yaml` (lấy `Persona_Path` từ Bảng đen). Ghi nhận giá trị `# FILE_KEY:` trong file.

| Điều kiện | Verdict | Hành động |
|-----------|---------|-----------|
| ≥ pass_threshold + 0 auto-fail | PASS | → Phase 7 |
| pass_threshold − 10 đến pass_threshold − 1 | REVISE | Ghi issues vào `gate6-issues.md` |
| < pass_threshold − 10 | FAIL | Escalate User |

### Scripted Validation
Chạy:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/qa-checker/scripts/validate-qa.ps1" -QAResultPath "[Đường dẫn 06-qa-result.md]"
```
- Exit code = 0 → tiếp tục.
- Exit code > 0 → kiểm tra output, sửa lỗi verdict/score, chạy lại.

### Format gate6-issues.md (nếu REVISE)

```yaml
## Round N
- id: ISSUE_NAME
  location: "section/paragraph cụ thể"
  criteria: "Tiêu chí vi phạm + điểm trừ"
  severity: HIGH/MEDIUM
  status: OPEN
```
