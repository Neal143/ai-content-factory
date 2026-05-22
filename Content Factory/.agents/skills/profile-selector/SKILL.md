---
name: Profile Selector
description: Chọn chế độ viết (Auto/Basic/Nâng cao), validate constraints, patch prompt files.
last_update: 19/05/2026 15:41 (GMT+7)
---

# Profile Selector

> File: profile-selector/SKILL.md
> Last update: 19/05/2026 15:41 (GMT+7)
> Vai trò: Chọn chế độ viết, tạo profile, validate constraints, patch prompt files.
> Sử dụng khi: Workflow content-post.md gọi ở Bước 2 (lần chạy mới). KHÔNG chạy khi resume.
> Output: `profiles/active.json` đã tạo + prompt files đã patch (nếu Basic/Advanced).

## Bước 1: Dọn patch thừa

// turbo
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
```
(Nếu không có `.bak` → script in "Nothing to restore" và exit 0. Không lỗi.)

## Bước 2: Hỏi User

```text
Chọn chế độ viết:
1️⃣ Auto — Viết theo cấu hình mặc định
2️⃣ Thử nghiệm Basic — Tùy chỉnh cấu trúc (separator, số câu)
3️⃣ Thử nghiệm Nâng cao — Tùy chỉnh toàn diện (+ heading, word count)
```

## Bước 3: Xử lý theo chế độ


### 3A — Auto

3. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action validate
   ```
4. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action patch
   ```
5. Hoàn thành skill.

### 3B — Basic

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

### 3C — Nâng cao

Tương tự Basic nhưng hỏi thêm 5 biến (A1–A6), set `"mode":"advanced"`.

---

**Danh sách câu hỏi Basic (B1–B10):**
```text
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
```text
[A1] Ngữ cảnh sử dụng chuỗi dài: ___
[A2] Spacing heading section — dòng trống trên/dưới (ví dụ: 1-0): ___
[A3] Spacing heading đoạn — dòng trống trên/dưới (ví dụ: 1-0): ___
[A4] Số từ toàn bài (ví dụ: 1500-1800): ___
[A5] Số từ mỗi phần — Hook/Story/Deep Dive/Pivot/Closing: ___
[A6] Số từ tối đa mỗi đoạn: ___
```


Hoàn thành skill. Workflow tiếp tục Bước 3.
