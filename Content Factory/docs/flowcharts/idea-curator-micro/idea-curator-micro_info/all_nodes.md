# Giải thích các Node Idea Curator

## ref_bb
File đầu vào (BẮT BUỘC): `00-blackboard.yaml`. Chứa các cấu hình cơ sở (`topic`, `Target_Pillar`, `Target_Audience`, `Is_Novel_Angle`).

## ref_pillar
File cấu hình: `.agents/skills/idea-curator/references/pillar-guide.md` (Verbatim 100%):
1. Pillar là gì?
Pillar (trụ cột) là 3-5 chủ đề chính mà người viết cam kết xoay quanh. Mọi bài viết đều phải thuộc về ít nhất 1 pillar. Viết ngoài pillar = mất thương hiệu cá nhân.
2. Cách đọc Pillars
Dữ liệu pillars được lưu trong `[Persona_Path]/pillars.yaml`. Nếu file trống, lấy từ `personas/_default/pillars.yaml`.
3. Cách chấm Viral Score
- Gây tranh cãi (4đ): Topic có đi ngược lại niềm tin phổ biến không?
- Cá nhân hóa (3đ): Người đọc có thấy mình trong đó không?
- Ứng dụng tức thời (3đ): Đọc xong có thể làm ngay không?
Tổng: /10. Cần ≥ 7 để PASS Gate 1.

## read_inputs
Đọc `00-blackboard.yaml`, thư viện Insight/Concept từ Vault (DIKW) và `pillar-guide.md`.

## check_mode
Kiểm tra cờ định tuyến: `Is_Novel_Angle` là `True` HOẶC DIKW trả về rỗng?

## mode_standard
Kịch bản 1 (Thuần Vault). Điều kiện: `Is_Novel_Angle == False` + Gói DIKW hợp lệ.
Hành động: BẮT BUỘC tham chiếu 100% Insight + Solution/Concept từ Vault. Không sáng tạo vượt xa nguồn.

## mode_improvise
Kịch bản 2 (Suy luận Sáng tạo). Điều kiện: `Is_Novel_Angle == True` HOẶC DIKW trả về rỗng.
Hành động: Dùng kiến thức LLM sáng tạo dựa trên `topic` + `Target_Pillar`. TUYỆT ĐỐI CẤM kết hợp chéo Data Vault.

## gen_brief
Khởi tạo Idea Brief:
1. Contrarian Angle: Điều gì đa số người ta tin là đúng nhưng thực ra sai (hoặc ngược lại)?
2. Core Tension: Mâu thuẫn cốt lõi mà reader đang chịu đựng.
3. Hidden Belief: Niềm tin ẩn mà bài viết sẽ phá vỡ.
4. Transformation Promise: Reader thay đổi gì sau khi đọc? (before → after rõ ràng).
5. Viral Score (tổng /10, cần ≥ 7).
6. ⛔ BẮT BUỘC giữ nguyên văn từ Blackboard: `topic`, `Target_Pillar`, `Target_Audience` (nếu có), `Is_Novel_Angle`. Bổ sung góc nhìn và lưu thành `01-idea-brief.md`.

## validate_script
Bắt đầu chạy script: `powershell -ExecutionPolicy Bypass -File ".agents/skills/idea-curator/scripts/validate-idea.ps1" -IdeaPath "[Đường dẫn file Idea Brief]"`

## check_blackboard
**CHECK 1: Blackboard Integrity**
Đảm bảo LLM giữ lại các biến cốt lõi từ Blackboard. Trích xuất `Is_Novel_Angle` để định tuyến các check kế. File bắt buộc phải có đủ `topics`, `Target_Pillar`, và `Is_Novel_Angle`.

## check_audience
**CHECK 2: Audience Routing**
Kịch bản 1 (Thuần Vault / `Is_Novel_Angle == False`) bắt buộc phải có đối tượng độc giả mục tiêu `Target_Audience`. Kịch bản 2 bỏ qua.

## check_viral
**CHECK 3: Viral Score Threshold**
Đảm bảo Viral Score được sinh ra đúng cấu trúc số (`Score X/10`) và vượt ngưỡng `>= 7`.

## check_structural
**CHECK 4: Structural Completeness**
Chống việc LLM bỏ sót các section yêu cầu trong Dàn bài. Bắt buộc phải có đủ 4 keyword section: `Contrarian`, `Core Tension`, `Hidden Belief`, `Transformation Promise`.

## check_dikw
**CHECK 5: DIKW Reference Integrity**
Kịch bản 1 (Thuần Vault) bắt buộc phải sử dụng Insight và Solution từ thư viện để đảm bảo chuyên môn. Bắt buộc có các keyword `insight` và (`solution` hoặc `concept`) trong nội dung file. Kịch bản 2 bỏ qua.

## revise_idea
Nếu Exit code > 0 ở bất kỳ rào cản nào: Đọc log báo cáo chi tiết, sửa Idea Brief theo lỗi. Tối đa 3 lần retry. Ghi log: `[Phase 1 Self-Check] Verdict: PASS/REVISE | Attempt: N/3`. Nếu FAIL 3 lần → Dừng pipeline, escalate cho User.
