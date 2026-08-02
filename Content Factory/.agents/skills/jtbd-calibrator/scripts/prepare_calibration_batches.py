import sys
import json
import uuid
import argparse
import os

# Fix Windows console encoding (cp1252 -> utf-8)
# Tranh UnicodeEncodeError khi print tieng Viet co dau hoac emoji
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def create_calibration_batches(parsed_json_path, split_dir, batch_size, source_file=None, source_link=None):
    try:
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    except Exception as e:
        print(f"[ERR] Khong the doc file audiences_parsed.json: {e}")
        sys.exit(1)

    book_entry = parsed_data.get("book")
    chunk_entries = parsed_data.get("chunks", [])
    
    if not book_entry:
        print("[ERR] Khong tim thay thong tin Book trong audiences_parsed.json")
        sys.exit(1)
        
    os.makedirs(split_dir, exist_ok=True)
    
    items_queue = []
    
    # Xu ly Book
    if isinstance(book_entry, str):
        book_payload = {"jtbd_raw": book_entry}
    else:
        book_payload = {k: v for k, v in book_entry.items()}
    book_payload["scope"] = "book"
    book_payload["chunk_index"] = None
    book_payload["chunk_name"] = None
    book_payload["uid"] = "uid_book"
    if source_link:
        book_payload["source_link"] = f"[[{source_link}#^book-overview]]"
        book_payload["source_path"] = f"02-sources/books/{source_link}.md#^book-overview"
    items_queue.append(book_payload)
    
    # Xu ly Chunks
    for chunk in chunk_entries:
        idx = chunk.get("chunk_index", 0)
        chunk_payload = {k: v for k, v in chunk.items()}
        chunk_payload["scope"] = "chunk"
        chunk_payload["uid"] = f"uid_chunk_{idx:02d}"
        if source_link:
            chunk_payload["source_link"] = f"[[{source_link}#^chunk-{idx:02d}]]"
            chunk_payload["source_path"] = f"02-sources/books/{source_link}.md#^chunk-{idx:02d}"
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
    
    # === SINH CONTEXT FILE PER-UID (neu co source_file) ===

    if source_file and os.path.exists(source_file):
        import re as _re
        with open(source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()

        # Parse header (truoc data_chunk dau tien) va tung chunk
        header = source_content.split('<data_chunk>')[0]
        chunks_raw = _re.findall(r'<data_chunk>(.*?)</data_chunk>', source_content, _re.DOTALL)

        chunk_lookup = {}
        for chunk_text in chunks_raw:
            idx_match = _re.search(r'CHUNK_index=(\d+)', chunk_text)
            if idx_match:
                chunk_lookup[int(idx_match.group(1))] = chunk_text.strip()

        for batch_idx, batch in enumerate(batches_data, 1):
            # Ghi 1 file context rieng cho moi uid trong batch
            for item in batch:
                uid = item.get("uid", "unknown")
                ctx_lines = [
                    f"# Context: {uid}",
                    "> Khi sua loi #2, #3 hoac #4: trich dan nguyen van >=20 ky tu tu phan <data_chunk> ben duoi vao truong `context_quote`.",
                    ""
                ]
                if item.get("scope") == "book":
                    ctx_lines.append(f"## {uid} -- BOOK HEADER")
                    ctx_lines.append(header.strip())
                else:
                    c_idx = item.get("chunk_index")
                    c_name = item.get("chunk_name", "Unknown")
                    if c_idx is not None and c_idx in chunk_lookup:
                        ctx_lines.append(f"## {uid} -- Chunk {c_idx}: {c_name}")
                        ctx_lines.append(chunk_lookup[c_idx])

                ctx_path = os.path.join(split_dir, f"ctx_{uid}.md")
                with open(ctx_path, 'w', encoding='utf-8') as f:
                    f.write("\n\n".join(ctx_lines))



    session_state_path = os.path.join(split_dir, "session_state.json")
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    print(f"[OK] Da phan tach 1 Book + {len(chunk_entries)} chunks thanh {total_batches} lo (kich thuoc {batch_size}). Du lieu luu tai: {split_dir}/")


def create_recalibration_batches(parsed_json_path, split_dir, batch_size):
    """Ham rieng biet cho mode re-calibrate. KHONG sua ham create_calibration_batches()."""
    try:
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    except Exception as e:
        print(f"[ERR] Khong the doc file: {e}")
        sys.exit(1)

    entries = parsed_data.get("entries", [])
    os.makedirs(split_dir, exist_ok=True)

    # Tao items_queue — loai bo context_text va context_warning (tranh bloat output)
    items_queue = []
    for idx, entry in enumerate(entries, 1):
        item = {k: v for k, v in entry.items() if k not in ('context_text', 'context_warning')}
        item['uid'] = f'uid_recalib_{idx:03d}'
        items_queue.append(item)

    batches_data = [items_queue[i:i + batch_size] for i in range(0, len(items_queue), batch_size)]
    total_batches = len(batches_data)

    session_state = {
        "mode": "re-calibrate",
        "total_batches": total_batches,
        "current_batch": 1,
        "completed": False,
        "batches_data": batches_data,
        "calibrated_items": [],
    }

    # Sinh context file per-uid (lay context_text tu entries goc)
    for batch_idx, batch in enumerate(batches_data, 1):
        # Ghi 1 file context rieng cho moi uid trong batch
        for item in batch:
            uid = item.get("uid")
            recalib_idx = int(uid.split('_')[-1]) - 1
            ctx_lines = [
                f"# Context: {uid}",
                "> Khi sua loi #2, #3 hoac #4: trich dan nguyen van >=20 ky tu tu phan <data_chunk> ben duoi vao truong `context_quote`.",
                ""
            ]
            if 0 <= recalib_idx < len(entries):
                original_entry = entries[recalib_idx]
                context_text = original_entry.get("context_text", "")
                original_filename = original_entry.get("original_filename", "Unknown")
                ctx_lines.append(f"## {uid} -- {original_filename}")
                ctx_lines.append(context_text)

            ctx_path = os.path.join(split_dir, f"ctx_{uid}.md")
            with open(ctx_path, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(ctx_lines))



    session_state_path = os.path.join(split_dir, "session_state.json")
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    print(f"[OK] Da phan tach {len(entries)} audiences thanh {total_batches} lo (kich thuoc {batch_size}). Du lieu luu tai: {split_dir}/")

def get_next_calibration_batch(session_dir):
    session_state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(session_state_path):
        print("[ERR] Khong tim thay session_state.json")
        sys.exit(1)

    with open(session_state_path, 'r', encoding='utf-8') as f:
        session_state = json.load(f)

    if session_state.get("completed"):
        print("[OK] HOAN THANH - Qua trinh Calibration da hoan tat.")
        sys.exit(0)

    current_batch = session_state["current_batch"]
    items_to_process = session_state["batches_data"][current_batch - 1]
    batch_password = uuid.uuid4().hex[:8]
    
    session_state["current_batch_password"] = batch_password
    with open(session_state_path, 'w', encoding='utf-8') as f:
        json.dump(session_state, f, ensure_ascii=False, indent=2)

    # Them context_file path vao moi item truoc khi ghi batch output
    for item in items_to_process:
        uid = item.get("uid", "unknown")
        ctx_path = os.path.join(os.path.abspath(session_dir), f"ctx_{uid}.md")
        if os.path.exists(ctx_path):
            item["context_file"] = ctx_path

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
            "context_quote": "",
            "reason": "[ĐIỀN VÀO ĐÂY]"
        })
    temp_file_path = os.path.join(os.path.abspath(session_dir), "calib_eval_temp.json")
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(template_output, f, ensure_ascii=False, indent=2)

    print(f"Lo du lieu {current_batch}/{session_state['total_batches']} da san sang tai: {batch_file_path}")
    print(f"[INFO] Tep lam bai da duoc tao san tai: {temp_file_path}. Vui long mo tep nay, thay the cac truong [DIEN VAO DAY] bang cau tra loi va goi --submit-file.")
    print(f"[INFO] Context files: moi uid co 1 file ctx_<uid>.md rieng (doc khi can sua loi #2, #3 hoac #4 — trich dan nguyen van vao truong context_quote)")

def validate_calibration_submission(session_dir, submit_file):
    session_state_path = os.path.join(session_dir, "session_state.json")
    with open(session_state_path, 'r', encoding='utf-8') as f:
        session_state = json.load(f)

    if session_state.get("completed"):
        print("[ERR] Qua trinh da hoan thanh, khong nhan them ket qua.")
        sys.exit(1)

    try:
        with open(submit_file, 'r', encoding='utf-8') as f:
            submission = json.load(f)
    except Exception as e:
        print(f"[ERR] File submit khong hop le: {e}")
        sys.exit(1)

    expected_password = session_state.get("current_batch_password")
    if submission.get("password") != expected_password:
        print("[ERR] TU CHOI TRUY CAP: Mat khau khong khop.")
        sys.exit(1)

    current_batch = session_state["current_batch"]
    expected_items = session_state["batches_data"][current_batch - 1]
    
    original_items_map = {item["uid"]: item for item in expected_items}
    expected_uids = set(original_items_map.keys())
    
    entries = submission.get("entries", [])
    submitted_uids = {e.get("uid") for e in entries}

    if expected_uids != submitted_uids:
        print(f"[ERR] UID khong khop. Yeu cau: {expected_uids}, Nhan duoc: {submitted_uids}")
        sys.exit(1)

    req_fields = ["uid", "audience_Job_performer", "audience_main_job", "audience_circumstance", "aliases", "reason"]
    for entry in entries:
        if any(k not in entry for k in req_fields):
            print(f"[ERR] Doi tuong {entry.get('uid')} thieu truong du lieu bat buoc.")
            sys.exit(1)
        if not isinstance(entry["aliases"], list):
            print(f"[ERR] Truong 'aliases' cua {entry.get('uid')} phai la mot mang (list).")
            sys.exit(1)

        # Anti-lazy validation
        for val in entry.values():
            if isinstance(val, str) and "[ĐIỀN VÀO ĐÂY]" in val:
                print(f"[ERR] Entry {entry.get('uid')} chua thay the truong placeholder '[ĐIỀN VÀO ĐÂY]'.")
                sys.exit(1)
            elif isinstance(val, list):
                for sub_val in val:
                    if isinstance(sub_val, str) and "[ĐIỀN VÀO ĐÂY]" in sub_val:
                        print(f"[ERR] Entry {entry.get('uid')} chua thay the truong placeholder '[ĐIỀN VÀO ĐÂY]' trong mang.")
                        sys.exit(1)

    # === KIEM TRA CHAT LUONG JTBD (tu dong truoc khi merge) ===
    import subprocess
    validator_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "validate_jtbd_quality.py"
    )
    if os.path.exists(validator_script):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "-X", "utf8", validator_script, submit_file],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env
        )
        if result.stdout.strip():
            print(result.stdout)
        if result.returncode != 0:
            sys.exit(1)

    # === KIEM TRA CONTEXT QUOTE (khi reason chua #2, #3 hoac #4) ===
    for entry in entries:
        reason = entry.get("reason", "")
        if "#2" in reason or "#3" in reason or "#4" in reason:
            quote = entry.get("context_quote", "").strip()
            if len(quote) < 20:
                print(f"❌ Entry {entry.get('uid')}: reason chua #2/#3/#4 nhung `context_quote` "
                      f"thieu hoac qua ngan (<20 ky tu). Doc context file ctx_{entry.get('uid')}.md "
                      f"va trich dan nguyen van >=20 ky tu tu phan <data_chunk>.")
                sys.exit(1)
            # Validate quote ton tai trong context file
            ctx_file = os.path.join(os.path.abspath(session_dir), f"ctx_{entry.get('uid')}.md")
            if os.path.exists(ctx_file):
                with open(ctx_file, 'r', encoding='utf-8') as cf:
                    ctx_content = cf.read()
                # Chi validate trong phan data_chunk
                import re as _re
                chunks = _re.findall(r'<data_chunk>(.*?)</data_chunk>', ctx_content, _re.DOTALL)
                chunk_text = '\n'.join(chunks) if chunks else ctx_content
                if quote not in chunk_text:
                    print(f"❌ Entry {entry.get('uid')}: `context_quote` khong tim thay trong noi dung "
                          f"<data_chunk> cua file ctx_{entry.get('uid')}.md. Trich dan phai la nguyen van.")
                    sys.exit(1)

    for entry in entries:
        uid = entry["uid"]
        merged_item = original_items_map[uid].copy()
        merged_item["audience_Job_performer"] = entry["audience_Job_performer"]
        merged_item["audience_main_job"] = entry["audience_main_job"]
        merged_item["audience_circumstance"] = entry["audience_circumstance"]
        merged_item["aliases"] = entry["aliases"]
        session_state["calibrated_items"].append(merged_item)

    # === GHI AUDIT LOG (append per-batch) ===
    run_folder = os.path.dirname(os.path.abspath(session_dir))
    
    # Tìm vault root để tính relative path cho Source link
    vault_root = run_folder
    while vault_root and os.path.basename(vault_root) != 'vault':
        parent = os.path.dirname(vault_root)
        if parent == vault_root:
            break
        vault_root = parent

    audit_path = os.path.join(run_folder, "calibration_audit.md")
    is_new_file = not os.path.exists(audit_path)

    with open(audit_path, 'a', encoding='utf-8') as af:
        if is_new_file:
            af.write("# Calibration Audit Log\n\n")
            af.write("> Auto-generated. Ghi lai toan bo ket qua LLM hieu dinh JTBD.\n\n")

        af.write(f"## Batch {current_batch:02d}\n\n")
        for entry in entries:
            uid = entry["uid"]
            orig = original_items_map.get(uid, {})
            # Thong tin cu
            old_performer = orig.get("audience_Job_performer", "")
            old_job = orig.get("audience_main_job", "")
            old_circ = orig.get("audience_circumstance", "")
            old_fn = orig.get("original_filename", uid)
            # Thong tin moi
            new_performer = entry["audience_Job_performer"]
            new_job = entry["audience_main_job"]
            new_circ = entry["audience_circumstance"]
            new_aliases = ", ".join(entry.get("aliases", []))
            reason = entry.get("reason", "")

            # Xac dinh co thay doi khong
            changed = (old_performer != new_performer or
                       old_job != new_job or
                       old_circ != new_circ)
            status = "CHANGED" if changed else "KEPT"

            af.write(f"### {uid} ({status})\n\n")
            # Mini table cho Source + Context (Obsidian popup cho Context)
            source_link = orig.get("source_link", "")
            source_path = orig.get("source_path", "")
            ctx_filename = f"ctx_{uid}.md"
            ctx_abs = os.path.join(os.path.abspath(session_dir), ctx_filename)
            has_source = bool(source_link and source_path)
            has_ctx = os.path.exists(ctx_abs)
            if has_source or has_ctx:
                af.write("| Source | Context |\n|---|---|\n| ")
                if has_source:
                    link_text = source_link.strip("[]")
                    abs_source = os.path.join(vault_root, source_path.split('#')[0])
                    rel_source = os.path.relpath(abs_source, run_folder).replace('\\', '/')
                    if '#' in source_path:
                        rel_source += '#' + source_path.split('#', 1)[1]
                    af.write(f"[{link_text}](<{rel_source}>)")
                af.write(" | ")
                if has_ctx:
                    ctx_rel = os.path.relpath(ctx_abs, run_folder).replace('\\', '/')
                    af.write(f"[{ctx_filename}]({ctx_rel})")
                af.write(" |\n\n")
            # Before/After table cho JTBD fields
            af.write("| Field | Before | After |\n|---|---|---|\n")
            af.write(f"| **Performer** | {old_performer} | {new_performer} |\n")
            af.write(f"| **Main Job** | {old_job} | {new_job} |\n")
            af.write(f"| **Circumstance** | {old_circ} | {new_circ} |\n\n")
            af.write(f"- **File**: `{old_fn}`\n")
            af.write(f"- **Aliases**: {new_aliases}\n")
            af.write(f"- **Reason**: {reason}\n\n")

    session_state["current_batch"] += 1
    
    if session_state["current_batch"] > session_state["total_batches"]:
        session_state["completed"] = True
        
        final_output = []
        for item in session_state["calibrated_items"]:
            clean_item = item.copy()
            if "uid" in clean_item:
                del clean_item["uid"]
            final_output.append(clean_item)
            
        mode = session_state.get("mode", "calibrate")
        filename = "jtbd_recalibrated.json" if mode == "re-calibrate" else "jtbd_calibrated.json"
        output_path = os.path.join(run_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=2)

        # Ghi summary vao cuoi audit log
        total_items = len(session_state["calibrated_items"])
        with open(audit_path, 'a', encoding='utf-8') as af:
            af.write(f"---\n\n## Summary\n\n")
            af.write(f"- **Total entries**: {total_items}\n")
            af.write(f"- **Total batches**: {session_state['total_batches']}\n")
            af.write(f"- **Output file**: `{filename}`\n")
            
        print(f"[OK] HOAN THANH - File {filename} da duoc khoi tao thanh cong tai: {os.path.abspath(output_path)}")
        print(f"[INFO] Audit log: {os.path.abspath(audit_path)}")
    else:
        print("[OK] Hop nhat thanh cong. Vui long goi --get-next cho lo du lieu tiep theo.")

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
    parser.add_argument("--source-file", type=str, help="File nguồn gốc (dùng sinh context file)")
    parser.add_argument("--source-link", type=str, help="Ten source cho Obsidian wikilink, VD: 'Beyond the rainbow bridge'")
    args = parser.parse_args()

    if args.split_dir and args.parsed_json:
        # Auto-detect mode tu parsed JSON
        with open(args.parsed_json, 'r', encoding='utf-8') as _f:
            _peek = json.load(_f)
        if _peek.get("mode") == "re-calibrate":
            create_recalibration_batches(args.parsed_json, args.split_dir, args.batch_size)
        else:
            create_calibration_batches(args.parsed_json, args.split_dir, args.batch_size, args.source_file, args.source_link)
    elif args.get_next and args.session_dir:
        get_next_calibration_batch(args.session_dir)
    elif args.submit_file and args.session_dir:
        validate_calibration_submission(args.session_dir, args.submit_file)
    else:
        parser.print_help()
