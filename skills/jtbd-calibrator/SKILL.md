---
name: JTBD Calibrator
description: Chuan hoa JTBD va hieu dinh (calibrate) cac bien Performer, Job, Circumstance. Ho tro 2 mode — calibrate (tu source tho) va re-calibrate (tu audiences da ton tai).
---

# JTBD Calibrator Skill

> **Tên file**: .agents/skills/jtbd-calibrator/SKILL.md
> **Last update**: 28/07/2026 17:20 (GMT+7)
> **Vai trò**: Skill chuẩn hóa và hiệu đính JTBD từ file nguồn thô.
> **Sử dụng khi**: Được Agent điều phối gọi khi cần chuẩn hóa JTBD từ dữ liệu thô.
> **Output**: `jtbd_calibrated.json`, `audiences_parsed.json`
> **Tóm tắt logic hoạt động**: Parse file nguồn thô bằng script (chống ảo giác) → Phân lô dữ liệu → LLM hiệu chỉnh 4 biến JTBD (Main Job, Circumstance, Performer, Aliases) theo tiêu chuẩn Problem Space → Submit tự động kiểm tra keyword → Vòng lặp batch có khóa → Xuất file chuẩn hóa.

// turbo-all

> ⚠️ **BẮT BUỘC TIẾNG VIỆT CÓ DẤU**: Toàn bộ output JTBD (`audience_main_job`, `audience_circumstance`, `audience_Job_performer`, `aliases`, `reason`) **PHẢI viết tiếng Việt có dấu đầy đủ**. TUYỆT ĐỐI KHÔNG viết tiếng Việt không dấu (VD: "thiet lap" thay vì "thiết lập"). Vi phạm rule này sẽ làm hỏng toàn bộ pipeline downstream.

## 1. QUY TẮC VỆ SINH (HYGIENE)

Skill này chạy trong thư mục làm việc (`work_dir`) do Agent cấp. KHÔNG tự tạo mới thư mục này.
- **Thư mục dùng chung:** `[work_dir]` (Dùng work_dir path được Agent truyền trực tiếp qua INPUT. KHÔNG tự derive.)
- File tạm (JSON output từ script, debug logs) → BẮT BUỘC ghi vào `[work_dir]/`

## 2. Input & Output

**INPUT (nhận từ Agent điều phối):**
- `mode`: `calibrate` (mặc định) hoặc `re-calibrate`
- `work_dir`: Thư mục làm việc (tạo sẵn bởi Agent, mọi file tạm và output ghi vào đây)

**INPUT bổ sung theo mode:**
| Mode | Input | Ghi chú |
|---|---|---|
| `calibrate` | `source_type` (VD: `book`), `source_file` (path file nguồn) | Giữ nguyên flow hiện tại |
| `re-calibrate` | `vault_root` (path tới vault root) | Đọc toàn bộ audiences từ `_audience_index.yaml` |

**OUTPUT:**
- `[work_dir]/jtbd_calibrated.json` (chế độ parse_book, chuyển cho Skill 2)
- `[work_dir]/jtbd_recalibrated.json` (chế độ re-calibrate, chuyển cho Skill 2)
- `[work_dir]/audiences_parsed.json` (file phụ, dùng để enrich Decision Map ở các bước sau)

## 3. Quy Trình Thực Thi

> ⚠️ **Cách ly Rác (Warning Isolation):** Chunks chứa cờ `> [!warning]` được parser tự động cách ly — không parse, không tạo JTBD entry. Không cần Agent xử lý.

**Bước 1 — Nạp dữ liệu thô:**

**1A. Chế độ calibrate (tạo mới từ sách)**
| `source_type` | Script | Ghi chú |
|---|---|---|
| `book` | `parse_book_audiences.py` | Parse file cache sách (META_BOOK_AUDIENCE / META_CHUNK_AUDIENCE) |

```bash
python .agents/skills/jtbd-calibrator/scripts/parse_[source_type]_audiences.py \
       [source_file] --output_json "[work_dir]/audiences_parsed.json"
```

**1B. Chế độ re-calibrate (hiệu chỉnh lại kho hiện tại)**
```bash
python .agents/skills/jtbd-calibrator/scripts/extract_existing_audiences.py \
       --audience-index "vault/01-Atomic/Audiences/_audience_index.yaml" \
       --vault-root "[vault_root]" \
       --output-json "[work_dir]/audiences_parsed.json"
```

**Bước 2 — Phân Lô Dữ Liệu & Sinh Context (Script):**
```bash
python .agents/skills/jtbd-calibrator/scripts/prepare_calibration_batches.py \
    --parsed-json "[work_dir]/audiences_parsed.json" \
    --split-dir "[work_dir]/calib_batches" \
    --batch-size 5 \
    --source-file "[source_file_neu_co]" \
    --source-link "[Ten_Sach_neu_co]"
```
> Script tự động đọc `mode` từ JSON và sinh context file phù hợp. Bỏ qua `--source-file` và `--source-link` nếu chạy chế độ re-calibrate. Lệnh sinh `ctx_{uid}.md` riêng cho mỗi uid kèm **context password**. Đọc file context khi cần sửa lỗi #2, #3 hoặc #4.

**Bước 3 — JTBD Calibration (Chu trình xử lý tịnh tiến):**

Đọc **Phần 4: TIÊU CHUẨN HIỆU ĐÍNH JTBD** ở cuối file này. Lặp lại chu trình sau cho đến khi hệ thống báo hoàn thành:

1. **Cấp phát dữ liệu:**
```bash
python .agents/skills/jtbd-calibrator/scripts/prepare_calibration_batches.py \
    --session-dir "[work_dir]/calib_batches" --get-next
```
> Dùng `view_file` đọc `[work_dir]/calib_batches/current_calib_batch.json` để lấy danh sách cần xử lý.

2. **Hiệu chỉnh JTBD (Calibration):** Với mỗi mục trong batch, template `calib_eval_temp.json` có `audience_main_job` và `audience_circumstance` **rỗng**. Đọc `jtbd_raw` từ `current_calib_batch.json` (bước cấp phát), bóc tách thành Main Job và Circumstance, rồi hiệu chỉnh 4 biến theo **đúng thứ tự** sau:

   > **Mode re-calibrate:** Template `calib_eval_temp.json` có `audience_main_job` và `audience_circumstance` **đã được pre-fill** với giá trị hiện tại (không rỗng). Không cần bóc tách từ `jtbd_raw`. Đọc giá trị pre-fill → chạy qua tiêu chuẩn → hiệu chỉnh nếu vi phạm, giữ nguyên nếu đạt chuẩn.

   **a. `audience_main_job` (Hiệu chỉnh đầu tiên):**
   Đọc giá trị raw pre-fill → Chạy qua tiêu chuẩn Main Job (Phần 4.1) và tiêu chuẩn Problem Space (Phần 4.3) → Ghi đè bằng bản đã hiệu chỉnh.
   Nếu Main Job chứa Clarifier, Clarifier cũng phải đạt chuẩn Problem Space theo Phần 4.2 và 4.3.

   **b. `audience_circumstance` (Hiệu chỉnh thứ hai):**
   Đọc giá trị raw pre-fill → Chạy qua tiêu chuẩn Clarifier & Circumstance (Phần 4.2) và tiêu chuẩn Problem Space (Phần 4.3) → Ghi đè bằng bản đã hiệu chỉnh.

   **c. `audience_Job_performer` (Hiệu chỉnh thứ ba):**
   Dựa trên `audience_main_job` **ĐÃ HIỆU CHỈNH** ở bước (a), suy luận Danh xưng cụ thể phù hợp theo Phần 4.4.

   **d. `aliases` (Sinh lại cuối cùng):**
   Kết hợp `audience_main_job` + `audience_circumstance` **ĐÃ HIỆU CHỈNH** và tự suy ra 2-3 cụm từ đồng nghĩa phổ biến mà người bình thường sẽ dùng để diễn đạt cùng một Job trong cùng Circumstance.

   **e. `reason`:**
   Liệt kê số thứ tự lỗi đã sửa (theo Checklist 4.1.2 #1-#7, 4.2 #8-#9, 4.3 #10-#12) + mô tả ngắn gọn.
   - Nếu giữ nguyên giá trị raw → ghi `"Đạt chuẩn, giữ nguyên"`.
   - Nếu có lỗi #2, #3 hoặc #4 → **BẮT BUỘC** đọc context file riêng của uid đó (trường `context_file` trong `current_calib_batch.json`) và thêm `ctx_pwd:[password]` vào cuối reason.
   - Ví dụ: `"Lỗi #1: Bỏ 'Giúp tôi'"` (không cần password)
   - Ví dụ: `"Lỗi #4: 'chăm sóc' → ongoing → context: tiêm chủng → 'Tiêm phòng cho con'. ctx_pwd:abc12345"` (có password)

3. **Ghi tệp kết quả tạm:** Hệ thống đã tự động tạo sẵn tệp `[work_dir]/calib_batches/calib_eval_temp.json` điền sẵn mật khẩu và cấu trúc. Hãy mở tệp đó ra bằng công cụ chỉnh sửa tệp (hoặc overwrite bằng write_to_file), thay thế CÁC TRƯỜNG `[ĐIỀN VÀO ĐÂY]` bằng câu trả lời hiệu chỉnh của bạn và lưu lại.

4. **Nộp bài:**
```bash
python .agents/skills/jtbd-calibrator/scripts/prepare_calibration_batches.py \
    --session-dir "[work_dir]/calib_batches" \
    --submit-file "[work_dir]/calib_batches/calib_eval_temp.json"
```
> Script tự động kiểm tra chất lượng keyword trước khi chấp nhận:
> - 🔴 Vi phạm → Submit bị từ chối. Đọc thông báo lỗi, sửa trực tiếp `calib_eval_temp.json`, lưu lại rồi gọi lệnh submit **lại cùng lệnh trên**. Lặp lại cho đến khi hết vi phạm.
> - ✅ CLEAN → Chấp nhận.

5. Chờ phản hồi. Nếu script báo hoàn thành (đã tự động sinh `jtbd_calibrated.json` hoặc `jtbd_recalibrated.json`), tiến trình hoàn tất. Hãy dừng thực thi và bàn giao file output tương ứng cho Agent điều phối.

---

## 4. TIÊU CHUẨN HIỆU ĐÍNH JTBD (REFERENCE)

### 4.1 Tiêu chuẩn Main Job

#### 4.1.1 Công thức phát biểu

```
Động từ (verb) + Tân ngữ (object) + [Clarifier tùy chọn]
```

Ví dụ mẫu chuẩn:
- **visit family on special occasions** *(thăm gia đình vào các dịp đặc biệt)*
- **remove snow from pathways** *(dọn tuyết khỏi lối đi)*
- **listen to music on a run** *(nghe nhạc khi chạy bộ)* — "on a run" là Clarifier
- **prepare a meal** *(chuẩn bị bữa ăn)* — không có Clarifier

#### 4.1.2 Checklist kiểm tra Main Job (7 điều kiện bắt buộc)

| # | Điều kiện | Hướng dẫn hiệu chỉnh | Ví dụ sai → đúng |
| :--- | :--- | :--- | :--- |
| 1 | **Bắt đầu bằng động từ** | Bỏ toàn bộ từ đệm/xưng hô ở đầu câu | "Giúp tôi lên kế hoạch kỳ nghỉ" → **"Lên kế hoạch kỳ nghỉ gia đình"** |
| 2 | **Đơn trị** — không "và/hoặc/and/or" | ⚠️ **Đọc context file** của uid để hiểu domain → Hỏi "Why?" 1 lần → gộp thành 1 Big Job → ghi `ctx_pwd` vào reason | "Rửa rau và cắt thịt" → Why? → **"Chuẩn bị bữa ăn"** |
| 3 | **Có chủ đích** — không hành vi cơ học | ⚠️ **Đọc context file** của uid → thay verb cơ học bằng verb mang mục tiêu → ghi `ctx_pwd` vào reason | "Nhìn vào bức tranh" → **"Thấu hiểu tác phẩm nghệ thuật"** |
| 4 | **Có trạng thái kết thúc** — verb phải telic (có điểm hoàn tất tự nhiên) | ⚠️ **Đọc context file** của uid. Áp dụng Litmus Test: *"[Tân ngữ] đã được [Verb]-ed → người thực hiện có thể dừng lại vì mục tiêu đã được giải quyết trọn vẹn?"* Nếu KHÔNG → verb ongoing → đọc context tìm hành động thay thế thỏa mãn CẢ HAI: (a) telic — pass litmus test, VÀ (b) có chủ đích — không rơi vào hành vi cơ học (#3). Ghi `ctx_pwd` vào reason. VD sai: "Nuôi dưỡng trẻ" → "Cho con ăn" (telic nhưng cơ học, fail #3). VD đúng: "Nuôi dưỡng trẻ" → context về dinh dưỡng → **"Thiết lập chế độ dinh dưỡng cho con"** (telic + có chủ đích) | "Quản lý tài chính" → "tài chính đã được quản lý?" → Không → context: lập ngân sách → **"Lập ngân sách gia đình"** |
| 5 | **Góc nhìn cá nhân** | Bỏ lớp quan sát/sở thích, giữ nguyên action + object gốc | "Mọi người thích tham dự hội thảo" → **"Tham dự hội thảo"** |
| 6 | **Không công nghệ/giải pháp** | Trừu tượng hóa: bỏ method/technology, giữ mục tiêu gốc (suy từ verb+object) | "Tìm kiếm bằng từ khóa trong CSDL" → **"Truy xuất nội dung"** |
| 7 | **Kiểm tra ngược (Litmus Test cuối cùng)** | Áp dụng: *"[Tân ngữ] đã được [Verb]-ed → người thực hiện có thể dừng lại?"* Nếu câu trả lời là KHÔNG (hành động vẫn phải tiếp tục ngày mai) → quay lại #4 sửa verb | "Sức khỏe đã được quản lý?" → Không, vẫn phải quản lý → sửa verb (#4) |

> **Context file cho #2, #3, #4:** Mỗi uid có file context riêng (trường `context_file` trong `current_calib_batch.json`, sinh tự động ở Bước 2). Khi sửa lỗi #2, #3 hoặc #4, **BẮT BUỘC** đọc file context của uid đang xử lý, thêm `ctx_pwd:[password]` vào `reason`. Script sẽ reject nếu thiếu.
>
> **Re-validate bắt buộc:** Sau khi sửa bất kỳ lỗi nào, kiểm tra lại kết quả cuối cùng qua TOÀN BỘ 7 điều kiện. Đặc biệt: sửa #4 (telic) có thể tạo vi phạm #3 (cơ học); sửa #2 (gộp compound) có thể tạo vi phạm #4 (ongoing). Nếu kết quả vi phạm bất kỳ điều kiện nào → sửa lại cho đến khi thỏa mãn tất cả.
>
> **Need/Why:** Xử lý hoàn toàn ở Phần 4.3 Problem Space — áp dụng cho Main Job, Clarifier VÀ Circumstance.

---

### 4.2 Tiêu chuẩn Clarifier và Circumstance

Cả Clarifier và Circumstance đều mô tả bối cảnh (context) thực tế bao quanh việc thực hiện công việc. Bối cảnh được cấu thành từ 3 chiều kích:
1. **Thời gian (Time):** Khi nào? (muộn giờ, mùa cao điểm, dịp đặc biệt)
2. **Địa điểm (Place):** Ở đâu? (tại nhà, ngoài đường, dưới trời mưa)
3. **Trạng thái thực hiện / Ràng buộc tình huống (Manner):** Trạng thái thể chất, phương thức vận hành, ràng buộc tương tác trực tiếp (đang di chuyển, cho con, cho việc học tập, một mình)

#### 4.2.1 Phân biệt cấu trúc Clarifier và Circumstance

Sự khác biệt nằm ở **vị trí ngữ pháp và tính bắt buộc**:

| | Clarifier | Circumstance |
| :--- | :--- | :--- |
| **Vị trí** | Nhúng trực tiếp vào đuôi câu Main Job | Đứng đằng sau câu Main Job |
| **Cấu trúc** | Cụm giới từ bổ ngữ ở đuôi câu | Mệnh đề "Khi..." / "Trong khi..." / "Trong lúc..." |
| **Bản chất hệ thống** | Tùy chọn nhúng vào câu (Optional) | Bắt buộc xuất hiện đồng hành (Mandatory) |

Ví dụ Clarifier:
- "listen to music **on a run**" — "on a run" là Clarifier (nhúng trong Main Job)
- "chuẩn bị tài liệu **cho việc học tập**" — "cho việc học tập" là Clarifier
- "nuôi con nhỏ **có sự tham gia của ông bà**" — Clarifier khóa phạm vi nghiên cứu

**Cấu trúc viết Circumstance:** Bắt buộc dạng mệnh đề **"Khi..." (When)**, **"Trong khi..."** hoặc **"Trong lúc..." (While)**.
**Chủ ngữ:** Khi Circumstance liên quan đến hành vi hoặc trạng thái của ai đó, BẮT BUỘC nêu rõ chủ thể. CẤM ẩn chủ ngữ.

> ⚠️ **QUY TẮC HIỆU CHỈNH CIRCUMSTANCE:**
> - **#8** — Nếu thiếu cấu trúc "Khi..."/"Trong khi..."/"Trong lúc..." → viết lại dưới dạng mệnh đề "Khi...".
> - **#9** — Nếu ẩn chủ ngữ (VD: "Khi đang di chuyển" → ai?) → bổ sung chủ thể rõ ràng.
> - Nếu chứa Need/Why → áp dụng nguyên tắc "Tách, không vứt" (Phần 4.3.1, #10-#12).
> - KHÔNG thay đổi vị trí — không chuyển Clarifier thành Circumstance hay ngược lại.

---

### 4.3 Quy tắc Problem Space (áp dụng cho Main Job, Clarifier VÀ Circumstance)

Sức mạnh cốt lõi của JTBD là **tách biệt triệt để mục tiêu (Goal/Job) ra khỏi nhu cầu và thước đo thành công (Need/Why)**. Quy tắc dưới đây áp dụng cho **cả** Main Job, Clarifier và Circumstance.

#### 4.3.1 Ba nhóm loại trừ Need/Why

Bất kỳ từ ngữ nào mô tả các khía cạnh sau đều **không được phép** xuất hiện trong Main Job, Clarifier hoặc Circumstance:

**Nhóm 1 (#10) — Tính từ/trạng từ chỉ chất lượng hiệu suất:**
Nhanh, dễ dàng, rẻ, an toàn, toàn diện, hiệu quả, chính xác, lành mạnh, thành công, bền vững, tối ưu, đúng đắn...
→ Đây là thước đo so sánh giữa các giải pháp, phải tách riêng thành Needs.

**Nhóm 2 (#11) — Kỳ vọng cảm xúc hoặc mệnh đề phụ chứa cảm xúc:**
Tận hưởng, thấy vui, bớt lo lắng, yêu thích, vừa lòng, bớt giận, "mà không làm tổn thương...", "mà không gây áp lực...", "mà không ảnh hưởng đến..."
→ Là thước đo cảm xúc xã hội, xử lý riêng ở tầng Needs.

**Nhóm 3 (#12) — Mệnh đề mục đích/hướng cải tiến:**
"nhằm...", "sao cho...", "in order to...", "so that...", "để tiết kiệm...", "để giảm thiểu...", "để hỗ trợ..."
→ Bản chất là Need/Desired Outcome (Minimize/Maximize), không phải Job.

**Nguyên tắc xử lý: Tách, không vứt.**
Khi phát hiện Need/Why, tách phần Need/Why ra khỏi câu phát biểu. Nếu bên trong Need/Why chứa context thực tế (đối tượng, hoạt động phẳng, tình huống), giữ lại context đó dưới dạng Clarifier phẳng.

| # | Nhóm | Hướng dẫn hiệu chỉnh | Ví dụ |
| :--- | :--- | :--- | :--- |
| #10 | Nhóm 1 (Qualifying adj) | Xóa adjective, giữ phần còn lại | "Tìm vé máy bay **rẻ nhất**" → **"Tìm vé máy bay"** |
| #11 | Nhóm 2 (Emotional) | Xóa cảm xúc, giữ context thực tế nếu có | "Lên kế hoạch kỳ nghỉ **mà gia đình đều tận hưởng**" → **"Lên kế hoạch kỳ nghỉ gia đình"** |
| #12 | Nhóm 3 (Purpose clause) | Xóa mệnh đề mục đích, giữ context thực tế nếu có | "Nấu ăn **nhằm đảm bảo dinh dưỡng cho gia đình**" → **"Nấu ăn cho gia đình"** |

⚠️ **Phân biệt từ "to" (khi viết tiếng Anh) — tránh quét mù quáng:**
1. *Prepositional verb* [HỢP LỆ — GIỮ]: "Listen **to** music", "Respond **to** issues"
2. *Direction* [HỢP LỆ — GIỮ]: "Commute **to** work", "Get **to** a destination"
3. *Infinitive of purpose* [CẤM — XÓA]: "Write a report **to** please my boss" → "Write a report"

#### 4.3.2 Bảng đối chiếu bối cảnh hợp lệ vs. bẫy Why

| Loại bối cảnh | Hợp lệ (Flat Context) | Bẫy "Why/Need" (SAI) | Phân tích lỗi |
| :--- | :--- | :--- | :--- |
| **Tác nhân con người** | "Chuẩn bị tài liệu **cho học sinh**" | "Chuẩn bị tài liệu **cho học sinh dễ hiểu**" | "Dễ hiểu" là qualifying adjective (Need) |
| **Bối cảnh hoạt động** | "Nghe nhạc **khi đang chạy bộ**" | "Nghe nhạc **khi đang chạy bộ để tăng thể lực**" | "Tăng thể lực" là thước đo hiệu suất (Why) |
| **Trạng thái tự nhiên** | "Lái xe **khi trời tối**" | "Lái xe **để rút ngắn thời gian di chuyển**" | Mục đích tối ưu hóa (Improvement Direction) |
| **Trạng thái tình huống** | "Lựa chọn đồ chơi **cho trẻ tự kỷ**" | "Lựa chọn đồ chơi **để hỗ trợ phát triển trí não**" | "Phát triển trí não" là lợi ích mong đợi (Why) |

> **Lưu ý về bối cảnh hoạt động phẳng:** "Việc học tập" (studying), "chuyến đi" (trip), "đang chạy bộ" (on a run) là các **hoạt động bối cảnh phẳng** — hoàn toàn không chứa tính từ chỉ chất lượng, không chứa cảm xúc, không có hướng cải tiến. Chúng chỉ ra khoảng thời gian/bối cảnh lớn bao quanh hành động, do đó **hoàn toàn hợp lệ**. KHÔNG xóa nhầm.

---

### 4.4 Tiêu chuẩn Job Performer

- Tên gọi phải đơn giản, liên kết trực tiếp với Main Job **đã hiệu chỉnh**.
- Suy luận từ Main Job calibrated. VD: "nuôi dưỡng sức khỏe của trẻ" → "cha mẹ"; "giảng dạy kiến thức" → "giáo viên".
- Nếu Main Job quá chung chung không xác định được chủ thể (VD: "ăn cơm") → Giữ nguyên "Người".
- Lưu ý bối cảnh chuyên môn: Đầu bếp chuyên nghiệp vs. người nấu ăn tại nhà có nhu cầu hoàn toàn khác khi cùng "chuẩn bị bữa ăn".
