## HasValidation
Kiểm tra xem Phase hiện tại có script validation tương ứng được cấu hình trong bảng `$validationScripts` hay không (các phase 1-7 và 45). Nếu có, chạy lại script đó. Nếu không, chuyển sang xét các luật kiểm tra inline.

## IsPhase0
Kiểm tra xem Phase hiện tại có phải là Phase 0 (Semantic Router) hay không. Do không dùng script validate rời, Semantic Router có cơ chế validation nội tuyến (inline) riêng.

## RunValidate
Hệ thống gọi lại script `validate-*.ps1` tương ứng bằng một tiến trình con (ví dụ: `validate-idea.ps1` cho Phase 1). Mục đích: Sentinel tự tay chạy lại bộ test, không tin tưởng vào báo cáo PASS của Agent.

## ValidateStatus
Kiểm tra Exit Code của script validation. Nếu khác `0`, tức là Agent đã báo cáo láo kết quả PASS -> gán lỗi (bật cờ Fail).

## Check5B
(Phase 0) Kiểm tra tính toàn vẹn của `00-blackboard.yaml`: Phải tồn tại và chứa đủ 4 trường bắt buộc `topic`, `Target_Pillar`, `Is_Novel_Angle`, `Persona_Path`.

## Check5C
(Phase 0) Kiểm tra định dạng của trường `topic`: Bắt buộc phải là `snake_case` tiếng Anh, dài từ 2 đến 4 từ.

## Check5D
(Phase 0) Kiểm tra trường `Persona_Path` không được chứa ký tự backslash kép (`\\`) do lỗi escape sai của LLM.
