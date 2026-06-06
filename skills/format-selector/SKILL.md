---
name: Format Selector
description: Chọn chế độ viết (Auto/Basic/Nâng cao), validate constraints, patch prompt files.
last_update: 23/05/2026 (GMT+7)
---

# Format Selector

> File: format-selector/SKILL.md
> Last update: 23/05/2026 (GMT+7)
> Vai trò: Chọn chế độ viết, tạo cấu hình format JSON, validate constraints, patch prompt files.
> Sử dụng khi: Workflow content-post.md gọi ở Bước 2 (lần chạy mới). KHÔNG chạy khi resume.
> Output: `formats/active.json` đã tạo + prompt files đã patch (nếu Basic/Advanced).

## Bước 1: Dọn patch thừa

// turbo
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-format.ps1" -Action restore
```
(Nếu không có `.bak` → script in "Nothing to restore" và exit 0. Không lỗi.)

## Bước 2: Hỏi User

```text
Chọn chế độ viết:
1️⃣ Auto — Viết theo cấu hình mặc định
2️⃣ Thử nghiệm Basic — Tùy chỉnh cấu trúc (separator, số câu)
3️⃣ Thử nghiệm Nâng cao — Tùy chỉnh toàn diện (+ word count)
```

## Bước 3: Xử lý theo chế độ


### 3A — Auto

3. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-format.ps1" -Action validate
   ```
4. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-format.ps1" -Action patch
   ```
5. Hoàn thành skill.

### 3B — Basic

1. Agent hỏi user 10 biến (B1–B10) qua chat (xem danh sách câu hỏi bên dưới).
2. Agent parse câu trả lời: `3-5` → `{"min":3,"max":5}`. `3` → `{"min":3,"max":3}`. Invalid → hỏi lại.
3. Agent tạo `formats/active.json` (merge câu trả lời vào default.json, set `"mode":"basic"`).
4. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-format.ps1" -Action validate
   ```
   Exit 0 → tiếp. Exit 1 → Agent đọc output, giải thích lỗi cho user, hỏi sửa.
5. // turbo
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-format.ps1" -Action patch
   ```

### 3C — Nâng cao

Tương tự Basic nhưng hỏi thêm 4 biến (A1–A4), set `"mode":"advanced"`.

---

**Danh sách câu hỏi Basic (B1–B10):**
```text
══ SECTION ══
[B1] Phân tách giữa các section:
     — Marker (mặc định: không có. VD: ———, ***): ___
     — Dòng trống phía trên (mặc định: 1): ___
     — Dòng trống phía dưới (mặc định: 1): ___
[B2] Section có heading? (mặc định: không): ___
     — Nếu có — dòng trống phía trên heading (mặc định: 1): ___
     — Nếu có — dòng trống phía dưới heading (mặc định: 0): ___
     💡 Khi cả B1 marker lẫn B2 heading cùng bật: [section trước] → separator → heading → [section sau]. Spacing cộng dồn.

══ PARAGRAPH ══
[B3] Phân tách giữa các đoạn văn:
     — Marker (mặc định: không có): ___
     — Dòng trống phía trên (mặc định: 1): ___
     — Dòng trống phía dưới (mặc định: 0): ___
[B4] Đoạn có heading? (mặc định: không): ___
     — Nếu có — dòng trống phía trên heading (mặc định: 1): ___
     — Nếu có — dòng trống phía dưới heading (mặc định: 0): ___
     💡 Khi cả B3 marker lẫn B4 heading cùng bật: [đoạn trước] → separator → heading → [đoạn sau]. Spacing cộng dồn.
[B5] Số câu mỗi đoạn (mặc định: 8-10): ___
     💡 2 câu dưới 4 từ liền nhau được tính là 1 câu.

══ CHAIN ══
[B6] Phân tách giữa các chuỗi câu trong đoạn:
     — Marker (mặc định: không có): ___
     — Dòng trống phía trên (mặc định: 0): ___
     — Dòng trống phía dưới (mặc định: 0): ___
[B7] Số câu mỗi chuỗi bình thường (mặc định: 1-2): ___
[B8] Số câu mỗi chuỗi dài (mặc định: 3-5): ___
[B9] Số chuỗi dài mỗi bài (mặc định: 3-5): ___

══ HIỂN THỊ ══
[B10] Bài viết có title trong output cuối? (mặc định: không): ___
```

**Câu hỏi bổ sung Nâng cao (A1–A4):**
```text
[A1] Ngữ cảnh sử dụng chuỗi dài (mặc định: tạo chiều sâu cảm xúc hoặc lập luận phức tạp): ___
[A2] Số từ toàn bài (mặc định: 1300-1800, dung sai ±10%): ___
[A3] Phân bổ từ mỗi section — nhập % hoặc số tuyệt đối (mặc định: 6/16/52/16/10 %): ___
     💡 Thứ tự: Hook / Story / Deep Dive / Pivot / Closing. Nếu nhập %, agent tính min-max dựa trên A2. Tổng phải = 100%.
[A4] Số từ tối đa mỗi đoạn (mặc định: 400): ___
```


Hoàn thành skill. Workflow tiếp tục Bước 3.
