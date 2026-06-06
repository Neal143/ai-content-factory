## ReadContext
### Bước 1: Tiếp nhận Context & Khai báo Nguồn
- Tiếp nhận từ Workflow `/content-post`: `mapped_topics` (topic IDs) và `Target_Audience` (Audience ID hoặc array Audience IDs).
- Đọc kĩ `.agents/skills/dikw-bridge/references/injection-rules.md`.
- **Phân giải User ID**: Trích xuất `[User]` từ phần cuối của `Persona_Path` trong Bảng đen (ví dụ: `Persona_Path: personas/Neal` → `[User]` = `Neal`).

**Nguồn 1 — Vault Atoms (Ưu tiên cao nhất):**
- Path: `vault/01-Atomic/`
- Quét 6 thư mục vật lý (Direct Read, TUYỆT ĐỐI không dùng LLM extraction):
  1. `Stories/` → Wisdom (W)
  2. `Solutions/` → Knowledge (K)
  3. `Insights/` → Knowledge (K)
  4. `Concepts/` → Information (I)
  5. `Quotes/` → Data (D)
  6. `Data-Points/` → Data (D)

**Nguồn 2-4 — Extract Stories bổ sung (chỉ phục vụ Wisdom layer):**

| Nguồn | Path | Confidence |
|-------|------|------------|
| Viral Posts | `vault/[User]/Viral Posts/` | 0.9 |
| Posted | `vault/[User]/Posted/` | 0.8 |

**Exclude**: `.obsidian`, `.git`, `.gitkeep`, `Template`, `_Templates`, `_System`

## FilterAnchors
### Bước 2: Lọc Nhánh Chính (Bộ lọc O(1) Đa Điều Kiện)
- Tầng 2: **Insights** = Anchors. Quét các file `Insights` thoả mãn ĐỒNG THỜI:
  - Có ít nhất một topic thuộc mảng `mapped_topics`.
  - Có `belongs_to_audience` khớp với `Target_Audience` (strip `[[]]` trước khi so sánh):
    - `Target_Audience` là string → so sánh trực tiếp.
    - `Target_Audience` là array → khớp nếu trùng **bất kỳ** phần tử nào.
- Các file Insight thỏa mãn sẽ là Mỏ neo gốc (Anchors) đưa vào Rổ nguyên liệu.

## FilterRoots
### Bước 3: Lọc Nhánh Rễ (Validate Graph Links & Purge)
- **Tầng 3 (Validate `supports_insight`):** Scan `Solutions`, `Concepts`. Chỉ lấy các Atom nào có Node Link `supports_insight` trỏ VÀO MỘT TRONG CÁC file Insight (Tầng 2) đang có trong Rổ.

## FilterLeaves
- **Tầng 4 (Validate `supports_knowledge`):** Scan `Stories`, `Quotes`, `Data-Points`. Chỉ lấy các Atom nào có Node Link `supports_knowledge` trỏ VÀO MỘT TRONG CÁC file Solution/Concept (Tầng 3) đang có trong Rổ.

## Purge
- **⛔ Orphan Purge:** Drop hoàn toàn các Atom thiếu Link Graph, hoặc Link trỏ ra ngoài Rổ nguyên liệu. Không đưa rác vào quy trình.
- **Anti-Repetition:** Đọc `production-log.md` để tự động loại bỏ các Atoms đã được sử dụng trong 3 bài post gần nhất.
