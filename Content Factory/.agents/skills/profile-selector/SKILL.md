---
name: Profile Selector
description: Chọn chế độ viết (Auto/Basic/Nâng cao), validate constraints, patch prompt files.
last_update: 23/05/2026 (GMT+7)
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
[B1] Phân tách giữa các section:
     — Marker hiển thị giữa các section (mặc định: không có, chỉ dòng trống. Nhập ký hiệu nếu muốn, VD: ———, ***): ___
     — Số dòng trống phía trên marker (mặc định: 1): ___
     — Số dòng trống phía dưới marker (mặc định: 1): ___
[B2] Phân tách giữa các đoạn văn:
     — Marker hiển thị giữa các đoạn (mặc định: không có): ___
     — Số dòng trống phía trên (mặc định: 1): ___
     — Số dòng trống phía dưới (mặc định: 0): ___
[B3] Số câu mỗi đoạn (mặc định: 8-10): ___
[B4] Phân tách giữa các chuỗi câu trong đoạn:
     — Marker hiển thị giữa các chuỗi (mặc định: không có): ___
     — Số dòng trống phía trên (mặc định: 0): ___
     — Số dòng trống phía dưới (mặc định: 0): ___
[B5] Số câu mỗi chuỗi bình thường (mặc định: 1-2): ___
[B6] Số câu mỗi chuỗi dài (mặc định: 3-5): ___
[B7] Số chuỗi dài mỗi bài (mặc định: 3-5): ___
[B8] Bài viết có title trong output cuối? (mặc định: không): ___
[B9] Section có heading trong output cuối? (mặc định: không): ___
[B10] Đoạn có heading trong output cuối? (mặc định: không): ___
```

**Câu hỏi bổ sung Nâng cao (A1–A6):**
```text
[A1] Ngữ cảnh sử dụng chuỗi dài: ___
[A2] Spacing heading section — dòng trống trên/dưới (ví dụ: 1-0): ___
[A3] Spacing heading đoạn — dòng trống trên/dưới (ví dụ: 1-0): ___
[A4] Số từ toàn bài (ví dụ: 1500-1800): ___
[A5] Số từ mỗi section: ___
[A6] Số từ tối đa mỗi đoạn: ___
```


Hoàn thành skill. Workflow tiếp tục Bước 3.
