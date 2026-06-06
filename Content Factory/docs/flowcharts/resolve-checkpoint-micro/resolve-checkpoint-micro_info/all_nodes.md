# Giải thích các Node trong Sơ đồ resolve-checkpoint

## scan_runs
Kiểm tra sự tồn tại của thư mục gốc: `output/runs`.

## fail_dir
Báo lỗi: `[FAIL] Thu muc 'output/runs' khong ton tai.` (Và `Exit 1`).

## find_inprogress
Lấy danh sách các thư mục run và sắp xếp giảm dần: `Sort-Object Name -Descending`.
Quét từng thư mục tìm file `checkpoint.yaml` có chứa đoạn văn bản: `status:\s*in_progress`.

## fail_no_session
Báo lỗi: `[FAIL] Khong tim thay pipeline dang do (checkpoint.yaml voi status: in_progress).` (Và `Exit 1`).

## parse_checkpoint
Trích xuất dữ liệu từ `checkpoint.yaml` bằng Regex:
- `current_phase`: Match `current_phase:\s*(\S+)`
- `completed_phases`: Match `completed_phases:\s*\[([^\]]+)\]`

## parse_bb
Đọc file `00-blackboard.yaml` trong thư mục run đang xử lý.
Trích xuất biến `Persona_Path` bằng Regex: `Persona_Path:\s*"?([^"\r\n]+)"?`

## fail_bb
Báo lỗi: `[FAIL] 00-blackboard.yaml khong ton tai trong $runFolderRel.` (Và `Exit 1`).

## build_files
Khởi tạo mảng `$loadFiles` chứa mặc định `"00-blackboard.yaml"`.
Nếu tồn tại file `"00.5-dikw-combo.md"`, bổ sung vào mảng.
Map `completed_phases` sang file theo bảng cấu hình (Verbatim):
```powershell
$phaseFileMap = @{
    1  = "01-idea-brief.md"
    2  = "02-research-brief.md"
    3  = "03-hook.md"
    4  = "04-outline.md"
    5  = "05-draft.md"
    6  = "06-qa-result.md"
    7  = "07-final.md"
    45 = "04.5-persona-pack.md"
}
```
Quá trình kiểm tra vật lý: Nếu file ánh xạ không tồn tại trên ổ cứng, in lỗi `[FAIL] File khong ton tai: ... (checkpoint ghi completed nhung file mat)` và cộng dồn biến đếm `$missingCount++`.

## check_corrupted
Đánh giá tính toàn vẹn thông qua biến đếm lỗi: `$missingCount -gt 0`.

## fail_corrupted
Báo lỗi: `[FAIL] $missingCount file(s) trong completed_phases khong ton tai. State bi corrupted.` (Và `Exit 1`).

## output_env
In ra môi trường 4 biến:
- `RUN_FOLDER=$runFolderRel`
- `CURRENT_PHASE=$currentPhase`
- `PERSONA_PATH=$personaPath`
- `LOAD_FILES=$($loadFiles -join ',')`
Trả về tín hiệu thành công (`Exit 0`).
