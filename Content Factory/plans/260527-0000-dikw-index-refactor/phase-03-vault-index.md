---
name: phase-03-vault-index.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Phase
usage: Hướng dẫn thực thi Phase 3 — Tạo script build-vault-index và định nghĩa vault_index.json schema
output: Script build-vault-index.ps1 + file vault_index.json
logic: Quét 6 thư mục 01-Atomic, parse frontmatter, tạo nodes + edges index
---

# Phase 03: Build Vault Index

**Trạng thái:** ⬜ Pending
**Nhóm BRIEF:** A (A1 + A2)
**Dependencies:** Phase 1, Phase 2 (data phải clean trước khi build index)

---

## Task 3.1: Tạo script `build-vault-index.ps1`

**File mới:** `.agents/skills/dikw-bridge/scripts/build-vault-index.ps1`

**Mô tả:**
- Tên file: build-vault-index.ps1
- Last update: ngày tạo
- Vai trò: Quét vault, parse frontmatter, xuất index JSON
- Sử dụng khi: Được gọi bởi Get-DIKWCombo trước mỗi query
- Output: `vault_index.json`
- Logic: Quét 6 thư mục → parse YAML frontmatter (block đầu tiên) → strip wikilinks → xuất JSON

**Tham số:**
- `-VaultPath` (bắt buộc): Path đến `vault/01-Atomic/` (tương đối từ CWD)
- `-OutputPath` (bắt buộc): Path xuất `vault_index.json`

**Logic chi tiết:**

```
1. Định nghĩa 6 thư mục + type mapping:
   Insights → "insight"
   Solutions → "solution"
   Concepts → "concept"
   Stories → "story"
   Quotes → "quote"
   Data-Points → "data_point"

2. Exclude rules:
   - Bỏ qua thư mục: Audiences/, _DLQ/
   - Bỏ qua file: .gitkeep, file/thư mục prefix "_"

3. Với mỗi file .md trong 6 thư mục:
   a. Đọc nội dung file
   b. Parse frontmatter: CHỈ block đầu tiên
      - Dòng 1 phải là "---"
      - Đọc đến dòng "---" tiếp theo, dừng
      - Parse YAML key-value bằng regex: ^(\w+):\s*(.+)$
   c. Strip wikilinks: bỏ "[[" và "]]" từ tất cả giá trị
   d. Tạo node entry:
      - key: path tương đối từ CWD (VD: "vault/01-Atomic/Insights/GI_example.md")
      - value: {type, topics, source_id, belongs_to_audience, confidence, status, insight_type, subtype, knowledge_type}
   e. Lưu tạm raw edge data:
      - Nếu có "supports_insight" → lưu {atom_path, target_filename}
      - Nếu có "supports_knowledge" → lưu {atom_path, target_filename}

4. Build filename→full_path lookup table:
   - Từ tất cả nodes đã tạo, tạo dict: { "GI_example" → "vault/01-Atomic/Insights/GI_example.md" }
   - Key = filename không đuôi .md (vì frontmatter wikilink không có .md)

5. Resolve edges:
   - Với mỗi raw edge: dùng lookup table để chuyển target_filename → full_path
   - Nếu target_filename KHÔNG tìm thấy trong lookup → log warning, bỏ qua edge (orphan)
   - Kết quả: edges.supports_insight = { atom_full_path: target_full_path }

6. Gộp thành JSON object: { metadata: { last_updated, node_count, edge_count }, nodes: {...}, edges: {...} }
7. Ghi ra OutputPath (UTF-8 no BOM)
```

**YAML Frontmatter Parser — Quy tắc quan trọng:**
- CHỈ đọc block đầu tiên (dòng 1 = `---`, kết thúc tại `---` tiếp theo)
- Schema B files chứa fake YAML trong comment block HTML → parser PHẢI bỏ qua
- Các trường YAML có thể là: string, number, array inline `[a, b, c]`, hoặc `null`
- Array detection: giá trị bắt đầu bằng `[` → parse bằng `ConvertFrom-Json`
- Wikilink strip: `[[some-id]]` → `some-id`

**⚠️ CWD Constraint:** Script phải chạy với working directory = `Content Factory/`

**Kiểm tra:**
1. Chạy script → `vault_index.json` được tạo.
2. Mở JSON → xác nhận số nodes ≈ 260 (tổng atoms hiện có).
3. Spot-check 5 nodes: `type`, `topics`, `source_id` đúng với file gốc.
4. Xác nhận edges `supports_insight` và `supports_knowledge` có dữ liệu.
5. Xác nhận KHÔNG có node nào từ `Audiences/` hay `_DLQ/`.

---

## Task 3.2: Định nghĩa `vault_index.json` output schema

**File output:** `.agents/skills/dikw-bridge/vault_index.json` (auto-generated, không commit vào Git)

**Schema chính thức:**

```json
{
  "metadata": {
    "last_updated": "2026-05-27T00:00:00Z",
    "node_count": 260,
    "edge_count": 200
  },
  "nodes": {
    "vault/01-Atomic/Insights/GI_example.md": {
      "type": "insight",
      "topics": ["dieu_hoa_cam_xuc", "phat_trien_tam_ly_tre"],
      "source_id": "good-inside",
      "belongs_to_audience": "cha-me_ap-dung-chien-luoc...",
      "confidence": 0.9,
      "status": "processed",
      "insight_type": "pain_point",
      "subtype": null,
      "knowledge_type": null
    }
  },
  "edges": {
    "supports_insight": {
      "vault/01-Atomic/Solutions/GI_sol.md": "vault/01-Atomic/Insights/GI_example.md"
    },
    "supports_knowledge": {
      "vault/01-Atomic/Stories/GI_story.md": "vault/01-Atomic/Solutions/GI_sol.md"
    }
  }
}
```

**Quy tắc:**
- `nodes` key = path tương đối từ Content Factory root (bắt buộc format `vault/01-Atomic/...`)
- `topics` = array of strings (đã strip `[[]]`)
- `belongs_to_audience` = string (đã strip `[[]]`)
- `supports_insight`, `supports_knowledge` = string — đã resolve từ filename → full path (VD: `"GI_example"` → `"vault/01-Atomic/Insights/GI_example.md"`)
- Trường thiếu trong frontmatter → `null` trong JSON
- `confidence` parse thành number, không phải string

---

**Hoàn thành Phase 3 → Chuyển sang Phase 4.**
