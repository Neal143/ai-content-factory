---
name: Curate Vivids
description: Core Skill Phase 2 — Đánh giá, tinh lọc vivid metadata trong file sách thô và tiến hành niêm phong dữ liệu (parsed_metadata.json, pipeline_report.md).
---

# Curate Vivids Skill (Phase 2)

- **Tên file**: .agents/skills/curate-vivids/SKILL.md
- **Last update**: 21/05/2026 20:00 (GMT+7)
- **Vai trò**: Định nghĩa quy trình kỹ thuật tinh lọc vivid metadata và niêm phong dữ liệu.
- **Được sử dụng khi**: Được triệu hồi bởi **VividCuratorAgent** trong Phase 2 của workflow `/book-extractor`.
- **Output**: File cache `vault/02-sources/books/[Tên Sách].md` đã được tinh lọc, curation log `vivid_curation_log.json`, và các tệp niêm phong `parsed_metadata.json`, `pipeline_report.md`.
- **Tóm tắt logic hoạt động**: Nạp ngữ cảnh từ Blackboard -> Quét và đánh giá từng vivid theo bộ lọc loại thải và thang điểm rubric -> Loại bỏ vivid không đạt chất lượng -> Thực thi các script Python niêm phong.

---

## 1. Điều kiện Đầu vào

Các biến được nạp tự động từ tệp tin Blackboard chung `00-blackboard.yaml`:
1. **`book_name`**: Tên của cuốn sách đang xử lý (String).
2. **`cache_file`**: Đường dẫn file cache sách thô (e.g., `vault/02-sources/books/[Tên Sách].md`).
3. **`run_folder`**: Thư mục chạy của phiên (e.g., `.extraction_runs/[slug]_[YYYY-MM-DD]/`).
4. **`slug`**: Tên slug của cuốn sách (String).

---

## 2. Quy trình Thực thi Kỹ thuật

### Bước 2.1: Tiếp nhận & Validate
- Xác minh Blackboard đã được nạp chính xác.
- Kiểm tra file cache tại `cache_file` tồn tại và không rỗng.
- Kiểm tra `run_folder` tồn tại trên đĩa.

### Bước 2.2: Phân tích & Lọc Vivid (Vivid Curation per-chunk)

Duyệt qua MỖI chunk (từ `## Chunk N:` đến `</data_chunk>`) trong file cache sách:

#### 1. Nhận diện thẻ META vivid:
- `META_CHUNK_AUDIENCE: content_type=vivid_circumstance`
- `META_INSIGHT: content_type=vivid_insight | supports_insight=...`
- `META_KNOWLEDGE: content_type=vivid_knowledge | supports_knowledge=...`
- Bỏ qua các thẻ đã có body là `[NOT_FOUND]`.

#### 2. Bộ lọc loại thải toàn cục (Universal Disqualifiers):
Nếu vi phạm **BẤT KỲ** điều nào dưới đây -> **DISCARD ngay, không chấm điểm** -> Thay thế nội dung dòng body ngay dưới thẻ META thành `[NOT_FOUND]`.

| Mã | Disqualifier | Ghi chú |
|---|---|---|
| **U1** | Vivid quá "sáng tạo", không ăn nhập với nội dung chunk | Không thể truy vết nguồn gốc từ bất kỳ đoạn nào trong sách. |
| **U2** | Cliché quá mòn, não người đọc bỏ qua tự động | "ánh đèn cuối đường hầm", "bước ra khỏi vùng an toàn", "hai mặt đồng xu"... |
| **U3** | Là câu nhận định/kết luận/tri thức diễn đạt lại | Không chứa hình ảnh trực quan hoặc show-don't-tell. |
| **U4** | Trùng lặp hoàn toàn về ý | Đã có một vivid tương tự được giữ trong cùng chunk. |

#### 3. Bộ lọc loại thải riêng theo Loại Vivid:

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

---

### Bước 2.3: Chấm điểm Rubric (Chỉ áp dụng khi vượt qua vòng loại thải)

Chấm điểm độc lập cho từng vivid từ 0 đến 2 điểm trên 5 tiêu chí (Tối đa 10 điểm, cần đạt **>= 7 điểm** để được giữ lại - KEEP).

#### Rubric đánh giá chi tiết:

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

### Bước 2.4: Ghi Curation Log & Cập nhật Cache

1. Với mỗi vivid bị **DISCARD**:
   - Thay thế chính xác dòng body ngay dưới thẻ META của vivid đó thành `[NOT_FOUND]`.
   - **BẮT BUỘC giữ nguyên dòng thẻ META**, không sửa đổi hay xóa dòng META.
2. Tổng hợp tất cả kết quả đánh giá (KEEP & DISCARD) thành tệp tin JSON cấu trúc:
   - Đường dẫn ghi file: `[run_folder]/vivid_curation_log.json`
   - Sử dụng đúng format JSON của hệ thống (bao gồm các trường: `chunk_index`, `type`, `parent`, `original_text`, `disqualifier`, `scores`, `total`, `verdict`, `reason`).

---

### Bước 2.5: Thực thi Niêm phong Dữ liệu (Sealing Data)

Sau khi hoàn thành cập nhật file cache và ghi log curation, Agent bắt buộc phải chạy tuần tự các lệnh PowerShell sau để niêm phong tài sản dữ liệu của cuốn sách:

```powershell
# 1. Trích xuất cấu trúc metadata dạng JSON:
python .agents/skills/book-extractor/scripts/extract_metadata.py "[cache_file]" --output_json "[run_folder]/parsed_metadata.json"

# 2. Tạo Baseline đối chiếu CSV & Pipeline Report:
python .agents/skills/book-extractor/scripts/generate_baseline.py "[run_folder]/parsed_metadata.json" "[cache_file]" --report "[run_folder]/pipeline_report.md"
```

*Lưu ý*: Hãy lấy chính xác các đường dẫn `cache_file` và `run_folder` thực tế từ Blackboard để truyền vào lệnh, không để lại placeholder.

---

## 3. Output Specs

1. **File cache đã lọc**: Cập nhật đè lên `vault/02-sources/books/[Tên Sách].md`.
2. **Curation Log**: `[run_folder]/vivid_curation_log.json`.
3. **parsed_metadata.json**: Ghi nhận toàn bộ metadata của cuốn sách sau khi đã lọc sạch vivid.
4. **pipeline_report.md**: Báo cáo tổng thể tiến trình và đối chiếu chất lượng của đợt trích xuất sách.
