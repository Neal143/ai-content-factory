## IsFail
Kiểm tra cờ `$failed` tổng hợp từ tất cả các Check 1 đến Check 5. Nếu có bất kỳ lỗi nào, dừng toàn bộ luồng, in thông báo cho User và trả về `Exit 1`.

## IsPhase4
Kiểm tra xem có phải Phase 4 (Structure Designer) vừa PASS hay không. Nếu đúng, kích hoạt tạo Checkpoint tự động để lưu trạng thái phiên làm việc đầu tiên.

## RunCheckpoint
Chạy script `create-checkpoint.ps1` dưới dạng tiến trình con.

## ScanFiles
Duyệt qua danh sách các file output bắt buộc (từ 00 đến 07) theo đúng thứ tự Pipeline. Dựa vào sự tồn tại của file để tính toán `completed_phases` và `current_phase`.

## PrintWarn
Nếu quá trình quyét file để tính toán phase bị lỗi (ví dụ không tìm thấy bất kỳ file nào), sẽ in ra cảnh báo lỗi Checkpoint nhưng không thoát đột ngột (vẫn tiếp tục kiểm tra Phase 7).

## GenYaml
Ghi dữ liệu trạng thái vào file `checkpoint.yaml` (ghi đè nếu có).

## PrintHalt
In ra CLI tín hiệu `[HALT]` yêu cầu dừng Pipeline ngay lập tức để User mở cuộc hội thoại (session) mới và gõ `/content-post tiếp tục`.

## IsPhase7
Kiểm tra xem có phải Phase 7 (Format Agent - phase cuối) vừa PASS hay không.

## RunKeyRotate
Chạy script `generate-phase-key.ps1` để tự động xoay vòng khóa (rotate key) cho tất cả SKILL và Reference, chuẩn bị sẵn sàng cho phiên tạo bài viết tiếp theo.
