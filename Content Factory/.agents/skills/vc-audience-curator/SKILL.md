---
name: Audience-Curator
description: "Full semantic dedup và tổ chức lại cây phả hệ cho Audiences của một Persona."
last_update: 14/07/2026 15:46 (GMT+7)
---

# Audience-Curator Skill

> **Tên file**: .agents/skills/vc-audience-curator/SKILL.md
> **Vai trò**: Semantic dedup và xếp cây cho Audiences.
> **Sử dụng khi**: Gọi từ VaultCuratorAgent.
> **Output**: `_audience_index.yaml` đã gộp + atoms đã cập nhật + `vault_index.json` đã rebuild.

## INPUT
- `--output-dir`: Thư mục lưu trạng thái batch

## LUỒNG XỬ LÝ

> ⚠️ **ANTI-CHEATING RULE (CẤM GIAN LẬN)**:
> TUYỆT ĐỐI KHÔNG ĐƯỢC viết script Python/Bash (như `auto_run.py`) để chạy vòng lặp tự động và gán bừa kết quả "keep" cho toàn bộ mẻ.
> Mục đích của Skill này là CẦN TRÍ THÔNG MINH CỦA LLM để suy luận ngữ nghĩa (Semantic Reasoning). Bạn BẮT BUỘC PHẢI tự mình gọi lệnh `--get-next`, tự đọc `current_batch.json` bằng công cụ `view_file`, và tự động não suy luận cho từng item trước khi `--submit`. Viết script bypass là hành vi phá hoại hệ thống!

Audiences có cấu trúc cây phả hệ (Big -> Little -> Micro) qua trường `parent_audience`.
Trùng lặp có thể xảy ra giữa bất kỳ cấp nào: cùng level, cross-level, con trùng cha.
-> KHÔNG nhóm theo level. Gửi flat list toàn bộ audiences kèm context cây.

### Bước 1: Khởi tạo Batch
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill vc-audience-curator \
    --meta-source "vault/01-Atomic/Audiences/_audience_index.yaml" \
    --batch-size 20 \
    --output-dir "<output_dir>"
```
Script đọc `_audience_index.yaml`, tạo flat list toàn bộ audiences, chia rolling batch ~20 entries/batch.
Mỗi entry trong batch chứa: `file_ref`, `audience_level`, `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `parent_audience`, `aliases`.

### Bước 2: Vòng lặp xử lý (lặp đến khi script in "ALL_DONE")

**Bước 2a — Lấy batch:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --get-next --output-dir "<output_dir>"
```
Mở `<output_dir>/current_batch.json` bằng `view_file`.
File chứa 2 phần:
- `anchors`: danh sách survivors từ các batch trước (file_ref + level + JTBD fields + parent_audience)
- `items`: danh sách audiences cần đánh giá trong batch này (cùng format)

**Bước 2b — LLM đánh giá:**
Với mỗi batch, LLM nhận `items` VÀ `anchors`, xác định:
- Audience nào trong items trùng lặp với nhau? Trùng lặp với anchor nào?
- Survivor selection:
  + Nếu 1 trong 2 là parent của audience kia -> ưu tiên parent làm survivor.
  + Nếu cùng level: giữ audience có nhiều Insights trỏ tới hơn.
  + Nếu khác level: giữ audience ở level cao hơn (Big > Little > Micro).
- Audience nào bị gộp (loser -> resolved_to survivor hoặc anchor)?

**LUẬT SO KHỚP** (bắt buộc tuân thủ):
- MATCH: Hai audiences mô tả cùng JTBD (cùng performer + cùng main_job + circumstance chỉ khác cách diễn đạt). Áp dụng cho MỌI cặp level.
- NO MATCH: Khác main_job, HOẶC khác circumstance cực đoan (2 trạng thái khác nhau).
- Cascade khi merge sẽ tự động xử lý reparenting children, redirect references.
- LƯU Ý ĐỊNH DẠNG: Tham số `loser_file` và `survivor_file` phải là **chính xác tên file (dùng dấu gạch ngang '-')**, tuyệt đối KHÔNG chứa đuôi `.md` và KHÔNG chứa dấu ngoặc vuông `[[ ]]`. Tuyệt đối không được nhầm lẫn với ID (dấu gạch dưới).

Điền kết quả vào `<output_dir>/results_temp.json`:
```json
{
  "decisions": [
    {"action": "keep", "audience_file": "cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan"},
    {"action": "merge", "loser_file": "...", "survivor_file": "...", "reasoning": "..."}
  ]
}
```

**Bước 2c — Submit:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --submit --results-file "<output_dir>/results_temp.json" --output-dir "<output_dir>"
```
Script validate + gọi `cascade_merge.py --action merge-audience` cho từng cặp merge.
Survivors từ batch này được thêm vào anchors cho batch tiếp theo.
Quay lại Bước 2a.

### Bước 3: Rebuild Index
```powershell
powershell -ExecutionPolicy Bypass -File .agents/scripts/build-vault-index.ps1
```
