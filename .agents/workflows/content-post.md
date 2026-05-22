---
description: Pipeline sản xuất nội dung viral 7 giai đoạn – chạy 1 phiên liên tục qua hệ thống Sub-Agents chuyên biệt.
---

> **Last Update**: 21/05/2026 11:22 (GMT+7)

# Workflow: Viết bài viral (Content Post)

> **LỆNH**: `/content-post [yêu cầu]` | `/content-post tiếp tục` (resume)

> PIPELINE_STATUS: SẴN SÀNG

## Output Rules

- Run folder: `output/runs/[YYYY-MM-DD]_[topic-slug]/`
- DIKW Combo: `00.5-dikw-combo.md` – output Bước 5, phục vụ resume (không có khi `Is_Novel_Angle=True`).
- Gate issues: `gate5-issues.md`, `gate6-issues.md` trong run folder.
- 🚫 KHÔNG ghi ra `output/` root hoặc `vault/output/`.
- Context mất/truncate – đọc file trong run folder.

## 🚫 HÀNH VI BỊ CẤM (Vi phạm = Dừng pipeline, escalate User)

1. CẤM tạo file script mới (`.py`, `.js`, `.sh`, `.ps1`).
2. CẤM hardcode nội dung bài viết vào biến string/array.
3. CẤM hardcode điểm QA vào frontmatter.
4. CẤM padding word count bằng copy-paste hoặc đoạn vô nghĩa.
5. CẤM ghi file vào `vault/output/`.
6. TRUNCATION GUARD: Context chứa `truncated due to its long length` – DỪNG pipeline, thông báo User.
7. SYSTEM DRIFT GUARD: Script báo lỗi – CHỈ sửa nội dung viết. Nghi script hỏng – DỪNG + BÁO User. KHÔNG tạo script dò lỗi, KHÔNG bóp méo bài.

## Hướng dẫn thực thi

### Bước 1: Gate - Kiểm tra Pipeline Status
- Đọc dòng `PIPELINE_STATUS` ở đầu file này.
- `SẴN SÀNG` – tiếp tục Bước 2.
- `CHƯA SẴN SÀNG` – **DỪNG**. Thông báo User chạy:
  ```
  powershell -ExecutionPolicy Bypass -File ".agents/scripts/generate-phase-key.ps1"
  ```
- **Ngoại lệ**: `/content-post tiếp tục` – bỏ qua Bước 1, chuyển thẳng mục Resume.

### Bước 2: Chọn Chế Độ Viết
- **AGENT**: Triệu hồi **ProfileSelectorAgent** (đọc nhận thức tại `.agents/agents/profile-selector/AGENT.md` và thực thi quy trình kỹ thuật tại `.agents/skills/profile-selector/SKILL.md`).
- **Ngoại lệ**: `/content-post tiếp tục` – bỏ qua Bước 2 (profile đã tồn tại từ lần chạy trước, prompt đã patch). Skip thẳng tới mục Resume.

### Bước 3: Validate Persona
Chạy [1 LẦN DUY NHẤT]:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/validate-persona.ps1"
```
- Exit 0 – Lấy `PERSONA_PATH` từ dòng cuối output. Lưu cho toàn pipeline.
- Exit 1 – DỪNG pipeline.

### Bước 4: Semantic Router
- **Input**: `[yêu cầu tạo nội dung]` từ lệnh.
- **AGENT**: Triệu hồi **SemanticRouterAgent** (đọc nhận thức tại `.agents/agents/semantic-router/AGENT.md` và thực thi quy trình định tuyến tại `.agents/skills/semantic-router/SKILL.md`).
- **Output**: Blackboard 6 biến (`Target_Pillar`, `Target_Audience`, `topic`, `Is_Novel_Angle`, `Persona_Path`, `resolved_jtbd`) – persist vào `00-blackboard.yaml` trong run folder.
  - `Is_Novel_Angle == False` – chạy **Bước 5 (DIKW Bridge)**.
  - `Is_Novel_Angle == True` – bypass Bước 5, chạy **Bước 6 (bắt đầu Phase 1)**.
- **Lưu snapshot cấu hình**: `Copy-Item "profiles/active.json" -Destination "[run-folder]/00-profile.json"` (trace ngược bài viết – cấu hình đã dùng).
- Sentinel Phase 0:
  ```powershell
  powershell -ExecutionPolicy Bypass -File ".agents/scripts/detect-bypass.ps1" -RunFolder "output/runs/[run-folder]/" -Phase 0
  ```

### Bước 5: DIKW Bridge
- **AGENT**: Triệu hồi **DikwBridgeAgent** (đọc nhận thức tại `.agents/agents/dikw-bridge/AGENT.md` và thực thi quy trình kết nối tri thức tại `.agents/skills/dikw-bridge/SKILL.md`).

### Bước 6: Pipeline 7 Phases (chạy qua các Sub-Agents chuyên biệt)

> **RULES:** (1) Blackboard lũy kế truyền nguyên cho mỗi phase. (2) Sau mỗi phase chạy Sentinel `detect-bypass.ps1 -RunFolder "output/runs/[run-folder]/" -Phase N`. FAIL – dừng, escalate. (3) Mỗi AGENT.md + SKILL.md có Self-Check Gate cuối.

**Bảng định tuyến Sub-Agents:**

| Phase | Agent | Cấu hình Agent | Core SKILL path | Output |
|-------|-------|----------------|-----------------|--------|
| 1 – Ý tưởng | **IdeaCuratorAgent** | `.agents/agents/idea-curator/AGENT.md` | `.agents/skills/idea-curator/SKILL.md` | `01-idea-brief.md` |
| 2 – Nghiên cứu | **InsightAgent** | `.agents/agents/insight-agent/AGENT.md` | `.agents/skills/insight-agent/SKILL.md` | `02-research-brief.md` |
| 3 – Hook / Mở bài | **HookEngineerAgent** | `.agents/agents/hook-engineer/AGENT.md` | `.agents/skills/hook-engineer/SKILL.md` | `03-hook.md` |
| 4 – Cấu trúc / Dàn ý | **StructureDesignerAgent** | `.agents/agents/structure-designer/AGENT.md` | `.agents/skills/structure-designer/SKILL.md` | `04-outline.md` |
| 4.5 – Persona | **PersonaLoaderAgent** | `.agents/agents/persona-loader/AGENT.md` | `.agents/skills/persona-loader/SKILL.md` | `04.5-persona-pack.md` |
| 5 – Viết bài | **VoiceWriterAgent** | `.agents/agents/voice-writer/AGENT.md` | `.agents/skills/voice-writer/SKILL.md` | `05-draft.md` |
| 6 – QA & Scoring | **QaCheckerAgent** | `.agents/agents/qa-checker/AGENT.md` | `.agents/skills/qa-checker/SKILL.md` | `06-qa-result.md` |
| 7 – Đóng gói | **FormatAgent** | `.agents/agents/format-agent/AGENT.md` | `.agents/skills/format-agent/SKILL.md` | `07-final.md` + `output/posts/[YYYY-MM-DD]-[topic-slug].md` |

**Quy tắc thực thi của Sub-Agents:**
1. Mỗi phase: Đọc cấu hình nhận thức của tác nhân tại tệp **`AGENT.md`** để nạp vai trò tư duy chuyên biệt, sau đó bắt buộc `view_file` quy trình **`SKILL.md`** tương ứng để lấy mã khóa thực thi `EXECUTION_KEY` và thực thi ghi output.
2. Sau khi ghi output, ghi dòng cuối: `<!-- execution_key: [EXECUTION_KEY từ SKILL.md] -->`
3. Chạy Sentinel kiểm định. **Phase 4.5 dùng `-Phase 45`** (integer).
4. Tất cả `run_command` trong Bước 6 đều `SafeToAutoRun = true`.

**Checkpoint tự động tại Phase 4:** Khi Phase 4 Sentinel PASS – `checkpoint.yaml` được tạo TỰ ĐỘNG bởi Sentinel ở trạng thái `in_progress` (làm điểm neo fail-safe). Agent **TIẾP TỤC** chạy Phase 4.5 ngay lập tức mà không dừng.

**Phase 6 REVISE:** `gate6-issues.md` – VoiceWriterAgent sửa draft và QaCheckerAgent chấm lại (tối đa 3 lần). FAIL – escalate User.

### Bước 7: Hoàn thành
Xác nhận: (1) artifacts trong run folder, (2) bài viết cuối tại `output/posts/` đã **strip sạch `<!-- execution_key: ... -->`**, (3) `production-log.md` & `hook-history.md` đã cập nhật bởi FormatAgent. Sentinel sẽ tự động lưu `checkpoint.yaml` thành completed. Thông báo User hoàn thành.

Sau khi hoàn thành:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/apply-profile.ps1" -Action restore
```

## CHECKPOINT & RESUME DỰ PHÒNG (FAIL-SAFE)

### Ghi checkpoint

`checkpoint.yaml` được tạo **TỰ ĐỘNG** bởi `detect-bypass.ps1` khi Phase 4 PASS và Phase 7 PASS.
Agent **KHÔNG** tự tạo checkpoint thủ công dưới mọi hình thức.

- Phase 4 PASS → `checkpoint.yaml` ghi `status: in_progress` (điểm neo dự phòng).
- Phase 7 PASS → `checkpoint.yaml` ghi `status: completed`.

### Resume (`/content-post tiếp tục`) — Chỉ dùng khi pipeline bị lỗi giữa chừng

> **Lưu ý Profile:** Khi resume, `profiles/active.json` vẫn tồn tại từ lần chạy trước.
> Prompt files đã được patch. KHÔNG chạy lại Bước 2.
> Restore sẽ chạy ở Bước 7 khi pipeline hoàn thành.

1. Bỏ qua Bước 1 (Gate) và Bước 2 (Chọn Chế Độ Viết).
2. Chạy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/scripts/resolve-checkpoint.ps1"
   ```
   - Exit 0 – Parse output: `RUN_FOLDER`, `CURRENT_PHASE`, `PERSONA_PATH`, `LOAD_FILES`.
   - Exit 1 – Thông báo User theo error message.
3. 🚫 **BẮT BUỘC `view_file`** đọc NỘI DUNG ĐẦY ĐỦ mọi file trong `LOAD_FILES` (path = `RUN_FOLDER/filename`). KHÔNG chỉ đọc tên file.
4. Chạy Phase 4.5 (BẮT BUỘC – do Persona Pack không còn trong context khi resume).
5. Tiếp tục từ phase sau `CURRENT_PHASE`. Không hỏi lại input.

## XỬ LÝ LỖI

1. FAIL Poka-Yoke gate – Agent tự sửa và Retry (max 3 lần).
2. FAIL 3 lần – Escalate User.
3. Agent drifting – Revert + ghi log.
4. Bypass Sentinel FAIL – Dừng ngay. Không retry. Escalate User kèm danh sách file vi phạm.
