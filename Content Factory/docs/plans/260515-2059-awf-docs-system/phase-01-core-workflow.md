# Phase 01: Blueprint Workflow Core (`content-post.md`)
Status: ✅ Complete

## Objective
Phân tích và tài liệu hóa luồng sản xuất nội dung cốt lõi `content-post.md` thành sơ đồ trực quan (Mermaid Flowchart), làm rõ cơ chế 2 phiên (multi-session) và các chốt chặn (Poka-Yoke).

## Quy tắc thực thi
⚠️ **QUAN TRỌNG:** 
1. Mỗi lần thực thi CHỈ làm 1 task duy nhất, sau đó báo cáo và CHỜ User nghiệm thu (Review) trước khi sang task tiếp theo.
2. Tất cả các sơ đồ (flowchart) ĐỀU PHẢI dùng trục ngang (`graph LR` hoặc `flowchart LR`) và khung ngang (`direction LR` cho các subgraph).
3. Tuyệt đối KHÔNG dùng mã màu (loại bỏ hoàn toàn khai báo `classDef` và gán class `:::`). Việc biểu thị chức năng chỉ được xác định thông qua hình dạng (shape) thuần túy của node để đảm bảo sơ đồ sạch và thân thiện với machine-readable.
4. BẮT BUỘC gọi workflow `[/mermaid-diagram-writer]` để định hướng thực thi mỗi task. Kết quả của mỗi task (file sơ đồ và tài liệu `_info`) phải được lưu gọn trong 1 thư mục riêng biệt tương ứng, đặt tại `docs/flowcharts/`.
5. BẮT BUỘC mọi nội dung trong các subtask cũng phải được sơ đồ hóa vào chung 1 sơ đồ hoặc lưu lại vào note phù hợp (đối với những thông tin không thể sơ đồ hóa) để đảm bảo rằng kết quả tạo ra phản ánh chính xác và đầy đủ toàn bộ tài liệu của Factory thuộc về task đó.
6. Đối với các file không phải file code, BẮT BUỘC phải copy nguyên văn toàn bộ nội dung và phân bổ vào đúng note. KHÔNG ĐƯỢC diễn dịch lại và KHÔNG lặp lại những thông tin luồng đi đã thể hiện trên sơ đồ. Đặc biệt, LOẠI BỎ các thông tin hệ thống không cần thiết cho việc đọc hiểu sơ đồ như `execution_key` hay `file_key` ra khỏi note.


## Tasks
- [x] Phân tích logic hiện hành của `content-post.md`.
- [x] Vẽ sơ đồ Mermaid chi tiết cho luồng `content-post.md` (Đã lưu tại `docs/flowcharts/content-pipeline-macro.mmd`).
- [x] Cập nhật/Review lại file luồng `content-post.md` để tối ưu (nếu cần) trước khi chốt luồng. *(Skipped: Tuân thủ lệnh "Read-only" đối với các file của factory trong session này).*

## Files Created/Modified
- `docs/flowcharts/content-pipeline-macro.mmd`

---
Next Phase: [Phase 02](phase-02-specs.md)
