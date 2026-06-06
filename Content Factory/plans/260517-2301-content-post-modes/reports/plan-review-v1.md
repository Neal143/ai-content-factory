# Rà Soát Plan — Danh Sách Vấn Đề & Fix

**Last update:** 17/05/2026 23:12 (GMT+7)

---

## 🔴 Nghiêm trọng (gây lỗi/sập pipeline)

### V1: `apply-profile.ps1` dùng `Read-Host` — pipeline AI treo
- **Vấn đề:** Script dùng `Read-Host` interactive. AI agent gọi `run_command` → script chờ input → treo.
- **Fix:** Agent hỏi user qua chat, tự tạo `profiles/active.json`. Script CHỈ làm 3 việc: `validate`, `patch`, `restore`. Xóa bỏ `-Mode` và `-Action create` khỏi script. Thêm `-Action validate`.
- **Ảnh hưởng:** Phase 01 (redesign script), Phase 05 (workflow thay đổi).

### V2: Biến `$profile` trùng PowerShell built-in
- **Vấn đề:** PowerShell có sẵn `$profile` (đường dẫn PS profile). Ghi đè gây xung đột.
- **Fix:** Đổi thành `$formatProfile` trong toàn bộ Phase 02.

### V3: format-agent FATAL RULE xung đột marker stripping
- **Vấn đề:** L23: "TUYỆT ĐỐI KHÔNG thao tác trên text body". Strip marker `⁂` = thao tác text body → Agent từ chối.
- **Fix:** Phase 04 sửa FATAL RULE thêm ngoại lệ: "Ngoại lệ: strip marker phân cách phần và thay bằng dòng trống."

---

## 🟡 Quan trọng (gây lỗi validation với draft hợp lệ)

### V4: CHECK 13b Chain Sentences FAIL — break draft hiện tại ở Auto
- **Vấn đề:** Draft hiện tại có thể có dòng 1-2 câu → CHECK 13b FAIL vì < min 3.
- **Fix:** Thêm `"mode"` vào active.json. Auto → WARN. Basic/Advanced → FAIL.

### V5: Pipeline crash → prompt files kẹt ở trạng thái patch
- **Vấn đề:** Crash sau patch, trước restore → SKILL.md chứa giá trị thử nghiệm vĩnh viễn.
- **Fix:** Đầu Bước -1, LUÔN chạy restore trước để dọn patch thừa.

### V6: `Invoke-Patch` patch từng phần — trạng thái nửa vời
- **Vấn đề:** Pattern P01 match nhưng P03 không → file patch 1/2 → inconsistent.
- **Fix:** Pre-flight check: verify TẤT CẢ pattern trước khi patch. Thiếu 1 → ABORT toàn bộ.

---

## 🟢 Nhỏ (thiếu sót, output không chính xác)

### V7: Thiếu patch voice-writer word budget table (L45-L51)
- **Vấn đề:** Bảng mặc định (Hook=100, Story=250...) không được patch ở Advanced.
- **Fix:** Thêm patch entries P14-P18 cho bảng word budget. Chỉ patch khi Advanced.
- **Ghi chú:** Rủi ro thấp vì L43 nói "Đọc word count từ Outline", nhưng nên patch cho nhất quán.

### V8: Fallback section parse (không marker) dùng hardcode
- **Vấn đề:** Khi không có marker, script hardcode tách bằng 2+ blank lines. Nếu user config khác → sai.
- **Fix:** Script đọc `section_separator.blank_lines_above + blank_lines_below` từ profile để tạo regex động.

### V9: Resume thiếu kiểm tra profiles/active.json
- **Vấn đề:** `/content-post tiếp tục` skip Bước -1. Nếu active.json bị xóa → validator crash.
- **Fix:** Bước resume kiểm tra active.json tồn tại. Không có → copy default.json.
