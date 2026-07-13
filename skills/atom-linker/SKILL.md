---
name: Atom-Linker
description: "Liên kết Atom mới vào DAG: tìm parent node, gán audience, clone cross-audience. Xử lý theo batch 10 atoms/lần."
last_update: 13/07/2026 09:38 (GMT+7)
---

# Atom-Linker Skill

> **Tên file**: .agents/skills/atom-linker/SKILL.md
> **Vai trò**: Tìm parent node cho Atom mới và liên kết vào cấu trúc DAG.
> **Sử dụng khi**: Được gọi từ VaultCuratorAgent, hoặc thủ công khi cần align atoms.
> **Output**: Atoms đã có supports_* link + belongs_to_audience. Orphans được tag `status: orphan`.
> **Tóm tắt logic**: Nhận atoms → Script chia batch → Vòng lặp: Search alignment → LLM đánh giá → điền template → submit (script validate + patch link) → Reframe clones (nếu có) → Rebuild index.

> ⛔ **CẤM TUYỆT ĐỐI**:
> 1. KHÔNG ĐƯỢC PHÉP dùng `view_file` hay bất kỳ công cụ nào đọc trực tiếp file atom trong `vault/01-Atomic/`,
>    TRỪ KHI đường dẫn đó có trong kết quả search `vault/.curation_temp/rag_results.json` (candidate atoms cần so sánh).
>    Nội dung atom nguồn (trong batch): đọc từ `current_batch.json` (field `atoms_content`).
> 2. KHÔNG ĐƯỢC PHÉP tạo file script mới (`.py`, `.js`, `.sh`, `.ps1`).

## INPUT
- `--atoms`: Danh sách đường dẫn file Atom
- `--output-dir`: Thư mục lưu trạng thái batch

## THAM SỐ PHỄU LỌC

| Parameter | Value |
|---|---|
| Keyword Threshold | >= 4 |
| Top-K | 15 |
| MAX_CLONES | 3 |
| Scope Filter | Khác Type (DAG hierarchy) |

## QUY TRÌNH THỰC THI

### Bước 1: Khởi tạo Batch
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill align --atoms "path1.md,path2.md,..." --batch-size 10 --output-dir "<output_dir>/align"
```
> Nếu danh sách atoms quá dài (>100 files), dùng `--atoms-file <file>` thay `--atoms`. File hỗ trợ `.txt` (1 path/dòng) hoặc `.json` (array).

### Bước 2: Vòng lặp xử lý (lặp đến khi script in "ALL_DONE")

**Bước 2a -- Lấy batch:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --get-next --output-dir "<output_dir>/align"
```
Nếu in `ALL_DONE` → chuyển Bước 3. Nếu không, mở `<output_dir>/align/current_batch.json` bằng `view_file`.

**Bước 2b -- Với mỗi atom trong batch:**
1. Chạy Search:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .agents/scripts/Search-SemanticAtom.ps1 -Mode "alignment" -SourceAtomPath "<atom_path>"
   ```
2. Đọc `vault/.curation_temp/rag_results.json`.
3. LLM đánh giá candidates → điền quyết định vào entry tương ứng trong `<output_dir>/align/results_temp.json`:
   - **0 match**: `decision: "orphan"`, `reasoning` giải thích.
   - **1 match (1 Audience)**: `decision: "linked"`, `parent_path`, `link_type` (`insight` hoặc `knowledge`), `audience`, `reasoning`.
   - **Nhiều match (nhiều Audience, tối đa 3)**: `decision: "cloned"`, `parent_path`, `link_type`, `clone_targets` (danh sách audience ids), `reasoning`.
4. Lặp cho atom tiếp theo.

> ⚠️ **KHÔNG** tự gọi `patch-semantics.py`, tự clone file, hay tự ghi `status: orphan`. Script sẽ thực hiện sau khi validate.
> ⚠️ Dùng công cụ file (`write_to_file` với `Overwrite: true`) để ghi `results_temp.json`. **KHÔNG** truyền nội dung JSON qua terminal — sẽ lỗi encoding/quoting với tiếng Việt.

**Bước 2c -- Submit kết quả:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --submit --results-file "<output_dir>/align/results_temp.json" --output-dir "<output_dir>/align"
```
Nếu FAIL → đọc lỗi cụ thể, sửa `results_temp.json`, submit lại.
Nếu PASS → script tự patch links + tạo clones + đánh dấu batch hoàn thành → quay lại Bước 2a.
Nếu PASS kèm `SESSION_BREAK` → **dừng ngay lập tức**. Không gọi `--get-next` nữa. User sẽ copy prompt từ output sang conversation mới.

**Bước 2d -- Reframe Clone Content (nếu có):**
Nếu batch vừa xử lý có atoms với `decision: "cloned"`:
1. Đọc `<output_dir>/align/pending_reframe.json`.
2. Với mỗi clone: mở file clone → reframe body content cho audience mục tiêu (giữ nguyên frontmatter đã được script patch).
3. Sau khi reframe xong tất cả → quay lại Bước 2a.

### Bước 3: Poka-Yoke Guard
Mỗi lần gọi `patch-semantics.py --action add`, script tự kiểm tra 3 rule:
- Audience Match (source và target cùng audience)
- No Cycle (link mới không tạo vòng lặp)
- Type Valid (tuân thủ DAG hierarchy)

Nếu REJECT -> Không ghi file, log lý do.

### Bước 4: Rebuild Index
Sau khi script in `ALL_DONE`: `powershell -ExecutionPolicy Bypass -File .agents/scripts/build-vault-index.ps1`
