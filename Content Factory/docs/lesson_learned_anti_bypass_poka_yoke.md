# Bài Học Kinh Nghiệm: Thiết kế Hệ thống Agentic AI

**Ngày cập nhật**: 01/06/2026 11:00 (GMT+7)
**Vai trò**: Ghi chép lại các triết lý thiết kế lõi (Poka-Yoke) rút ra từ quá trình xây dựng hệ thống, giải quyết từ nguyên nhân gốc rễ (Tải nhận thức) đến kiến trúc lưu trữ (Cô lập dữ liệu) và cuối cùng là trải nghiệm của AI (Chống lách luật).

---

## 1. Bài học về Tải Nhận Thức (Cognitive Load & Micro-Tasking)

Đặc tính tâm lý cực kỳ quan trọng của Agentic AI là sự suy giảm chất lượng đầu ra (Degradation) khi bị "nhồi nhét" quá nhiều tác vụ phải suy luận trong cùng một lúc. **Agent rất lười và dễ mất tập trung đối với các tác vụ đòi hỏi logic phức tạp trên một tập dữ liệu quá dài**.

### 💡 THE BATCHING TIP (Nghệ thuật chia nhỏ và LLM-CAPTCHA)

Khi giao việc cho Agent, nếu đưa toàn bộ dữ liệu vào một file duy nhất hoặc yêu cầu báo cáo quá đơn giản, Agent sẽ có xu hướng:
1. Đánh giá sơ sài, copy/paste ở những items cuối.
2. Viết mã Python để tự động hóa (bypass) vì task có tính quy luật.
3. Bỏ sót dữ liệu do đứt gãy context window.

**Giải pháp 1: Tiền xử lý rác (Pre-filtering bằng Code)**
Trước khi đẩy dữ liệu vào lô cho AI suy luận, hệ thống phải tự động gạt bỏ những dữ liệu rác (Ví dụ: script `parse_book_audiences.py` tự động cách ly các chunk có chứa cờ `> [!warning]`). Đừng bắt LLM suy luận trên những dữ liệu mà code hoàn toàn có thể lọc được (Quy tắc: Code làm việc của Code, LLM làm việc của LLM). Giúp tiết kiệm token và giảm tải nhận thức ngay từ gốc.

**Giải pháp 2: Micro-Tasking (Chia lô dữ liệu)**
Bắt buộc chia nhỏ quy trình thành các vòng lặp xử lý (Batch-by-batch). Backend script cắt dữ liệu thành từng lô (VD: 5-10 items/lô). Agent xử lý xong lô nào, nộp bài lô đó để nhận lô tiếp theo.

**Giải pháp 3: Giao tiếp qua File (In-File Communication thay vì Terminal Bloat)**
Khi cung cấp dữ liệu lô cho Agent, KHÔNG BAO GIỜ in toàn bộ nội dung lô (ví dụ một mảng JSON dài 200 dòng) ra Terminal (stdout). Việc này sẽ làm "phình to" lịch sử ngữ cảnh (Context Window) của LLM, dẫn đến hiện tượng trôi ngữ cảnh (Context Drift) khiến Agent quên mất các instruction ở đầu.
*Cách làm chuẩn:* Script chỉ in ra màn hình: `"Lô tiếp theo đã sẵn sàng. Hãy đọc file current_batch.json để lấy dữ liệu"*. Bắt Agent dùng lệnh `view_file` để đọc.

**Giải pháp 4: LLM-CAPTCHA (Báo cáo chống fake bằng code)**
Việc chia lô là chưa đủ nếu output quá đơn giản. Để chặn triệt để hành vi viết script bypass, cấu trúc JSON nộp bài phải chứa các trường bắt buộc AI phải **suy luận ngôn ngữ (reasoning)** - thứ mà một đoạn script thuần túy không thể fake được (Ví dụ: bắt buộc chấm điểm C1-C5 và giải thích bằng text ở trường `reason`).
*Nguyên lý Thanh lọc (Output Sanitization):* Mặc dù bắt Agent xuất ra các trường `reason` để làm CAPTCHA, backend script khi nhận bài sẽ âm thầm vứt bỏ các trường này, chỉ chắt lọc lại dữ liệu cốt lõi để ráp thành file kết quả gọn nhẹ.

**Giải pháp 5: Cryptographic Token-Passing (Password Gate)**
Mặc dù đã chia lô, nếu tất cả các lô nằm phơi bày cùng lúc, Agent lười biếng có thể dùng tool đọc tất cả các file batch để xử lý song song. Để ngăn chặn, backend script sẽ "khóa" toàn bộ lô tương lai. Khi cấp phát lô hiện tại (`--get-next`), script sinh ra một `batch_password`. Khi nộp bài (`--submit-file`), bắt buộc phải nộp kèm đúng password này thì hệ thống mới chấm điểm và mở khóa lô tiếp theo. Cơ chế này ép Agent đi đúng tiến độ tuần tự tuyệt đối (Strict Sequential Progression).

#### Phân tích thực tiễn: Batching tại Session 2 vs Session 3

**1. Session 2 (Curate Vivids) - Lô dữ liệu phẳng (Flat Batching):**
- **Đặc thù dữ liệu:** Danh sách phẳng các Vivid candidates độc lập.
- **Cách chia lô:** Cắt ngẫu nhiên/tuần tự 10 vivids mỗi lô.
- **Cách đặt LLM-CAPTCHA:** Bắt buộc Agent phải chấm điểm 5 tiêu chí (C1-C5) và ghi rõ lý do bằng text vào trường `reason`.

**2. Session 3 (Audience Matcher) - Lô tịnh tiến & Rolling Dedup:**
- **Đặc thù dữ liệu:** Có tính phân cấp (Book level -> Chunk level) và phụ thuộc chéo (cần gom nhóm các Audience giống nhau).
- **Cách chia lô & CAPTCHA:**
  - *Giai đoạn Calibration:* Lô 5 items. Bắt buộc Agent đọc Hành động chung để **nội suy** ra Danh xưng và sáng tạo 2-3 `aliases`. (Script không thể tự sáng tạo từ đồng nghĩa).
  - *Giai đoạn Rolling Dedup:* Lô tịnh tiến. Nhận `anchors` và `items_to_process`. Bắt buộc áp dụng quy tắc 3-Verdict (IDENTICAL/DISTINCT) để đánh giá ngữ nghĩa xem có gộp hay không.

👉 *Kết quả:* Nhờ sự kết hợp 5 giải pháp trên, hệ thống vừa duy trì sự tập trung của AI, vừa ép AI phải "đổ mồ hôi" suy luận sâu, vô hiệu hóa hoàn toàn ý định dùng script để ăn gian.

---

## 2. Bài học về Quản lý Trạng thái & Cô lập Dữ liệu (Macro-Session Isolation)

Hệ quả đầu tiên của thiết kế Micro-Tasking là số lượng file sinh ra sẽ cực kỳ nhiều (raw text, temp file, log, discard list cho từng lô). Khi pipeline phình to, việc đổ tất cả I/O vào chung thư mục Root `run_folder` tạo ra một bãi rác không thể kiểm soát, gây nhiễu loạn luồng dữ liệu của các Agent chạy sau.

### 💡 Phân vùng I/O (Session Scoping)
- **Rác và Dữ liệu tạm (Session-scoped)**: Tất cả những file phục vụ riêng cho vòng lặp Micro-Tasking của một Agent (ví dụ: `chunk_NN_raw.txt`, `gate.json`, `current_batch.json`, `topic_eval_temp.json`) bắt buộc phải bị nhốt trong thư mục riêng của session đó (`session_1/`, `session_2/`, `session_4/`).
- **Dữ liệu chuyển giao (Handoff State)**: Những file mang tính chất bản lề, được dùng để truyền từ Agent này sang Agent khác (`parsed_metadata.json`, `pipeline_report.md`, `miner_progress.yaml`) mới được phép nằm ở Root `[run_folder]`. Điều này giúp hạ tầng lúc nào cũng sạch sẽ và có tính kế thừa cao.

### 💡 Cô lập đa tầng (Nested Isolation cho Multi-Phase Session)
Tại Session 3 (Audience Matcher), do Agent phải trải qua 3 vòng lặp khác nhau (Calibration, Dedup, External Match), việc vứt các file làm bài tạm (`current_batch.json`, `eval_temp.json`) trực tiếp vào `session_3/` sẽ gây ghi đè chéo và xung đột dữ liệu giữa các Phase.
- **Giải pháp:** Cấu trúc cách ly nhiều lớp. Vòng lặp nào nhốt file tạm vào thư mục con của vòng lặp đó (VD: `session_3/calib_batches/calib_eval_temp.json`). Bản thân thư mục `session_3/` cũng phải giữ sạch sẽ.

### 💡 Lỗ hổng Trailing Slash (Lỗi đường dẫn)
- Lỗi kinh điển trong Python khi dùng `os.path.dirname("thư_mục_con/")` là nó sẽ trả về `"thư_mục_con"` thay vì thư mục cha, dẫn đến việc file bị lưu lệch khỏi thư mục Root, làm đứt gãy cơ chế Session Scoping.
- **Giải pháp bọc thép**: Bắt buộc phải dùng `os.path.abspath(path)` trước khi bóc tách đường dẫn: 
  `run_folder = os.path.dirname(os.path.abspath(session_dir))`

### 💡 Tự phục hồi hạ tầng (Self-Healing Infrastructure)
- Khi chia nhỏ lô và nhốt vào nhiều thư mục sâu (VD: `session_3/dedup_batches/`), thư mục này có thể chưa tồn tại lúc script chạy. Nếu dùng script xuất JSON thẳng vào đó, Python sẽ crash báo lỗi `FileNotFoundError`.
- **Giải pháp**: Luôn gọi `os.makedirs(os.path.dirname(output_path), exist_ok=True)` trước khi ghi file, giúp hạ tầng tự sinh ra thư mục chứa nếu nó bị thiếu, tránh việc bắt Agent phải sửa lỗi thủ công.

### 💡 Quản lý Trạng thái & Khôi phục (Idempotent Resumability)
- Vấn đề: Với 50 lô dữ liệu, nếu cuộc hội thoại dài quá mức và Agent bị mất trí nhớ, hoặc bắt buộc phải tạo Chat mới (đổi Agent), làm sao Agent mới biết làm tiếp từ đâu?
- **Giải pháp**: Backend script phải luôn duy trì một file `session_state.json` để track biến `current_batch` và `completed`. Nhờ đó, Agent hoàn toàn là một **Stateless Worker**. Dù có thay Agent khác, nó chỉ cần chạy lệnh `--get-next`, hệ thống sẽ tự động đưa đúng cái lô đang làm dở ra mà không hề bị lặp lại từ đầu.

### 💡 Xóa mềm bảo toàn cấu trúc (Tombstoning)
- Khi Agent loại bỏ lượng lớn dữ liệu (Ví dụ: DISCARD các vivid ở Session 2), nếu xóa hẳn đoạn text đó ra khỏi file gốc, cấu trúc index và tọa độ chunk_id của toàn bộ sách sẽ bị xô lệch, làm hỏng dữ liệu của các Agent chạy sau.
- **Giải pháp:** Áp dụng kỹ thuật Tombstoning. Thay thế phần nội dung bị loại bằng chuỗi `[NOT_FOUND]`, giữ nguyên vị trí và cấu trúc metadata. Việc này bảo vệ tuyệt đối tính toàn vẹn tham chiếu (Referential Integrity).

### 💡 Tái thủy hóa Dữ liệu (Payload Re-hydration)
- Để giảm tải tối đa Context Window, trong các vòng lặp lô, script tước bỏ toàn bộ metadata nặng nề không cần thiết. Tuy nhiên, khi kết thúc một Macro-Session, các dữ liệu nguyên thủy đó (như `jtbd_raw`) sẽ được script tự động "join" (Re-hydrate) ngược trở lại vào file Handoff cuối cùng (VD: ghép vào `audience_decision_map.json`). Nhờ vậy, Session tiếp theo vừa nhận được quyết định mới, vừa có đủ ngữ cảnh phong phú ban đầu mà không cần tốn token parse lại toàn bộ sách.


---

## 3. Bài học xương máu về UX cho Agent (Anti-Bypass Pattern)

Sau khi đã chia nhỏ lô (Mục 1) và nhốt dữ liệu lô vào các session folder an toàn (Mục 2), hệ quả cuối cùng là Agent phải lặp lại thao tác xử lý file rất nhiều lần. Khi đó, Agent có xu hướng "đi tắt" (bypass) bằng cách tự động viết script Python để xử lý hàng loạt thay vì dùng IDE. Hậu quả là script tự viết thường bị lỗi logic hoặc ghi sai thư mục.

### 💡 THE GOLDEN TIP (Bí quyết thao túng tâm lý AI)

Khi backend script chuẩn bị dữ liệu batch và trả kết quả ra Terminal cho Agent, câu lệnh hướng dẫn (prompt) đóng vai trò sống còn.

**Tuyệt đối KHÔNG DÙNG TỪ "TẠO" (Create)**:
❌ *Sai:* "Vui lòng tạo một file `eval_temp.json` với cấu trúc sau..."
👉 *Hậu quả:* Từ khóa "Tạo" kích hoạt "tư duy lập trình" của Agent. Nó nghĩ rằng đây là một task coding và sẽ viết script.

**Bắt buộc dùng mẫu câu "ĐÃ ĐƯỢC TẠO SẴN" và "ĐIỀN VÀO CHỖ TRỐNG" (Pre-filled Template)**:
✅ *Đúng:* `"📝 Tệp làm bài ĐÃ ĐƯỢC TẠO SẴN tại: <path>. ⚠️ Vui lòng mở tệp này ra và SỬA/THAY THẾ các trường [ĐIỀN VÀO ĐÂY]."`
👉 *Kết quả:* Nhấn mạnh rằng file **đã tồn tại**, Agent sẽ từ bỏ ý định lập trình. Thay vào đó, nó sẽ bật công cụ IDE lên, mở file đó ra, và ngoan ngoãn điền kết quả vào đúng các vị trí được đánh dấu `[ĐIỀN VÀO ĐÂY]`.

Đây là triết lý **Poka-Yoke (chống sai lầm)** cấp độ UX cho AI. Backend script chịu trách nhiệm sinh template (Pre-filled), biến task phức tạp thành task "Fill in the blanks" cực kỳ nhẹ nhàng.

### 💡 Tước đoạt quyền I/O (Infrastructure-Delegated I/O)
Để đảm bảo Schema của các file cấu trúc lớn (ví dụ: `audiences_parsed.json`, `jtbd_calibrated.json`, `internal_map.json`, `collected_decisions.json`...) đạt độ chuẩn xác tuyệt đối 100%, hệ thống áp dụng nguyên tắc: **Agent tuyệt đối không được phép tự tạo các file kết quả cuối cùng**.
Thay vì yêu cầu Agent tự tổng hợp dữ liệu và tự tạo file, Backend Script sẽ tự động đọc các file `eval_temp.json` đã điền của Agent, gom lại, và tự động lập trình xuất ra file tổng hợp. Agent chỉ đóng vai trò là "bộ xử lý trung tâm" (Pure Function), còn Script đóng vai trò là "đôi tay" xử lý nhập xuất (I/O). Điều này loại bỏ hoàn toàn rủi ro AI bị ảo giác làm sai format JSON hoặc đặt sai tên file.

### 💡 Bắt lỗi khắt khe & Tự sửa chữa (Fail-Loud Validation & Self-Correction)
Ngay cả khi dùng Pre-filled template, LLM vẫn có thể mắc lỗi (ví dụ: quên điền một vài trường, tính tổng điểm C1-C5 sai logic, tựa ý đẻ thêm key lạ, hoặc truyền sai UID).
- **Giải pháp:** Khi Agent gọi lệnh `--submit-file`, backend script phải hoạt động như một giám khảo cực kỳ hà khắc. Nó phải quét toàn bộ JSON: kiểm tra `uid` có khớp không, có sót chữ `[ĐIỀN VÀO ĐÂY]` nào không, logic điểm số có hợp lệ không. 
- Nếu phát hiện lỗi, script lập tức quăng lỗi `sys.exit(1)` kèm thông báo cực kỳ rõ ràng ra Terminal (VD: `❌ LỖI: Chưa thay thế trường [ĐIỀN VÀO ĐÂY] ở UID 123`). Agent sẽ đọc được lỗi này và **tự động sửa lại file rồi submit lần 2** (Vòng lặp Self-Correction) trước khi "chất độc" kịp ngấm vào hệ thống.

---

## Tóm lược: Kiến trúc Poka-Yoke 3 Lớp
Kiến trúc hoàn hảo của một hệ thống Agentic AI vận hành theo chuỗi nhân quả sau:
1. **Lớp Xử lý (Processing Layer):** Áp dụng **Micro-Tasking** kết hợp với **LLM-CAPTCHA** và **Password Gate** để chống quá tải nhận thức và vô hiệu hóa năng lực đọc song song của AI.
2. **Lớp Hạ tầng (Infrastructure Layer):** Thiết lập **Macro/Nested Session Isolation** cùng cơ chế **Self-Healing** để giam lỏng dữ liệu rác, giữ cho Terminal và không gian làm việc luôn vô trùng.
3. **Lớp Giao tiếp (UX Layer):** Cài cắm **Anti-Bypass Prompting** (Pre-filled Templates) làm đòn thao túng tâm lý, ép Agent đóng vai trò "người điền form" thay vì "kỹ sư tự động hóa".
