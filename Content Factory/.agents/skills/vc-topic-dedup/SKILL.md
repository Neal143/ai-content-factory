---
name: Topic-Dedup
description: "Full semantic dedup cho Topics của một Persona. Quét toàn bộ pool hiện có, LLM đánh giá trùng lặp, script cascade merge."
last_update: 14/07/2026 15:46 (GMT+7)
---

# Topic-Dedup Skill

> **Tên file**: .agents/skills/vc-topic-dedup/SKILL.md
> **Vai trò**: Semantic dedup chỉ dành riêng cho Topics.
> **Sử dụng khi**: Gọi từ VaultCuratorAgent hoặc thủ công khi cần giảm số lượng topics.
> **Output**: `topic_map.yaml` đã gộp + atoms đã cập nhật + `vault_index.json` đã rebuild.

## INPUT
- `--output-dir`: Thư mục lưu trạng thái batch

## LUỒNG XỬ LÝ

> ⚠️ **ANTI-CHEATING RULE (CẤM GIAN LẬN)**:
> TUYỆT ĐỐI KHÔNG ĐƯỢC viết script Python/Bash (như `auto_run.py`) để chạy vòng lặp tự động và gán bừa kết quả "keep" cho toàn bộ mẻ.
> Mục đích của Skill này là CẦN TRÍ THÔNG MINH CỦA LLM để suy luận ngữ nghĩa (Semantic Reasoning). Bạn BẮT BUỘC PHẢI tự mình gọi lệnh `--get-next`, tự đọc `current_batch.json` bằng công cụ `view_file`, và tự động não suy luận cho từng item trước khi `--submit`. Viết script bypass là hành vi phá hoại hệ thống!

### Bước 1: Khởi tạo Batch
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill vc-topic-dedup \
    --meta-source "[persona-path]/topic_map.yaml" \
    --batch-size 25 \
    --output-dir "<output_dir>"
```
Script đọc `topic_map.yaml`, nhóm theo pillar prefix, chia rolling batch ~25 items/batch.
Mỗi batch chỉ chứa topics cùng pillar prefix.

### Bước 2: Vòng lặp xử lý (lặp đến khi script in "ALL_DONE")

**Bước 2a — Lấy batch:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --get-next --output-dir "<output_dir>"
```
Mở `<output_dir>/current_batch.json` bằng `view_file`.
File chứa 2 phần:
- `anchors`: danh sách survivors từ các batch trước (id + label)
- `items`: danh sách topics cần đánh giá trong batch này (id + label)

**Bước 2b — LLM đánh giá:**
Với mỗi batch, LLM nhận `items` (id + label) VÀ `anchors` (id + label), xác định:
- Topic nào trong items trùng lặp với nhau? Trùng lặp với anchor nào?
- Topic nào giữ lại (survivor — topic có tên chuẩn hơn)?
- Topic nào bị gộp (loser → resolved_to survivor hoặc anchor)?

**LUẬT SO KHỚP** (bắt buộc tuân thủ):
- CHỈ merge cùng pillar prefix (VD: p1_ với p1_). TUYỆT ĐỐI KHÔNG merge cross-pillar.
- Hai topics dùng từ giống nhưng mô tả 2 khía cạnh khác nhau của cùng chủ đề → KHÔNG merge.
- Chỉ merge khi 2 topics thực sự mô tả CÙNG MỘT khái niệm (Synonym, Paraphrase, Reorder).
- Phải đánh giá trên CẢ HAI `id` (English) và `label` (Vietnamese) để quyết định.
- LƯU Ý ĐỊNH DẠNG: Tham số `loser_id` và `survivor_id` phải là **chính xác ID của topic (có chứa dấu gạch dưới '_')**, tuyệt đối KHÔNG chứa đuôi `.md` và KHÔNG chứa dấu ngoặc vuông `[[ ]]`. Tuyệt đối không được nhầm lẫn với tên file (dấu gạch ngang '-').

Điền kết quả vào `<output_dir>/results_temp.json`:
```json
{
  "decisions": [
    {"action": "keep", "topic_id": "p1_child_brain_development"},
    {"action": "merge", "loser_id": "p1_whole_brain_integration", "survivor_id": "p1_child_brain_development", "reasoning": "..."}
  ]
}
```

**Bước 2c — Submit:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --submit --results-file "<output_dir>/results_temp.json" --output-dir "<output_dir>"
```
Script validate: kiểm tra survivor_id tồn tại trong pool hoặc anchors, cross-pillar firewall.
Nếu PASS → script gọi `cascade_merge.py --action merge-topic` cho từng cặp merge.
Survivors từ batch này được thêm vào anchors cho batch tiếp theo.
Quay lại Bước 2a.

### Bước 3: Rebuild Index
```powershell
powershell -ExecutionPolicy Bypass -File .agents/scripts/build-vault-index.ps1
```
