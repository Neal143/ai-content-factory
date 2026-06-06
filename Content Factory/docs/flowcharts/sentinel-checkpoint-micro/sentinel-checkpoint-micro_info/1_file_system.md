## Check1
Quét thư mục `output/*` và thư mục gốc `.` để tìm các file script bị cấm (`*.py`, `*.js`, `*.sh`). Mục đích: Ngăn chặn LLM tự ý sinh script ảo để hardcode dữ liệu hoặc bypass hệ thống. Nếu phát hiện, gán cờ `failed = $true`.

## Check2
Quét thư mục `vault/output/`. Theo thiết kế, output phải được lưu ở `output/`, không được lưu vào bên trong `vault`. Nếu phát hiện file lưu sai vị trí, gán cờ `failed = $true`.
