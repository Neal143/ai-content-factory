---
name: BUG-REPORT-GI-Topic-Skip.md
last_update: 26/05/2026 23:40 (GMT+7)
role: Báo cáo điều tra lỗi (Bug Report)
usage: Tài liệu ghi nhận lỗi Agent skip Semantic Dedup khi parse good-inside. Dùng làm input cho task backfill topics.
output: Phân tích nguyên nhân, bằng chứng, phạm vi ảnh hưởng, hướng khắc phục
logic: Truy vết từ triệu chứng (topic ID sai) → bằng chứng file hệ thống → xác định bước bị skip → đánh giá phạm vi ảnh hưởng
---

# 🐛 BUG REPORT: Agent Skip Bước 1.5 Semantic Dedup — Good Inside

**Ngày phát hiện:** 26/05/2026  
**Phát hiện bởi:** Audit BRIEF-DIKW-Index  
**Mức độ:** Nghiêm trọng (toàn bộ good-inside atoms bị ẩn khỏi DIKW query khi viết tự do)  
**Trạng thái:** Chưa fix  

---

## 1. Triệu chứng

Toàn bộ 32 Insight files `GI_*` trong `vault/01-Atomic/Insights/` có **cùng một mảng topics giống hệt nhau**:

```yaml
topics: ["parenting", "child-psychology", "child-behavior", "emotional-regulation"]
```

Các topic IDs này là **tiếng Anh dạng keyword** (`parenting`, `child-psychology`), **KHÔNG** nằm trong `topic_map.yaml` (nơi dùng Vietnamese slug IDs như `dieu_hoa_cam_xuc`, `phat_trien_tam_ly_tre`).

**Hệ lụy trực tiếp:**
- Khi `Target_Source_IDs` rỗng (user viết tự do, không chỉ định nguồn sách), DIKW Bridge Bước 2 chỉ dùng `topic match` → không có topic nào khớp → **100% good-inside atoms biến mất** khỏi rổ nguyên liệu.
- Khi `Target_Source_IDs = ["good-inside"]`, Pre-Filter vẫn tìm thấy atoms qua `source_id` match → hệ thống hoạt động bình thường. Vì vậy lỗi này **ẩn** trong điều kiện vận hành thông thường.

---

## 2. Bằng chứng

### 2.1. File `resolved_topics.json` — KHÔNG tồn tại

**Vị trí kỳ vọng:** `extraction_runs/good-inside_2026-05-21/resolved_topics.json`  
**Trạng thái thực tế:** Không tồn tại.

File `resolved_topics.json` là output bắt buộc của Bước 1.5 Semantic Dedup (được tạo bởi `topic_manager.py batch-commit`). Việc file này vắng mặt chứng minh **Bước 1.5 chưa bao giờ được thực thi**.

**So sánh với `the-whole-brain-child`:**  
`extraction_runs/the-whole-brain-child_2026-04-17/` — cần kiểm tra xem run folder này có `resolved_topics.json` không để xác nhận hệ thống `topic_manager` hoạt động đúng cho sách khác.

### 2.2. File `proposed_topics.json` — KHÔNG tồn tại

**Vị trí kỳ vọng:** `extraction_runs/good-inside_2026-05-21/proposed_topics.json`  
**Trạng thái thực tế:** Không tồn tại.

File `proposed_topics.json` là input cho `topic_manager.py batch-commit` (Batch Bước 4-5 trong `topic_manager.md`). Việc file này vắng mặt xác nhận Agent **cũng chưa chạy Batch Bước 4** (ghi file dedup).

### 2.3. File `atomizer_context.json` — Dữ liệu bất thường

**Vị trí:** `extraction_runs/good-inside_2026-05-21/atomizer_context.json`

```json
{
    "source_acronym": "GI",
    "book_meta": {
        "book_name": "Good Inside",
        "author": "Dr. Becky Kennedy",
        "year": "2022"
    },
    "book_topics": ["parenting", "child-psychology"],
    "chunk_topics_map": {
        "2": ["child-behavior", "emotional-regulation"],
        "3": ["child-behavior", "emotional-regulation"],
        // ... 30 chunks, TẤT CẢ đều có cùng 2 topics giống hệt
        "31": ["child-behavior", "emotional-regulation"]
    }
}
```

**3 dấu hiệu bất thường:**

| Dấu hiệu | Giải thích |
|---|---|
| 30 chunks cùng topics | Cuốn sách 31 chương, mỗi chương bàn về khía cạnh khác nhau (chia ly, ăn vạ, nói dối, sợ hãi...) nhưng tất cả đều gán `["child-behavior", "emotional-regulation"]`. Điều này vi phạm `topic-taxonomy.md` Chunk Topics quy định: *"Medium — Luận điểm cốt lõi của chunk — phải là một sub-claim cụ thể"*. |
| Topic IDs dạng English keyword | `topic-taxonomy.md` quy tắc chung: *"`id`: English snake_case, 2-5 từ, dạng danh từ/cụm danh từ"*. IDs `parenting` và `child-psychology` quá rộng (có thể làm tên sub-field học thuật → vi phạm Broad check). |
| File tạo từ working memory | SKILL.md L96 quy định rõ: *"KHÔNG tự tổng hợp `book_topics` hoặc `chunk_topics_map` từ working memory. Đọc từ `resolved_topics.json` và copy nguyên."* Nhưng vì `resolved_topics.json` không tồn tại, Agent buộc phải lấy từ working memory → vi phạm L96. |

---

## 3. Chuỗi sự kiện tái dựng

```
Bước 1.1  ✅  Chọn Pillar → (không rõ Pillar nào — cần kiểm tra thêm)
Bước 1.2  ⚠️  Sinh Book Topics → "parenting", "child-psychology" (quá rộng, sai format)
Bước 1.3  ⚠️  Sinh Chunk Topics → gán đồng loạt "child-behavior", "emotional-regulation" cho 30 chunks
Bước 1.4  ❓  Self-Check Gate → không rõ có chạy không (nếu chạy, lẽ ra phải flag topics quá rộng)
Bước 1.5  ❌  Semantic Dedup → SKIP HOÀN TOÀN (không có proposed_topics.json, không có resolved_topics.json)
Bước 2.2  ⚠️  Đóng gói Context → tạo atomizer_context.json từ working memory (vi phạm L96)
Bước 2.3  ✅  Chạy atomizer.py → atoms được tạo nhưng với topics sai
```

---

## 4. Phạm vi ảnh hưởng

### 4.1. Atoms bị ảnh hưởng

Tất cả file có prefix `GI_` trong `vault/01-Atomic/`:

| Thư mục | Số lượng (ước tính) | Trường bị sai |
|---|---|---|
| `Insights/` | 32 files | `topics` |
| `Solutions/` | cần kiểm tra | `topics` |
| `Concepts/` | cần kiểm tra | `topics` |
| `Stories/` | cần kiểm tra | `topics` |
| `Quotes/` | cần kiểm tra | `topics` |
| `Data-Points/` | cần kiểm tra | `topics` |

### 4.2. `topic_map.yaml` — KHÔNG bị ảnh hưởng

Vì Bước 1.5 bị skip, `topic_manager.py` chưa bao giờ được gọi → `topic_map.yaml` không bị ghi thêm topics sai. Đây là điểm tích cực: không cần cleanup `topic_map.yaml`.

### 4.3. Hệ thống downstream

| Hệ thống | Ảnh hưởng |
|---|---|
| DIKW Bridge (viết tự do) | GI_ atoms biến mất khi `Target_Source_IDs` rỗng |
| DIKW Bridge (chỉ định source) | Không ảnh hưởng (tìm thấy qua `source_id` match) |
| `bundle-atoms.ps1` | Không ảnh hưởng (quét path, không dùng topics) |
| Obsidian Dataview | Không ảnh hưởng (query theo `belongs_to_audience`, không dùng topics) |

---

## 5. Hướng khắc phục

### 5.1. Fix dữ liệu GI_ atoms → Xem BRIEF Nhóm C
Việc sửa lại `topics` trong toàn bộ atomic files `GI_*` đã được đưa vào scope `docs/BRIEF-DIKW-Index.md` → **Nhóm C** và đã được thực thi. Bug report này không bao gồm phần fix data.

### 5.2. Upgrade hệ thống — Ngăn lỗi tái diễn

**Vấn đề thiết kế:** `book-parser/SKILL.md` Bước 2.2 yêu cầu Agent đọc `resolved_topics.json` để tạo `atomizer_context.json`. Nhưng không có cơ chế **chặn cứng** nếu file này không tồn tại — Agent vẫn có thể tự tạo `atomizer_context.json` từ working memory và chạy tiếp Phase 2.

**Đề xuất: Thêm Poka-Yoke Gate trước Phase 2**

Bổ sung vào `book-parser/SKILL.md` tại đầu Bước 2.2 — một bước kiểm tra bắt buộc:

```markdown
> ⛔ **GATE CHECK (Bắt buộc):** Trước khi tạo `atomizer_context.json`,
> kiểm tra file `[run_folder]/resolved_topics.json` có tồn tại không.
> - Nếu KHÔNG tồn tại → DỪNG NGAY. Báo lỗi: "resolved_topics.json 
>   không tìm thấy. Bước 1.5 Semantic Dedup chưa hoàn thành. 
>   Không được tiếp tục Phase 2."
> - Nếu CÓ tồn tại → tiếp tục đọc và copy dữ liệu.
```

Ngoài ra, có thể bổ sung validation trong `atomizer.py`: kiểm tra `chunk_topics_map` có tất cả chunks cùng topics giống hệt nhau không → cảnh báo bất thường.

**Thời điểm thực hiện:** Sau khi hoàn thành BRIEF (Nhóm A + B + C). Không ảnh hưởng đến scope hiện tại.

---

## 6. Liên quan

- **BRIEF:** `docs/BRIEF-DIKW-Index.md` → Nhóm C
- **SKILL bị vi phạm:** `.agents/skills/book-parser/SKILL.md` (Bước 1.5, L59-61, L96)
- **Run folder:** `extraction_runs/good-inside_2026-05-21/`
- **Topic Manager:** `.agents/references/topic_manager/topic_manager.md`
