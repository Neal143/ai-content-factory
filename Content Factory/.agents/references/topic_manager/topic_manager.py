import os
import json
import yaml

# ── Hằng số: Comment header cho topic_map.yaml ──
TOPIC_MAP_HEADER = (
    "# BẢN ĐỒ TOPIC\n"
    "# id: English snake_case — dùng cho AI matching, script calls, frontmatter tags\n"
    "# label: Tiếng Việt đầy đủ dấu — CHỈ dùng cho human readability, KHÔNG dùng để match\n"
)

def _write_topic_map(data, path):
    """Helper ghi topic_map.yaml — bảo toàn comment header."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(TOPIC_MAP_HEADER)
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


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

    if not os.path.exists(topic_map_path):
        data = {"topics": []}
    else:
        with open(topic_map_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {"topics": []}
        if "topics" not in data:
            data = {"topics": []}

    for i, raw_id in enumerate(new_topics):
        t_id = raw_id.replace('-', '_').lower()  # Poka-Yoke normalize
        data["topics"].append({
            "id": t_id,
            "label": labels[i],
            "pillar_parents": [pillar_parent],
            "belongs_to_audience": belongs_to_audience
        })

    _write_topic_map(data, topic_map_path)
    print(f"✅ Đã ghi {len(new_topics)} topic mới vào {topic_map_path}")


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
                if aud not in existing:
                    existing.append(aud)
                    updated = True
            topic["belongs_to_audience"] = existing
            break

    if updated:
        _write_topic_map(data, topic_map_path)
        print(f"✅ Đã append audience vào topic '{resolved_id}'")
    else:
        print(f"ℹ️ Audience đã tồn tại trong '{resolved_id}', không cần cập nhật.")


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

    Tóm tắt logic:
      1. Đọc proposed_topics.json
      2. Tách entries thành 2 nhóm: creates và merges
      3. Deduplicate creates theo id (giữ first, gộp audiences + groups)
      4. Xử lý TẤT CẢ creates trước (gọi confirm_new)
      5. Xử lý TẤT CẢ merges sau (gọi update_audience)
      6. Build output dict: group → [resolved_id, ...]
      7. Ghi resolved_topics.json
    """
    # Đọc input
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pillar = data["pillar"]
    entries = data["entries"]

    # ── Bước 1: Tách creates và merges ──
    creates = [e for e in entries if e["action"] == "create"]
    merges = [e for e in entries if e["action"] == "merge"]

    # ── Bước 2: Deduplicate creates theo id ──
    # Nếu LLM sinh cùng 1 topic mới cho 2 chunks khác nhau,
    # chỉ tạo 1 lần, gộp audiences.
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
    # Key = group (vd: "book", "1", "2", ...)
    # Value = [resolved_id, ...]
    output = {}

    # Từ creates (đã dedup) — resolved_id = tid (normalized)
    for tid, info in seen_ids.items():
        for group in info["groups"]:
            output.setdefault(group, [])
            if tid not in output[group]:
                output[group].append(tid)

    # Từ merges — normalize resolved_to khớp với id đã ghi bởi confirm_new
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
