# Plugin Topic Manager — 2-Pass Semantic Dedup

**Tên file:** `SKILL.md`
**Last update:** 01/06/2026 23:55 (GMT+7)
**Vai trò:** Cẩm nang hướng dẫn vận hành 2-pass Semantic Dedup cho Agent.
**Được sử dụng khi nào:** Khi Plugin được triệu gọi để xử lý proposed_topics.json.
**Output:** File resolved_topics.json hoàn chỉnh và topic_map.yaml được cập nhật.
**Tóm tắt logic hoạt động:**
  - Hướng dẫn chi tiết cách chạy từng lệnh CLI trong 3 chặng.
  - Cung cấp bảng quy luật so khớp ngữ nghĩa MATCH / NO MATCH bất biến để LLM ra quyết định chuẩn xác.

---

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
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[topic_map_yaml_path]" --prepare-external
   ```
2. **Mở file làm bài:** View file `session_4/external_temp.json`.
3. **Quyết định:** Đọc file `topic_map.yaml` toàn cục. Đối chiếu 5 unique topics:
   - `create`: Nếu khái niệm chưa tồn tại trong YAML toàn cục.
   - `merge`: Nếu khái niệm đã tồn tại sẵn trong YAML. Điền `resolved_to` là ID gốc trong YAML.
4. **Nộp bài:**
   ```bash
   python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[topic_map_yaml_path]" --submit-external
   ```
5. **Lặp lại:** Gọi lại bước 1 cho đến khi màn hình báo hoàn tất Chặng 2.

---

### CHẶNG 3: BIÊN DỊCH & COMMIT
Tự động chạy ngầm biên dịch và cập nhật YAML, không cần LLM can thiệp:
```bash
python .agents/plugins/topic_manager/skills/topic_manager/scripts/dedup_engine.py --session-dir "[session_4_dir]" --map-path "[topic_map_yaml_path]" --compile-and-commit
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
- **Pillar Override:** Nếu `merge` vào topic sẵn có, bắt buộc kế thừa Pillar của topic gốc đó.
- **Global Scope:** Khi quét so khớp ở Chặng 2, bắt buộc đối chiếu với toàn bộ `topic_map.yaml`, không lọc theo Pillar.
