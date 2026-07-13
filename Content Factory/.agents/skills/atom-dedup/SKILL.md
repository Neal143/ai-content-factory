---
name: Atom-Dedup
description: "Loại bỏ trùng lặp ngữ nghĩa giữa các Atom trong Vault. Xử lý theo batch 10 atoms/lần."
last_update: 13/07/2026 09:38 (GMT+7)
---

# Atom-Dedup Skill

> **Tên file**: .agents/skills/atom-dedup/SKILL.md
> **Vai trò**: Tìm và hợp nhất các Atom trùng lặp ngữ nghĩa.
> **Sử dụng khi**: Được gọi từ VaultCuratorAgent sau auto-tagger, hoặc thủ công khi cần dedup.
> **Output**: Atoms đã dedup (loser bị xóa, survivor được enrich) + vault_index.json đã rebuild.
> **Tóm tắt logic**: Nhận scope + atoms → Script chia batch → Vòng lặp: Search → LLM đánh giá → điền template → submit (script validate + merge) → Rebuild index.

> ⛔ **CẤM TUYỆT ĐỐI**:
> 1. KHÔNG ĐƯỢC PHÉP dùng `view_file` hay bất kỳ công cụ nào đọc trực tiếp file atom trong `vault/01-Atomic/`,
>    TRỪ KHI đường dẫn đó có trong kết quả search `vault/.curation_temp/rag_results.json` (candidate atoms cần so sánh).
>    Nội dung atom nguồn (trong batch): đọc từ `current_batch.json` (field `atoms_content`).
> 2. KHÔNG ĐƯỢC PHÉP tạo file script mới (`.py`, `.js`, `.sh`, `.ps1`).

## INPUT
- `--scope`: `incremental` hoặc `full`
- `--atoms`: Danh sách đường dẫn file Atom (không cần cho scope `full`)
- `--output-dir`: Thư mục lưu trạng thái batch

## THAM SỐ PHỄU LỌC

| Parameter | Value |
|---|---|
| Keyword Threshold | >= 6 |
| Top-K | 10 |
| Scope Filter | Cùng Audience + cùng Type |

## LUỒNG 1: DEDUP INCREMENTAL

### Bước 1: Khởi tạo Batch
```bash
python .agents/scripts/prepare_curation_batches.py \
    --init --skill dedup --atoms "path1.md,path2.md,..." --batch-size 10 --output-dir "<output_dir>/dedup"
```
> Nếu danh sách atoms quá dài (>100 files), dùng `--atoms-file <file>` thay `--atoms`. File hỗ trợ `.txt` (1 path/dòng) hoặc `.json` (array).

### Bước 2: Vòng lặp xử lý (lặp đến khi script in "ALL_DONE")

**Bước 2a -- Lấy batch:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --get-next --output-dir "<output_dir>/dedup"
```
Nếu in `ALL_DONE` → chuyển Bước 3. Nếu không, mở `<output_dir>/dedup/current_batch.json` bằng `view_file`.

**Bước 2b -- Với mỗi atom trong batch:**
1. Chạy Search:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .agents/scripts/Search-SemanticAtom.ps1 -Mode "dedup" -Scope "incremental" -SourceAtomPath "<atom_path>"
   ```
2. Đọc `vault/.curation_temp/rag_results.json`.
3. LLM đánh giá: atom nào trong kết quả thực sự trùng lặp ngữ nghĩa?
4. Điền quyết định vào entry tương ứng trong `<output_dir>/dedup/results_temp.json`:
   - **Nếu có trùng**: `decision: "merge"`, điền `merge_with` (đường dẫn atom trùng), `survivor` (atom giữ lại — chọn theo quy tắc Merge bên dưới), `enriched_content` (body đã gộp 2 atoms), `reasoning`.
   - **Nếu không trùng**: `decision: "pass"`, `reasoning` giải thích.
5. Lặp cho atom tiếp theo trong batch.

> ⚠️ **KHÔNG** tự gọi `patch-semantics.py` hay xóa file. Script sẽ thực hiện merge sau khi validate.
> ⚠️ Dùng công cụ file (`write_to_file` với `Overwrite: true`) để ghi `results_temp.json`. **KHÔNG** truyền nội dung JSON qua terminal — sẽ lỗi encoding/quoting với tiếng Việt.

**Bước 2c -- Submit kết quả:**
```bash
python .agents/scripts/prepare_curation_batches.py \
    --submit --results-file "<output_dir>/dedup/results_temp.json" --output-dir "<output_dir>/dedup"
```
Nếu FAIL → đọc lỗi cụ thể, sửa `results_temp.json`, submit lại.
Nếu PASS → script tự redirect links + enrich survivor + xóa loser + đánh dấu batch hoàn thành → quay lại Bước 2a.
Nếu PASS kèm `SESSION_BREAK` → **dừng ngay lập tức**. Không gọi `--get-next` nữa. User sẽ copy prompt từ output sang conversation mới.

### Bước 3: Rebuild Index
Sau khi script in `ALL_DONE`: `powershell -ExecutionPolicy Bypass -File .agents/scripts/build-vault-index.ps1`

---

## LUỒNG 2: DEDUP FULL (Dọn dẹp định kỳ)

### Xử lý Layer-by-layer (KHÔNG chia batch -- pairwise từ script)
Trình tự bắt buộc: **Insight -> Rebuild -> Solution/Concept -> Rebuild -> Evidence -> Rebuild**.

Với mỗi layer:
1. Chạy Search:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .agents/scripts/Search-SemanticAtom.ps1 -Mode "dedup" -Scope "full" -Layer "<insight|solution|evidence>"
   ```
2. Đọc `vault/.curation_temp/dedup_pairs.json` -- chứa danh sách cặp nghi trùng.
3. LLM duyệt từng cặp: xác nhận trùng lặp hay không.
4. **Nếu trùng**: Merge Atomic Operation.
5. Sau khi xong layer: Rebuild Index -> Chuyển layer tiếp.

---

## MERGE ATOMIC OPERATION (chỉ áp dụng cho LUỒNG 2)

> Trong LUỒNG 1 (incremental), merge được script tự thực thi sau khi `--submit` PASS. Agent chỉ cần điền `enriched_content` vào template. Quy tắc chọn survivor vẫn giống nhau.

4 bước tuần tự:
1. **Chọn Survivor**: Atom có nhiều node con hơn (kiểm tra edges trong `vault_index.json`). Nếu bằng nhau: chọn atom có body content dài hơn.
2. **Enrich Content**: LLM bổ sung chi tiết duy nhất từ atom loser vào body của survivor (KHÔNG lặp nội dung).
3. **Redirect Links**: Chạy `python .agents/scripts/patch-semantics.py --action redirect --old-target <loser_filename> --new-target <survivor_filename>`.
4. **Xóa Loser**: Xóa file loser khỏi vault.
