---
name: BUG-REPORT-Format-Paragraph-Spacing.md
last_update: 28/05/2026 21:50 (GMT+7)
role: Báo cáo điều tra lỗi (Bug Report / Brief)
usage: Tài liệu ghi nhận lỗi và giải pháp xử lý dòng trống/paragraph spacing trong Format Agent
output: Phân tích nguyên nhân, bằng chứng, phạm vi ảnh hưởng, hướng khắc phục cho lỗi Paragraph Spacing
logic: Truy vết từ cơ chế strip markers của Format Agent → lỗi dính đoạn/paragraph merging → đề xuất giải pháp xử lý khoảng trắng tối ưu
---

# 🐛 BUG REPORT: Paragraph Spacing Logic Flaw in Format Agent

**Ngày phát hiện:** 28/05/2026  
**Phát hiện bởi:** World-class Agentic AI System Architect  
**Mức độ:** Trung bình (Ảnh hưởng đến thẩm mỹ xuất bản và khả năng chống quét AI, nhưng hiện tại đang được LLM thông minh tự động bypass)  
**Trạng thái:** Đã ghi nhận Brief - Chờ phê duyệt thực thi  

---

## 1. Triệu chứng & Bằng chứng thực tế

Trong bài viết đã xuất bản `output/posts/2026-05-28-book_review_whole_brain.md` (hoặc các file nháp trung gian), có sự không nhất quán về mặt khoảng cách dòng trống giữa các đoạn văn nếu quy tắc xóa marker được áp dụng một cách máy móc.

### 1.1. Bằng chứng từ file nguồn `05-draft.md`
Khi kiểm tra cấu trúc phân đoạn tại Section `Deep Dive` trong `05-draft.md`:

```markdown
<!-- PARAGRAPH: 3 -->
<!-- PARAGRAPH_HEADING: Sự bất cân xứng bên trong não -->
Để hiểu vì sao phương pháp đồng cảm lại hiệu quả diệu kỳ đến vậy...
Khi trẻ hoảng loạn...
Những lý lẽ cứng nhắc giống như những mũi tên bắn vào hư không. Đó là lúc chúng ta cần một giải pháp khoa học thực sự hiệu quả.
<!-- PARAGRAPH: 4 -->
<!-- PARAGRAPH_HEADING: Giải pháp Kết nối và Điều hướng -->
Tiến sĩ Daniel J. Siegel và chuyên gia trị liệu Tina Payne Bryson đã đề xuất giải pháp...
```

**Quan sát kỹ thuật:**
- Không hề có dòng trống ngăn cách giữa dòng kết thúc của Paragraph 3 (`Những lý lẽ cứng nhắc...`) và marker mở đầu của Paragraph 4 (`<!-- PARAGRAPH: 4 -->`).

### 1.2. Cơ chế gây lỗi (The Spacing Flaw)
Theo chỉ dẫn trong `format-agent/SKILL.md` (Phase 7):
- `<!-- PARAGRAPH: N -->` → Xóa (luôn xóa)
- `<!-- PARAGRAPH_HEADING: ... -->` → Xóa

Nếu một bộ engine (Script Python Regex hoặc LLM tuân thủ máy móc) thực hiện phép thế chuỗi đơn thuần (string replace):
- `<!-- PARAGRAPH: 4 -->` $\rightarrow$ `""`
- `<!-- PARAGRAPH_HEADING: ... -->` $\rightarrow$ `""`

Kết quả văn bản sau khi xóa sẽ là:
```markdown
Những lý lẽ cứng nhắc giống như những mũi tên bắn vào hư không. Đó là lúc chúng ta cần một giải pháp khoa học thực sự hiệu quả.
Tiến sĩ Daniel J. Siegel và chuyên gia trị liệu Tina Payne Bryson đã đề xuất giải pháp...
```
**Hai đoạn văn bị gộp/dính liền sát nhau (chỉ cách nhau một ký tự xuống dòng `\n`, không có dòng trống `\n\n`), tạo thành một khối văn bản duy nhất về mặt hiển thị Markdown.**

---

## 2. Nguyên nhân gốc rễ (Root Cause)

1. **Thiếu tính bao phủ của quy tắc dọn dẹp (Naive Regex/String Strip):** Quy tắc định nghĩa trong `SKILL.md` chỉ tập trung vào việc xóa bản thân thẻ bình luận `<!-- ... -->` mà chưa chuẩn hóa khoảng trắng (whitespace) xung quanh thẻ đó.
2. **Sự không đồng bộ giữa Phase 5 và Phase 7:** 
   - `Voice Writer` (Phase 5) tạo ra draft nhưng không bắt buộc chèn dòng trống ngăn cách trước các marker `<!-- PARAGRAPH: N -->`.
   - `Format Agent` (Phase 7) thì giả định rằng văn bản thô đã có sẵn dòng trống, hoặc tin tưởng vào khả năng tự bù đắp của LLM khi sinh file.

> [!NOTE]  
> **Tại sao lỗi chưa bùng phát diện rộng?**  
> Hiện tại, Phase 7 đang sử dụng LLM thông minh để thực thi nhiệm vụ format. Dựa trên tri thức ngôn ngữ tự nhiên và quy tắc chung *"Giữa các đoạn: cách dòng trên 1 dòng trống"*, LLM tự động bổ sung dòng trống giữa các đoạn khi ghi file `07-final.md`. Lỗi này hiện chỉ là **lỗi logic tiềm ẩn (Silent Flaw)**, sẽ lập tức bùng phát thành **lỗi thật (Active Bug)** khi hệ thống được tối ưu hóa sang dạng Script-based / Deterministic Formatting (tiết kiệm token).

---

## 3. Đánh giá bối cảnh hệ thống (System Evaluation)

Dưới góc nhìn của chuyên gia kiến trúc thế giới (World-class System Architect):

*   **Vấn đề này có quan trọng không?**
    *   **Có.** Spacing và formatting chuẩn là ranh giới giữa một bài viết chuyên nghiệp và một bài viết "rác AI". Sự thiếu hụt dòng trống làm tăng tỷ lệ bị gắn cờ bởi các công cụ AI Classifier (do khối lượng câu dài dồn cục) và hủy hoại trải nghiệm đọc trên di động.
*   **Có cần giải quyết ngay lập tức không?**
    *   **Không.** Do năng lực tự phục hồi (Self-Healing) của LLM ở Phase 7 đang hoạt động tốt như một tấm lá chắn tạm thời.
*   **Trigger thời điểm giải quyết:** 
    *   **Trigger 1:** Khi refactor Phase 7 từ LLM-based sang Script-based (deterministic python/powershell formatter).
    *   **Trigger 2:** Khi nâng cấp bộ validation `validate-format.ps1` để tự động kiểm tra khoảng cách dòng giữa các đoạn văn (Poka-Yoke Spacing Gate).

---

## 4. Giải pháp Đề xuất Tối ưu (Anti-Overengineering)

### Phương án A: Chuẩn hóa Marker Cleaning (Đề xuất ưu tiên)
Thay vì hướng dẫn xóa thẻ bình luận một cách mù quáng, chúng ta sửa quy tắc thay thế trong `format-agent/SKILL.md` và script format/validation:

1. **Regex thay thế thông minh (Regex-based Replacement):**
   Thay thế marker bằng dòng trống một cách chủ động.
   ```regex
   # Tìm marker PARAGRAPH cùng với bất kỳ khoảng trắng/dòng trống liền kề nào
   \s*<!--\s*PARAGRAPH:\s*\d+\s*-->\s*(<!--\s*PARAGRAPH_HEADING:.*?-->\s*)?
   ```
   $\rightarrow$ Thay thế toàn bộ cụm này bằng đúng **1 dòng trống** (`\n\n`), trừ khi nó nằm ở đầu tài liệu.

2. **Cập nhật Hướng dẫn trong `SKILL.md` (Phase 7):**
   ```diff
   - - `<!-- PARAGRAPH: N -->` → Xóa (luôn xóa)
   - - `<!-- PARAGRAPH_HEADING: ... -->` → Xóa
   + - Marker phân đoạn (`<!-- PARAGRAPH: N -->` và `<!-- PARAGRAPH_HEADING: ... -->`): 
   +   Thay thế toàn bộ khối marker này (bao gồm cả dòng chứa nó) bằng đúng 1 dòng trống để ngăn cách giữa các đoạn văn, tránh lỗi dính đoạn.
   ```

### Phương án B: Poka-Yoke Spacing Validation (Bảo vệ Downstream)
Cập nhật script `validate-format.ps1` để tự động quét file `07-final.md` hoặc output post:
- Phát hiện bất kỳ dòng nào có độ dài lớn (ví dụ > 150 ký tự) đứng liền kề nhau mà không có dòng trống ngăn cách (loại trừ danh sách, bảng biểu).
- Nếu phát hiện $\rightarrow$ Trả về Exit Code `3` (Spacing Violation) để Agent tự động sửa đổi.

---

## 5. Kết luận & Hướng đi tiếp theo

Tài liệu này được lập ra để đóng vai trò làm **Brief chuẩn bị cho nâng cấp hệ thống (System Upgrade Brief)** ở conversation tiếp theo. 

*   **Hành động hiện tại:** Lưu trữ brief tại [docs/BUG-REPORT-Format-Paragraph-Spacing.md](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/docs/BUG-REPORT-Format-Paragraph-Spacing.md).
*   **Hành động tiếp theo:** Chuyển brief này sang session mới chuyên về Refactor/Optimize Phase 7 để triển khai tích hợp giải pháp Regex / Validation Spacing mà không ảnh hưởng đến các session sản xuất nội dung hiện tại.
