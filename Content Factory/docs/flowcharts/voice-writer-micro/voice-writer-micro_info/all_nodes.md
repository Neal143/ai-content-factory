# Giải thích các Node Khởi tạo và Viết nháp

## read_refs
Bước 1: Đọc tham chiếu BẮT BUỘC.
Dùng tool `view_file` đọc lần lượt 3 file tham chiếu. Ghi nhận `FILE_KEY` ở dòng cuối mỗi file.

## ref_rules
Quy định từ `.agents/skills/voice-writer/references/writing-rules.md` (Verbatim 100%):
1. Voice DNA Application
- Dùng đúng pronoun từ `voice-dna.yaml`: `voice.pronouns.self`, `voice.pronouns.audience`, `voice.pronouns.expert_after_intro`. Sai pronoun = AUTO-FAIL.
- Rải fillers tự nhiên theo `voice.fillers.min_per_post` → `voice.fillers.max_per_post`.
- Tuyệt đối không dùng từ trong `voice.anti_patterns.banned_words`.
- Rải parentheticals nếu `voice.parentheticals.enabled: true`.
2. Engagement Rules
- Tần suất engage reader theo `voice.engagement.frequency`.
- Dùng patterns từ `voice.engagement.patterns`.
- Nếu vượt quá `max_gap` câu liên tiếp không engage → QA phạt.
3. Story Rewriting — 5 Subtypes
- personal: Ngôi 1, cảm xúc sâu.
- observed: Ngôi 3, thân mật.
- secondhand: Attribution rõ.
- historical: Ngắn gọn.
- famous_world: Người/tổ chức nổi tiếng thế giới + trích nguồn.
4. VTS v19.0 — Value Threading (BẮT BUỘC)
Mỗi cụm 3-5 câu PHẢI có ít nhất 1 value signal. Phân bổ: Hook (Value Promise), Story (Result Preview), Deep Dive (Pain Avoidance + Value Promise), Pivot (Social Proof + Value Promise), Closing (Result Preview / Personal Commitment).
5. Killer Statements
Mỗi bài cần ≥ 2 "Killer Statements".
6. Constraint-based Improvise
- Có Vivid: Phóng tác chi tiết vệ tinh, CẤM phát minh quy chiếu xa lạ.
- Khuyết Vivid: Phóng tác Cảm giác từ Logic. TUYỆT ĐỐI CẤM DÙNG tu từ, so sánh hay ẩn dụ sáo rỗng.
7. Authority Citation — Credential Cascade
- Đa dạng hóa theo `citation_patterns` và tuân thủ `diversity_rule`.
8. Word Count: 1500-1800 từ. KHÔNG quá 1800 từ.

## ref_anti_ai
Quy định từ `.agents/skills/voice-writer/references/anti-ai-patterns.md` (Verbatim 100%):
⛔ AUTO-FAIL (5 patterns — phát hiện 1 cái = fail ngay):
1. Dash Connector ("X - Y - Z")
2. Staccato ("Sáng mở mắt. Cả ngày chạy. Tối nằm.")
3. Micro-Staccato ("Đổi đời luôn. Một. Viết ra giấy.")
4. Anaphora ("Không X. Không Y. Không Z.")
5. Repetitive ("X là vốn. Y là vốn. Z là vốn.")
⚠️ HIGH-RISK (5 patterns — cộng dồn ≥ 3 = fail):
6. QA Pattern ("Kết quả? Bất ngờ lắm.")
7. Numbered Lists ("1. Làm A. 2. Làm B.")
8. Logic Symbols ("X + Y = Thành công")
9. Generic Transitions ("Đầu tiên... Tiếp theo... Cuối cùng...")
10. Metaphor Stack (3+ ẩn dụ chồng chất)
Giới hạn: Max 3 dấu `...` và Max 3 dấu `!` mỗi bài.

## ref_blacklist
Quy định từ `.agents/skills/voice-writer/references/english-blacklist.md` (Verbatim 100%):
Từ cấm: mindset, team, level up, focus, passion, content, viral, hustle, deadline, feedback, skill, trend, insight, networking. Ngoại lệ: Tên riêng và thuật ngữ chuyên ngành (marketing, startup).

## fail_read_refs
`⛔ FATAL RULE`: PHẢI dùng tool đọc thành công cả 3 file tham chiếu. Nếu File Not Found → DỪNG, BÁO USER. Cấm hallucinate nội dung.

## extract_input
Bước 2: Nhận input (Trích xuất từ Global Context).
1. `Outline 5 phần` (Phase 4)
2. `Persona Pack` (Phase 4.5)
3. `Atomic Combo`
4. `Minified JSON Vivid Payload`

## write_draft
Bước 3: Viết bài section-by-section.
Tuyệt đối KHÔNG viết toàn bộ 1500-1800 từ trong 1 lượt.
**Word Budget:**
Hook (100), Story (250), Deep Dive (800), Pivot (250), Closing (150).

Quy tắc JTBD (Deconstructed):
- `audience_Job_performer`: Cấm ghép nguyên chuỗi, Phải biến thiên (vd: "bố mẹ", "chúng ta").
- `audience_main_job`: Cấm ghép nguyên chuỗi, Phải biến thiên động từ.
- `audience_circumstance`: Cấm ghép nguyên chuỗi, Phải biến thiên trạng từ.

Ghi vào `05-draft.md` trong run folder. Section 1 overwrite, section 2-5 append. Mỗi section kết thúc bằng 1 dòng trống.
Append cuối file (sau khi hoàn thành toàn bộ):
<!-- ref_keys: writing-rules=[key1], anti-ai=[key2], english-blacklist=[key3] -->

## validate_script
Bước 4: Scripted Validation.
Chạy script: `powershell -ExecutionPolicy Bypass -File ".agents/skills/voice-writer/scripts/validate-draft.ps1" -DraftPath "[Đường dẫn file Draft]"`

## check_format
Kiểm tra cấu trúc và định dạng (Verbatim từ script):
- **CHECK 1**: Word Count. Lọc comment `<!--[^>]*-->`. Range: 1500-1800 từ.
- **CHECK 7**: No Headings. Đếm số dòng bắt đầu bằng `#` (bỏ qua YAML frontmatter).
- **CHECK 8**: Paragraph Structure. `>= 5` đoạn. Tách đoạn: `\r?\n\s*\r?\n`.
- **CHECK 9**: Max Paragraph Length. Mỗi đoạn `<= 400` từ.
- **CHECK 13**: Paragraph Sentence Count. Mỗi đoạn văn phải có 3-5 câu (bỏ qua câu < 4 từ).

## check_lexical
Kiểm tra từ vựng và Voice DNA (Verbatim từ script):
- **CHECK 2**: Banned Words. Regex case-insensitive từ blacklist: `(?i)\b$([regex]::Escape($word))\b`.
- **CHECK 10**: Unique Word Ratio. Tỷ lệ từ vựng duy nhất `>= 30%`.
- **CHECK 11**: Pronoun Self Compliance. Regex check sự tồn tại của từ xưng hô trong `voice-dna.yaml` (biến `self:\s*"([^"]+)"`).
- **CHECK 12**: Filler Count Compliance. Regex đếm tổng số lượng fillers, đảm bảo trong range `min_per_post` đến `max_per_post`.

## check_anti_ai
Kiểm tra dấu hiệu rập khuôn Anti-AI và dấu câu (Verbatim từ script):
- **CHECK 3**: Dash Connector. Regex: `\w+\s+-\s+\w+\s+-\s+\w+`.
- **CHECK 4**: Staccato. 2+ câu liên tiếp <= 8 từ. Tách câu: `(?<!\b(?:[A-Z]|TS|GS|ThS|BS|Dr|Mr|Mrs|Ms|vs))[.!?…]+\s+`.
- **CHECK 5**: Anaphora. 3+ dòng bắt đầu bằng cùng 2 từ đầu tiên. Regex: `^\s*(\S+\s+\S+)`.
- **CHECK 6**: Punctuation Limits. Max 3 `...` (Regex `\.{3}`) và Max 3 `!` (Regex `!`).

## check_keys
Kiểm tra bằng chứng tham chiếu:
- **CHECK 14**: Reference File Keys. Trích xuất comment: `<!--\s*ref_keys:\s*([^>]+)-->` và so sánh với `FILE_KEY` trong các file gốc. Nếu keys là `PENDING`, báo cảnh báo. Nếu lệch, đánh `FAIL`.

## revise_draft
Chỉnh sửa lại draft ngay lập tức. Sửa cục bộ, KHÔNG viết lại toàn bộ bài. Đọc vị trí issue và ghi đè phần cần thiết.

## self_check
Bước 5: Self-Check Gate.
Điều kiện tiên quyết: Script validation BẮT BUỘC đạt `ALL OBJECTIVE CHECKS PASSED`.

## check_sas
Vi phạm SAS v18.2: Mọi story trace back: ① vault, ② famous person/org + nguồn, ③ published book + tác giả. Bịa = AUTO-FAIL.

## fail_sas
Hành vi: FAIL, dừng pipeline và escalate User. Ghi log: `[Phase 5 Self-Check] Verdict: FAIL | Attempt: N/3`

## check_quality
Kiểm tra các tiêu chí Subjective Gate 5:
1. Voice DNA: 100% pronoun/filler/tone compliance.
2. Anti-AI: Zero AI signatures (10 patterns).
3. Vivid: Neo chặt JSON gốc, cấm ẩn dụ sáo rỗng.
4. Engagement: Không gap > 5 câu liên tiếp không value signal.
5. Killer Statements: ≥ 2 câu mạnh, đáng nhớ.
6. Atom Integrity: No fabricated atoms, all verified.
7. KCS v18.2: Credibility intro cho Solution/Concept.
8. JTBD: Không chứa chuỗi tĩnh JTBD.
Verdict: PASS / REVISE / FAIL.

## issue_tracking
Bước 6: Ghi vào `output/runs/[run-folder]/gate5-issues.md` theo format (Verbatim):
Round N
- id: ISSUE_NAME
  location: "paragraph X, câu Y-Z"
  criteria: "Tiêu chí vi phạm"
  severity: HIGH/MEDIUM
  status: OPEN

Sau đó quay về chế độ Revision Mode (Bước 7), lặp lại tối đa 3 round (Attempt N/3).
