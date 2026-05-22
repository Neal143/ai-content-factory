# Topic Manager — Reference Module

> **Dùng như thế nào:** Các Skill (inbox-processor, story-architect, book-parser)
> đọc file này và thực thi ngay các bước dưới đây tại chỗ — không in gì ra chat,
> không cần Workflow gọi riêng.

## Mục đích

Semantic Dedup Gate tập trung. Nhận proposed topics vừa sinh, so sánh ngữ nghĩa
với toàn bộ `topic_map.yaml`, quyết định MATCH hoặc NO MATCH, ghi kết quả vào YAML.

---

## Input — nhận từ Skill đang gọi (in working memory)

Trước khi đọc module này, Skill đang gọi phải có sẵn trong working memory
danh sách proposed topics. Mỗi topic là một bộ 4 biến:

| Biến | Kiểu | Ví dụ | Nguồn |
|---|---|---|---|
| `id` | English snake_case | `habit_building` | Skill sinh ra |
| `label` | Tiếng Việt có dấu | `Xây dựng thói quen` | Skill sinh ra |
| `pillar` | Tên Pillar đúng trong `pillars.yaml` | `Personal Growth` | Skill chọn ở bước Pillar gốc |
| `audience` | Wikilink đến file audience | `[[audience_file.md]]` | Skill cung cấp |

Ví dụ working memory trước khi gọi module:
```
topic 1: id=habit_building, label=Xây dựng thói quen, pillar=Personal Growth, audience=[[busy_professional.md]]
topic 2: id=mindfulness,    label=Chánh niệm,         pillar=Mental Health,   audience=[[busy_professional.md]]
```

> ⛔ Nếu Skill chưa sinh topics, KHÔNG được gọi module này.

---

## Bước 1: Xác định đường dẫn

- `MAP_PATH` = `personas/[Tên_user]/topic_map.yaml`
- `SCRIPT_PATH` = `.agent\references\topic_manager\topic_manager.py`

---

## Bước 2: Đọc topic_map.yaml hiện tại

Dùng `view_file` tool để đọc file tại `MAP_PATH`.
Ghi nhớ toàn bộ danh sách: `id`, `label`, `pillar_parents` của từng topic.

---

## Bước 3: Semantic Dedup — Xử lý từng proposed topic

Với **từng topic** vừa sinh (từ Skill đang gọi module này), so sánh ngữ nghĩa
với TOÀN BỘ `topic_map.yaml` — **không lọc theo Pillar**.

### Tiêu chí MATCH

Hai topics là MATCH khi cùng mô tả **một khái niệm**, bất kể cách diễn đạt:
- Synonym: `habit_formation` ≈ `habit_building`
- Paraphrase: `building_habits` ≈ `habit_building`
- Reorder từ: `goal_achievement_strategy` ≈ `strategy_for_goal_achievement`

### Khi MATCH

```text
resolved_id = id của topic B (đã tồn tại trong YAML)
```

Gọi script để append audience:
```bash
python [SCRIPT_PATH] --map-path [MAP_PATH] update-audience \
  --topic "[resolved_id]" \
  --audiences "[audience của proposed topic]"
```

### Khi NO MATCH

```text
resolved_id = id của proposed topic (Poka-Yoke normalize trong script)
```

Gọi script để ghi mới:
```bash
python [SCRIPT_PATH] --map-path [MAP_PATH] confirm-new \
  --topics "[id]" \
  --labels "[label]" \
  --pillar "[pillar]" \
  --audiences "[audience]"
```

---

## Bước 4: Kết thúc — Cập nhật Working Memory

Sau khi xử lý qua Semantic Dedup cho toàn bộ topics, Skill (Agent) tự động biến đổi dữ liệu trong bộ nhớ:
- **Với topic NO MATCH:** Giữ nguyên `id` ban đầu (hiểu là `resolved_id`).
- **Với topic MATCH:** Ghi đè `id` ban đầu bằng cái `id` gốc đã tồn tại trong YAML (hiểu là `resolved_id`).

**Không in gì ra chat.** Mảng biến lúc này sẽ là danh sách các `[resolved_id_1, resolved_id_2, ...]`.
Tiếp tục ngay các bước tiếp theo của Skill đang gọi và BẮT BUỘC dùng mảng `[resolved_id]` này khi ghi danh sách `topics` trong YAML frontmatter cho Atom. (Biến `belongs_to_audience` ghi vào Atom vẫn giữ nguyên là audience đã lấy từ đầu, độc lập với tiến trình này).

---

## Nguyên tắc bất biến

| Nguyên tắc | Mô tả |
|---|---|
| One Topic, One Pillar | Một khái niệm chỉ được tồn tại 1 lần trong toàn bộ YAML |
| Pillar Override | Nếu MATCH → BẮT BUỘC dùng Pillar của topic B, bỏ Pillar gốc |
| Global Scope | Dedup scan TOÀN BỘ topic_map, không filter theo Pillar |
| belongs_to_audience là array | Luôn append, không ghi đè |

---

## Chế độ Batch (dành cho caller có volume lớn — VD: book-parser)

Khi Skill đang gọi có **>10 proposed topics** cần xử lý, **THAY THẾ toàn bộ
Bước 3 và Bước 4** bằng quy trình batch sau. Bước 1 và 2 giữ nguyên.

### Batch Bước 3: Semantic Dedup (in-memory — logic giống Bước 3 cũ)

Vẫn đọc `topic_map.yaml`, so sánh ngữ nghĩa từng proposed topic với toàn bộ
danh sách. Quyết định MATCH hoặc NO MATCH cho từng topic. **Không gọi script.**

⚠️ **Internal Dedup bổ sung:** Nếu 2 proposed topics từ 2 chunks khác nhau cùng
ngữ nghĩa (VD: chunk 3 và chunk 7 cùng sinh `emotional_regulation`), chỉ giữ
1 entry `create` duy nhất — các chunk sau dùng lại id đó (giống như MATCH nội bộ).

### Batch Bước 4: Ghi file `proposed_topics.json`

Ghi TẤT CẢ kết quả dedup vào 1 file JSON duy nhất tại `[run_folder]/proposed_topics.json`.

**Cấu trúc bắt buộc:**

```json
{
  "pillar": "[Tên Pillar đã chốt]",
  "entries": [
    {
      "scope": "book hoặc chunk",
      "chunk_index": "integer (1, 2, ...) nếu scope=chunk, null nếu scope=book",
      "action": "create hoặc merge",
      "id": "[proposed_id]",
      "label": "[label tiếng Việt — CHỈ khi action=create]",
      "resolved_to": "[existing_id_in_YAML — CHỈ khi action=merge]",
      "audiences": ["[[audience_wikilink]]"]
    }
  ]
}
```

**Quy tắc ghi entries:**
- Topic **NO MATCH** (hoàn toàn mới) → `action: "create"`, kèm `id`, `label`, `audiences`.
- Topic **MATCH** (đã tồn tại trong YAML) → `action: "merge"`, kèm `id` (proposed), `resolved_to` (id gốc trong YAML), `audiences`.
- Topic **trùng nội bộ** (2 chunks sinh cùng topic mới) → chỉ 1 entry `create` cho lần đầu, các lần sau ghi `action: "merge"` với `resolved_to` = id đã tạo ở lần đầu.
- `scope`: Book topics dùng `"book"`. Chunk topics dùng `"chunk"`.
- `chunk_index`: Lấy từ `parsed_metadata.json` hoặc file cache `CHUNK_index`. Integer, **KHÔNG** dùng string. `null` cho book.

### Batch Bước 5: Chạy 1 lệnh CLI duy nhất

```bash
python .agent/references/topic_manager/topic_manager.py \
  --map-path [MAP_PATH] \
  batch-commit \
  --input  [run_folder]/proposed_topics.json \
  --output [run_folder]/resolved_topics.json
```

### Batch Bước 6: Đọc output → Cập nhật Working Memory

Đọc `[run_folder]/resolved_topics.json`. File có cấu trúc:

```json
{
  "book": ["resolved_id_1", "resolved_id_2"],
  "1": ["resolved_id_3", "resolved_id_4"],
  "2": ["resolved_id_5"]
}
```

Lưu vào working memory:
- `book_topics` = giá trị key `"book"`
- `chunk_topics_map` = toàn bộ các key còn lại (chunk index → mảng resolved_id)
