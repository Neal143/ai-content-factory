# Phase 05: Pipeline Integration & Test

**Tên file:** phase-05-integration.md
**Last update:** 18/05/2026 22:20 (GMT+7)
**Vai trò:** Tích hợp vào workflow content-post.md và kiểm thử end-to-end.
**Được sử dụng khi nào?:** Khi thực thi Phase 05 (cuối cùng).
**Output:** content-post.md đã cập nhật + kết quả test.
**Tóm tắt logic hoạt động:** Thêm bước chọn chế độ vào đầu pipeline, gọi apply-profile.ps1, và restore sau khi xong.

Status: ⬜ Pending
Dependencies: Phase 01, 02, 03, 04

---

## Objective

1. Tích hợp chọn chế độ (Auto/Basic/Advanced) vào `content-post.md`.
2. Kiểm thử end-to-end: chạy pipeline với profile thử nghiệm, verify mọi component hoạt động đồng bộ.

---

## Task 1: Cập nhật `content-post.md`

**File:** `.agents/workflows/content-post.md`

### 1.1. Thêm Bước -1: Chọn Chế Độ

**Vị trí:** Trước `### Gate: Kiểm tra Pipeline Status` (L33), thêm section mới:

```markdown
### Bước -1: Chọn Chế Độ Viết

**Bước -1a: Dọn patch thừa (fix V5)**
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
```
(Nếu không có `.bak` → script in "Nothing to restore" và exit 0. Không lỗi.)

**Bước -1b: Hỏi User:**
```
Chọn chế độ viết:
1️⃣ Auto — Viết theo cấu hình mặc định
2️⃣ Thử nghiệm Basic — Tùy chỉnh cấu trúc (separator, số câu)
3️⃣ Thử nghiệm Nâng cao — Tùy chỉnh toàn diện (+ heading, word count)
```

**Xử lý (fix V1 — agent tạo JSON, script chỉ validate/patch):**

- **1 (Auto):**
  Agent copy `profiles/default.json` → `profiles/active.json` (dùng tool write_to_file hoặc run_command copy).
  Không cần patch (giá trị = mặc định). Chuyển thẳng Gate.

**Bước -1c: Lưu snapshot cấu hình vào run folder**
```powershell
Copy-Item "profiles/active.json" -Destination "[run-folder]/00-profile.json"
```
Mục đích: Trace ngược từ bài viết output → cấu hình thử nghiệm đã dùng.

- **2 (Basic):**
  1. Agent hỏi user 10 biến (B1–B10) qua chat (xem danh sách câu hỏi bên dưới).
  2. Agent parse câu trả lời: `3-5` → `{"min":3,"max":5}`. `3` → `{"min":3,"max":3}`. Invalid → hỏi lại.
  3. Agent tạo `profiles/active.json` (merge câu trả lời vào default.json, set `"mode":"basic"`).
  4. // turbo
     ```powershell
     powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action validate
     ```
     Exit 0 → tiếp. Exit 1 → Agent đọc output, giải thích lỗi cho user, hỏi sửa.
  5. // turbo
     ```powershell
     powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action patch
     ```

- **3 (Nâng cao):** Tương tự Basic nhưng hỏi thêm 5 biến (A1–A2–A3–A4–A5–A6), set `"mode":"advanced"`.

**Danh sách câu hỏi Basic (B1–B10):**
```
[B1] Cách tách phần — marker (mặc định: ⁂, để trống = chỉ dòng trống): ___
[B1] Dòng trống phía trên marker: ___
[B1] Dòng trống phía dưới marker: ___
[B2] Cách tách đoạn — marker (để trống = không dùng): ___
[B2] Dòng trống phía trên: ___
[B2] Dòng trống phía dưới: ___
[B3] Số câu mỗi đoạn (ví dụ: 3-5): ___
[B4] Cách tách chuỗi câu — marker (để trống = không dùng): ___
[B4] Dòng trống phía trên: ___
[B4] Dòng trống phía dưới: ___
[B5] Số câu mỗi chuỗi bình thường (ví dụ: 3-5): ___
[B6] Số câu mỗi chuỗi dài (ví dụ: 6-8): ___
[B7] Số chuỗi dài mỗi bài (ví dụ: 0-2): ___
[B8] Bài viết có title trong output cuối? (yes/no): ___
[B9] Section có heading trong output cuối? (yes/no): ___
[B10] Đoạn có heading trong output cuối? (yes/no): ___
```

**Câu hỏi bổ sung Nâng cao (A1–A6):**
```
[A1] Ngữ cảnh sử dụng chuỗi dài: ___
[A2] Spacing heading section — dòng trống trên/dưới (ví dụ: 1-0): ___
[A3] Spacing heading đoạn — dòng trống trên/dưới (ví dụ: 1-0): ___
[A4] Số từ toàn bài (ví dụ: 1500-1800): ___
[A5] Số từ mỗi phần — Hook/Story/Deep Dive/Pivot/Closing: ___
[A6] Số từ tối đa mỗi đoạn: ___
```

- **Ngoại lệ**: `/content-post tiếp tục` → bỏ qua Bước -1 (profile đã tồn tại từ phiên trước, prompt đã patch). Chỉ chạy Bước -1a (restore dọn thừa) rồi skip tới Resume.
```

### 1.2. Thêm Restore ở Bước 3 (Hoàn thành)

**Vị trí:** Tại `### Bước 3: Hoàn thành` (L95), thêm:

```markdown
Sau khi hoàn thành:
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
```
```

### 1.3. Cập nhật mục CHECKPOINT & MULTI-SESSION

**Vị trí:** Tại `### Resume` (L109), thêm note:

```markdown
> **Lưu ý Profile:** Khi resume, `profiles/active.json` vẫn tồn tại từ phiên trước.
> Prompt files đã được patch. KHÔNG chạy lại Bước -1.
> Restore sẽ chạy ở Bước 3 khi pipeline hoàn thành.
```

---

## Task 2: Kiểm thử

### 2.1. Unit Test — Từng component

| Test | Lệnh | Expected |
|------|-------|----------|
| Validate OK | `apply-profile.ps1 -Action validate` (default.json) | VALIDATION PASSED, exit 0 |
| Validate FAIL | `apply-profile.ps1 -Action validate` (B3=`3-4`, B5=`3-5`) | Báo lỗi R3, exit 1 |
| Patch OK | `apply-profile.ps1 -Action patch` | Pre-flight pass → `.bak` tạo → files patched |
| Patch FAIL | `apply-profile.ps1 -Action patch` (SKILL.md bị sửa tay) | Pre-flight FAIL → ABORT → không tạo `.bak` |
| Restore | `apply-profile.ps1 -Action restore` | Files khôi phục, `.bak` xóa |
| Restore empty | `apply-profile.ps1 -Action restore` (không có `.bak`) | "Nothing to restore", exit 0 |
| Draft validation default | `validate-draft.ps1` với `default.json` | Kết quả giống bản cũ |
| Draft validation custom | `validate-draft.ps1` với custom `active.json` | Check 13a dùng khoảng tùy chỉnh |
| Chain check Auto | `validate-draft.ps1` với `mode=auto` | Chain checks = WARN |
| Chain check Basic | `validate-draft.ps1` với `mode=basic` | Chain checks = FAIL |
| Format marker strip | Draft có `⁂` → format-agent | Không chứa `⁂`, có dòng trống thay |

### 2.2. Regression Test

Chạy toàn bộ pipeline `content-post` ở chế độ **Auto** với nội dung thật. Verify:
- [ ] Mọi validation check PASS giống phiên bản cũ.
- [ ] Output bài viết cuối không khác biệt so với trước khi refactor.
- [ ] Restore hoàn tất, không còn `.bak` files.
- [ ] `profiles/active.json` tồn tại sau pipeline.

### 2.3. Experimental Test

Chạy pipeline ở chế độ **Basic** với tham số tùy chỉnh (ví dụ: `sentences_per_paragraph: 2-7`). Verify:
- [ ] AI viết bài theo instruction đã patch.
- [ ] Validator check theo giá trị tùy chỉnh.
- [ ] Restore hoàn tất sau pipeline.

---

## Files to Modify

| File | Scope thay đổi |
|------|----------------|
| `content-post.md` | Thêm Bước -1 (chọn chế độ), thêm restore ở Bước 3, note resume |

## Lưu ý Quan Trọng

### Quy tắc CẤM trong content-post.md
Dòng L23: `CẤM tạo file script mới (.py, .js, .sh, .ps1)`. Quy tắc này áp dụng cho AI AGENT khi CHẠY pipeline — KHÔNG áp dụng cho developer khi PHÁT TRIỂN hệ thống. `apply-profile.ps1` là script hệ thống được tạo trước, KHÔNG phải script agent tự tạo runtime.

### Backward Compatibility
- Nếu `profiles/active.json` không tồn tại (pipeline cũ chưa upgrade) → validator fallback về hardcoded defaults → hệ thống vẫn chạy bình thường.
- Nếu user không chọn chế độ (skip Bước -1) → pipeline vẫn chạy như cũ.

---

## Tổng kết toàn Plan

| Phase | Files tạo mới | Files sửa vĩnh viễn | Files bị patch tạm (.bak + restore) | Files refactor đọc JSON |
|-------|---------------|---------------------|--------------------------------------|-------------------------|
| 01 | `profiles/default.json`, `apply-profile.ps1` | — | — | — |
| 02 | — | — | — | `validate-draft.ps1`, `validate-outline.ps1` |
| 03 | — | `voice-writer/SKILL.md` (structural markers), `structure-designer/SKILL.md` (keyword) | `voice-writer/SKILL.md`, `writing-rules.md`, `structure-designer/SKILL.md`, `format-agent/SKILL.md` | — |
| 04 | — | `format-agent/SKILL.md` (strip/format structural markers) | — | `validate-format.ps1` |
| 05 | — | `content-post.md` | — | — |

**Tổng:** 2 file mới, 4 file sửa vĩnh viễn, 4 file bị patch tạm, 3 file refactor đọc JSON. Ước tính 3–4 sessions.
