# 8-Point Quality Gate Reference

```
=== CẤU TRÚC (có data không?) ===
□ [1] NON-EMPTY:      Response > 200 ký tự
□ [2] CORRECT_CHUNK:   Giá trị `CHUNK=` trong response khớp tên chunk agent yêu cầu

=== NỘI DUNG BẮT BUỘC (①②) ===
□ [3] HAS_AUDIENCE:    `chunk_audience=` tồn tại, giá trị không rỗng; hoặc `META_CHUNK_AUDIENCE:` tồn tại, giá trị `[NO_JTBD_FOUND]`
□ [4] HAS_INSIGHT:     Mục ① có ít nhất 1 Insight với đủ: "insight_type=" và "insight_name="
□ [5] HAS_KNOWLEDGE:   Mục ② có ít nhất 1 Tri thức với đủ: "knowledge_type=", "knowledge_name=", "stance=", "supports_insight="

=== NỘI DUNG OPTIONAL (③④) ===
□ [6] HAS_OPTIONAL_MARKERS: Section ③④ phải có nội dung HOẶC [NOT_FOUND]. Không được bỏ trống.
     Áp dụng cho: ③ Evidence/Shocking fact, ④ Story/Case Study
     ⑤ Quote: không enforce. Fail sau supplement → chấp nhận, không cắm cờ.

=== KIỂM CHỨNG CHÉO (Cross-Validation) ===
□ [7] LINK_INTEGRITY (Script Xác thực Khóa Ngoại):
     - Mọi `supports_insight` (ở ②) bắt buộc khớp (hoặc là chuỗi con) của một `insight_name` (ở ①).
     - Mọi `supports_knowledge` (ở ③④⑤) bắt buộc khớp (hoặc là chuỗi con) của một giá trị `knowledge_name` đã định danh (ở ②).
     -> Tự động hoàn toàn bằng Python (Cho phép Substring Match để bao dung với lỗi LLM rút gọn chữ).
□ [8] SEMANTIC_ALIGNMENT (Agent kiểm duyệt Ngữ nghĩa - Semantic Judgment):
     - Trục 1 (Audience→Insight): Mức độ tương thích chặt chẽ giữa JTBD Audience và Insight.
     - Trục 2 (Insight→Knowledge): Trọng lượng hỗ trợ thực tế của Tri Thức đối với Insight được trỏ về.
     ⚠️ Mỗi trục riêng lẻ phải đạt điểm số ≥ 4. Bất kỳ trục nào có điểm số < 4 đều FAIL.

Phân chia thực thi:
- Gates [1-7]: Script gate_checker.py (Shift-Left Auto-Repair) + quality_gate.py (deterministic)
- Gate [8]: Agent đánh giá per-chunk (Semantic Score — cần LLM judgment)
```
