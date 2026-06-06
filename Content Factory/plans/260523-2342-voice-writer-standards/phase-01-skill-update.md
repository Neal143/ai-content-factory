# Phase 01: SKILL.md Update

> **File:** plans/260523-2342-voice-writer-standards/phase-01-skill-update.md
> **Last update:** 24/05/2026 13:06 (GMT+7)

Status: ✅ Complete
Dependencies: Không

## Objective

Cập nhật `voice-writer/SKILL.md` để AI đọc 5 tài liệu chuẩn tiếng Việt và tuân thủ các quy tắc khi viết bài.

## Target File

`.agents/skills/voice-writer/SKILL.md`

## Tasks

### Task 1: Copy file chuẩn tiếng Việt vào folder references nội bộ
**Mục đích:** Đảm bảo tính đóng gói (encapsulation) của skill. Voice Writer không được phép trỏ ra ngoài workspace hoặc trỏ sang các folder skill/resource khác để tránh tight coupling. Nếu `viet-chuyen-nghiep` bị xóa/sửa đổi cấu trúc, `voice-writer` không bị gãy.

**Hành động:** Dùng `run_command` (Copy-Item) hoặc `read_file`/`write_to_file` để copy 5 file sau từ `d:\AI\AI content factory - v3.7B\viet-chuyen-nghiep\resources\check\` sang `d:\AI\AI content factory - v3.7B\Content Factory\.agents\skills\voice-writer\references\`:
- `capitalization.md`
- `english-mixing.md`
- `prose-format.md`
- `punctuation.md`
- `ai-detection.md`

### Task 1.5: Xóa bỏ hoàn toàn Mục 4 trong `prose-format.md`
**Mục đích:** Hủy bỏ logic quản lý độ dài đoạn ở file tham chiếu để tập trung toàn bộ rule quản lý độ dài đoạn vào bảng Constraints của `SKILL.md` (Single Source of Truth), giúp loại bỏ hoàn toàn sự phân mảnh logic.

**Hành động:** Trong file `.agents/skills/voice-writer/references/prose-format.md` (vừa được copy sang), dùng công cụ `replace_file_content` hoặc `run_command` (sed) **xóa bỏ hoàn toàn** phần nội dung từ `## 4. Độ dài đoạn văn biến thiên` cho đến trước `## 5. Cấm headers trong storytelling/blog`. Cũng xóa luôn dòng `- [ ] Độ dài đoạn biến thiên` ở phần Checklist.

---

### Task 1.6: Thêm placeholder FILE_KEY vào 5 file mới
**Mục đích:** Để script `generate-phase-key.ps1` có thể tìm thấy và inject random key vào 5 file này.

**Hành động:** Dùng `write_to_file` hoặc lệnh bash để append chính xác chuỗi `\n\n> FILE_KEY: PENDING` vào cuối cùng của cả 5 file vừa copy (trong thư mục `references/`). Ký tự ngắt dòng `\n\n` đảm bảo regex của hệ thống luôn bắt trúng kể cả khi file gốc bị khuyết newline ở EOF.

---

### Task 2: Bổ sung 5 file tham chiếu chuẩn tiếng Việt

**Vị trí:** Dòng 19-24.

**Trước:**
```markdown
### Bước 1: Đọc tham chiếu BẮT BUỘC
Dùng tool `view_file` đọc lần lượt 3 file:
- `.agents/skills/voice-writer/references/writing-rules.md`
- `.agents/skills/voice-writer/references/anti-ai-patterns.md`
- `.agents/skills/voice-writer/references/english-blacklist.md`

> ⛔ **FATAL RULE:** PHẢI dùng tool đọc thành công cả 3. File Not Found → DỪNG, BÁO USER. Cấm hallucinate nội dung.

Sau khi đọc mỗi file, ghi nhận giá trị `FILE_KEY` ở dòng cuối file đó.

Sau khi hoàn thành toàn bộ nội dung `05-draft.md`, append vào **cuối file** dòng:
```
<!-- ref_keys: writing-rules=[key1], anti-ai=[key2], english-blacklist=[key3] -->
```
Thay [key1], [key2], [key3] bằng đúng giá trị FILE_KEY đã đọc từ mỗi file.
```

**Sau:**
```markdown
### Bước 1: Đọc tham chiếu BẮT BUỘC
Dùng tool `view_file` đọc lần lượt BẮT BUỘC toàn bộ các file sau:
- `.agents/skills/voice-writer/references/writing-rules.md`
- `.agents/skills/voice-writer/references/anti-ai-patterns.md`
- `.agents/skills/voice-writer/references/english-blacklist.md`
- `.agents/skills/voice-writer/references/capitalization.md`
- `.agents/skills/voice-writer/references/english-mixing.md`
- `.agents/skills/voice-writer/references/prose-format.md`
- `.agents/skills/voice-writer/references/punctuation.md`
- `.agents/skills/voice-writer/references/ai-detection.md`

> ⛔ **FATAL RULE:** PHẢI dùng tool đọc thành công toàn bộ. File Not Found → DỪNG, BÁO USER. Cấm hallucinate nội dung.

Sau khi đọc mỗi file, ghi nhận giá trị `FILE_KEY` ở dòng cuối file đó.

Sau khi hoàn thành toàn bộ nội dung `05-draft.md`, append vào **cuối file** dòng:
```
<!-- ref_keys: writing-rules=[key1], anti-ai=[key2], english-blacklist=[key3], capitalization=[key4], english-mixing=[key5], prose-format=[key6], punctuation=[key7], ai-detection=[key8] -->
```
Thay [key1]...[key8] bằng đúng giá trị FILE_KEY đã đọc từ mỗi file.
```

> **Giải thích đường dẫn:** Sử dụng đường dẫn tương đối từ Content Factory root trỏ thẳng vào thư mục references nội bộ của skill. Đoạn này cũng gộp luôn Task cập nhật FATAL RULE.

---



### Task 4: Cập nhật dòng Anti-AI trong bảng Constraints

**Vị trí:** Dòng 82 (bảng `Constraints áp dụng cho MỖI section`).

**Trước:**
```markdown
| **Anti-AI** | Quét 10 patterns (anti-ai-patterns.md) + blacklist (english-blacklist.md). Đặc biệt: Micro-Staccato (2+ câu ≤8 từ kề nhau) + Anaphora (3+ câu cùng cụm mở đầu) |
```

**Sau:**
```markdown
| **Anti-AI** | Quét 10 patterns + blacklist + AI detection. Đặc biệt: Cấm AI Labels (Key, Note, Summary). Cấm lạm dụng từ nối (>3 lần/bài). Cấm trộn tiếng Anh. |
```

Rồi **THÊM 1 dòng mới vào cuối bảng** (sau dòng `| **Chain** |`):

```markdown
| **Prose & Punc** (AUTO-FAIL) | Không dùng Title Case (H2+ viết hoa chữ đầu). Không dấu hai chấm trong tiêu đề. Dấu câu sát từ trước, cách từ sau. Cấm em-dash `—` (đổi sang từ nối hoặc ` - `). Cấm Oxford comma `, và`. Cấm Bullet trong thân văn xuôi. Độ dài đoạn văn phải biến thiên, tránh các đoạn liên tiếp có số câu bằng nhau. |
```

> **Xác nhận an toàn:** Dòng `| **Paragraph** |` và `| **Chain** |` giữ nguyên 100% nội dung gốc — `apply-profile.ps1` pre-flight sẽ PASS.

---

### Task 5: Thêm VN Standards vào Self-Check Gate

**Vị trí:** Bảng `Bước 5: Self-Check Gate` (Dòng 109-119).

**THÊM 1 dòng mới** ngay dưới dòng `| JTBD |`:

```markdown
| VN Standards | Đúng chuẩn viết hoa (H2+), không trộn tiếng Anh, Prose format (không bullet), Punctuation chuẩn | → REVISE, quay Bước 3 |
```

---

### Task 6: Cập nhật metadata

**Vị trí:** Frontmatter YAML dòng 4.

Cập nhật `last_update` thành ngày thực thi thực tế.

---

## Verification

Sau khi hoàn thành tất cả 7 task, kiểm tra:

1. ✅ Danh sách file tham chiếu = 8 (3 cũ + 5 mới)
2. ✅ FATAL RULE dùng "toàn bộ" thay vì "cả 3"
3. ✅ Bảng Constraints có dòng `Prose & Punc` ở cuối
4. ✅ Dòng `| **Paragraph** |` byte-for-byte giống gốc
5. ✅ Dòng `| **Chain** |` byte-for-byte giống gốc
6. ✅ Self-Check Gate có dòng `VN Standards`
7. ✅ Chạy `apply-profile.ps1 -Action validate` → PASS
8. ✅ Chạy `apply-profile.ps1 -Action patch` → Pre-flight PASS

---
Next Phase: phase-02-script-update.md
