# Phase 03: Chuẩn hóa Thư viện Kỹ năng (SKILLS)
Status: ✅ Complete
Dependencies: Phase 02

## Objective
Tài liệu hóa kiến trúc nội bộ của các Kỹ năng (Micro LOD) vào thư mục `docs/`, tuyệt đối KHÔNG can thiệp hay chỉnh sửa bất kỳ file `SKILL.md` hay script nào của hệ thống.

## Quy tắc thực thi
⚠️ **QUAN TRỌNG:** 
1. Mỗi lần thực thi CHỈ làm 1 task duy nhất, sau đó báo cáo và CHỜ User nghiệm thu (Review) trước khi sang task tiếp theo.
2. Tất cả các sơ đồ (flowchart) ĐỀU PHẢI dùng trục ngang (`graph LR` hoặc `flowchart LR`) và khung ngang (`direction LR` cho các subgraph).
3. Tuyệt đối KHÔNG dùng mã màu (loại bỏ hoàn toàn khai báo `classDef` và gán class `:::`). Việc biểu thị chức năng chỉ được xác định thông qua hình dạng (shape) thuần túy của node để đảm bảo sơ đồ sạch và thân thiện với machine-readable.
4. BẮT BUỘC gọi workflow `[/mermaid-diagram-writer]` để định hướng thực thi mỗi task. Kết quả của mỗi task (file sơ đồ và tài liệu `_info`) phải được lưu gọn trong 1 thư mục riêng biệt tương ứng, đặt tại `docs/flowcharts/`.
5. BẮT BUỘC mọi nội dung trong các subtask cũng phải được sơ đồ hóa vào chung 1 sơ đồ hoặc lưu lại vào note phù hợp (đối với những thông tin không thể sơ đồ hóa) để đảm bảo rằng kết quả tạo ra phản ánh chính xác và đầy đủ toàn bộ tài liệu của Factory thuộc về task đó.
6. Đối với các file không phải file code, BẮT BUỘC phải copy nguyên văn toàn bộ nội dung và phân bổ vào đúng note. KHÔNG ĐƯỢC diễn dịch lại và KHÔNG lặp lại những thông tin luồng đi đã thể hiện trên sơ đồ. Đặc biệt, LOẠI BỎ các thông tin hệ thống không cần thiết cho việc đọc hiểu sơ đồ như `execution_key` hay `file_key` ra khỏi note.

## Tasks
1. [x] Vẽ sơ đồ Micro (LOD 2) cho `generate-phase-key.ps1` (Mở khóa luồng ở trên cùng).
2. [x] Vẽ sơ đồ Micro (LOD 2) cho `validate-persona.ps1` (Bước 3).

3. [x] Vẽ sơ đồ Micro (LOD 2) cho `semantic-router` (Skill — Bước 4)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `scripts/direct_match.ps1`

4. [x] Vẽ sơ đồ Micro (LOD 2) cho Global Scripts: Sentinel & Checkpoint
   - [x] Đã xử lý xong file `detect-bypass.ps1`
   - [x] Đã xử lý xong file `create-checkpoint.ps1`

5. [x] Vẽ sơ đồ Micro (LOD 2) cho `dikw-bridge` (Skill — Bước 5)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `references/injection-rules.md`

6. [x] Vẽ sơ đồ Micro (LOD 2) cho `idea-curator` (Skill — Phase 1)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `references/pillar-guide.md`
   - [x] Đã xử lý xong file `scripts/validate-idea.ps1`

7. [x] Vẽ sơ đồ Micro (LOD 2) cho `insight-agent` (Skill — Phase 2)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `scripts/validate-research.ps1`

8. [x] Vẽ sơ đồ Micro (LOD 2) cho `hook-engineer` (Skill — Phase 3)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `references/hook-formulas.md`
   - [x] Đã xử lý xong file `scripts/validate-hook.ps1`

9. [x] Vẽ sơ đồ Micro (LOD 2) cho `structure-designer` (Skill — Phase 4)
   - [x] Đã xử lý xong file `SKILL.md`
   - [x] Đã xử lý xong file `scripts/validate-outline.ps1`

10. [x] Vẽ sơ đồ Micro (LOD 2) cho `resolve-checkpoint.ps1` (Khôi phục Phiên 2)
    - [x] Đã xử lý xong file `resolve-checkpoint.ps1`

11. [x] Vẽ sơ đồ Micro (LOD 2) cho `persona-loader` (Skill — Phase 4.5)
    - [x] Đã xử lý xong file `SKILL.md`
    - [x] Đã xử lý xong file `scripts/validate-persona-pack.ps1`

12. [x] Vẽ sơ đồ Micro (LOD 2) cho `voice-writer` (Skill — Phase 5)
    - [x] Đã xử lý xong file `SKILL.md`
    - [x] Đã xử lý xong file `references/anti-ai-patterns.md`
    - [x] Đã xử lý xong file `references/english-blacklist.md`
    - [x] Đã xử lý xong file `references/writing-rules.md`
    - [x] Đã xử lý xong file `scripts/validate-draft.ps1`

13. [x] Vẽ sơ đồ Micro (LOD 2) cho `qa-checker` (Skill — Phase 6)
    - [x] Đã xử lý xong file `SKILL.md`
    - [x] Đã xử lý xong file `scripts/validate-qa.ps1`

14. [x] Vẽ sơ đồ Micro (LOD 2) cho `format-agent` (Skill — Phase 7)
    - [x] Đã xử lý xong file `SKILL.md`
    - [x] Đã xử lý xong file `scripts/validate-format.ps1`

15. [x] Viết tài liệu `docs/SKILLS_BLUEPRINT.md` thống kê kiến trúc tổ hợp và các điểm hardcode của toàn bộ hệ thống.
## Files to Modify (ONLY DOCS)
- `docs/flowcharts/*-micro.mmd` (Tạo sơ đồ cho 10 Skills)
- `docs/SKILLS_BLUEPRINT.md` (Tạo mới)
