---
name: Auto-Tagger
description: "Chuẩn hóa metadata (description + keywords) cho mỗi Atom trong Vault. Xử lý theo batch 10 atoms/lần."
last_update: 13/07/2026 09:38 (GMT+7)
---

# Auto-Tagger Skill

> **Tên file**: .agents/skills/auto-tagger/SKILL.md
> **Vai trò**: Sinh `description` và `keywords` cho các Atom chưa có metadata đầy đủ.
> **Sử dụng khi**: Được gọi từ VaultCuratorAgent sau khi skill sinh atom hoàn tất, hoặc thủ công khi cần tag lại file cũ.
> **Output**: Các file Atom đã cập nhật YAML frontmatter + `vault_index.json` đã rebuild.
> **Tóm tắt logic**: Nhận danh sách atoms → Script chia batch (10/batch) → Vòng lặp: get-next → LLM sinh metadata → điền template → submit (script validate + ghi YAML) → Sau tất cả batch: rebuild index.

> ⛔ **CẤM TUYỆT ĐỐI**:
> 1. KHÔNG ĐƯỢC PHÉP dùng `view_file` hay bất kỳ công cụ nào đọc trực tiếp file trong `vault/01-Atomic/`.
>    Toàn bộ nội dung atom chỉ được truy cập thông qua `current_batch.json` (field `atoms_content` chứa `frontmatter` + `body` của mỗi atom).
> 2. KHÔNG ĐƯỢC PHÉP tạo file script mới (`.py`, `.js`, `.sh`, `.ps1`).

## INPUT
- Danh sách đường dẫn file Atom cần xử lý (tương đối từ gốc workspace), truyền qua tham số `--atoms`.
- Thư mục lưu trạng thái batch, truyền qua tham số `--output-dir`.

## QUY TRÌNH THỰC THI

### Bước 1: Khởi tạo Batch
Chạy script chia batch:
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill tag \
    --atoms "path1.md,path2.md,..." \
    --batch-size 10 \
    --output-dir "<output_dir>"
```
> Nếu danh sách atoms quá dài (>100 files), dùng `--atoms-file <file>` thay `--atoms`. File hỗ trợ `.txt` (1 path/dòng) hoặc `.json` (array).

Script tạo các batch files + manifest tại `<output_dir>/`.

### Bước 2: Vòng lặp xử lý (lặp đến khi script in "ALL_DONE")

**Bước 2a — Lấy batch tiếp theo:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --get-next --output-dir "<output_dir>"
```
Nếu in `ALL_DONE` → chuyển Bước 3. Nếu không, mở `<output_dir>/current_batch.json` bằng `view_file` để xem danh sách atoms.

**Bước 2b — Xử lý từng atom và điền kết quả:**
Với mỗi atom trong `current_batch.json` (đọc content từ field `atoms_content`):
1. **Đọc content**: Lấy `frontmatter` và `body` từ `atoms_content` trong `current_batch.json`.
2. **Kiểm tra Audience**: Nếu `type: audience` → điền `action: "skipped"` trong template.
3. **Kiểm tra Metadata**: Nếu `description` VÀ `keywords` đã có đầy đủ → điền `action: "skipped"`.
4. **Nếu cần tag** (một hoặc cả hai thiếu):
   a. **Sinh `description`**: LLM đọc body content, sinh 1 câu mô tả 30-50 từ (tiếng Việt).
   b. **Sinh `keywords`**: LLM sinh mảng phẳng 8-11 từ khóa KHÔNG trùng nhau, chia theo 3 tier:

   | Atom Type | Tier Rộng (2-3 từ) | Tier Trung (2-3 từ) | Tier Hẹp (4-6 từ) |
   |---|---|---|---|
   | Insight | Lĩnh vực/domain | Chủ đề nhánh | Biểu hiện cụ extreme, cảm xúc, tình huống kích hoạt |
   | Solution/Concept | Lĩnh vực/domain | Chủ đề nhánh | Tên kỹ thuật, alias/synonym, cơ chế, đặc điểm |
   | Story | Lĩnh vực/domain | Chủ đề nhánh | Loại nhân vật, bối cảnh, hành động, kết quả |
   | Quote | Lĩnh vực/domain | Chủ đề nhánh | Tên tác giả, cụm từ đặc trưng |
   | Data-Point | Lĩnh vực/domain | Chủ đề nhánh | Nguồn nghiên cứu, thuật ngữ/chỉ số đo lường, phát hiện |

   c. Điền `action: "tagged"`, `description`, `keywords`, `reasoning` vào entry tương ứng trong `<output_dir>/results_temp.json`.
5. **Nếu đã đầy đủ**: Điền `action: "skipped"`.

> ⚠️ **KHÔNG** tự ghi YAML vào file atom. Chỉ điền kết quả vào `results_temp.json`. Script sẽ ghi YAML sau khi validate.
> ⚠️ Dùng công cụ file (`write_to_file` với `Overwrite: true`) để ghi `results_temp.json`. **KHÔNG** truyền nội dung JSON qua terminal — sẽ lỗi encoding/quoting với tiếng Việt.

**Bước 2c — Submit kết quả:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --submit --results-file "<output_dir>/results_temp.json" --output-dir "<output_dir>"
```
Nếu FAIL → đọc lỗi cụ thể, sửa `results_temp.json`, submit lại.
Nếu PASS → script tự ghi YAML + đánh dấu batch hoàn thành → quay lại Bước 2a.
Nếu PASS kèm `SESSION_BREAK` → **dừng ngay lập tức**. Không gọi `--get-next` nữa. User sẽ copy prompt từ output sang conversation mới.

### Bước 3: Rebuild Index
Sau khi script in `ALL_DONE`, chạy:
```powershell
powershell -ExecutionPolicy Bypass -File .agents/scripts/build-vault-index.ps1
```

## OUTPUT
- Các file Atom đã có đầy đủ `description` và `keywords`.
- `vault_index.json` đã rebuild với metadata mới.
