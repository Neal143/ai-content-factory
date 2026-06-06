# Phase 02: Pipeline Verification
Status: ⬜ Pending
Dependencies: [Phase 01: Code Modification](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/plans/260521-1114-single-session-pipeline/phase-01-code-modification.md)

> **Mô tả file**:
> - **Tên file**: `plans/260521-1114-single-session-pipeline/phase-02-verification.md`
> - **Last update**: 21/05/2026 11:20 (GMT+7)
> - **Vai trò**: Đặc tả chi tiết các bước kiểm định và xác thực luồng chạy liền mạch của pipeline.
> - **Được sử dụng khi nào**: Sau khi hoàn thành Phase 01.
> - **Output**: Báo cáo kết quả kiểm thử.
> - **Tóm tắt logic**: Thực hiện chạy thử nghiệm độc lập Sentinel Phase 4 và Phase 7 để đảm bảo không còn lỗi cú pháp và không còn in tín hiệu ngắt pipeline.

---

## Objective
Xác thực thực tế luồng chạy của pipeline sau khi sửa đổi, đảm bảo Sentinel chạy thành công, checkpoint được tạo chính xác nhưng không phát sinh tín hiệu `[HALT]` ngắt quãng tại Phase 4.

## Requirements
### Functional
- [ ] Chạy kiểm thử độc lập script `create-checkpoint.ps1` với một thư mục chạy giả lập.
- [ ] Xác nhận file `checkpoint.yaml` được tạo đúng định dạng và có trạng thái `in_progress` khi chạy thử Phase 4.
- [ ] Xác nhận output terminal của script không còn bất kỳ dòng nào chứa nhãn `[HALT]`.

### Non-Functional
- [ ] Đảm bảo không làm ảnh hưởng đến dữ liệu bài viết thực tế đang sản xuất.

---

## Implementation Steps

### Task 1: Chạy thử độc lập script checkpoint
- **Mục tiêu**: Chạy script `create-checkpoint.ps1` thủ công trên một run folder thực tế (hoặc tạm thời) để kiểm tra output.
- **Lệnh thực thi**:
  ```powershell
  # Tìm một thư mục chạy gần nhất trong output/runs/
  # Ví dụ: output/runs/2026-05-21_intro-post/ (nếu có) hoặc tạo một folder test tạm thời
  powershell -ExecutionPolicy Bypass -File ".agents/scripts/create-checkpoint.ps1" -RunFolder "output/runs/[tên-thư-mục-gần-nhất]"
  ```
- **Xác nhận**: Output terminal hiển thị:
  `[CHECKPOINT] Da luu checkpoint.yaml thanh cong.`
  `[CHECKPOINT] Cap nhat checkpoint cho Phase ... Tiep tuc...`
  Không hiển thị dòng chữ `[HALT]` và không bắt dừng.

### Task 2: Chạy kiểm định Sentinel Phase 4
- **Mục tiêu**: Gọi Sentinel `detect-bypass.ps1` tại Phase 4 để xác nhận luồng kiểm định tự động gọi checkpoint thành công và không dừng.
- **Lệnh thực thi**:
  ```powershell
  powershell -ExecutionPolicy Bypass -File ".agents/scripts/detect-bypass.ps1" -RunFolder "output/runs/[tên-thư-mục-gần-nhất]" -Phase 4
  ```
- **Xác nhận**: Sentinel in ra `[SENTINEL PASS] Phase 4 PASS` và không có tín hiệu ngắt quãng.

---

## Test Criteria
- [ ] File `checkpoint.yaml` trong thư mục chạy thử có nội dung:
  ```yaml
  status: in_progress
  current_phase: ...
  completed_phases: [...]
  last_updated: "..."
  ```
- [ ] Đầu ra của Sentinel khi chạy Phase 4 đạt Verdict: **PASS**.

## Notes
Mọi lệnh chạy thử cần được ghi nhận log cụ thể để đối chiếu.
