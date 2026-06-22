# Plugin Topic Manager — 2-Pass Semantic Dedup

**Tên file:** `SKILL.md`
**Last update:** 22/06/2026 15:42 (GMT+7)
**Vai trò:** Cẩm nang hướng dẫn vận hành 2-pass Semantic Dedup cho Agent.
**Được sử dụng khi nào:** Khi Plugin được triệu gọi để xử lý proposed_topics.json.
**Output:** File resolved_topics.json hoàn chỉnh và topic_map.yaml được cập nhật.
**Tóm tắt logic hoạt động:**
  - Hướng dẫn chi tiết cách chạy từng lệnh CLI trong 3 chặng.
  - Cung cấp bảng quy luật so khớp ngữ nghĩa MATCH / NO MATCH bất biến để LLM ra quyết định chuẩn xác.

---

> **Biến bắt buộc từ Caller:**
> - `[session_4_dir]`: Đường dẫn thư mục session_4 (truyền từ book-parser).
> - `[Persona_Path]`: Đường dẫn thư mục persona (VD: `personas/Vuon-ong-steiner`). Được book-parser truyền khi ủy thác. Nếu không được truyền, xác định bằng cách lấy thư mục con duy nhất trong `personas/`.

## HƯỚNG DẪN VẬN HÀNH 2-PASS DEDUP CLI

### CHẶNG 1: QUÉT NỘI BỘ (INTERNAL DEDUP)
1. **Khởi tạo và nhận Batch 5 topics:**
   ```bash
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --prepare-internal
   ```
2. **Mở file làm bài:** View file `session_4/internal_temp.json`.
3. **Quyết định:** So sánh ngữ nghĩa 5 topics trong batch với nhau và với danh sách `anchors`. Điền hành động:
   - `create`: Nếu topic mô tả khái niệm hoàn toàn mới chưa xuất hiện.
   - `merge`: Nếu topic bị trùng lặp ngữ nghĩa với anchor hoặc topic trước trong cùng batch. Điền `resolved_to` là ID của topic đó.
4. **Nộp bài:**
   ```bash
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --submit-internal
   ```
5. **Lặp lại:** Gọi lại bước 1 cho đến khi màn hình báo hoàn tất Chặng 1.

---

### CHẶNG 2: SO KHỚP NGOẠI VI (EXTERNAL MATCH)
1. **Khởi tạo và nhận Batch 5 unique topics:**
   ```bash
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[Persona_Path]/topic_map.yaml" --prepare-external
   ```
2. **Mở file làm bài:** View file `session_4/external_temp.json`.
3. **Quyết định:** Đọc file `[Persona_Path]/topic_map.yaml`. Đối chiếu 5 unique topics:
   - `create`: Nếu khái niệm chưa tồn tại trong YAML toàn cục.
   - `merge`: Nếu khái niệm đã tồn tại sẵn trong YAML. Điền `resolved_to` là ID gốc trong YAML.
4. **Nộp bài:**
   ```bash
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[Persona_Path]/topic_map.yaml" --submit-external
   ```
5. **Lặp lại:** Gọi lại bước 1 cho đến khi màn hình báo hoàn tất Chặng 2.

---

### CHẶNG 3: BIÊN DỊCH & COMMIT
Tự động chạy ngầm biên dịch và cập nhật YAML, không cần LLM can thiệp:
```bash
python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[Persona_Path]/topic_map.yaml" --compile-and-commit
```

---

## BỘ LUẬT SO KHỚP NGỮ NGHĨA (MATCH / NO MATCH)

| Tiêu chí MATCH | Mô tả ngữ nghĩa |
|---|---|
| **Synonym** | Các từ đồng nghĩa biểu thị cùng khái niệm (VD: `habit_formation` ≈ `habit_building`) |
| **Paraphrase** | Cách diễn đạt khác nhau của cùng một hành động (VD: `building_habits` ≈ `habit_building`) |
| **Reorder** | Đảo vị trí danh từ/động từ nhưng nghĩa bất biến (VD: `goal_achievement_strategy` ≈ `strategy_for_goal_achievement`) |

### Nguyên Tắc Bất Biến:
- **One Topic, One Pillar:** Một khái niệm chỉ được gán cho một Pillar duy nhất trong YAML.
- **Pillar Override:** Nếu `merge` vào topic sẵn có, bắt buộc kế thừa Pillar của topic gốc đó. Chỉ được merge khi cả 2 topic có cùng tiền tố Pillar (VD: `p1_` merge vào `p1_`).
- **Global Scope:** Khi quét so khớp ở Chặng 2, đối chiếu với toàn bộ `topic_map.yaml` nhưng CHỈ xét merge với các topic có CÙNG tiền tố Pillar. Các topic khác tiền tố được coi là khái niệm độc lập.
- **Cross-Pillar Firewall (NO MATCH):** Cùng label nhưng khác tiền tố Pillar (VD: `p3_tri_tuong_tuong` vs `p4_tri_tuong_tuong`) là 2 khái niệm ĐỘC LẬP. Tuyệt đối KHÔNG được merge.
