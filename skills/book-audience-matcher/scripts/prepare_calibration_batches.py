import sys
import json
import uuid
import argparse
import os

def create_calibration_batches(parsed_json_path, split_dir, batch_size):
    try:
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    except Exception as e:
        print(f"❌ Không thể đọc file audiences_parsed.json: {e}")
        sys.exit(1)

    book_entry = parsed_data.get("book")
    chunk_entries = parsed_data.get("chunks", [])
    
    if not book_entry:
        print("❌ Không tìm thấy thông tin Book trong audiences_parsed.json")
        sys.exit(1)
        
    os.makedirs(split_dir, exist_ok=True)
    
    items_queue = []
    
    # Xử lý Book
    if isinstance(book_entry, str):
        book_payload = {"jtbd_raw": book_entry}
    else:
        book_payload = {k: v for k, v in book_entry.items()}
    book_payload["scope"] = "book"
    book_payload["chunk_index"] = None
    book_payload["chunk_name"] = None
    book_payload["uid"] = "uid_book"
    items_queue.append(book_payload)
    
    # Xử lý Chunks
    for chunk in chunk_entries:
        idx = chunk.get("chunk_index", 0)
        chunk_payload = {k: v for k, v in chunk.items()}
        chunk_payload["scope"] = "chunk"
        chunk_payload["uid"] = f"uid_chunk_{idx:02d}"
        items_queue.append(chunk_payload)
        
    batches_data = [items_queue[i:i + batch_size] for i in range(0, len(items_queue), batch_size)]
    total_batches = len(batches_data)
    
    session_state = {
        "total_batches": total_batches,
        "current_batch": 1,
        "completed": False,
        "batches_data": batches_data,
        "calibrated_items": []
    }
    
    session_state_path = os.path.join(split_dir, "session_state.json")
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã phân tách 1 Book + {len(chunk_entries)} chunks thành {total_batches} lô (kích thước {batch_size}). Dữ liệu lưu tại: {split_dir}/")

def get_next_calibration_batch(session_dir):
    session_state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(session_state_path):
        print("❌ Không tìm thấy session_state.json")
        sys.exit(1)

    with open(session_state_path, 'r', encoding='utf-8') as f:
        session_state = json.load(f)

    if session_state.get("completed"):
        print("🎉 HOÀN THÀNH — Quá trình Calibration đã hoàn tất.")
        sys.exit(0)

    current_batch = session_state["current_batch"]
    items_to_process = session_state["batches_data"][current_batch - 1]
    batch_password = uuid.uuid4().hex[:8]
    
    session_state["current_batch_password"] = batch_password
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    batch_output = {
        "batch_index": current_batch,
        "batch_password": batch_password,
        "total_batches": session_state["total_batches"],
        "items_to_process": items_to_process
    }

    batch_file_path = os.path.join(os.path.abspath(session_dir), "current_calib_batch.json")
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
            "audience_Job_performer": "[ĐIỀN VÀO ĐÂY]",
            "audience_main_job": item.get("audience_main_job", ""),
            "audience_circumstance": item.get("audience_circumstance", ""),
            "aliases": ["[ĐIỀN VÀO ĐÂY]", "[ĐIỀN VÀO ĐÂY]"],
            "reason": "[ĐIỀN VÀO ĐÂY]"
        })
    temp_file_path = os.path.join(os.path.abspath(session_dir), "calib_eval_temp.json")
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(template_output, f, ensure_ascii=False, indent=2)

    print(f"Lô dữ liệu {current_batch}/{session_state['total_batches']} đã sẵn sàng tại: {batch_file_path}")
    print(f"📝 Tệp làm bài đã được tạo sẵn tại: {temp_file_path}. Vui lòng mở tệp này, thay thế các trường [ĐIỀN VÀO ĐÂY] bằng câu trả lời và gọi --submit-file.")

def validate_calibration_submission(session_dir, submit_file):
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
        print("❌ ⛔ TỪ CHỐI TRUY CẬP: Mật khẩu không khớp.")
        sys.exit(1)

    current_batch = session_state["current_batch"]
    expected_items = session_state["batches_data"][current_batch - 1]
    
    original_items_map = {item["uid"]: item for item in expected_items}
    expected_uids = set(original_items_map.keys())
    
    entries = submission.get("entries", [])
    submitted_uids = {e.get("uid") for e in entries}

    if expected_uids != submitted_uids:
        print(f"❌ UID không khớp. Yêu cầu: {expected_uids}, Nhận được: {submitted_uids}")
        sys.exit(1)

    req_fields = ["uid", "audience_Job_performer", "audience_main_job", "audience_circumstance", "aliases", "reason"]
    for entry in entries:
        if any(k not in entry for k in req_fields):
            print(f"❌ Đối tượng {entry.get('uid')} thiếu trường dữ liệu bắt buộc.")
            sys.exit(1)
        if not isinstance(entry["aliases"], list):
            print(f"❌ Trường 'aliases' của {entry.get('uid')} phải là một mảng (list).")
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

    for entry in entries:
        uid = entry["uid"]
        merged_item = original_items_map[uid].copy()
        merged_item["audience_Job_performer"] = entry["audience_Job_performer"]
        merged_item["audience_main_job"] = entry["audience_main_job"]
        merged_item["audience_circumstance"] = entry["audience_circumstance"]
        merged_item["aliases"] = entry["aliases"]
        session_state["calibrated_items"].append(merged_item)

    session_state["current_batch"] += 1
    
    if session_state["current_batch"] > session_state["total_batches"]:
        session_state["completed"] = True
        
        final_output = []
        for item in session_state["calibrated_items"]:
            clean_item = item.copy()
            if "uid" in clean_item:
                del clean_item["uid"]
            final_output.append(clean_item)
            
        run_folder = os.path.dirname(os.path.abspath(session_dir))
        output_path = os.path.join(run_folder, "jtbd_calibrated.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)
            
        print(f"🎉 HOÀN THÀNH — File jtbd_calibrated.json đã được khởi tạo thành công tại: {os.path.abspath(output_path)}")
    else:
        print("✅ Hợp nhất thành công. Vui lòng gọi --get-next cho lô dữ liệu tiếp theo.")

    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batching Gatekeeper cho Calibration")
    parser.add_argument("--parsed-json", type=str, help="Đường dẫn tới audiences_parsed.json")
    parser.add_argument("--split-dir", type=str, help="Thư mục chứa dữ liệu phân lô")
    parser.add_argument("--batch-size", type=int, default=5, help="Số mục mỗi lô")
    parser.add_argument("--session-dir", type=str, help="Thư mục session")
    parser.add_argument("--get-next", action="store_true", help="Cấp phát lô dữ liệu tiếp theo")
    parser.add_argument("--submit-file", type=str, help="File JSON kết quả để xác thực")
    args = parser.parse_args()

    if args.split_dir and args.parsed_json:
        create_calibration_batches(args.parsed_json, args.split_dir, args.batch_size)
    elif args.get_next and args.session_dir:
        get_next_calibration_batch(args.session_dir)
    elif args.submit_file and args.session_dir:
        validate_calibration_submission(args.session_dir, args.submit_file)
    else:
        parser.print_help()
