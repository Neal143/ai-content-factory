# Giải thích các Node Phase Key Generator

## start
Khởi chạy script `generate-phase-key.ps1`.
Được sử dụng khi: (1) User chạy thủ công lần đầu / sau crash. (2) `detect-bypass.ps1` gọi tự động sau Phase 7.

## check_param
Kiểm tra xem script có được truyền tham số `PersonaPath` không.

## auto_detect
Nếu không có tham số `PersonaPath`, script tự động dò tìm thư mục `personas/`. Nếu chỉ có duy nhất 1 thư mục con, nó sẽ tự động nhận diện đó là Persona mặc định.

## loop_skills
Lặp qua 9 thư mục kỹ năng (semantic-router, idea-curator, insight-agent, hook-engineer, structure-designer, persona-loader, voice-writer, qa-checker, format-agent).

## replace_skill_key
Tìm Regex `(?m)^> EXECUTION_KEY: .+$` trong file `SKILL.md` tương ứng.

## save_skill
Ghi đè file với một mã Hex ngẫu nhiên 8 ký tự (unique cho mỗi file).

## inc_fail_skill
Nếu file `SKILL.md` không tồn tại hoặc không tìm thấy placeholder `EXECUTION_KEY`, báo lỗi và tăng bộ đếm `FailCount++`.

## next_skill
Tiếp tục vòng lặp cho đến khi duyệt hết 9 file `SKILL.md`.

## loop_refs
Lặp qua 3 file Reference của Phase 5 (voice-writer): `writing-rules.md`, `anti-ai-patterns.md`, `english-blacklist.md`.

## replace_ref_key
Tìm Regex `(?m)^> FILE_KEY: .+$` trong file Reference tương ứng.

## save_ref
Ghi đè file với một mã Hex ngẫu nhiên 8 ký tự.

## inc_fail_ref
Nếu file Reference không tồn tại hoặc không tìm thấy placeholder `FILE_KEY`, báo lỗi và tăng bộ đếm `FailCount++`.

## next_ref
Tiếp tục vòng lặp cho đến khi duyệt hết 3 file Reference.

## check_persona
Nếu giá trị `PersonaPath` tồn tại, tiến hành inject FILE_KEY cho các file Persona. Nếu không, bỏ qua vòng lặp Persona.

## loop_persona
Lặp qua 5 file cấu hình Persona YAML của Phase 6 (qa-checker): `voice-dna.yaml`, `scoring-rules.yaml`, `audience.yaml`, `profile.yaml`, `authorities.yaml`.

## replace_persona_key
Tìm Regex `(?m)^# FILE_KEY: .+$` trong file Persona tương ứng.

## save_persona
Ghi đè file với một mã Hex ngẫu nhiên 8 ký tự.

## inc_fail_persona
Nếu file Persona YAML không tồn tại hoặc không tìm thấy placeholder `# FILE_KEY`, báo lỗi và tăng bộ đếm `FailCount++`.

## next_persona
Tiếp tục vòng lặp cho đến khi duyệt hết 5 file Persona.

## check_fail
Tổng kết số lỗi. Nếu `FailCount > 0`, script sẽ báo lỗi.

## fail_exit
Kết thúc script với mã Exit Code 1. (Dừng toàn bộ).

## update_status
Nếu không có lỗi (FailCount = 0), tìm file `.agents/workflows/content-post.md` và đổi trạng thái placeholder `> PIPELINE_STATUS: ` thành `SẴN SÀNG`.

## done
Kết thúc script thành công với mã Exit Code 0. Đã inject tổng cộng 17 keys (nếu có Persona) hoặc 12 keys (nếu không có Persona).
