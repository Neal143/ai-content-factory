# Giải thích các Node của Content Pipeline Macro (core-workflow)

## cmd_new
Điểm bắt đầu của tiến trình tạo bài viết mới. Lệnh khởi chạy: `/content-post`.

## check_status
Cổng kiểm tra (Gate). Đọc biến số `PIPELINE_STATUS` nằm trong file `.agents/workflows/content-post.md`. Trạng thái BẮT BUỘC phải là `SẴN SÀNG` mới được chạy.

## p0
**Bước 3: validate-persona.ps1**
Script khởi chạy duy nhất 1 lần. Đọc và kiểm tra tính hợp lệ của thư mục và các file YAML của Persona. Trả về `PERSONA_PATH`.

## p05
**Bước 4: semantic-router**
SKILL Agent đầu tiên được gọi. Đọc yêu cầu topic và gán nó vào đúng một Pillar thương hiệu theo cấu hình.

## sen0, sen1, sen2, sen3, sen4, sen45, sen5, sen6
**Sentinel Gate (`detect-bypass.ps1`)**
Chốt chặn an ninh bắt buộc chạy sau mỗi Phase để rà quét tính toàn vẹn của mã hóa (EXECUTION_KEY và FILE_KEY). Nếu có bất kỳ dấu hiệu bypass (nhảy cóc, tự chế output), Sentinel sẽ ném lỗi.

## escalate
**Dừng khẩn cấp & Escalate User**
Điểm tập kết của mọi lỗi nghiêm trọng không thể tự phục hồi. Luồng sẽ chuyển hướng về đây và dừng ngay lập tức nếu:
1. PIPELINE_STATUS là "CHƯA SẴN SÀNG" (Pipeline bị khóa).
2. Lỗi Persona (Cấu hình Persona không hợp lệ, Exit code 1 từ `validate-persona.ps1`).
3. Trượt bài kiểm tra an ninh Sentinel (Exit code > 0) ở bất kỳ Phase nào. (Không được phép retry).
4. Lỗi Resolve Checkpoint (Không tìm thấy checkpoint hoặc run folder lỗi khi resume).
5. Voice Writer hoặc QA Checker vượt quá số lần tự sửa tối đa (Retry > 3 lần) ở Gate 5 hoặc Gate 6.
Trong mọi trường hợp, Agent phải báo cáo chi tiết cho User nguyên nhân và dừng thực thi.

## check_novel
Semantic Router xác định xem góc nhìn của bài viết có phải là ý tưởng đột phá hoàn toàn mới (`Is_Novel_Angle = True`) hay không.

## run_folder
Thư mục lưu trữ (Data Sink) của phiên chạy hiện tại. Tọa độ: `output/runs/[YYYY-MM-DD]_[topic-slug]/`.
Tất cả các output từ Bước 4 đến Phase 7 (ngoại trừ file xuất bản cuối cùng) đều được ghi vào đây để dễ dàng debug và resume. Các file bao gồm:
- `00-blackboard.yaml`: File bảng đen (Chứa 6 biến môi trường).
- `00.5-dikw-combo.md`: File nguyên liệu DIKW thô.
- `01-idea-brief.md`: Bản tóm tắt ý tưởng.
- `02-research-brief.md`: Kết quả nghiên cứu sâu.
- `03-hook.md`: Câu mở đầu giật tít.
- `04-outline.md`: Dàn ý chi tiết.
- `04.5-persona-pack.md`: Hồ sơ tính cách người viết.
- `05-draft.md`: Bản nháp bài viết.
- `06-qa-result.md`: Báo cáo chấm điểm của QA.
- `07-final.md`: Bản thảo cuối cùng (chưa strip mã hệ thống).

## p2_1
**Phase 1: idea-curator**
Từ insight, nảy ra góc nhìn contrarian (đi ngược số đông) và chấm Viral Score. Khởi tạo `01-idea-brief.md` vào Run Folder.

## p2_2
**Phase 2: insight-agent**
Mổ xẻ Idea Brief để đào sâu luận điểm (Sub-insight). Tạo `02-research-brief.md` vào Run Folder.

## p2_3
**Phase 3: hook-engineer**
Chuyên gia giật tít. Ứng dụng các Hook Formula để viết mở bài. Tạo `03-hook.md` vào Run Folder.

## p2_4
**Phase 4: structure-designer**
Kỹ sư dàn ý. Xây dựng xương sống cho bài viết theo chuẩn KCS v18.2 và VTS v19.0. Tạo `04-outline.md` vào Run Folder.

## pause_cp
Chốt chặn bảo vệ Session 1 (Kết thúc Phiên 1). Sentinel Phase 4 tự động tạo file `checkpoint.yaml`. Pipeline trả về cờ `[HALT]`. Agent thông báo cho User và DỪNG NGAY LẬP TỨC. (Mục đích: Giải phóng Context Window, chống LLM bị kiệt quệ token).

## cmd_resume
Điểm bắt đầu của Phiên 2. Lệnh khởi chạy: `/content-post tiếp tục`. (Được phép bypass chốt chặn PIPELINE_STATUS).

## p_resolve
Khởi chạy script `resolve-checkpoint.ps1` để dọn dẹp bộ nhớ và khôi phục môi trường.

## err_resolve
Nếu không tìm thấy `checkpoint.yaml` hoặc run folder bị lỗi, dừng và báo lỗi.

## load_files
Bước quan trọng của cơ chế phục hồi ngữ cảnh. Agent dùng tool `view_file` ĐỌC LẠI NỘI DUNG của toàn bộ các file markdown sinh ra từ Phiên 1 (được liệt kê trong biến `LOAD_FILES`). CẤM chỉ đọc tên file.

## p45
**Phase 4.5: persona-loader**
SKILL nạp Persona (Bắt buộc chạy sau khi Resume). Tạo `04.5-persona-pack.md` vào Run Folder.

## p5
**Phase 5: voice-writer**
Tiến hành viết nội dung chi tiết theo từng phân đoạn nhỏ. Tạo `05-draft.md` vào Run Folder.

## gate5
**Self-Check Gate 5**
Voice Writer tự chấm chéo chất lượng bài viết của mình.

## err_g5
Nếu Gate 5 không đạt, lỗi được lưu vào file `gate5-issues.md` trong Run Folder. Voice Writer bắt buộc tự đọc file này và tự sửa lỗi cục bộ.

## p6
**Phase 6: qa-checker**
Chuyên gia kiểm duyệt chất lượng độc lập. Chấm 130 điểm theo rubric và check Poka-Yoke "Atom Attribution". Tạo `06-qa-result.md` vào Run Folder.

## gate6
**Self-Check Gate 6**
QA Checker trả về Verdict (PASS/REVISE/FAIL).

## err_g6
Nếu Verdict là REVISE, lỗi lưu vào `gate6-issues.md` trong Run Folder. Luồng bắt buộc phải lùi lại một bước: Chuyển lại cho Voice Writer (Phase 5) viết lại và sửa phần bị sai.

## p7
**Phase 7: format-agent**
Định dạng lại bài viết. Đóng gói YAML Frontmatter, chuẩn hóa Spacing. Xuất bản `07-final.md` vào Run Folder.

## out_post
Output cuối cùng để publish (Đã strip mã Execution Key). Lưu tại `output/posts/[YYYY-MM-DD]-[topic-slug].md`.

## write_log
Cập nhật 2 file nhật ký lưu trữ toàn hệ thống: `production-log.md` và `hook-history.md`. Sau đó hệ thống tiến hành Xóa file `checkpoint.yaml`.

## check_cp
Kiểm tra xem `checkpoint.yaml` có tồn tại (trước khi bị xóa) hay không. (Quy trình đánh dấu session).

## update_cp
Đánh dấu status của checkpoint = `completed`.

## end_pipe
Kết thúc hoàn chỉnh Pipeline. Pipeline đã hoàn thành vòng đời và sẵn sàng cho chu trình mới.
