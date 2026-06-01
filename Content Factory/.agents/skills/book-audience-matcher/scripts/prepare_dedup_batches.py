import sys
import json
import uuid
import argparse
import os

def create_dedup_batches(jtbd_path, split_dir, batch_size):
    try:
        with open(jtbd_path, 'r', encoding='utf-8') as f:
            jtbd_data = json.load(f)
    except Exception as e:
        print(f"❌ Không thể đọc file jtbd_calibrated: {e}")
        sys.exit(1)

    book_entry = next((item for item in jtbd_data if item.get("scope") == "book"), None)
    if not book_entry:
        print("❌ Không tìm thấy Book entry trong jtbd_calibrated.json")
        sys.exit(1)

    chunk_entries = [item for item in jtbd_data if item.get("scope") == "chunk"]
    
    os.makedirs(split_dir, exist_ok=True)

    # Edge case: 0 chunks
    if not chunk_entries:
        internal_map = {
            "unique_audiences": [{
                "uid": "uid_book",
                "id": None,
                "semantic_query": None,
                "file_ref": None,
                "internal_parents": []
            }],
            "chunk_mapping": {"book": "uid_book"}
        }
        map_path = os.path.join(os.path.dirname(os.path.abspath(split_dir)), "internal_map.json")
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(internal_map, f, ensure_ascii=False, indent=2)
        print("🎉 HOÀN THÀNH — 0 chunks. Đã sinh internal_map.json chỉ chứa Book.")
        sys.exit(0)

    items_queue = []
    
    book_payload = {k: v for k, v in book_entry.items() if k not in ["content"]}
    book_payload["uid"] = "uid_book"
    items_queue.append(book_payload)

    chunk_index_to_uid = {}
    for item in chunk_entries:
        idx = item.get("chunk_index", 0)
        uid = f"uid_chunk_{idx:02d}"
        chunk_index_to_uid[str(idx)] = uid
        
        chunk_payload = {k: v for k, v in item.items() if k not in ["content"]}
        chunk_payload["uid"] = uid
        items_queue.append(chunk_payload)

    batches_data = [items_queue[i:i + batch_size] for i in range(0, len(items_queue), batch_size)]
    total_batches = len(batches_data)

    session_state = {
        "total_batches": total_batches,
        "current_batch": 1,
        "completed": False,
        "established_audiences": [],
        "collapse_map": {},
        "batches_data": batches_data,
        "chunk_index_to_uid": chunk_index_to_uid
    }

    session_state_path = os.path.join(split_dir, "session_state.json")
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    print(f"✅ 1 Book + {len(chunk_entries)} chunks → {total_batches} rolling batches (size={batch_size}). Output: {split_dir}/")

def get_next_dedup_batch(session_dir):
    session_state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(session_state_path):
        print("❌ Không tìm thấy session_state.json")
        sys.exit(1)

    with open(session_state_path, 'r', encoding='utf-8') as f:
        session_state = json.load(f)

    if session_state.get("completed"):
        print("🎉 HOÀN THÀNH — Quá trình Internal Dedup đã hoàn tất.")
        sys.exit(0)

    current_batch = session_state["current_batch"]
    batches_data = session_state["batches_data"]
    
    items_to_process = batches_data[current_batch - 1]
    batch_password = uuid.uuid4().hex[:8]
    
    session_state["current_batch_password"] = batch_password
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    anchors = session_state.get("established_audiences", [])
    
    compact_anchors = []
    for a in anchors:
        compact_anchors.append({
            "uid": a["uid"],
            "id": a["id"],
            "semantic_query": a["semantic_query"],
            "file_ref": a["file_ref"]
        })

    batch_output = {
        "batch_index": current_batch,
        "batch_password": batch_password,
        "total_batches": session_state["total_batches"],
        "anchors": compact_anchors,
        "items_to_process": items_to_process
    }

    batch_file_path = os.path.join(os.path.abspath(session_dir), "current_dedup_batch.json")
    with open(batch_file_path, 'w', encoding='utf-8') as f:
        json.dump(batch_output, f, ensure_ascii=False, indent=2)

    # Tự động sinh tệp Template
    template_output = {
        "password": batch_password,
        "entries": []
    }
    for item in items_to_process:
        template_output["entries"].append({
            "uid": item["uid"],
            "id": "[ĐIỀN VÀO ĐÂY]",
            "semantic_query": "[ĐIỀN VÀO ĐÂY]",
            "file_ref": "[ĐIỀN VÀO ĐÂY]",
            "collapse_target": None,
            "internal_parents": ["[ĐIỀN VÀO ĐÂY]"],
            "reason": "[ĐIỀN VÀO ĐÂY]"
        })
    temp_file_path = os.path.join(os.path.abspath(session_dir), "dedup_eval_temp.json")
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(template_output, f, ensure_ascii=False, indent=2)

    print(f"Batch {current_batch}/{session_state['total_batches']} đã sẵn sàng tại: {batch_file_path}")
    print(f"📝 Tệp làm bài đã được tạo sẵn tại: {temp_file_path}. Vui lòng mở tệp này, thay thế các trường [ĐIỀN VÀO ĐÂY] bằng câu trả lời và gọi --submit-file.")

def resolve_collapse_chain(collapse_map, start_uid):
    current = start_uid
    visited = set()
    while current in collapse_map:
        if current in visited:
            break
        visited.add(current)
        current = collapse_map[current]
    return current

def validate_dedup_submission(session_dir, submit_file):
    session_state_path = os.path.join(session_dir, "session_state.json")
    with open(session_state_path, 'r', encoding='utf-8') as f:
        session_state = json.load(f)

    if session_state.get("completed"):
        print("❌ Quá trình đã hoàn thành, không nhận thêm kết quả.")
        sys.exit(1)

    try:
        with open(submit_file, 'r', encoding='utf-8') as f:
            submission = json.load(f)
    except Exception as e:
        print(f"❌ File submit không hợp lệ: {e}")
        sys.exit(1)

    expected_password = session_state.get("current_batch_password")
    if submission.get("password") != expected_password:
        print("❌ ⛔ ACCESS DENIED: Password không khớp.")
        sys.exit(1)

    current_batch = session_state["current_batch"]
    expected_items = session_state["batches_data"][current_batch - 1]
    expected_uids = {item["uid"] for item in expected_items}
    
    entries = submission.get("entries", [])
    submitted_uids = {e.get("uid") for e in entries}

    if expected_uids != submitted_uids:
        print(f"❌ UID mismatch. Expected: {expected_uids}, Got: {submitted_uids}")
        sys.exit(1)

    anchors = session_state.get("established_audiences", [])
    valid_target_uids = {a["uid"] for a in anchors}.union(expected_uids)

    # Validate từng entry
    for entry in entries:
        req_fields = ["uid", "id", "semantic_query", "file_ref", "collapse_target", "internal_parents", "reason"]
        if any(k not in entry for k in req_fields):
            print(f"❌ Entry {entry.get('uid')} thiếu trường bắt buộc.")
            sys.exit(1)
        
        uid = entry["uid"]
        target = entry["collapse_target"]
        
        # Chống gộp Book
        if uid == "uid_book" and target is not None:
            print("❌ uid_book KHÔNG BAO GIỜ được phép có collapse_target (Book phải luôn sống sót).")
            sys.exit(1)

        if target is not None and target not in valid_target_uids:
            print(f"❌ collapse_target {target} không hợp lệ.")
            sys.exit(1)
            
        parents = entry["internal_parents"]
        if not isinstance(parents, list) or any(p not in valid_target_uids for p in parents):
            print(f"❌ internal_parents chứa UID không hợp lệ.")
            sys.exit(1)

        # Anti-lazy validation
        for val in entry.values():
            if isinstance(val, str) and "[ĐIỀN VÀO ĐÂY]" in val:
                print(f"❌ LỖI: Entry {entry.get('uid')} chưa thay thế trường placeholder '[ĐIỀN VÀO ĐÂY]'.")
                sys.exit(1)
            elif isinstance(val, list):
                for sub_val in val:
                    if isinstance(sub_val, str) and "[ĐIỀN VÀO ĐÂY]" in sub_val:
                        print(f"❌ LỖI: Entry {entry.get('uid')} chưa thay thế trường placeholder '[ĐIỀN VÀO ĐÂY]' trong mảng.")
                        sys.exit(1)

    # Cập nhật State
    for entry in entries:
        uid = entry["uid"]
        target = entry["collapse_target"]
        
        if target:
            session_state["collapse_map"][uid] = target
        else:
            session_state["established_audiences"].append({
                "uid": uid,
                "id": entry["id"],
                "semantic_query": entry["semantic_query"],
                "file_ref": entry["file_ref"],
                "internal_parents": entry["internal_parents"]
            })

    session_state["current_batch"] += 1
    
    if session_state["current_batch"] > session_state["total_batches"]:
        session_state["completed"] = True
        
        # Build internal_map.json
        # 1. Map chunk_index -> survivor
        chunk_mapping = {"book": resolve_collapse_chain(session_state["collapse_map"], "uid_book")}
        for c_idx, c_uid in session_state["chunk_index_to_uid"].items():
            resolved = resolve_collapse_chain(session_state["collapse_map"], c_uid)
            chunk_mapping[c_idx] = resolved
            
        # 2. Resolve phantom parents in unique_audiences
        unique_audiences = []
        for aud in session_state["established_audiences"]:
            resolved_parents = []
            for p in aud.get("internal_parents", []):
                resolved_p = resolve_collapse_chain(session_state["collapse_map"], p)
                if resolved_p not in resolved_parents and resolved_p != aud["uid"]:
                    resolved_parents.append(resolved_p)
            aud["internal_parents"] = resolved_parents
            unique_audiences.append(aud)
            
        internal_map = {
            "unique_audiences": unique_audiences,
            "chunk_mapping": chunk_mapping
        }
        
        run_folder = os.path.dirname(os.path.abspath(session_dir))
        map_path = os.path.join(run_folder, "internal_map.json")
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump(internal_map, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 HOÀN THÀNH — internal_map.json đã sẵn sàng tại: {os.path.abspath(map_path)}")
    else:
        print("✅ Submit thành công. Vui lòng gọi --get-next cho batch tiếp theo.")

    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rolling Dedup Gatekeeper cho Audience Matcher")
    parser.add_argument("--jtbd-calibrated", type=str, help="Path tới jtbd_calibrated.json")
    parser.add_argument("--split-dir", type=str, help="Thư mục chứa session dedup")
    parser.add_argument("--batch-size", type=int, default=5, help="Số items mỗi batch")
    parser.add_argument("--session-dir", type=str, help="Thư mục session")
    parser.add_argument("--get-next", action="store_true", help="Lấy batch tiếp theo")
    parser.add_argument("--submit-file", type=str, help="File JSON kết quả để duyệt")
    args = parser.parse_args()

    if args.split_dir and args.jtbd_calibrated:
        create_dedup_batches(args.jtbd_calibrated, args.split_dir, args.batch_size)
    elif args.get_next and args.session_dir:
        get_next_dedup_batch(args.session_dir)
    elif args.submit_file and args.session_dir:
        validate_dedup_submission(args.session_dir, args.submit_file)
    else:
        parser.print_help()
