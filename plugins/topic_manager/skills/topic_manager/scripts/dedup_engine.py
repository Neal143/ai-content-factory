"""
Tên file: dedup_engine.py
Last update: 01/06/2026 23:55 (GMT+7)
Vai trò: Quản lý quy trình 2-Pass Semantic Dedup (Internal & External) và Biên dịch (Compile & Commit) YAML.
Sử dụng khi nào: Trong Phase 1, Bước 1.5 của book-parser, khi Plugin topic_manager được triệu gọi.
Output:
  - internal_state.json & internal_temp.json (Chặng 1)
  - external_state.json & external_temp.json (Chặng 2)
  - resolved_topics.json (Chặng 3 - Biên dịch)
Tóm tắt logic hoạt động:
  - Chặng 1 (Internal): Rolling batch 5 items, gộp các raw topics trùng lặp nội bộ, xuất unique_topics.json.
  - Chặng 2 (External): Rolling batch 5 items, đối chiếu unique topics với global topic_map.yaml.
  - Chặng 3 (Compile & Commit): Dò ngược luồng gộp, cộng dồn audiences, gọi topic_manager.py để cập nhật YAML, xuất resolved_topics.json.
"""
import os
import json
import yaml
import uuid
import sys
import argparse

# Nhóm 0: Đảm bảo import trực tiếp module topic_manager.py nằm cùng thư mục scripts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import topic_manager

# ==================== CHẶNG 1: INTERNAL DEDUP ====================

def prepare_internal(session_dir, proposed_topics_path):
    """Khởi tạo trạng thái và chuẩn bị batch 5 raw topics cho chặng Internal Dedup"""
    # Nhóm 1.1: Tạo thư mục session và cấu hình đường dẫn file state
    os.makedirs(session_dir, exist_ok=True)
    state_file = os.path.join(session_dir, "internal_state.json")
    
    # Nhóm 1.2: Khởi tạo trạng thái ban đầu từ proposed_topics.json nếu file state chưa tồn tại
    if not os.path.exists(state_file):
        if not os.path.exists(proposed_topics_path):
            print(f"❌ Lỗi: Không tìm thấy file proposed_topics.json tại: {proposed_topics_path}")
            sys.exit(1)
        with open(proposed_topics_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        state = {
            "pending": data.get("entries", []),
            "resolved": {},
            "unique_topics": [],
            "pillar": data.get("pillar", ""),
            "completed": False
        }
    else:
        # Nhóm 1.3: Nạp lại file state cũ nếu đang tiếp tục xử lý batch dang dở
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
    # Nhóm 1.4: Kiểm tra nếu chặng 1 đã hoàn tất thì thoát
    if state.get("completed"):
        print("🎉 Chặng 1 (Internal Dedup) ĐÃ HOÀN THÀNH. Hãy bắt đầu Chặng 2.")
        return
        
    pending = state.get("pending", [])
    
    # Nhóm 1.5: Kiểm tra nếu hết hàng chờ pending, đánh dấu hoàn thành và xuất các file map trung gian
    if not pending:
        state["completed"] = True
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        with open(os.path.join(session_dir, "unique_topics.json"), 'w', encoding='utf-8') as f:
            json.dump(state["unique_topics"], f, ensure_ascii=False, indent=2)
        with open(os.path.join(session_dir, "internal_map.json"), 'w', encoding='utf-8') as f:
            json.dump(state["resolved"], f, ensure_ascii=False, indent=2)
        print("🎉 Chặng 1 (Internal Dedup) ĐÃ HOÀN THÀNH. Đã tạo unique_topics.json và internal_map.json.")
        return
        
    # Nhóm 1.6: Lấy 5 raw topics đầu tiên trong danh sách pending để gộp thành lô batch
    batch = pending[:5]
    
    # Nhóm 1.7: Sinh mã khóa bảo vệ (Password Gate) ngẫu nhiên để chống bypass tiến trình tuần tự
    batch_password = uuid.uuid4().hex[:8]
    state["password"] = batch_password
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    # Nhóm 1.8: Trích xuất tối đa 5 unique topics gần nhất làm anchors phục vụ rolling comparison
    anchors = state.get("unique_topics", [])[-5:]
    
    # Nhóm 1.9: Tạo file pre-filled template internal_temp.json để Agent điền form trong IDE
    template_data = {
        "password": batch_password,
        "anchors": anchors,
        "batch_topics": []
    }
    for item in batch:
        template_data["batch_topics"].append({
            "proposed_id": item["id"],
            "label": item["label"],
            "action": "[ĐIỀN VÀO ĐÂY: create hoặc merge]",
            "resolved_to": "[ĐIỀN VÀO ĐÂY: Nếu merge, điền id của anchor hoặc topic trước trong batch. Nếu create, để trống]",
            "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích lý do chọn action này (LLM-CAPTCHA)]"
        })
        
    temp_file = os.path.join(session_dir, "internal_temp.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
        
    print(f"📝 Tệp làm bài Chặng 1 ĐÃ SẴN SÀNG tại: {temp_file}")
    print("⚠️ Hãy mở tệp trên trong IDE, điền form quyết định rồi chạy cờ --submit-internal.")


def submit_internal(session_dir, submit_file):
    """Validate bài làm Chặng 1 và cập nhật trạng thái internal_state.json"""
    # Nhóm 1.10: Kiểm tra sự tồn tại của file internal_state.json trước khi submit
    state_file = os.path.join(session_dir, "internal_state.json")
    if not os.path.exists(state_file):
        print("❌ Lỗi: Không tìm thấy internal_state.json. Hãy gọi --prepare-internal trước.")
        sys.exit(1)
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    if state.get("completed"):
        print("❌ Reject: Chặng 1 đã hoàn tất từ trước.")
        return
        
    # Nhóm 1.11: Đọc và phân tích file nộp bài JSON của Agent
    try:
        with open(submit_file, 'r', encoding='utf-8') as f:
            submit_data = json.load(f)
    except Exception as e:
        print(f"❌ Reject: Lỗi đọc file submit: {str(e)}")
        return
        
    # Nhóm 1.12: Xác thực Password Gate bảo mật xem có đúng phiên batch hiện tại không
    if submit_data.get("password") != state.get("password"):
        print("❌ Reject: Sai password bảo mật")
        return
        
    pending = state.get("pending", [])
    batch = pending[:5]
    submit_topics = submit_data.get("batch_topics", [])
    
    # Nhóm 1.13: Kiểm tra số lượng items trong form có khớp với lô batch được cấp phát không
    if len(submit_topics) != len(batch):
        print(f"❌ Reject: Số lượng items trong form ({len(submit_topics)}) khác với lô ({len(batch)})")
        return
        
    resolved = state.setdefault("resolved", {})
    unique_topics = state.setdefault("unique_topics", [])
    current_batch_created = set()
    
    # Nhóm 1.14: Duyệt kiểm duyệt nghiêm ngặt từng dòng quyết định
    for i, t in enumerate(submit_topics):
        proposed_id = t.get("proposed_id", "")
        action = t.get("action", "")
        reason = t.get("reasoning", "")
        
        # Nhóm 1.14.1: Kiểm tra khớp đề xuất ID
        if proposed_id != batch[i]["id"]:
            print(f"❌ Reject: Mismatch proposed_id ở vị trí {i} ('{proposed_id}' vs '{batch[i]['id']}')")
            return
            
        # Nhóm 1.14.2: Kiểm tra action hợp lệ (chỉ chấp nhận create hoặc merge)
        if action not in ["create", "merge"]:
            print(f"❌ Reject: Action '{action}' tại topic '{proposed_id}' không hợp lệ")
            return
            
        # Nhóm 1.14.3: Kiểm tra LLM-CAPTCHA (reasoning có thực sự được phân tích sâu sắc >= 15 ký tự không)
        if "[ĐIỀN VÀO ĐÂY" in reason or len(reason.strip()) < 15:
            print(f"❌ Reject: Thiếu reasoning LLM-CAPTCHA tại topic '{proposed_id}'")
            return
            
        # Nhóm 1.14.4: Xử lý khi chọn create mới
        if action == "create":
            unique_id = proposed_id.replace('-', '_').lower()
            resolved[proposed_id] = unique_id
            current_batch_created.add(unique_id)
            if not any(x["id"] == unique_id for x in unique_topics):
                unique_topics.append({
                    "id": unique_id,
                    "label": batch[i]["label"],
                    "pillar": state["pillar"]
                })
        # Nhóm 1.14.5: Xử lý khi chọn merge (so khớp) vào topic đã ghi nhận
        else:
            resolved_to = t.get("resolved_to", "").replace('-', '_').lower()
            if not resolved_to or "[ĐIỀN VÀO ĐÂY" in resolved_to:
                print(f"❌ Reject: Merge topic '{proposed_id}' nhưng thiếu trường resolved_to")
                return
            exists_in_unique = any(x["id"] == resolved_to for x in unique_topics)
            exists_in_batch = resolved_to in current_batch_created
            if not (exists_in_unique or exists_in_batch):
                print(f"❌ Reject: resolved_to '{resolved_to}' không tồn tại trong tập hợp unique")
                return
            resolved[proposed_id] = resolved_to
            
    # Nhóm 1.15: Tiến tới lô tiếp theo, xóa lô cũ ra khỏi hàng chờ pending
    state["pending"] = pending[len(batch):]
    
    # Nhóm 1.16: Nếu hoàn tất toàn bộ pending, xuất 2 file kết quả chặng 1
    if not state["pending"]:
        state["completed"] = True
        with open(os.path.join(session_dir, "unique_topics.json"), 'w', encoding='utf-8') as f:
            json.dump(state["unique_topics"], f, ensure_ascii=False, indent=2)
        with open(os.path.join(session_dir, "internal_map.json"), 'w', encoding='utf-8') as f:
            json.dump(state["resolved"], f, ensure_ascii=False, indent=2)
        print("🎉 Chặng 1 (Internal Dedup) ĐÃ HOÀN THÀNH. Đã tạo unique_topics.json và internal_map.json.")
    else:
        print(f"✅ Đã duyệt xong lô batch! Còn lại {len(state['pending'])} items. Vui lòng gọi tiếp --prepare-internal.")
        
    # Nhóm 1.17: Cập nhật lưu lại file trạng thái
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== CHẶNG 2: EXTERNAL MATCH ====================

def prepare_external(session_dir, map_path):
    """Khởi tạo trạng thái và chuẩn bị batch 5 unique topics cho chặng so khớp ngoại vi"""
    # Nhóm 2.1: Kiểm tra sự tồn tại của file unique_topics.json từ chặng 1
    state_file = os.path.join(session_dir, "external_state.json")
    unique_topics_file = os.path.join(session_dir, "unique_topics.json")
    
    if not os.path.exists(unique_topics_file):
        print(f"❌ Lỗi: Không tìm thấy unique_topics.json tại: {unique_topics_file}. Hãy hoàn tất Chặng 1 trước.")
        sys.exit(1)
        
    # Nhóm 2.2: Khởi tạo trạng thái external matcher nếu chưa có
    if not os.path.exists(state_file):
        with open(unique_topics_file, 'r', encoding='utf-8') as f:
            unique_topics = json.load(f)
        state = {
            "pending": unique_topics,
            "resolved": {},
            "completed": False
        }
    else:
        # Nhóm 2.3: Nạp lại trạng thái nếu đang tiếp tục xử lý
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            
    # Nhóm 2.4: Kiểm tra trạng thái hoàn thành
    if state.get("completed"):
        print("🎉 Chặng 2 (External Match) ĐÃ HOÀN THÀNH. Vui lòng chạy cờ --compile-and-commit.")
        return
        
    pending = state.get("pending", [])
    
    # Nhóm 2.5: Nếu đã hết hàng chờ, ghi nhận hoàn thành chặng và xuất external_decisions.json
    if not pending:
        state["completed"] = True
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        with open(os.path.join(session_dir, "external_decisions.json"), 'w', encoding='utf-8') as f:
            json.dump(state["resolved"], f, ensure_ascii=False, indent=2)
        print("🎉 Chặng 2 (External Match) ĐÃ HOÀN THÀNH. Đã tạo external_decisions.json.")
        return
        
    # Nhóm 2.6: Phân lô 5 unique topics tiếp theo
    batch = pending[:5]
    
    # Nhóm 2.7: Sinh mã bảo mật lô chống bypass tiến trình
    batch_password = uuid.uuid4().hex[:8]
    state["password"] = batch_password
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    # Nhóm 2.8: Sinh file pre-filled external_temp.json để Agent điền form trong IDE
    template_data = {
        "password": batch_password,
        "batch_topics": []
    }
    for item in batch:
        template_data["batch_topics"].append({
            "proposed_id": item["id"],
            "label": item["label"],
            "action": "[ĐIỀN VÀO ĐÂY: create hoặc merge]",
            "resolved_to": "[ĐIỀN VÀO ĐÂY: Nếu merge, điền id gốc trong topic_map.yaml. Nếu create, để trống]",
            "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích lý do chọn action này (LLM-CAPTCHA)]"
        })
        
    temp_file = os.path.join(session_dir, "external_temp.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
        
    print(f"📝 Tệp làm bài Chặng 2 ĐÃ SẴN SÀNG tại: {temp_file}")
    print(f"⚠️ Hãy mở tệp trong IDE, đối chiếu với: {map_path}, điền form rồi chạy cờ --submit-external.")


def submit_external(session_dir, map_path, submit_file):
    """Validate bài làm Chặng 2 và cập nhật trạng thái external_state.json"""
    # Nhóm 2.9: Kiểm tra sự tồn tại của file external_state.json
    state_file = os.path.join(session_dir, "external_state.json")
    if not os.path.exists(state_file):
        print("❌ Lỗi: Không tìm thấy external_state.json. Hãy gọi --prepare-external trước.")
        sys.exit(1)
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    if state.get("completed"):
        print("❌ Reject: Chặng 2 đã hoàn tất từ trước.")
        return
        
    # Nhóm 2.10: Đọc và phân tích file nộp bài external_temp.json
    try:
        with open(submit_file, 'r', encoding='utf-8') as f:
            submit_data = json.load(f)
    except Exception as e:
        print(f"❌ Reject: Lỗi đọc file submit: {str(e)}")
        return
        
    # Nhóm 2.11: Kiểm tra khóa mật mã bảo vệ lô
    if submit_data.get("password") != state.get("password"):
        print("❌ Reject: Sai password bảo mật")
        return
        
    # Nhóm 2.12: Đọc file topic_map.yaml toàn cục để phục vụ công tác xác thực ID tồn tại
    if not os.path.exists(map_path):
        print(f"❌ Lỗi: Không tìm thấy file map toàn cục tại: {map_path}")
        sys.exit(1)
        
    with open(map_path, 'r', encoding='utf-8') as f:
        global_map = yaml.safe_load(f) or {"topics": []}
    global_ids = {t["id"] for t in global_map.get("topics", [])}
    
    pending = state.get("pending", [])
    batch = pending[:5]
    submit_topics = submit_data.get("batch_topics", [])
    
    # Nhóm 2.13: Kiểm tra khớp số lượng đề xuất trong lô
    if len(submit_topics) != len(batch):
        print(f"❌ Reject: Số lượng items trong form ({len(submit_topics)}) khác với lô ({len(batch)})")
        return
        
    resolved = state.setdefault("resolved", {})
    
    # Nhóm 2.14: Duyệt kiểm duyệt nghiêm ngặt từng quyết định nộp lên
    for i, t in enumerate(submit_topics):
        proposed_id = t.get("proposed_id", "")
        action = t.get("action", "")
        reason = t.get("reasoning", "")
        
        # Nhóm 2.14.1: Kiểm tra ID đề xuất khớp
        if proposed_id != batch[i]["id"]:
            print(f"❌ Reject: Mismatch proposed_id ở vị trí {i} ('{proposed_id}' vs '{batch[i]['id']}')")
            return
            
        # Nhóm 2.14.2: Kiểm tra action
        if action not in ["create", "merge"]:
            print(f"❌ Reject: Action '{action}' tại topic '{proposed_id}' không hợp lệ")
            return
            
        # Nhóm 2.14.3: Kiểm tra LLM-CAPTCHA
        if "[ĐIỀN VÀO ĐÂY" in reason or len(reason.strip()) < 15:
            print(f"❌ Reject: Thiếu reasoning LLM-CAPTCHA tại topic '{proposed_id}'")
            return
            
        # Nhóm 2.14.4: Lưu vết quyết định ghi mới
        if action == "create":
            unique_id = proposed_id.replace('-', '_').lower()
            resolved[proposed_id] = unique_id
        # Nhóm 2.14.5: Kiểm tra và lưu vết quyết định gộp vào ID toàn cục sẵn có
        else:
            resolved_to = t.get("resolved_to", "").replace('-', '_').lower()
            if not resolved_to or "[ĐIỀN VÀO ĐÂY" in resolved_to:
                print(f"❌ Reject: Merge topic '{proposed_id}' nhưng thiếu trường resolved_to")
                return
            if resolved_to not in global_ids:
                print(f"❌ Reject: resolved_to '{resolved_to}' không tồn tại trong file topic_map.yaml toàn cục")
                return
            resolved[proposed_id] = resolved_to
            
    # Nhóm 2.15: Cập nhật hàng chờ, loại bỏ lô batch đã hoàn tất
    state["pending"] = pending[len(batch):]
    
    # Nhóm 2.16: Xuất external_decisions.json khi duyệt hết pending unique topics
    if not state["pending"]:
        state["completed"] = True
        with open(os.path.join(session_dir, "external_decisions.json"), 'w', encoding='utf-8') as f:
            json.dump(state["resolved"], f, ensure_ascii=False, indent=2)
        print("🎉 Chặng 2 (External Match) ĐÃ HOÀN THÀNH. Đã tạo external_decisions.json.")
    else:
        print(f"✅ Đã duyệt xong lô batch! Còn lại {len(state['pending'])} items. Vui lòng gọi tiếp --prepare-external.")
        
    # Nhóm 2.17: Cập nhật file trạng thái external_state.json
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ==================== CHẶNG 3: COMPILE & COMMIT ====================

def compile_and_commit(session_dir, map_path):
    """
    Tự động hóa hoàn toàn chặng 3: 
    1. Đọc và dò luồng gộp: raw_id -> unique_id -> final_id.
    2. Gộp audiences tương ứng của tất cả các raw topics bị gộp.
    3. Trực tiếp import và gọi các hàm của topic_manager.py để cập nhật YAML toàn cục.
    4. Xuất resolved_topics.json cho atomizer.py.
    """
    # Nhóm 3.1: Kiểm tra sự tồn tại đầy đủ của các file kết quả trung gian từ cả 2 chặng
    proposed_file = os.path.join(session_dir, "proposed_topics.json")
    internal_map_file = os.path.join(session_dir, "internal_map.json")
    external_decisions_file = os.path.join(session_dir, "external_decisions.json")
    unique_topics_file = os.path.join(session_dir, "unique_topics.json")
    
    if not (os.path.exists(proposed_file) and os.path.exists(internal_map_file) and os.path.exists(external_decisions_file)):
        print("❌ Lỗi: Không thể biên dịch! Thiếu file kết quả của Chặng 1 hoặc Chặng 2.")
        sys.exit(1)
        
    # Nhóm 3.2: Đọc dữ liệu từ đề xuất thô và các tệp ánh xạ quyết định
    with open(proposed_file, 'r', encoding='utf-8') as f:
        proposed = json.load(f)
    with open(internal_map_file, 'r', encoding='utf-8') as f:
        internal_map = json.load(f)
    with open(external_decisions_file, 'r', encoding='utf-8') as f:
        external_decisions = json.load(f)
    with open(unique_topics_file, 'r', encoding='utf-8') as f:
        unique_topics = json.load(f)
        
    # Nhóm 3.3: Lấy danh sách ID hiện có trong topic_map.yaml toàn cục để biết topic nào cũ hay mới
    if not os.path.exists(map_path):
        global_ids = set()
    else:
        with open(map_path, 'r', encoding='utf-8') as f:
            global_map = yaml.safe_load(f) or {"topics": []}
        global_ids = {t["id"] for t in global_map.get("topics", [])}
        
    unique_labels = {t["id"]: t["label"] for t in unique_topics}
    
    final_topics = {}
    resolved_dict = {}
    
    # Nhóm 3.4: Ráp nối chuỗi gộp và gom nhóm lũy kế mảng audiences
    for entry in proposed.get("entries", []):
        raw_id = entry["id"]
        group = entry["source_group"]
        
        # Dò ngược: raw -> unique -> final
        unique_id = internal_map.get(raw_id, raw_id)
        final_id = external_decisions.get(unique_id, unique_id)
        
        is_external_merge = final_id in global_ids
        
        if final_id not in final_topics:
            label = unique_labels.get(final_id, entry["label"])
            final_topics[final_id] = {
                "label": label,
                "audiences": set(),
                "groups": set(),
                "is_external_merge": is_external_merge
            }
            
        for aud in entry.get("audiences", []):
            final_topics[final_id]["audiences"].add(aud)
        final_topics[final_id]["groups"].add(group)
        
    # Nhóm 3.5: Gọi hàm từ module topic_manager.py ghi trực tiếp xuống file topic_map.yaml toàn cục
    pillar = proposed.get("pillar", "")
    for final_id, data in final_topics.items():
        audiences_list = list(data["audiences"])
        if data["is_external_merge"]:
            # Gọi hàm append thêm audience vào topic đã có sẵn
            topic_manager.update_audience(map_path, final_id, audiences_list)
        else:
            # Gọi hàm ghi mới topic hoàn toàn mới vào YAML
            topic_manager.confirm_new(map_path, [final_id], [data["label"]], pillar, audiences_list)
            # Thêm ngay vào global_ids để tránh ghi trùng lặp trong cùng một lô chạy
            global_ids.add(final_id)
            
        # Ráp nối ID quyết định vào dictionary kết quả cho atomizer.py theo từng source_group (chunk index/book)
        for group in data["groups"]:
            resolved_dict.setdefault(group, [])
            if final_id not in resolved_dict[group]:
                resolved_dict[group].append(final_id)
                
    # Nhóm 3.6: Kết xuất file resolved_topics.json bàn giao
    out_file = os.path.join(session_dir, "resolved_topics.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(resolved_dict, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 BIÊN DỊCH VÀ COMMIT HOÀN TẤT!")
    print(f"👉 Đã cập nhật file: {map_path}")
    print(f"👉 Đã kết xuất file resolved_topics.json tại: {out_file}")


# ==================== CLI PARSER ====================

if __name__ == "__main__":
    # Nhóm 4.1: Định nghĩa cấu trúc cờ lệnh CLI cho bộ điều phối dedup_engine
    parser = argparse.ArgumentParser(description="Plugin Topic Manager - Trình điều phối 2-Pass Dedup Engine")
    parser.add_argument("--session-dir", required=True, help="Thư mục session quản lý trạng thái làm bài")
    parser.add_argument("--map-path", help="Đường dẫn đến file topic_map.yaml toàn cục")
    parser.add_argument("--proposed-topics-path", help="Đường dẫn đến proposed_topics.json")
    parser.add_argument("--submit-file", help="Đường dẫn đến file JSON nộp bài")
    
    parser.add_argument("--prepare-internal", action="store_true", help="Chuẩn bị batch cho Chặng 1 (Internal)")
    parser.add_argument("--submit-internal", action="store_true", help="Nộp bài cho Chặng 1 (Internal)")
    parser.add_argument("--prepare-external", action="store_true", help="Chuẩn bị batch cho Chặng 2 (External)")
    parser.add_argument("--submit-external", action="store_true", help="Nộp bài cho Chặng 2 (External)")
    parser.add_argument("--compile-and-commit", action="store_true", help="Chạy tự động hóa Chặng 3 (Biên dịch)")
    
    args = parser.parse_args()
    
    # Nhóm 4.2: Định tuyến hành động dựa trên cờ lệnh CLI được gọi
    if args.prepare_internal:
        proposed_path = args.proposed_topics_path or os.path.join(args.session_dir, "proposed_topics.json")
        prepare_internal(args.session_dir, proposed_path)
        
    elif args.submit_internal:
        submit_path = args.submit_file or os.path.join(args.session_dir, "internal_temp.json")
        submit_internal(args.session_dir, submit_path)
        
    elif args.prepare_external:
        if not args.map_path:
            print("❌ Lỗi: Cần truyền tham số --map-path cho External Matcher")
            sys.exit(1)
        prepare_external(args.session_dir, args.map_path)
        
    elif args.submit_external:
        if not args.map_path:
            print("❌ Lỗi: Cần truyền tham số --map-path cho External Matcher")
            sys.exit(1)
        submit_path = args.submit_file or os.path.join(args.session_dir, "external_temp.json")
        submit_external(args.session_dir, args.map_path, submit_path)
        
    elif args.compile_and_commit:
        if not args.map_path:
            print("❌ Lỗi: Cần truyền tham số --map-path cho Compile & Commit")
            sys.exit(1)
        compile_and_commit(args.session_dir, args.map_path)
        
    else:
        parser.print_help()
