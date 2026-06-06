# Phase 04: Fix Rollback & Cập Nhật AGENT.md

> **File:** plans/260523-2342-voice-writer-standards/phase-04-fix-rollback-and-agent.md
> **Last update:** 24/05/2026 14:15 (GMT+7)

Status: ⬜ Pending

## 1. Vấn Đề Hiện Tại

Quá trình kiểm tra chuyên sâu đã phát hiện ra 2 lỗ hổng logic dẫn đến rủi ro gãy hệ thống:

1. **Lỗ hổng 1 (Bị Rollback do hệ thống tự bảo vệ):** 
   - Lệnh `apply-profile.ps1 -Action patch` ở cuối Phase 03 đã bị `FAIL` do lỗi encoding trong file `format-agent/SKILL.md` (file này có sẵn lỗi từ trước).
   - Cơ chế tự động an toàn của AWF đã kích hoạt tính năng **Rollback**, tự động khôi phục toàn bộ các file `.md` về trạng thái backup cũ (`.bak`).
   - Hậu quả: Toàn bộ cập nhật của ta trên file `voice-writer/SKILL.md` (yêu cầu Agent đọc 8 file và điền 8 keys) đã bị ghi đè ngược trở lại thành phiên bản cũ (chỉ đọc 3 file và điền 3 keys).
2. **Lỗ hổng 2 (Thiếu sót cập nhật System Prompt):**
   - File `voice-writer/AGENT.md` (System Prompt chính) có chứa một **Sentinel Rule** (quy tắc vệ sĩ) được hard-code ở dòng 41 yêu cầu điền chuỗi `ref_keys` với 3 keys.
   - Nếu không cập nhật file này, Agent sẽ bị conflict: `SKILL.md` bảo điền 8, `AGENT.md` bảo điền 3 → dẫn đến Agent hallucinate hoặc fail CHECK 14 của `validate-draft.ps1`.

## 2. Giải Pháp (Tasks)

### Task 1: Khôi phục bản cập nhật cho `SKILL.md`
- **Mục tiêu:** Đưa file `.agents/skills/voice-writer/SKILL.md` trở lại trạng thái chuẩn của Phase 01.
- **Hành động:** 
  - Đổi danh sách đọc tham chiếu (Bước 1) từ 3 file thành 8 file.
  - Sửa chuỗi `ref_keys` từ 3 key thành 8 key.
  - Cập nhật dòng `Anti-AI` và thêm dòng `Prose & Punc (AUTO-FAIL)` vào bảng Constraints.
  - Thêm tiêu chí `VN Standards` vào bảng Self-Check Gate.
  - *(Lưu ý: Không chạy lại `apply-profile.ps1 -Action patch` để tránh kích hoạt rollback loop).*

### Task 2: Cập nhật Sentinel Rule trong `AGENT.md`
- **Mục tiêu:** Đồng bộ hóa rule xuất output của Agent với `SKILL.md`.
- **Hành động:** Trong file `.agents/agents/voice-writer/AGENT.md`, tìm dòng 41:
  - **Từ:** `- **Sentinel Rule**: Cuối tệp \`05-draft.md\` phải ghi nhận dòng chú thích \`<!-- ref_keys: writing-rules=[key1], anti-ai=[key2], english-blacklist=[key3] -->\`.`
  - **Thành:** `- **Sentinel Rule**: Cuối tệp \`05-draft.md\` phải ghi nhận dòng chú thích \`<!-- ref_keys: writing-rules=[key1], anti-ai=[key2], english-blacklist=[key3], capitalization=[key4], english-mixing=[key5], prose-format=[key6], punctuation=[key7], ai-detection=[key8] -->\`.`

### Task 3: Chạy lại `generate-phase-key.ps1`
- **Mục tiêu:** Khởi tạo lại mã `EXECUTION_KEY` cho `SKILL.md` mới vừa được khôi phục, đảm bảo tính nhất quán của hệ thống.

## 3. Tiêu chí hoàn thành (Verification)
- [ ] Lệnh `grep` tìm chuỗi `ref_keys:` trong thư mục `.agents` trả về chuỗi có 8 keys ở cả 2 file `SKILL.md` và `AGENT.md`.
- [ ] Chạy `generate-phase-key.ps1` báo `[OK] All 22 keys injected`.

---
Mời User duyệt plan này trước khi tiến hành thực thi.
