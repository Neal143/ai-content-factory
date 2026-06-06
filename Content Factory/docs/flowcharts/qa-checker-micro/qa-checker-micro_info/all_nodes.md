# Giải thích các Node QA Checker

## extract_draft
Bước 1: Trích xuất Draft từ Bảng đen.
`⛔ DEFAULT DENY:` Để chấm điểm khách quan, CẤM đọc các file sau trong Run Folder: `01-idea-brief.md`, `03-hook.md`, `04-outline.md`, `gate5-issues.md`, `gate6-issues.md`.
Lưu ý: TUYỆT ĐỐI KHÔNG dùng nội dung `02-research-brief.md` để thiên vị đánh giá.

## score_rules
Bước 2: Chấm từng rule theo bảng điểm (Tổng 130đ).

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
   grep_search(query="cụm từ trích xuất", file="output/runs/[run-folder]/05-draft.md")
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
| AI-01 | 4đ | Không dash connector |
| AI-02 | 4đ | Không staccato / micro-staccato |
| AI-03 | 4đ | Không anaphora |
| AI-04 | 4đ | Không repetitive pattern |
| AI-05 | 4đ | Language purity (không English lóng) |

**Auto-fail:** Bất kỳ pattern AI nào (5 items trên).

### Content (60đ)
| Rule | Điểm | Kiểm tra |
|------|------|----------|
| CT-01 | 10đ | Hook score ≥ 8 (từ Phase 3) |
| CT-02 | 10đ | Authority citations ≥ 2 |
| CT-03 | 10đ | Killer statements ≥ 2 |
| CT-04 | 10đ | Cross-check Vector Vivid (Fail nếu lạm dụng Extrapolate lệch chuẩn so với Constraint-based Improvise) |
| CT-05 | 10đ | Story verified (SAS pass) — xem **Atom Attribution Check** bên dưới |
| CT-06 | 10đ | Số lượng Vivid ≥ 3 |

**Auto-fail:** Engagement gap, fabricated story.

### Poetic (20đ)
| Rule | Điểm | Kiểm tra |
|------|------|----------|
| PM-01 | 5đ | Emotional adjectives đa dạng |
| PM-02 | 5đ | Sting test: ≥ 1 câu gây "nhói" |
| PM-03 | 5đ | Verb diversity (không lặp động từ) |
| PM-04 | 5đ | Redefinition: ≥ 1 câu tái định nghĩa khái niệm |

## atom_check
Bước 4: Thực hiện Atom Attribution Check (CT-05).
`⛔ FATAL RULE:` Đọc content atom từ `02-research-brief.md` (đã có trong Đầu vào). TUYỆT ĐỐI KHÔNG đọc file atom vật lý.
- Với mỗi UNIQUE `[Atom: đường-dẫn]` (trừ `none`), xuất Block đối chất:
  - **Draft Claim:** [Tóm tắt sự kiện như viết trong draft]
  - **Vault Fact:** [Trích dẫn nguyên văn 1-2 câu từ body content trong brief]
  - **Discrepancy Analysis:** [Phóng đại/bịa đặt/sai lệch so với brief?]
  - **CT-05 Score:** [KHÔNG sai lệch → tối đa | CÓ sai lệch → 0đ, trigger REVISE]

## determine_verdict
Bước 3 & 5: Cộng tổng điểm và xác định Verdict. Đọc `pass_threshold` từ `[Persona_Path]/scoring-rules.yaml`. Ghi nhận giá trị `# FILE_KEY:` trong file.

| Điều kiện | Verdict | Hành động |
|-----------|---------|-----------|
| ≥ pass_threshold + 0 auto-fail | PASS | → Phase 7 |
| pass_threshold − 10 đến pass_threshold − 1 | REVISE | Ghi issues vào `gate6-issues.md` |
| < pass_threshold − 10 | FAIL | Escalate User |

Ghi `06-qa-result.md` (Append: `<!-- persona_keys: voice-dna=[key], scoring-rules=[key] -->`).
Ghi log: `[Phase 6 Self-Check] Score: X/130 | Verdict: PASS/REVISE/FAIL | Attempt: N/3`.

## ref_draft
File đầu vào (BẮT BUỘC): `05-draft.md` (Bài viết cần chấm điểm).

## ref_research
File đầu vào (BẮT BUỘC): `02-research-brief.md` (Dùng để đếm `[Atom: ...]`).

## ref_rules
File cấu hình (BẮT BUỘC): `[Persona_Path]/scoring-rules.yaml` (Dùng để lấy `pass_threshold` và kiểm tra `FILE_KEY`).

## ref_dna
File cấu hình (BẮT BUỘC): `[Persona_Path]/voice-dna.yaml` (Dùng để kiểm tra `FILE_KEY` và đối chiếu Voice DNA).

## validate_script
Bắt đầu chạy script: `powershell -ExecutionPolicy Bypass -File ".agents/skills/qa-checker/scripts/validate-qa.ps1" -QAResultPath "[Đường dẫn 06-qa-result.md]"`

## check_score
**CHECK 1: KIỂM TRA ĐIỂM SÀN (Score Threshold Compliance)**
Đọc `pass_threshold` từ rules. Regex quét file QA lấy `(\d+)\s*/\s*(\d+)`. Điểm thực tế phải `>=` điểm sàn.

## check_verdict
**CHECK 2: TÍNH NHẤT QUÁN CỦA PHÁN QUYẾT (Verdict Consistency)**
Regex `(?i)VERDICT:\s*(PASS|REVISE|FAIL)`. Nếu Điểm >= Điểm sàn → PASS, Điểm sàn - 10 → REVISE, thấp hơn → FAIL. Chữ verdict AI ghi phải khớp với verdict tính từ toán học.

## check_atom
**CHECK 3: ĐỐI CHIẾU ATOM (Poka-Yoke)**
Đếm số lượng UNIQUE `[Atom: ...]` (trừ none) trong `02-research-brief.md` bằng số lần xuất hiện của cụm `Vault Fact\s*:` trong `06-qa-result.md`. Thiếu 1 block = FAIL CT-05 (0đ).

## check_keys
**CHECK 4: FILE_KEY PERSONA (Proof of Read)**
Regex `(?i)<!--\s*persona_keys:\s*voice-dna=(\w+),\s*scoring-rules=(\w+)\s*-->`. Phải khớp `# FILE_KEY:` từ `voice-dna.yaml` và `scoring-rules.yaml`. Cấm PENDING.

## revise_result
Nếu Exit code > 0 ở bất kỳ rào cản nào: Kiểm tra output của script, sửa lỗi verdict/score trong file kết quả (nếu AI tính sai toán hoặc đếm thiếu block), sau đó tự động chạy lại script `validate-qa.ps1`.
