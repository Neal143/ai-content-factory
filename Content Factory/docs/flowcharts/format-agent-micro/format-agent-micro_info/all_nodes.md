# Giải thích các Node Format Agent

## get_context
Bước 1: Trích xuất Điều kiện Đầu vào từ Bảng đen. TUYỆT ĐỐI CHỈ truy xuất và sử dụng 3 khối dữ liệu để đóng gói:
1. **`Draft đã PASS QA`** (Phase 5/6).
2. **`Topic Slug`** (đặt tên file).
3. **`Pillar gốc`** (update log + tags).

## add_yaml
Bước 2: Format bài viết và Nhúng YAML Frontmatter.
Quy tắc Format: File Name `[YYYY-MM-DD]-[topic-slug].md`.
`⛔ FATAL RULE — DATA INTEGRITY`: TUYỆT ĐỐI KHÔNG thao tác trên text body. Chỉ: nhúng YAML frontmatter, copy file, update logs, ghi execution key. Nội dung đã qua QA Phase 6. Mọi thay đổi text = vi phạm Data Integrity.
YAML Frontmatter (Chèn vào đầu file. BẮT BUỘC 1 dòng trống sau `---` kết thúc):
```yaml
---
title: "Tiêu đề bài viết"
date: YYYY-MM-DD
pillar: "Tên pillar"
topic: "topic_id_snake_case"
hook_formula: "F[number]"
word_count: [number]
qa_score: [number]/[max_score]
status: published
---
```

## save_files
Bước 3: Lưu bài vào 2 nơi.
1. `output/runs/[run-folder]/07-final.md` (giữ nguyên execution key).
2. `output/posts/[YYYY-MM-DD]-[topic-slug].md` (Strip 2 dòng comment kỹ thuật: `<!-- execution_key: ... -->` và `<!-- ref_keys: ... -->` bằng string replace, KHÔNG chỉnh nội dung khác).

## update_logs
Bước 4-6: Cập nhật file logs.
- Cập nhật `output/logs/production-log.md` — append entry (Có kiểm tra pillar diversity không trùng pillar 2 bài liên tiếp):
  ```
  ## [YYYY-MM-DD] — [Tiêu đề bài]
  - **Pillar**: [tên pillar]
  - **Topic**: "[topic_id_snake_case]"
  - **Hook Formula**: F[number]
  - **QA Score**: [number]/[max_score]
  - **Atoms Used**: [danh sách atom names]
  - **Revisions**: [số lần REVISE]
  - **Status**: published
  ```
- Cập nhật `output/logs/hook-history.md` — append 1 dòng:
  ```
  | [YYYY-MM-DD] | [Topic slug] | F[number] | [Hook score]/10 |
  ```

## ref_draft
File đầu vào (BẮT BUỘC): `05-draft.md` (Draft gốc từ Phase 5, dùng để đối chiếu độ chênh lệch số lượng từ với file 07-final.md).

## ref_prod_log
File lưu trữ (BẮT BUỘC): `production-log.md` (Dùng để kiểm tra lịch sử viết bài và Pillar Rotation).

## ref_hook_log
File lưu trữ (BẮT BUỘC): `hook-history.md` (Dùng để kiểm tra log hook có được append không).

## validate_script
Bắt đầu chạy script: `powershell -ExecutionPolicy Bypass -File .agents/skills/format-agent/scripts/validate-format.ps1 -DraftPath "output/runs/[run-folder]/07-final.md" -SourceDraftPath "output/runs/[run-folder]/05-draft.md"`

## check_logs
**CHECK 2 & 3: Production Log & Hook History Updated**
Quét `production-log.md` tìm Regex ngày `$today` (đảm bảo bài viết đã được append).
Quét `hook-history.md` đảm bảo File size `> 20` bytes.

## check_yaml
**CHECK 4 & 4.1: YAML Frontmatter & Spacing**
Tìm block `(?s)^---\r?\n(.+?)\r?\n---` và check sự tồn tại của 8 key: `title, date, pillar, topic, hook_formula, word_count, qa_score, status`.
Check Regex dòng trống sau frontmatter `(?s)^---.*?---\r?\n\r?\n` (Để Markdown parser không lỗi).

## check_pillar
**CHECK 5: Pillar Rotation**
Regex `\*\*Pillar\*\*:\s*(.+)` trên `production-log.md`, check bài áp chót không được trùng với `$currentPillar` từ Frontmatter hiện tại (đảm bảo đa dạng nội dung).

## check_integrity
**CHECK 6: Content Integrity (Poka-Yoke Trọng yếu)**
Đếm từ giữa `05-draft.md` (source content) và `07-final.md` (đã strip thẻ yaml). Word count delta BẮT BUỘC `<= 2%`. Chống Agent "nuốt" chữ khi rewrite nhầm.

## fix_issue
Xử lý lỗi theo Exit code:
- Exit code > 0: Đọc output script.
  + Content Integrity FAIL → KHÔNG tự fix, escalate User.
  + Lỗi khác (Format/YAML/Log) → tự fix, chạy lại (max 1 retry).
- Exit code > 0 lần 2: FAIL, Dừng pipeline, escalate User.
Ghi log: `[Phase 7 Gate] Verdict: PASS/FAIL | Attempt: N/2`.
