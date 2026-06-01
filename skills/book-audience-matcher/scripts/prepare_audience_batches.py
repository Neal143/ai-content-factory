# ==============================================================================
# Tên file: prepare_audience_batches.py
# Last update: 30/05/2026 15:30 (GMT+7)
# Vai trò: Chia unique audiences thành batch, quản lý session tuần tự có khóa (password gate).
# Sử dụng khi: Giai đoạn 2 (Bước 2.2 + 2.3) của book-audience-matcher.
# Output: Các file batch kèm password, session_state.json, collected_decisions.json (khi hoàn thành).
# Tóm tắt logic hoạt động:
#   - Split: Đọc internal_map.json, chia unique_audiences thành nhiều file batch kèm mật khẩu ngẫu nhiên
#     và khởi tạo file trạng thái session_state.json.
#   - Get-next: Copy file batch hiện tại sang thư mục chạy dưới dạng current_audience_batch.json.
#   - Submit: Kiểm tra tính hợp lệ của file nộp (password, UID, cấu trúc, số lượng) và cập nhật
#     trạng thái session để chuyển sang batch tiếp theo hoặc hoàn thành toàn bộ.
# ==============================================================================

import os
import sys
import json
import uuid
import argparse
import shutil

# ==============================================================================
# Nhóm 1: Hàm chia Batch (Split Mode)
# ==============================================================================
def create_batches(internal_map_path, split_dir, batch_size):
    """
    Đọc internal_map.json, chia unique_audiences thành các batch nhỏ và khởi tạo session_state.json.
    """
    # Đọc file internal_map.json
    try:
        with open(internal_map_path, 'r', encoding='utf-8') as f:
            internal_map = json.load(f)
    except Exception as e:
        print(f"❌ Không thể đọc file internal_map: {e}")
        sys.exit(1)

    unique_audiences = internal_map.get("unique_audiences", [])
    if not unique_audiences:
        print("❌ No unique audiences found")
        sys.exit(1)

    # Đảm bảo thư mục đầu ra tồn tại
    os.makedirs(split_dir, exist_ok=True)

    # Chia mảng unique_audiences thành các batch
    batches = [unique_audiences[i:i + batch_size] for i in range(0, len(unique_audiences), batch_size)]
    total_batches = len(batches)

    # Ghi từng batch file
    for idx, batch_items in enumerate(batches, start=1):
        batch_password = uuid.uuid4().hex[:8]
        
        # Chỉ trích xuất các trường cần thiết cho LLM, loại bỏ internal_parents để LLM tập trung vào External Match
        items_payload = []
        for item in batch_items:
            items_payload.append({
                "uid": item.get("uid"),
                "id": item.get("id"),
                "semantic_query": item.get("semantic_query"),
                "file_ref": item.get("file_ref")
            })

        batch_data = {
            "batch_index": idx,
            "batch_password": batch_password,
            "total_batches": total_batches,
            "items": items_payload
        }

        batch_file_path = os.path.join(split_dir, f"batch_{idx:02d}.json")
        with open(batch_file_path, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)

    # Khởi tạo trạng thái phiên làm việc (session_state.json)
    session_state = {
        "total_batches": total_batches,
        "current_batch": 1,
        "completed": False,
        "submitted_decisions": []
    }
    
    session_state_path = os.path.join(split_dir, "session_state.json")
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(unique_audiences)} unique audiences → {total_batches} batches (size={batch_size}). Output: {split_dir}/")

# ==============================================================================
# Nhóm 2: Hàm lấy Batch tiếp theo (Get-next Mode)
# ==============================================================================
def get_next_batch(session_dir):
    """
    Đọc session_state.json và copy batch hiện tại ra run-folder để LLM xử lý.
    """
    session_state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(session_state_path):
        print(f"❌ Không tìm thấy session_state.json tại: {session_dir}")
        sys.exit(1)

    with open(session_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # Kiểm tra xem session đã hoàn thành chưa
    if state.get("completed", False):
        print("🎉 HOÀN THÀNH")
        sys.exit(0)

    current_batch = state["current_batch"]
    total_batches = state["total_batches"]

    # Xác định đường dẫn file batch gốc và file copy đích (run-folder)
    batch_filename = f"batch_{current_batch:02d}.json"
    batch_src_path = os.path.join(session_dir, batch_filename)
    
    batch_dest_path = os.path.join(os.path.abspath(session_dir), "current_audience_batch.json")

    if not os.path.exists(batch_src_path):
        print(f"❌ Không tìm thấy file batch nguồn: {batch_src_path}")
        sys.exit(1)

    # Thực hiện copy file batch hiện tại ra vị trí sẵn sàng cho LLM
    try:
        shutil.copy(batch_src_path, batch_dest_path)
    except Exception as e:
        print(f"❌ Lỗi khi copy file batch: {e}")
        sys.exit(1)

    # Tự động sinh tệp Template
    with open(batch_src_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
        
    template_output = {
        "password": batch_data.get("batch_password"),
        "entries": []
    }
    for item in batch_data.get("items", []):
        template_output["entries"].append({
            "uid": item["uid"],
            "action": "[ĐIỀN VÀO ĐÂY: merge hoặc create]",
            "audience_filename": "[ĐIỀN VÀO ĐÂY]",
            "audience_level": "[ĐIỀN VÀO ĐÂY: big, little, micro]",
            "parent_audience_append": ["[ĐIỀN VÀO ĐÂY]"],
            "external_parents": ["[ĐIỀN VÀO ĐÂY]"],
            "reason": "[ĐIỀN VÀO ĐÂY]"
        })
    temp_file_path = os.path.join(os.path.abspath(session_dir), "audience_eval_temp.json")
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(template_output, f, ensure_ascii=False, indent=2)

    print(f"Batch {current_batch}/{total_batches} đã sẵn sàng tại: {batch_dest_path}")
    print(f"📝 Tệp làm bài đã được tạo sẵn tại: {temp_file_path}. Vui lòng mở tệp này, thay thế các trường [ĐIỀN VÀO ĐÂY] bằng câu trả lời và gọi --submit-file.")

# ==============================================================================
# Nhóm 3: Hàm xác thực và lưu kết quả nộp (Submit Mode)
# ==============================================================================
def validate_submission(session_dir, submit_file_path):
    """
    Kiểm tra tính hợp lệ của kết quả nộp của một batch, nếu khớp password và đầy đủ thông tin
    thì tích lũy quyết định và chuyển sang batch tiếp theo.
    """
    session_state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(session_state_path):
        print(f"❌ Không tìm thấy session_state.json tại: {session_dir}")
        sys.exit(1)

    with open(session_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    if state.get("completed", False):
        print("❌ Reject: Session này đã hoàn tất hoàn toàn, không thể nộp thêm.")
        sys.exit(1)

    current_batch = state["current_batch"]
    total_batches = state["total_batches"]

    # Đọc dữ liệu của batch hiện tại từ file session đã lưu
    batch_file_path = os.path.join(session_dir, f"batch_{current_batch:02d}.json")
    if not os.path.exists(batch_file_path):
        print(f"❌ Lỗi hệ thống: Không tìm thấy file batch {batch_file_path}")
        sys.exit(1)

    with open(batch_file_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)

    # Đọc dữ liệu người dùng submit
    if not os.path.exists(submit_file_path):
        print(f"❌ Reject: Không tìm thấy file kết quả nộp tại {submit_file_path}")
        sys.exit(1)

    try:
        with open(submit_file_path, 'r', encoding='utf-8') as f:
            submit_data = json.load(f)
    except Exception as e:
        print(f"❌ Reject: File nộp không phải định dạng JSON hợp lệ: {e}")
        sys.exit(1)

    # 1. Password check
    password_submitted = submit_data.get("password")
    password_expected = batch_data.get("batch_password")
    if password_submitted != password_expected:
        print("❌ Reject: Sai password")
        sys.exit(1)

    # 2. Entries count check
    entries = submit_data.get("entries", [])
    items = batch_data.get("items", [])
    if len(entries) != len(items):
        print(f"❌ Reject: Thiếu/thừa entries (Nộp {len(entries)} nhưng batch yêu cầu {len(items)})")
        sys.exit(1)

    # 3. UID set check
    uids_submitted = {entry.get("uid") for entry in entries}
    uids_expected = {item.get("uid") for item in items}
    if uids_submitted != uids_expected:
        print(f"❌ Reject: UID không khớp (Expected: {uids_expected}, Got: {uids_submitted})")
        sys.exit(1)

    # 4. Format check từng entry
    required_fields = {"uid", "action", "audience_filename", "audience_level", "parent_audience_append", "external_parents", "reason"}
    valid_actions = {"merge", "create"}

    for idx, entry in enumerate(entries):
        missing = required_fields - set(entry.keys())
        if missing:
            print(f"❌ Reject: Entry {idx} thiếu trường bắt buộc: {missing}")
            sys.exit(1)

        action = entry.get("action")
        if action not in valid_actions:
            print(f"❌ Reject: Entry {idx} có action không hợp lệ '{action}' (phải là merge hoặc create)")
            sys.exit(1)

        # Đảm bảo các trường kiểu list là list thực tế
        if not isinstance(entry.get("parent_audience_append"), list):
            print(f"❌ Reject: Entry {idx} trường parent_audience_append phải là list")
            sys.exit(1)

        if not isinstance(entry.get("external_parents"), list):
            print(f"❌ Reject: Entry {idx} trường external_parents phải là list")
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

    # NẾU TẤT CẢ VALIDATION ĐỀU ĐẠT
    print(f"✅ Batch {current_batch}/{total_batches} PASS validation.")

    # Gom các quyết định đã được duyệt vào danh sách tích lũy của session (tự động loại bỏ trường reason)
    for entry in entries:
        clean_entry = {k: v for k, v in entry.items() if k != "reason"}
        state["submitted_decisions"].append(clean_entry)
    
    # Tiến tới batch tiếp theo
    state["current_batch"] += 1

    # Kiểm tra xem đã xử lý xong toàn bộ các batch chưa
    if state["current_batch"] > total_batches:
        state["completed"] = True
        
        # Ghi file collected_decisions.json ra run-folder (cấp cha của session_dir)
        run_folder = os.path.dirname(os.path.abspath(session_dir))
        collected_path = os.path.join(run_folder, "collected_decisions.json")
        with open(collected_path, 'w', encoding='utf-8') as f:
            json.dump(state["submitted_decisions"], f, ensure_ascii=False, indent=2)
            
        print(f"🎉 HOÀN THÀNH — collected_decisions.json đã sẵn sàng tại: {os.path.abspath(collected_path)}")

    # Lưu lại trạng thái session mới nhất
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

# ==============================================================================
# Nhóm 4: Điều khiển dòng CLI
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Gatekeeper cho Audience Matcher")
    parser.add_argument("--internal-map", type=str, help="Path tới internal_map.json")
    parser.add_argument("--split-dir", type=str, help="Thư mục chứa batch files")
    parser.add_argument("--batch-size", type=int, default=5, help="Số items mỗi batch")
    parser.add_argument("--session-dir", type=str, help="Thư mục session (= split-dir)")
    parser.add_argument("--get-next", action="store_true", help="Lấy batch tiếp theo")
    parser.add_argument("--submit-file", type=str, help="File JSON kết quả để duyệt")
    
    args = parser.parse_args()

    # Route request dựa trên các tham số CLI truyền vào
    if args.split_dir and args.internal_map:
        create_batches(args.internal_map, args.split_dir, args.batch_size)
    elif args.get_next and args.session_dir:
        get_next_batch(args.session_dir)
    elif args.submit_file and args.session_dir:
        validate_submission(args.session_dir, args.submit_file)
    else:
        parser.print_help()
