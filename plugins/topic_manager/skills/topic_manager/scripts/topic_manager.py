"""
Tên file: topic_manager.py
Last update: 21/08/2026 22:50 (GMT+7)
Vai trò: Thư viện ghi nhận và lưu trữ topic mới / append audience vào topic_map.yaml.
Sử dụng khi nào: Được gọi trực tiếp bởi dedup_engine.py ở Chặng 3 (Compile & Commit).
Output: Cập nhật vật lý lên file topic_map.yaml.
Tóm tắt logic hoạt động:
  - confirm_new: Thêm các topics hoàn toàn mới vào YAML (tự động resolve pillar name chuẩn).
  - update_audience: Append mảng audiences vào topic đã tồn tại trong YAML (idempotent).
  - batch_commit: Batch commit từ file JSON (dành cho chế độ cũ).
"""
import os
import json
import yaml

# === NHÓM 1: Hằng số & Cấu hình Header YAML ===
TOPIC_MAP_HEADER = (
    "# BẢN ĐỒ TOPIC\n"
    "# id: English snake_case — dùng cho AI matching, script calls, frontmatter tags\n"
    "# label: Tiếng Việt đầy đủ dấu — CHỈ dùng cho human readability, KHÔNG dùng để match\n"
)

def _write_topic_map(data, path):
    """Helper ghi topic_map.yaml — bảo toàn comment header."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(TOPIC_MAP_HEADER)
        yaml.Dumper.ignore_aliases = lambda *args: True
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# === NHÓM 1.5: Helper Chuẩn hóa & Ánh xạ Dữ liệu ===
def _resolve_pillar_name(pillar_input, topic_map_path):
    """
    Poka-Yoke: Tự động ánh xạ key/prefix (vd: 'pillar_1', 'p1') sang trường 'name' trong pillars.yaml.
    Nếu input đã là name hợp lệ hoặc không tìm thấy pillars.yaml, trả về chuỗi gốc an toàn.
    """
    if not pillar_input or not isinstance(pillar_input, str):
        return pillar_input or ""
    
    clean_input = pillar_input.strip()
    persona_dir = os.path.dirname(os.path.abspath(topic_map_path))
    pillars_file = os.path.join(persona_dir, "pillars.yaml")
    
    if not os.path.exists(pillars_file):
        return clean_input

    try:
        with open(pillars_file, 'r', encoding='utf-8') as f:
            pillars_data = yaml.safe_load(f) or {}
        pillars_dict = pillars_data.get("pillars", {})
        
        lookup = {}
        for p_key, p_val in pillars_dict.items():
            if not isinstance(p_val, dict):
                continue
            p_name = p_val.get("name", "").strip()
            if p_name:
                lookup[p_key.lower()] = p_name
                # Hỗ trợ prefix rút gọn (vd: pillar_1 -> p1)
                short_key = p_key.replace("pillar_", "p").replace("pillar", "p").lower()
                lookup[short_key] = p_name
                lookup[p_name.lower()] = p_name

        return lookup.get(clean_input.lower(), clean_input)
    except Exception:
        return clean_input


# === NHÓM 2: Tạo Mới Topic (confirm_new) ===
def confirm_new(topic_map_path, new_topics, labels, pillar_parent, belongs_to_audience):
    """
    Ghi topics đã được LLM xác nhận là HOÀN TOÀN MỚI vào topic_map.yaml.
    Poka-Yoke: normalize id (lowercase + replace '-' -> '_') trước khi ghi.
    KHÔNG check trùng — LLM đã quyết định rồi.
    """
    if labels and len(labels) != len(new_topics):
        raise ValueError(f"❌ Số labels ({len(labels)}) không khớp với topics ({len(new_topics)})")

    if isinstance(pillar_parent, list):
        if len(pillar_parent) > 1:
            raise ValueError(f"❌ Vi phạm One Pillar: {pillar_parent}")
        pillar_parent = pillar_parent[0] if pillar_parent else ""

    # Poka-Yoke: Đảm bảo pillar_parent luôn là Tên tiếng Việt từ pillars.yaml
    pillar_parent = _resolve_pillar_name(pillar_parent, topic_map_path)

    if not os.path.exists(topic_map_path):
        data = {"topics": []}
    else:
        with open(topic_map_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {"topics": []}
        if "topics" not in data:
            data = {"topics": []}

    for i, raw_id in enumerate(new_topics):
        t_id = raw_id.replace('-', '_').lower()  # Poka-Yoke normalize
        # Sanitize: normalize [[[[slug]]]] -> [[slug]] trong belongs_to_audience
        clean_audiences = []
        for aud in belongs_to_audience:
            slug = aud.replace("[[", "").replace("]]", "")
            if slug:
                clean_audiences.append(f"[[{slug}]]")
        data["topics"].append({
            "id": t_id,
            "label": labels[i],
            "pillar_parents": [pillar_parent],
            "belongs_to_audience": clean_audiences
        })

    _write_topic_map(data, topic_map_path)
    print(f"✅ Đã ghi {len(new_topics)} topic mới vào {topic_map_path}")


# === NHÓM 3: Cập Nhật Audience (update_audience) ===
def update_audience(topic_map_path, resolved_id, new_audiences):
    """
    Append audience mới vào belongs_to_audience của topic đã tồn tại.
    Idempotent: chỉ append nếu audience chưa có trong list.
    """
    if not os.path.exists(topic_map_path):
        print(f"❌ Không tìm thấy {topic_map_path}")
        return

    with open(topic_map_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {"topics": []}

    updated = False
    for topic in data.get("topics", []):
        if topic.get("id") == resolved_id:
            existing = topic.get("belongs_to_audience", [])
            if isinstance(existing, str):
                existing = [existing]
            for aud in new_audiences:
                # Sanitize: normalize [[[[slug]]]] -> [[slug]]
                slug = aud.replace("[[", "").replace("]]", "")
                clean_aud = f"[[{slug}]]" if slug else ""
                if clean_aud and clean_aud not in existing:
                    existing.append(clean_aud)
                    updated = True
            topic["belongs_to_audience"] = existing
            break

    if updated:
        _write_topic_map(data, topic_map_path)
        print(f"✅ Đã append audience vào topic '{resolved_id}'")
    else:
        print(f"ℹ️ Audience đã tồn tại trong '{resolved_id}', không cần cập nhật.")


# === NHÓM 4: Batch Commit (batch_commit) ===
def _group_key(entry):
    """Convert scope+chunk_index sang dict key cho output."""
    if entry["scope"] == "book":
        return "book"
    return str(entry["chunk_index"])


def batch_commit(topic_map_path, input_path, output_path):
    """
    Tên: batch_commit
    Vai trò: Đọc proposed_topics.json, ghi topic mới/append audience vào topic_map.yaml,
             xuất resolved_topics.json cho atomizer.py.
    Khi nào sử dụng: Được gọi bởi Agent trong book-parser Phase 1, Bước 1.5 (Batch Mode).
    Output: topic_map.yaml (cập nhật) + resolved_topics.json (mới).
    """
    # Đọc input
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Poka-Yoke: Chuẩn hóa pillar sang Tên tiếng Việt
    pillar = _resolve_pillar_name(data.get("pillar", ""), topic_map_path)
    entries = data["entries"]

    # ── Bước 1: Tách creates và merges ──
    creates = [e for e in entries if e["action"] == "create"]
    merges = [e for e in entries if e["action"] == "merge"]

    # ── Bước 2: Deduplicate creates theo id ──
    seen_ids = {}  # id → {"label": ..., "audiences": set(), "groups": []}
    for entry in creates:
        tid = entry["id"].replace('-', '_').lower()  # Poka-Yoke normalize
        if tid in seen_ids:
            # Gộp audiences (idempotent)
            for aud in entry["audiences"]:
                seen_ids[tid]["audiences"].add(aud)
            seen_ids[tid]["groups"].append(_group_key(entry))
        else:
            seen_ids[tid] = {
                "label": entry["label"],
                "audiences": set(entry["audiences"]),
                "groups": [_group_key(entry)],
            }

    # ── Bước 3: Xử lý creates (gọi confirm_new) ──
    for tid, info in seen_ids.items():
        confirm_new(
            topic_map_path,
            new_topics=[tid],
            labels=[info["label"]],
            pillar_parent=pillar,
            belongs_to_audience=list(info["audiences"])
        )

    # ── Bước 4: Xử lý merges (gọi update_audience) ──
    for entry in merges:
        resolved_id = entry["resolved_to"].replace('-', '_').lower()  # Poka-Yoke normalize
        update_audience(
            topic_map_path,
            resolved_id=resolved_id,
            new_audiences=entry["audiences"]
        )

    # ── Bước 5: Build resolved_topics output ──
    output = {}

    # Từ creates (đã dedup)
    for tid, info in seen_ids.items():
        for group in info["groups"]:
            output.setdefault(group, [])
            if tid not in output[group]:
                output[group].append(tid)

    # Từ merges
    for entry in merges:
        group = _group_key(entry)
        resolved_id = entry["resolved_to"].replace('-', '_').lower()  # Poka-Yoke normalize
        output.setdefault(group, [])
        if resolved_id not in output[group]:
            output[group].append(resolved_id)

    # ── Bước 6: Ghi resolved_topics.json ──
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ Batch commit hoàn tất:")
    print(f"   Created: {len(seen_ids)} topics")
    print(f"   Merged:  {len(merges)} entries")
    print(f"   Output:  {output_path}")


# === NHÓM 5: Thực Thi CLI Parser ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Topic Manager — ghi dữ liệu vào topic_map.yaml")
    parser.add_argument("--map-path", required=True, help="Đường dẫn đến file topic_map.yaml")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # Chế độ 1: confirm-new — ghi topic mới
    p_new = subparsers.add_parser("confirm-new", help="Ghi topics hoàn toàn mới vào YAML")
    p_new.add_argument("--topics",    required=True, nargs="+", help="Danh sách Topic ID")
    p_new.add_argument("--labels",    required=True, nargs="+", help="Nhãn tiếng Việt tương ứng 1-1 với --topics")
    p_new.add_argument("--pillar",    required=True, help="Tên Pillar duy nhất (One Topic, One Pillar)")
    p_new.add_argument("--audiences", required=True, nargs="+", help="Danh sách Audience Links")

    # Chế độ 2: update-audience — append audience vào topic đã tồn tại
    p_upd = subparsers.add_parser("update-audience", help="Append audience mới vào topic đã tồn tại")
    p_upd.add_argument("--topic",     required=True, help="ID của topic đã tồn tại")
    p_upd.add_argument("--audiences", required=True, nargs="+", help="Danh sách Audience Links cần append")

    # Chế độ 3: batch-commit — xử lý hàng loạt từ file JSON
    p_batch = subparsers.add_parser("batch-commit", help="Batch commit từ proposed_topics.json")
    p_batch.add_argument("--input",  required=True, help="Đường dẫn proposed_topics.json")
    p_batch.add_argument("--output", required=True, help="Đường dẫn output resolved_topics.json")

    args = parser.parse_args()

    if args.mode == "confirm-new":
        confirm_new(args.map_path, args.topics, args.labels, args.pillar, args.audiences)
    elif args.mode == "update-audience":
        update_audience(args.map_path, args.topic, args.audiences)
    elif args.mode == "batch-commit":
        batch_commit(args.map_path, args.input, args.output)
