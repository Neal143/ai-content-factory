# -*- coding: utf-8 -*-
"""
Tên file: extract_vivids.py
Last update: 29/05/2026 17:15 (GMT+7)
Vai trò: (1) Trích xuất candidates vivid kèm context từ file cache sách. (2) Quản lý chuỗi đánh giá batch-by-batch với cơ chế Cryptographic Token-Passing.
Được sử dụng khi nào: Bước 2.2 của Core Skill Phase 2 (Curate Vivids).
Output:
  - Extraction Mode: vivid_candidates.json, vivid_chunks/ (batch files + session_state.json + _manifest.json).
  - Interactive Mode: In nội dung batch, xác thực bảng điểm, sinh discards.json khi hoàn tất chuỗi.
Tóm tắt logic hoạt động:
  Extraction Mode (khi có cache_file + --output + --split-dir):
    1. Đọc file cache, parse chunks, trích xuất vivid kèm context.
    2. Cắt tỉa (prune) knowledges thừa không có vivid reference.
    3. Gom chunks thành batch files, nhét password ngẫu nhiên vào mỗi batch.
    4. Tạo session_state.json (quản lý tiến trình) và _manifest.json.
  Interactive Mode (khi có --session-dir):
    --get-next: Xuất batch hiện tại ra current_batch.json trong run_folder.
    --submit-file: Xác thực password + số lượng vivid + format + rubric scores. Lưu discards. Xuất batch tiếp hoặc sinh discards.json.
"""

import sys
import re
import json
import argparse
import os
import uuid  # Dùng cho sinh password ngẫu nhiên trong batch files

# Cấu hình UTF-8 cho stdout và stderr trên Windows để chống lỗi UnicodeEncodeError khi in emoji/tiếng Việt
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def extract_pairs(match_group):
    """
    Trích xuất các cặp key=value được ngăn cách bằng dấu gạch đứng (|) từ một thẻ META.
    """
    target_dict = {}
    if not match_group:
        return target_dict
    pairs = match_group.split('|')
    for pair in pairs:
        if '=' in pair:
            k, v = pair.split('=', 1)
            target_dict[k.strip()] = v.strip()
    return target_dict

def parse_book_vivids(cache_file_path):
    """
    Đọc và phân tích file cache để trích xuất danh sách candidates vivid kèm context.
    """
    if not os.path.exists(cache_file_path):
        print(f"❌ File cache không tồn tại tại đường dẫn: {cache_file_path}")
        sys.exit(1)

    with open(cache_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Trích xuất tên sách từ META_BOOK ở header
    pattern_book = r'\*?\*?META_BOOK:\*?\*?\s*(.*?)(?=\n|$)'
    match_book = re.search(pattern_book, content)
    book_name = "Unknown Book"
    if match_book:
        book_meta = extract_pairs(match_book.group(1))
        book_name = book_meta.get("book_name", "Unknown Book")

    # 2. Tách các data chunks bằng thẻ <data_chunk>...</data_chunk>
    chunk_pattern = r'<data_chunk>([\s\S]*?)</data_chunk>'
    chunks_iter = re.finditer(chunk_pattern, content)
    
    parsed_chunks = []
    total_vivids = 0
    skipped_warnings_count = 0
    
    # Thống kê chi tiết loại vivid
    vivid_stats = {
        "vivid_circumstance": 0,
        "vivid_insight": 0,
        "vivid_knowledge": 0
    }

    for chunk_match in chunks_iter:
        chunk_content = chunk_match.group(1)

        # Cách ly chunk có chứa cờ warning
        if '> [!warning]' in chunk_content:
            skipped_warnings_count += 1
            continue

        # Lấy META_CHUNK để biết index và tên chunk
        pattern_chunk = r'\*?\*?META_CHUNK:\*?\*?\s*(.*?)(?=\n|$)'
        match_chunk = re.search(pattern_chunk, chunk_content)
        chunk_index = -1
        chunk_name = "Unknown Chunk"
        
        if match_chunk:
            chunk_meta = extract_pairs(match_chunk.group(1))
            chunk_index = int(chunk_meta.get("CHUNK_index", -1))
            chunk_name = chunk_meta.get("CHUNK", "Unknown Chunk")

        # Phân rã nội dung chunk bằng regex split dựa trên các thẻ META
        pattern_meta = r'\*?\*?META_(?:INSIGHT|KNOWLEDGE|EVIDENCE|STORY|QUOTE|CHUNK_AUDIENCE):\*?\*?\s*(.*?)(?=\n|$)'
        parts = re.split(pattern_meta, chunk_content)

        jtbd = ""
        insight = None
        knowledges = []
        vivids = []

        # parts[0] là phần mở đầu trước thẻ META đầu tiên
        # parts[1] là metadata của thẻ META đầu tiên, parts[2] là phần body text tiếp theo, và cứ thế...
        for i in range(1, len(parts), 2):
            meta_str = parts[i]
            body_text = parts[i+1].strip() if i+1 < len(parts) else ""
            
            # Làm sạch structural headers rác cuối body text
            body_text = re.sub(r'\n*^\s*[-*]*\s*[①②③④⑤].*$', '', body_text, flags=re.MULTILINE | re.DOTALL)
            body_text = re.sub(r'\n+\s*[-*]*\s*\*{0,2}🔥.*$', '', body_text, flags=re.MULTILINE | re.DOTALL)
            body_text = body_text.strip()

            meta_pairs = extract_pairs(meta_str)
            content_type = meta_pairs.get("content_type", "")

            # A. Nếu là thẻ META chứa vivid
            if content_type.startswith("vivid_"):
                # Thân của vivid luôn là dòng đầu tiên dưới thẻ META
                lines = body_text.split('\n')
                vivid_body = lines[0].strip() if lines else ""

                # Chỉ lưu các vivid active (bỏ qua [NOT_FOUND] hoặc trống)
                if vivid_body and vivid_body != "[NOT_FOUND]":
                    vivid_type = content_type
                    parent = ""
                    if vivid_type == "vivid_circumstance":
                        parent = "circumstance"
                    elif vivid_type == "vivid_insight":
                        parent = meta_pairs.get("supports_insight", "")
                    elif vivid_type == "vivid_knowledge":
                        parent = meta_pairs.get("supports_knowledge", "")

                    vivids.append({
                        "vivid_type": vivid_type,
                        "parent": parent,
                        "body": vivid_body
                    })
                    
                    # Cập nhật thống kê
                    total_vivids += 1
                    if vivid_type in vivid_stats:
                        vivid_stats[vivid_type] += 1
            
            # B. Nếu là thẻ META cấu trúc cha (chứa context)
            else:
                # Trích xuất JTBD
                if "chunk_audience" in meta_pairs:
                    jtbd = meta_pairs["chunk_audience"]
                
                # Trích xuất Insight cha
                if "insight_name" in meta_pairs:
                    insight = {
                        "name": meta_pairs["insight_name"],
                        "body": body_text
                    }
                
                # Trích xuất Knowledge cha
                if "knowledge_name" in meta_pairs:
                    knowledges.append({
                        "name": meta_pairs["knowledge_name"],
                        "body": body_text
                    })

        # Lưu chunk nếu có dữ liệu
        parsed_chunks.append({
            "chunk_index": chunk_index,
            "chunk_name": chunk_name,
            "context": {
                "jtbd": jtbd,
                "insight": insight,
                "knowledges": knowledges
            },
            "vivids": vivids
        })

    # Xây dựng cấu trúc dữ liệu JSON output
    output_data = {
        "book_name": book_name,
        "total_vivids": total_vivids,
        "chunks": parsed_chunks
    }

    return output_data, skipped_warnings_count, vivid_stats

def handle_get_next(session_dir):
    """
    Xuất batch hiện tại ra current_batch.json trong run_folder.
    Agent sẽ dùng view_file đọc file này thay vì đọc stdout.
    Nếu tất cả batch đã xử lý xong, in thông báo hoàn thành.
    """
    state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(state_path):
        print("❌ Không tìm thấy session_state.json. Hãy chạy Extraction Mode trước.")
        sys.exit(1)

    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    current = state['current_batch']
    total = state['total_batches']

    if current > total:
        print("✅ Tất cả batch đã được xử lý xong. File discards.json đã được tạo.")
        return

    batch_filename = f"batch_{current:02d}.json"
    batch_path = os.path.join(session_dir, batch_filename)

    if not os.path.exists(batch_path):
        print(f"❌ File batch không tồn tại: {batch_path}")
        sys.exit(1)

    # Sao chép batch hiện tại ra run_folder/current_batch.json để agent đọc qua view_file
    run_folder = os.path.dirname(session_dir)
    current_batch_path = os.path.join(run_folder, "current_batch.json")
    with open(batch_path, 'r', encoding='utf-8') as src:
        content = src.read()
    with open(current_batch_path, 'w', encoding='utf-8') as dst:
        dst.write(content)

    print(f"📋 BATCH {current}/{total} — Đã xuất: {current_batch_path}")
    print(f"⚠️ Dùng view_file đọc file trên → đánh giá từng vivid (Rubric C1-C5) → tạo eval_temp.json → gọi --submit-file.")

def handle_submit(session_dir, submit_file_path):
    """
    Xác thực bảng điểm của Agent: check password, đếm vivid, check format, validate rubric scores.
    Nếu hợp lệ: lưu discards vào session_state, xuất batch tiếp ra current_batch.json hoặc hoàn tất.
    """
    state_path = os.path.join(session_dir, "session_state.json")
    if not os.path.exists(state_path):
        print("❌ Không tìm thấy session_state.json.")
        sys.exit(1)

    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    current = state['current_batch']
    total = state['total_batches']

    if current > total:
        print("✅ Tất cả batch đã được xử lý xong rồi.")
        return

    # --- 1. Đọc file batch gốc để lấy password và danh sách vivid ---
    batch_filename = f"batch_{current:02d}.json"
    batch_path = os.path.join(session_dir, batch_filename)
    with open(batch_path, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)

    expected_password = batch_data.get('batch_password', '')

    # Đếm tổng vivid trong batch
    expected_vivid_count = 0
    for chunk in batch_data.get('chunks', []):
        expected_vivid_count += len(chunk.get('vivids', []))

    # --- 2. Đọc file nộp bài của Agent ---
    if not os.path.exists(submit_file_path):
        print(f"❌ File nộp bài không tồn tại: {submit_file_path}")
        sys.exit(1)

    with open(submit_file_path, 'r', encoding='utf-8') as f:
        submission = json.load(f)

    # --- 3. Xác thực Password ---
    submitted_password = submission.get('password', '')
    if submitted_password != expected_password:
        print(f"❌ SAI MẬT KHẨU. Bạn phải đọc file batch để lấy mật khẩu đúng.")
        sys.exit(1)

    # --- 4. Xác thực số lượng evaluations ---
    evaluations = submission.get('evaluations', [])
    if len(evaluations) != expected_vivid_count:
        print(f"❌ SỐ LƯỢNG KHÔNG KHỚP. Batch có {expected_vivid_count} vivids nhưng bạn nộp {len(evaluations)} evaluations.")
        print(f"   Bạn PHẢI chấm điểm cho TẤT CẢ vivid (cả KEEP lẫn DISCARD).")
        sys.exit(1)

    # --- 5. Xác thực format và rubric scores từng evaluation ---
    vong_loai_codes = {'U1', 'U2', 'U3', 'U4',
                       'C-D1', 'C-D2', 'C-D3',
                       'I-D1', 'I-D2', 'I-D3',
                       'K-D1', 'K-D2', 'K-D3'}
    score_keys = ('C1', 'C2', 'C3', 'C4', 'C5')

    for idx, ev in enumerate(evaluations):
        # 5a. Kiểm tra các trường bắt buộc chung
        if 'decision' not in ev or 'reason' not in ev or 'vivid_fragment' not in ev:
            print(f"❌ Evaluation #{idx+1} thiếu trường bắt buộc (vivid_fragment, decision, reason).")
            sys.exit(1)
        if not ev.get('reason', '').strip():
            print(f"❌ Evaluation #{idx+1} có trường 'reason' bị rỗng. Phải giải thích lý do.")
            sys.exit(1)

        # 5b. Validate KEEP: bắt buộc có scores, tổng >= 7
        if ev['decision'] == 'KEEP':
            if 'scores' not in ev:
                print(f"❌ Evaluation #{idx+1} là KEEP nhưng thiếu 'scores'. Phải chấm C1-C5 (0/1/2).")
                sys.exit(1)
            scores = ev['scores']
            for k in score_keys:
                if k not in scores or scores[k] not in (0, 1, 2):
                    print(f"❌ Evaluation #{idx+1}: điểm {k} không hợp lệ (phải là 0, 1, hoặc 2).")
                    sys.exit(1)
            total_score = sum(scores[k] for k in score_keys)
            if total_score < 7:
                print(f"❌ Evaluation #{idx+1} là KEEP nhưng tổng {total_score}/10 (cần ≥ 7). Phải DISCARD.")
                sys.exit(1)

        # 5c. Validate DISCARD: bắt buộc có disqualifier
        elif ev['decision'] == 'DISCARD':
            if 'disqualifier' not in ev:
                print(f"❌ Evaluation #{idx+1} là DISCARD nhưng thiếu 'disqualifier'.")
                sys.exit(1)
            dq = ev['disqualifier']
            if dq == 'LOW_SCORE':
                # LOW_SCORE: vivid vượt vòng loại nhưng tổng điểm rubric < 7
                if 'scores' not in ev:
                    print(f"❌ Evaluation #{idx+1} dùng LOW_SCORE nhưng thiếu 'scores'. Phải chấm C1-C5.")
                    sys.exit(1)
                scores = ev['scores']
                for k in score_keys:
                    if k not in scores or scores[k] not in (0, 1, 2):
                        print(f"❌ Evaluation #{idx+1}: điểm {k} không hợp lệ (phải là 0, 1, hoặc 2).")
                        sys.exit(1)
                total_score = sum(scores[k] for k in score_keys)
                if total_score >= 7:
                    print(f"❌ Evaluation #{idx+1} dùng LOW_SCORE nhưng tổng {total_score}/10 (≥ 7 phải KEEP).")
                    sys.exit(1)
            elif dq not in vong_loai_codes:
                print(f"❌ Evaluation #{idx+1}: disqualifier '{dq}' không hợp lệ. Dùng: {', '.join(sorted(vong_loai_codes))} hoặc LOW_SCORE.")
                sys.exit(1)

    # --- 6. Tái tạo discard records đầy đủ (tương thích apply_curation.py) ---
    new_discards = []
    for ev in evaluations:
        if ev['decision'] != 'DISCARD':
            continue

        # Tra cứu ngược vivid gốc trong batch file
        matched_chunk_index = None
        matched_vivid_type = None
        matched_parent = None
        fragment = ev['vivid_fragment'].strip()

        for chunk in batch_data.get('chunks', []):
            for vivid in chunk.get('vivids', []):
                if vivid['body'].startswith(fragment) or fragment in vivid['body']:
                    matched_chunk_index = chunk['chunk_index']
                    matched_vivid_type = vivid['vivid_type']
                    matched_parent = vivid['parent']
                    break
            if matched_chunk_index is not None:
                break

        if matched_chunk_index is None:
            print(f"⚠️ Cảnh báo: Không tìm thấy vivid khớp với fragment '{fragment}' trong batch.")
            continue

        new_discards.append({
            "chunk_index": matched_chunk_index,
            "vivid_type": matched_vivid_type,
            "parent": matched_parent,
            "body_fragment": fragment,
            "disqualifier": ev['disqualifier'],
            "reason": ev['reason']
        })

    # --- 7. Cập nhật session state ---
    state['submitted_discards'].extend(new_discards)
    state['current_batch'] = current + 1

    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"✅ Batch {current}/{total} đã được xác nhận. Ghi nhận {len(new_discards)} DISCARD(s).")

    # --- 8. Nếu còn batch tiếp theo → sao chép ra current_batch.json ---
    run_folder = os.path.dirname(session_dir)
    current_batch_path = os.path.join(run_folder, "current_batch.json")

    if state['current_batch'] <= total:
        next_batch_filename = f"batch_{state['current_batch']:02d}.json"
        next_batch_path = os.path.join(session_dir, next_batch_filename)
        with open(next_batch_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(current_batch_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"\n📋 BATCH {state['current_batch']}/{total} — Đã xuất: {current_batch_path}")
        print(f"⚠️ Dùng view_file đọc file trên → đánh giá → tạo eval_temp.json → gọi --submit-file.")
    else:
        # --- 9. Hoàn tất chuỗi → sinh discards.json, dọn file tạm ---
        discards_output_path = os.path.join(run_folder, "discards.json")
        with open(discards_output_path, 'w', encoding='utf-8') as f:
            json.dump(state['submitted_discards'], f, ensure_ascii=False, indent=2)

        # Dọn dẹp current_batch.json (file tạm không cần giữ)
        if os.path.exists(current_batch_path):
            os.remove(current_batch_path)

        print(f"\n🎉 HOÀN THÀNH TOÀN BỘ CHUỖI ĐÁNH GIÁ.")
        print(f"   Tổng DISCARD: {len(state['submitted_discards'])}")
        print(f"   File discards.json: {discards_output_path}")
        print(f"   → Bạn có thể tiếp tục Bước 2.4 (chạy apply_curation.py).")


def main():
    parser = argparse.ArgumentParser(description="Trích xuất candidates vivid / Quản lý chuỗi đánh giá batch.")
    parser.add_argument("cache_file", nargs='?', default=None, help="Đường dẫn tới file cache của sách (.md). Bắt buộc ở Extraction Mode.")
    parser.add_argument("--output", help="Đường dẫn lưu file JSON output candidates")
    parser.add_argument("--split-dir", help="Thư mục xuất các batch files để agent đánh giá chunk-by-chunk")
    parser.add_argument("--batch-size", type=int, default=15, help="Số vivids tối đa mỗi batch file (mặc định: 15)")
    # Interactive Mode arguments
    parser.add_argument("--session-dir", help="Thư mục chứa batch files (kích hoạt Interactive Mode)")
    parser.add_argument("--get-next", action="store_true", help="In nội dung batch đang chờ xử lý")
    parser.add_argument("--submit-file", help="Đường dẫn tới file JSON bảng điểm do Agent tạo")
    
    args = parser.parse_args()

    # === INTERACTIVE MODE ===
    if args.session_dir:
        session_dir = os.path.abspath(args.session_dir)
        if args.get_next:
            handle_get_next(session_dir)
        elif args.submit_file:
            handle_submit(session_dir, os.path.abspath(args.submit_file))
        else:
            print("❌ Interactive Mode yêu cầu --get-next hoặc --submit-file.")
            sys.exit(1)
        return

    # === EXTRACTION MODE (logic cũ, giữ nguyên) ===
    if not args.cache_file:
        print("❌ Extraction Mode yêu cầu cache_file.")
        sys.exit(1)
    if not args.output:
        print("❌ Extraction Mode yêu cầu --output.")
        sys.exit(1)

    # Chuyển đổi sang đường dẫn tuyệt đối
    cache_path = os.path.abspath(args.cache_file)
    output_path = os.path.abspath(args.output)

    print(f"🔍 Bắt đầu phân tích file cache: {cache_path}...")
    output_data, skipped_warnings_count, vivid_stats = parse_book_vivids(cache_path)

    # Đảm bảo thư mục đích tồn tại
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Ghi dữ liệu ra file JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # Gom chunks thành các batch files nếu có --split-dir
    batch_count = 0
    if args.split_dir:
        split_dir = os.path.abspath(args.split_dir)
        os.makedirs(split_dir, exist_ok=True)
        batch_size = args.batch_size

        # Cắt tỉa (Prune) các knowledges thừa không có vivid nào reference tới
        # Giữ nguyên insight và jtbd vì chúng là bối cảnh tổng thể cho toàn chunk
        for chunk in output_data['chunks']:
            if chunk.get('vivids'):
                referenced_parents = {v.get('parent') for v in chunk['vivids']}
                original_knowledges = chunk['context'].get('knowledges', [])
                chunk['context']['knowledges'] = [
                    k for k in original_knowledges
                    if k.get('name') in referenced_parents
                ]

        # Gom các chunks có vivid thành các batch dựa trên ngưỡng vivid tối đa
        active_chunks = [c for c in output_data['chunks'] if c.get('vivids')]
        batches = []
        current_batch = []
        current_vivid_count = 0

        for chunk in active_chunks:
            chunk_vivid_count = len(chunk['vivids'])

            # Nếu batch hiện tại đã có dữ liệu và thêm chunk này sẽ vượt ngưỡng → đóng batch
            if current_vivid_count + chunk_vivid_count > batch_size and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_vivid_count = 0

            current_batch.append(chunk)
            current_vivid_count += chunk_vivid_count

        # Batch cuối cùng
        if current_batch:
            batches.append(current_batch)

        # Ghi từng batch file kèm password ngẫu nhiên (uuid đã import ở đầu file)
        manifest_batches = []
        for batch_idx, batch_chunks in enumerate(batches, start=1):
            filename = f"batch_{batch_idx:02d}.json"
            batch_vivid_total = sum(len(c['vivids']) for c in batch_chunks)
            
            # Sinh password ngẫu nhiên 8 ký tự hex cho batch này
            batch_password = uuid.uuid4().hex[:8]
            
            batch_file_data = {
                "book_name": output_data['book_name'],
                "batch_index": batch_idx,
                "batch_password": batch_password,
                "chunks": [
                    {
                        "chunk_index": c['chunk_index'],
                        "chunk_name": c['chunk_name'],
                        "context": c['context'],
                        "vivids": c['vivids']
                    }
                    for c in batch_chunks
                ]
            }

            batch_path = os.path.join(split_dir, filename)
            with open(batch_path, 'w', encoding='utf-8') as bf:
                json.dump(batch_file_data, bf, ensure_ascii=False, indent=2)

            manifest_batches.append({
                "file": filename,
                "vivid_count": batch_vivid_total,
                "chunk_count": len(batch_chunks)
            })

        # Ghi file manifest tổng hợp (giữ backward compat, không chứa password)
        manifest = {
            "book_name": output_data['book_name'],
            "total_vivids": output_data['total_vivids'],
            "total_batches": len(manifest_batches),
            "batch_size": batch_size,
            "batches": manifest_batches
        }
        manifest_path = os.path.join(split_dir, "_manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest, mf, ensure_ascii=False, indent=2)

        # Tạo session_state.json (KHÔNG chứa password, chỉ chứa metadata quản lý)
        session_state = {
            "total_batches": len(manifest_batches),
            "current_batch": 1,
            "submitted_discards": []
        }
        state_path = os.path.join(split_dir, "session_state.json")
        with open(state_path, 'w', encoding='utf-8') as sf:
            json.dump(session_state, sf, ensure_ascii=False, indent=2)

        batch_count = len(manifest_batches)

    # In báo cáo kết quả
    print(f"✅ Trích xuất hoàn tất: {output_data['total_vivids']} vivids từ {len(output_data['chunks'])} chunks.")
    print(f"   Phân bổ: {vivid_stats['vivid_circumstance']} circumstance, {vivid_stats['vivid_insight']} insight, {vivid_stats['vivid_knowledge']} knowledge.")
    if skipped_warnings_count > 0:
        print(f"   Bỏ qua: {skipped_warnings_count} chunks (warning isolation).")
    print(f"   Output: {output_path}")
    if batch_count > 0:
        print(f"   Split: {batch_count} batch files (max {args.batch_size} vivids/batch) → {os.path.abspath(args.split_dir)}")

if __name__ == "__main__":
    main()
