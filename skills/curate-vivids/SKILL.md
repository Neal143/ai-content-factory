---
name: Curate Vivids
description: Core Skill Phase 2 — Đánh giá, tinh lọc vivid metadata trong file sách thô và tiến hành niêm phong dữ liệu. Sử dụng 2 script automation (extract_vivids.py trích xuất vivid kèm context, apply_curation.py áp dụng quyết định).
---

# Curate Vivids Skill (Phase 2)

- **Tên file**: .agents/skills/curate-vivids/SKILL.md
- **Last update**: 29/05/2026 17:15 (GMT+7)
- **Vai trò**: Định nghĩa quy trình kỹ thuật tinh lọc vivid metadata và niêm phong dữ liệu sử dụng bộ script chuẩn hóa kèm cơ chế Cryptographic Token-Passing.
- **Được sử dụng khi**: Được triệu hồi bởi **VividCuratorAgent** trong Phase 2 của workflow `/book-extractor`.
- **Output**:
  1. File JSON candidates: `vivid_candidates.json`
  2. Thư mục batch files kèm password + session state: `vivid_chunks/`
  3. File JSON discards (script tự động tạo sau chuỗi đánh giá): `discards.json`
  4. File cache `vault/02-sources/books/[Tên Sách].md` đã được tinh lọc.
  5. Curation log `session_2/vivid_curation_log.json`.
  6. Các tệp niêm phong `parsed_metadata.json`, `pipeline_report.md`.
- **Tóm tắt logic hoạt động**: Nạp cấu hình từ Blackboard -> Chạy extract_vivids.py trích xuất vivid kèm context, gom batch kèm password ngẫu nhiên -> Agent tương tác qua lệnh --session-dir (lấy batch → xuất current_batch.json → agent đọc + chấm rubric C1-C5 → nộp bảng điểm → script xác thực password + đếm vivid + rubric scores → mở khóa batch tiếp) -> Script tự động sinh discards.json khi hoàn thành chuỗi -> Chạy apply_curation.py áp dụng quyết định, ghi log, và tự động niêm phong dữ liệu.

---

## 1. Điều kiện Đầu vào

Các biến được nạp tự động từ tệp tin Blackboard chung `00-blackboard.yaml`:
1. **`book_name`**: Tên của cuốn sách đang xử lý (String).
2. **`cache_file`**: Đường dẫn file cache sách thô (e.g., `vault/02-sources/books/[Tên Sách].md`).
3. **`run_folder`**: Thư mục chạy của phiên (e.g., `vault/.extraction_runs/books/[slug]_[YYYY-MM-DD]/`).
4. **`slug`**: Tên slug của cuốn sách (String).

---

## 2. Quy trình Thực thi Kỹ thuật

### Bước 2.1: Tiếp nhận & Validate
- Xác minh Blackboard đã được nạp chính xác.
- Kiểm tra file cache tại `cache_file` tồn tại và không rỗng.
- Kiểm tra `run_folder` tồn tại trên đĩa.

### Bước 2.2: Trích xuất & Đánh giá Vivid

**A. Trích xuất (1 lệnh duy nhất):**

Triệu hồi script trích xuất candidates kèm đầy đủ ngữ cảnh, tự động gom thành các batch files:

```powershell
python .agents/skills/curate-vivids/scripts/extract_vivids.py "[cache_file]" --output "[run_folder]/session_2/vivid_candidates.json" --split-dir "[run_folder]/session_2/vivid_chunks"
```

**B. Đánh giá (Cryptographic Batch-by-batch Processing):**

> ⛔ **CẤM TUYỆT ĐỐI**: KHÔNG ĐƯỢC PHÉP dùng `view_file`, `cat`, hay bất kỳ công cụ nào đọc trực tiếp file trong thư mục `vivid_chunks/`. KHÔNG ĐƯỢC PHÉP tự viết script truy cập thư mục này. KHÔNG ĐƯỢC PHÉP redirect/pipe stdout của lệnh ra file.

**Vòng lặp (Lặp lại cho đến khi hệ thống báo hoàn thành):**

1. **Lấy Batch hiện tại:**
```powershell
python .agents/skills/curate-vivids/scripts/extract_vivids.py --session-dir "[run_folder]/session_2/vivid_chunks" --get-next
```
> Script xuất file `[run_folder]/session_2/current_batch.json` và TẠO SẴN tệp làm bài `[run_folder]/session_2/vivid_eval_temp.json`. Dùng `view_file` đọc current_batch.json để xem nội dung batch.

2. **Đánh giá từng vivid** trong batch theo Bước 2.3:
   - **Vòng loại**: Kiểm tra disqualifiers (U1-U4, type-specific D1-D3). Vi phạm → DISCARD ngay, không cần chấm điểm.
   - **Vòng điểm**: Nếu vượt qua vòng loại, chấm 5 tiêu chí C1-C5 (0, 1, hoặc 2 điểm mỗi tiêu chí, tối đa 10). Tổng ≥ 7 → KEEP. Tổng < 7 → DISCARD với `disqualifier: "LOW_SCORE"`.

3. **Mở tệp Bảng điểm ĐÃ ĐƯỢC TẠO SẴN** tại `[run_folder]/session_2/vivid_eval_temp.json` và SỬA/ĐIỀN VÀO các trường `[ĐIỀN VÀO ĐÂY]`:
```json
{
  "password": "MẬT KHẨU LẤY TỪ TRƯỜNG batch_password",
  "evaluations": [
    {
      "vivid_fragment": "20+ ký tự đầu body vivid",
      "decision": "KEEP",
      "scores": {"C1": 2, "C2": 2, "C3": 1, "C4": 2, "C5": 1},
      "reason": "Lý do giữ"
    },
    {
      "vivid_fragment": "20+ ký tự đầu body vivid",
      "decision": "DISCARD",
      "disqualifier": "U3",
      "reason": "Lý do loại (vòng loại)"
    },
    {
      "vivid_fragment": "20+ ký tự đầu body vivid",
      "decision": "DISCARD",
      "disqualifier": "LOW_SCORE",
      "scores": {"C1": 1, "C2": 0, "C3": 1, "C4": 1, "C5": 1},
      "reason": "Lý do loại (vòng điểm)"
    }
  ]
}
```
> **Quy tắc bắt buộc (script sẽ reject nếu vi phạm):**
> - Số evaluations PHẢI BẰNG CHÍNH XÁC số vivid trong batch.
> - **KEEP**: bắt buộc có `scores` (C1-C5, mỗi tiêu chí 0/1/2). Tổng phải ≥ 7.
> - **DISCARD vòng loại**: `disqualifier` là mã lỗi (U1-U4, C-D1..3, I-D1..3, K-D1..3). Không cần `scores`.
> - **DISCARD vòng điểm**: `disqualifier` là `LOW_SCORE`, kèm `scores` có tổng < 7.

4. **Nộp Bài:**
```powershell
python .agents/skills/curate-vivids/scripts/extract_vivids.py --session-dir "[run_folder]/session_2/vivid_chunks" --submit-file "[run_folder]/session_2/vivid_eval_temp.json"
```

5. Nếu hệ thống in ra batch tiếp theo → Quay lại bước 1.
   Nếu hệ thống in ra "🎉 HOÀN THÀNH" → File `discards.json` đã được tạo tự động. Chuyển sang Bước 2.4.

---

### Bước 2.3: Bộ lọc & Tiêu chuẩn Đánh giá (Tư duy Agent)

#### 1. Bộ lọc loại thải toàn cục (Universal Disqualifiers):
Nếu vi phạm **BẤT KỲ** điều nào dưới đây -> **DISCARD ngay, không chấm điểm**.

| Mã | Disqualifier | Ghi chú |
|---|---|---|
| **U1** | Vivid quá "sáng tạo", không ăn nhập với nội dung chunk | Không thể truy vết nguồn gốc từ bất kỳ đoạn nào trong sách. |
| **U2** | Cliché quá mòn, não người đọc bỏ qua tự động | "ánh đèn cuối đường hầm", "bước ra khỏi vùng an toàn", "hai mặt đồng xu"... |
| **U3** | Là câu nhận định/kết luận/tri thức diễn đạt lại | Không chứa hình ảnh trực quan hoặc show-don't-tell. |
| **U4** | Trùng lặp hoàn toàn về ý | Đã có một vivid tương tự được giữ trong cùng chunk. |

#### 2. Bộ lọc loại thải riêng theo Loại Vivid:

**A. vivid_circumstance:**
- **C-D1**: Dùng ẩn dụ hoặc hình tượng hóa (phải là cảnh literal thực tế, không dùng "X như Y").
- **C-D2**: Thiếu cả 3 vector: Thời gian/Không gian + Hành động thị giác/thính giác + Trạng thái vật lý hoặc cảm xúc.
- **C-D3**: Chỉ chứa nhãn cảm xúc trực tiếp ("mệt mỏi", "lo lắng") mà không có yếu tố tả thực (show-don't-tell).

**B. vivid_insight:**
- **I-D1**: Là mô tả cảnh thực tế (literal) — bắt buộc phải là ẩn dụ.
- **I-D2**: Diễn giải cảm xúc trực tiếp ("cảm thấy cô đơn", "rất kiệt sức").
- **I-D3**: Ẩn dụ mờ nhạt, cần nhiều câu giải thích mới kết nối được với insight hỗ trợ.

**C. vivid_knowledge:**
- **K-D1**: Chỉ mô tả trạng thái kết quả tĩnh (không thể hiện quá trình vận hành X biến đổi thành Y).
- **K-D2**: Hình ảnh quá chung chung, có thể dùng để minh họa bất kỳ tri thức nào khác.
- **K-D3**: Là ví dụ minh họa trang trí đơn thuần, bỏ đi không ảnh hưởng đến mức độ hiểu tri thức.

#### 3. Chấm điểm Rubric (Chỉ áp dụng khi vượt qua vòng loại thải)
Chấm điểm độc lập cho từng vivid từ 0 đến 2 điểm trên 5 tiêu chí (Tối đa 10 điểm, cần đạt **>= 7 điểm** để được giữ lại - KEEP). Nếu tổng < 7 → DISCARD với `disqualifier: "LOW_SCORE"` kèm `scores`.

**Loại 1 — vivid_circumstance:**
- **C1 - Concreteness**: Nhắm mắt đọc xong có hình dung được cảnh cụ thể? (Đủ 3 vector = 2đ; 2 vector = 1đ; mờ nhạt = 0đ).
- **C2 - Alignment**: Biểu hiện vật lý trực tiếp của JTBD? (Không cần giải thích = 2đ; cần 1-2 câu cầu nối = 1đ; lỏng lẻo = 0đ).
- **C3 - Freshness**: Gắn liền với bối cảnh đặc thù của sách? (Đặc thù = 2đ; trung bình = 1đ; copy-paste được = 0đ).
- **C4 - Hook Power**: Đứng độc lập có tạo được căng thẳng kéo đọc tiếp? (Tạo tension tốt = 2đ; cần setup = 1đ; flat = 0đ).
- **C5 - Recognition**: Độc giả mục tiêu có thấy bản thân trong đó? (Tần suất gặp cao = 2đ; một bộ phận nhận ra = 1đ; chung chung = 0đ).

**Loại 2 — vivid_insight:**
- **C1 - Metaphor Sharpness**: Vật thể ẩn dụ có hữu hình? (Vehicle rõ, gợi cảm = 2đ; hơi mờ = 1đ; trừu tượng = 0đ).
- **C2 - Alignment**: Ẩn dụ là hiện thân trực tiếp của cảm xúc insight? (Vật hóa hoàn hảo = 2đ; cần kết nối = 1đ; lỏng lẻo = 0đ).
- **C3 - Freshness**: Ẩn dụ xuất phát riêng từ lập luận của sách? (Rất riêng biệt = 2đ; trung bình = 1đ; generic = 0đ).
- **C4 - Hook Power**: Bản thân câu ẩn dụ đứng một mình tạo tension? (Có tension = 2đ; cần context = 1đ; flat = 0đ).
- **C5 - Emotional Punch**: Gây phản ứng cảm xúc tức thì? (Gật đầu/xót xa ngay = 2đ; cần giải thích = 1đ; trung tính = 0đ).

**Loại 3 — vivid_knowledge:**
- **C1 - Mechanism Concreteness**: Chỉ rõ quá trình biến đổi X -> Y? (Biến đổi động = 2đ; kết quả tĩnh = 1đ; snapshot = 0đ).
- **C2 - Alignment**: Minh họa trực tiếp cơ chế vận hành tri thức? (Hiểu ngay cơ chế = 2đ; cần giải thích thêm = 1đ; lỏng lẻo = 0đ).
- **C3 - Freshness**: Gắn với cách lý giải riêng biệt của tác giả? (Độc đáo = 2đ; trung bình = 1đ; generic = 0đ).
- **C4 - Hook Power**: Có tiềm năng làm câu mở đầu content? (Mạnh = 2đ; trung bình = 1đ; flat = 0đ).
- **C5 - Mechanism Visibility**: Tự giải thích logic mà không cần đọc tri thức? (Rõ ràng = 2đ; cần kết hợp chữ = 1đ; vô thưởng vô phạt = 0đ).

---

### Bước 2.4: Áp dụng Quyết định & Niêm phong (1 lệnh duy nhất)

> File `discards.json` đã được hệ thống tự động tạo ở Bước 2.2. KHÔNG cần tạo thủ công.

Chạy **1 lệnh duy nhất** để tự động hóa toàn bộ việc cập nhật cache, ghi log, và niêm phong dữ liệu:

```powershell
python .agents/skills/curate-vivids/scripts/apply_curation.py --discards "[run_folder]/session_2/discards.json" --candidates "[run_folder]/session_2/vivid_candidates.json" --cache_file "[cache_file]" --run_folder "[run_folder]"
```

> **GHI CHÚ QUAN TRỌNG**: Không cần gọi thêm bất kỳ lệnh nào khác. Script apply_curation.py đã được lập trình để tự động chain tuần tự các script niêm phong dữ liệu (`extract_metadata.py` và `generate_baseline.py`) ngay bên trong nó.

---

## 3. Output Specs

1. **vivid_candidates.json** (Bước 2.2): Danh sách vivid thô kèm context chunk đầy đủ, định dạng JSON chuẩn. Dùng bởi `apply_curation.py`.
2. **vivid_chunks/** (Bước 2.2): Thư mục chứa batch files (kèm password), `_manifest.json`, và `session_state.json`. Agent tương tác qua lệnh `--session-dir`.
3. **discards.json** (Bước 2.2, script tự động tạo sau khi hoàn thành chuỗi đánh giá): Chứa danh sách quyết định loại bỏ vivid, format tương thích 100% với `apply_curation.py`.
4. **File cache đã lọc**: Cập nhật trực tiếp đè lên `vault/02-sources/books/[Tên Sách].md` (body các vivid bị loại đổi thành `[NOT_FOUND]`).
5. **session_2/vivid_curation_log.json** (Bước 2.4): Log tổng hợp chi tiết trạng thái đánh giá (KEEP/DISCARD) của từng vivid.
6. **parsed_metadata.json** (Bước 2.4, tự động sinh): Cấu trúc metadata hoàn chỉnh của cuốn sách.
7. **pipeline_report.md** (Bước 2.4, tự động sinh): Báo cáo tiến trình và chất lượng của lượt trích xuất.
