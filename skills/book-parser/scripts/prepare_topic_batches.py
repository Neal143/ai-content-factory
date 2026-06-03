import os
import json
import glob
import re
import uuid
import argparse
import shutil
import subprocess
from pathlib import Path

"""
Tên file: prepare_topic_batches.py
Last update: 30/05/2026 06:15 (GMT+7)
Vai trò: Chia nội dung chunk sách thành batch, gatekeeper truy cập tuần tự, validate submission.
Sử dụng khi: Phase 4 (Topic Gen) của book-extractor pipeline.
Output:
  - [split-dir]/batch_NN.json (batch files)
  - [split-dir]/session_state.json (trạng thái batch)
  - [run_folder]/current_topic_batch.json (batch hiện tại cho Agent đọc)
  - [run_folder]/collected_topics.json (danh sách topics thô gom từ tất cả batch)
Tóm tắt logic:
  - --split-dir: Đọc chunk_XX_raw.txt + chunk_XX_gate.json → skip chunk passed=false
    → gom batch → ghi batch files + session_state.json.
  - --get-next: Đọc session_state → copy batch hiện tại → current_topic_batch.json.
  - --submit-file: Validate password + entries + evidence substring → PASS: advance,
    FAIL: in lỗi. Khi hết batch → gom submitted_topics → collected_topics.json.
"""

# === NHÓM 1: Parsing & Filtering chunks ===
def normalize_whitespace(text: str) -> str:
    """Normalize text for evidence substring matching"""
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_valid_chunks(run_folder: str) -> list:
    """Quét và lấy danh sách chunks hợp lệ (passed = true)"""
    chunks = []
    session_1_dir = os.path.join(os.path.abspath(run_folder), "session_1")
    chunk_files = sorted(glob.glob(os.path.join(session_1_dir, "chunk_*_raw.txt")))
    skipped_count = 0
    
    for raw_file in chunk_files:
        filename = os.path.basename(raw_file)
        chunk_idx_str = filename.replace("chunk_", "").replace("_raw.txt", "")
        if not chunk_idx_str.isdigit():
            continue
            
        chunk_index = int(chunk_idx_str)
        gate_file = os.path.join(session_1_dir, f"chunk_{chunk_idx_str.zfill(2)}_gate.json")
        
        # Default true if gate file missing, else check passed
        is_passed = True
        if os.path.exists(gate_file):
            try:
                with open(gate_file, 'r', encoding='utf-8') as f:
                    gate_data = json.load(f)
                    is_passed = gate_data.get("passed", False)
            except Exception:
                is_passed = False
        
        if not is_passed:
            skipped_count += 1
            continue
            
        with open(raw_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Get chunk name (first line typically)
        chunk_name = content.split('\n')[0].strip() if content.strip() else f"Chunk {chunk_index}"
        
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_name": chunk_name,
            "content": content,
            "raw_file_path": raw_file
        })
        
    return chunks, skipped_count

# === NHÓM 2: Batch splitting & file I/O ===
def create_batches(run_folder: str, split_dir: str, batch_size: int):
    """Tạo batch files từ valid chunks"""
    if os.path.exists(split_dir):
        shutil.rmtree(split_dir)
    os.makedirs(split_dir)
    
    chunks, skipped_count = get_valid_chunks(run_folder)
    
    batches = []
    for i in range(0, len(chunks), batch_size):
        batches.append(chunks[i:i + batch_size])
        
    total_batches = len(batches)
    
    for idx, batch_chunks in enumerate(batches):
        batch_idx = idx + 1
        batch_password = uuid.uuid4().hex[:8]
        
        batch_data = {
            "batch_index": batch_idx,
            "batch_password": batch_password,
            "total_batches": total_batches,
            "chunks": [
                {
                    "chunk_index": c["chunk_index"],
                    "chunk_name": c["chunk_name"],
                    "content": c["content"]
                } for c in batch_chunks
            ]
        }
        
        with open(os.path.join(split_dir, f"batch_{batch_idx:02d}.json"), 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
            
    # Create session state
    session_state = {
        "total_batches": total_batches,
        "current_batch": 1,
        "completed": total_batches == 0,
        "submitted_topics": []
    }
    
    with open(os.path.join(split_dir, "session_state.json"), 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)
        
    print(f"✅ {len(chunks)} chunks hợp lệ, {skipped_count} chunks skipped, {total_batches} batches tạo.")

# === NHÓM 2.5: Book Topics ===
def prepare_book_topics(run_folder: str):
    session_dir = os.path.join(os.path.abspath(run_folder), "session_4")
    os.makedirs(session_dir, exist_ok=True)
    temp_file_path = os.path.join(session_dir, "book_topics_temp.json")
    
    # Sinh Password Gate ngẫu nhiên
    batch_password = uuid.uuid4().hex[:8]
    
    template_data = {
        "password": batch_password,
        "pillar": "[ĐIỀN VÀO ĐÂY: Tên Pillar]",
        "book_topics": [
            {
                "id": "[ĐIỀN VÀO ĐÂY: snake_case]", 
                "label": "[ĐIỀN VÀO ĐÂY: Tiếng Việt]", 
                "tier": "[ĐIỀN VÀO ĐÂY: broad/medium/narrow]",
                "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích lý do chọn Topic này dựa trên tổng quan cuốn sách (LLM-CAPTCHA)]"
            },
            {
                "id": "[ĐIỀN VÀO ĐÂY: snake_case]", 
                "label": "[ĐIỀN VÀO ĐÂY: Tiếng Việt]", 
                "tier": "[ĐIỀN VÀO ĐÂY: broad/medium/narrow]",
                "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích lý do chọn Topic này dựa trên tổng quan cuốn sách (LLM-CAPTCHA)]"
            },
            {
                "id": "[ĐIỀN VÀO ĐÂY: (Tùy chọn) Bỏ qua slot này nếu không có]", 
                "label": "[ĐIỀN VÀO ĐÂY: (Tùy chọn)]", 
                "tier": "narrow",
                "reasoning": "[ĐIỀN VÀO ĐÂY: (Tùy chọn)]"
            }
        ]
    }
    
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(template_data, f, ensure_ascii=False, indent=2)
        
    state_file = os.path.join(session_dir, "book_topic_state.json")
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump({"password": batch_password}, f)
        
    print(f"📝 Tệp làm bài ĐÃ ĐƯỢC TẠO SẴN tại: {temp_file_path}")
    print(f"⚠️ Vui lòng mở tệp này ra bằng công cụ IDE, SỬA/THAY THẾ các trường [ĐIỀN VÀO ĐÂY], sau đó gọi --submit-book-topics.")

def submit_book_topics(run_folder: str, submit_file: str):
    session_dir = os.path.join(os.path.abspath(run_folder), "session_4")
    state_file = os.path.join(session_dir, "book_topic_state.json")
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        with open(submit_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc file: {str(e)}")
        return

    if data.get("password") != state.get("password"):
        print("❌ Reject: Sai password")
        return

    pillar = data.get("pillar", "")
    if "[ĐIỀN VÀO ĐÂY" in pillar or not pillar:
        print("❌ Reject: Pillar chưa được điền hợp lệ")
        return
        
    raw_topics = data.get("book_topics", [])
    valid_topics = []
    
    for idx, topic in enumerate(raw_topics):
        t_id = topic.get("id", "")
        if "[ĐIỀN VÀO ĐÂY" in t_id:
            continue
            
        t_label = topic.get("label", "")
        t_tier = topic.get("tier", "")
        t_reason = topic.get("reasoning", "")
        
        if "[ĐIỀN VÀO ĐÂY" in t_label or "[ĐIỀN VÀO ĐÂY" in t_tier:
            print(f"❌ Reject: Topic {idx} chưa điền đủ label/tier")
            return
            
        if "[ĐIỀN VÀO ĐÂY" in t_reason or len(t_reason.strip()) < 15:
            print(f"❌ Reject: Topic {idx} thiếu giải thích reasoning (LLM-CAPTCHA)")
            return
            
        if not re.match(r'^[a-z0-9_]+$', t_id):
            print(f"❌ Reject: Topic {idx} có id sai format '{t_id}'")
            return
            
        valid_topics.append({"id": t_id, "label": t_label, "tier": t_tier})

    if len(valid_topics) < 2:
        print("❌ Reject: Phải có ít nhất 2 book topics")
        return
        
    final_data = {"pillar": pillar, "book_topics": valid_topics}
    final_file = os.path.join(session_dir, "book_topics_draft.json")
    with open(final_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ PASS validation. book_topics_draft.json đã sẵn sàng tại:\n{final_file}")

# === NHÓM 3: Session state management ===
def get_next_batch(run_folder: str, session_dir: str):
    """Lấy batch hiện tại cho Agent đọc"""
    state_file = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(state_file):
        print("Lỗi: Không tìm thấy session_state.json")
        return
        
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    if state.get("completed", False):
        print("Đã hoàn tất toàn bộ batch. 🎉 HOÀN THÀNH")
        return
        
    current_batch = state["current_batch"]
    batch_file = os.path.join(session_dir, f"batch_{current_batch:02d}.json")
    
    if not os.path.exists(batch_file):
        print(f"Lỗi: Không tìm thấy file batch {batch_file}")
        return
        
    target_file = os.path.join(run_folder, "current_topic_batch.json")
    shutil.copy2(batch_file, target_file)
    
    # Sinh file template điền sẵn
    temp_file_path = os.path.join(run_folder, "topic_eval_temp.json")
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
        
    template_data = {
        "password": batch_data["batch_password"],
        "entries": [
            {
                "chunk_index": c["chunk_index"],
                "topics": [
                    {
                        "id": "[ĐIỀN VÀO ĐÂY: snake_case]",
                        "label": "[ĐIỀN VÀO ĐÂY: Tiếng Việt]",
                        "tier": "[ĐIỀN VÀO ĐÂY: broad/medium/narrow]",
                        "evidence": "[ĐIỀN VÀO ĐÂY: Trích nguyên văn]",
                        "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích sự liên kết logic giữa Chunk Topic này và Book Topic tương ứng (LLM-CAPTCHA)]"
                    },
                    {
                        "id": "[ĐIỀN VÀO ĐÂY: snake_case]",
                        "label": "[ĐIỀN VÀO ĐÂY: Tiếng Việt]",
                        "tier": "[ĐIỀN VÀO ĐÂY: broad/medium/narrow]",
                        "evidence": "[ĐIỀN VÀO ĐÂY: Trích nguyên văn]",
                        "reasoning": "[ĐIỀN VÀO ĐÂY: Giải thích sự liên kết logic giữa Chunk Topic này và Book Topic tương ứng (LLM-CAPTCHA)]"
                    }
                ]
            } for c in batch_data["chunks"]
        ]
    }
    with open(temp_file_path, 'w', encoding='utf-8') as tf:
        json.dump(template_data, tf, ensure_ascii=False, indent=2)

    print(f"Batch {current_batch}/{state['total_batches']} đã sẵn sàng tại:\n{target_file}")
    print(f"📝 Tệp làm bài ĐÃ ĐƯỢC TẠO SẴN tại: {temp_file_path}")
    print(f"⚠️ Vui lòng mở tệp này ra và SỬA/THAY THẾ các trường [ĐIỀN VÀO ĐÂY], sau đó gọi --submit-file.")

# === NHÓM 4: Submission validation ===
def validate_submission(run_folder: str, session_dir: str, submit_file: str):
    """Validate submission từ Agent và cập nhật state"""
    state_file = os.path.join(session_dir, "session_state.json")
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
    if state.get("completed", False):
        print("Lỗi: Quá trình phân tích đã hoàn tất.")
        return
        
    current_batch = state["current_batch"]
    batch_file = os.path.join(session_dir, f"batch_{current_batch:02d}.json")
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
        
    try:
        with open(submit_file, 'r', encoding='utf-8') as f:
            submit_data = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc file submit: {str(e)}")
        return
        
    # 1. Password check
    if submit_data.get("password") != batch_data["batch_password"]:
        print("❌ Reject: Sai password")
        return
        
    entries = submit_data.get("entries", [])
    batch_chunks = batch_data.get("chunks", [])
    
    # 2. Entries count
    if len(entries) != len(batch_chunks):
        print(f"❌ Reject: Thiếu/thừa entries (yêu cầu {len(batch_chunks)}, nhận {len(entries)})")
        return
        
    # Prepare lookup for chunk content validation
    expected_indices = set(c["chunk_index"] for c in batch_chunks)
    chunk_contents = {c["chunk_index"]: normalize_whitespace(c["content"]) for c in batch_chunks}
    
    for idx, entry in enumerate(entries):
        chunk_idx = entry.get("chunk_index")
        
        # 3. Chunk index matches
        if chunk_idx not in expected_indices:
            print(f"❌ Reject: chunk_index {chunk_idx} không khớp với batch hiện tại")
            return
            
        expected_indices.remove(chunk_idx)
        topics = entry.get("topics", [])
        
        # 4. Topics count
        if len(topics) < 2:
            print(f"❌ Reject: Entry {chunk_idx} thiếu topics (yêu cầu ≥2)")
            return
            
        for topic in topics:
            t_id = topic.get("id", "")
            t_label = topic.get("label", "")
            t_tier = topic.get("tier", "")
            t_evi = topic.get("evidence", "")
            
            # 5. Format id (snake_case, 2-5 words roughly checking alpha_numeric_underscores)
            if not re.match(r'^[a-z0-9_]+$', t_id) or not (1 < len(t_id.split('_')) <= 6):
                print(f"❌ Reject: Entry {chunk_idx} có id sai format '{t_id}' (yêu cầu snake_case, 2-5 từ)")
                return
                
            # 6. Label format (must contain some vietnamese chars or spaces, simple check)
            if not re.search(r'[a-zA-ZÀ-ỹ]', t_label):
                print(f"❌ Reject: Entry {chunk_idx} có label thiếu chữ/dấu hợp lệ '{t_label}'")
                return
                
            # 7. Tier format
            if t_tier not in ["broad", "medium", "narrow"]:
                print(f"❌ Reject: Entry {chunk_idx} có tier không hợp lệ '{t_tier}'")
                return
                
            # 8. Evidence substring check
            norm_evi = normalize_whitespace(t_evi)
            if norm_evi not in chunk_contents[chunk_idx]:
                print(f"❌ Reject: Entry {chunk_idx} evidence không tìm thấy trong nội dung chunk:\n'{t_evi}'")
                return
                
            # 9. LLM-CAPTCHA check
            t_reason = topic.get("reasoning", "")
            if "[ĐIỀN VÀO ĐÂY" in t_reason or len(t_reason.strip()) < 15:
                print(f"❌ Reject: Entry {chunk_idx} thiếu reasoning (LLM-CAPTCHA)")
                return
                
    # All checks passed
    print(f"✅ Batch {current_batch}/{state['total_batches']} PASS validation.")
    
    # Strip evidence and format for collected_topics
    clean_entries = []
    for entry in entries:
        clean_entry = {
            "chunk_index": entry["chunk_index"],
            "topics": [{"id": t["id"], "label": t["label"], "tier": t["tier"]} for t in entry["topics"]]
        }
        clean_entries.append(clean_entry)
        
    state["submitted_topics"].extend(clean_entries)
    
    # Advance
    state["current_batch"] += 1
    if state["current_batch"] > state["total_batches"]:
        state["completed"] = True
        
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    # === NHÓM 5: Output collection ===
    if state["completed"]:
        out_file = os.path.join(run_folder, "collected_topics.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(state["submitted_topics"], f, ensure_ascii=False, indent=2)
        print(f"🎉 HOÀN THÀNH — collected_topics.json đã sẵn sàng tại:\n{out_file}")

# === NHÓM 5.5: Xuất Dữ Liệu Đề Xuất Bàn Giao ===
def export_proposed_topics(run_folder: str, decision_map_path: str):
    """
    Gom dữ liệu topic từ book draft và chunk topics, gán nhãn audience tương ứng và xuất ra proposed_topics.json.
    Tệp xuất ra sẽ là đầu vào cho Plugin Topic Manager xử lý 2-Pass Dedup.
    """
    # Nhóm 5.5.1: Thiết lập thư mục session và cấu hình đường dẫn xuất file
    session_dir = os.path.join(os.path.abspath(run_folder), "session_4")
    out_file = os.path.join(session_dir, "proposed_topics.json")
    
    # Nhóm 5.5.2: Đọc dữ liệu nguồn thô của book, chunk và bản đồ phân phối audience
    with open(os.path.join(session_dir, "book_topics_draft.json"), 'r', encoding='utf-8') as f:
        book_data = json.load(f)
    with open(os.path.join(session_dir, "collected_topics.json"), 'r', encoding='utf-8') as f:
        chunk_data = json.load(f)
    with open(decision_map_path, 'r', encoding='utf-8') as f:
        dec_map = json.load(f)

    entries = []
    
    # Nhóm 5.5.3: Trích xuất và gắn mảng audience cho Book level
    book_aud = next((m["audience_filename"] for m in dec_map if m["scope"] == "book"), "")
    for t in book_data["book_topics"]:
        entries.append({
            "source_group": "book",
            "id": t["id"],
            "label": t["label"],
            "audiences": [f"[[{book_aud}]]"] if book_aud else []
        })
        
    # Nhóm 5.5.4: Trích xuất và gắn mảng audience cho từng Chunk level tương ứng
    for c in chunk_data:
        idx = c["chunk_index"]
        c_aud = next((m["audience_filename"] for m in dec_map if m.get("chunk_index") == idx), "")
        for t in c["topics"]:
            entries.append({
                "source_group": str(idx),
                "id": t["id"],
                "label": t["label"],
                "audiences": [f"[[{c_aud}]]"] if c_aud else []
            })
            
    # Nhóm 5.5.5: Ghi lưu kết quả proposed_topics.json cho plugin
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({"pillar": book_data["pillar"], "entries": entries}, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã kết xuất thành công {len(entries)} đề xuất vào: {out_file}")

# === NHÓM 6: CLI argument parser ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chuẩn bị và quản lý Batch Topic Gen")
    parser.add_argument("--run-folder", type=str, help="Thư mục chạy của sách")
    parser.add_argument("--split-dir", type=str, help="Thư mục chứa các file batch cắt nhỏ")
    parser.add_argument("--batch-size", type=int, default=10, help="Số chunks mỗi batch")
    
    parser.add_argument("--session-dir", type=str, help="Thư mục quản lý state (--split-dir)")
    parser.add_argument("--get-next", action="store_true", help="Lấy batch tiếp theo")
    parser.add_argument("--submit-file", type=str, help="File JSON kết quả từ Agent để duyệt")
    
    parser.add_argument("--prepare-book-topics", action="store_true", help="Sinh template cho Book Topics")
    parser.add_argument("--submit-book-topics", type=str, help="Submit file Book Topics")
    
    parser.add_argument("--export-proposed-topics", action="store_true", help="Kết xuất proposed_topics.json bàn giao cho Plugin")
    parser.add_argument("--decision-map", type=str, help="Đường dẫn audience_decision_map.json")
    
    args = parser.parse_args()
    
    if args.split_dir and args.run_folder and not args.get_next and not args.submit_file:
        create_batches(args.run_folder, args.split_dir, args.batch_size)
    elif args.get_next and args.session_dir:
        r_folder = os.path.dirname(os.path.abspath(args.session_dir))
        get_next_batch(r_folder, args.session_dir)
    elif args.submit_file and args.session_dir:
        r_folder = os.path.dirname(os.path.abspath(args.session_dir))
        validate_submission(r_folder, args.session_dir, args.submit_file)
    elif args.prepare_book_topics and args.run_folder:
        prepare_book_topics(args.run_folder)
    elif args.submit_book_topics and args.run_folder:
        submit_book_topics(args.run_folder, args.submit_book_topics)
    elif args.export_proposed_topics and args.run_folder and args.decision_map:
        export_proposed_topics(args.run_folder, args.decision_map)
    else:
        parser.print_help()
