# -*- coding: utf-8 -*-
"""
Tên file: apply_curation.py
Last update: 28/05/2026 21:55 (GMT+7)
Vai trò: Áp dụng quyết định loại bỏ (DISCARD) của agent vào file cache, ghi file log curation, và tự động gọi các sealing scripts tiếp theo.
Được sử dụng khi nào: Bước 2.4 của Core Skill Phase 2 (Curate Vivids).
Output:
1. File cache đã được lọc sạch (các body bị discard đổi thành [NOT_FOUND]).
2. Tệp tin log vivid_curation_log.json tại run_folder.
3. Kích hoạt tự động các file parsed_metadata.json và pipeline_report.md (chạy các sealing scripts).
Tóm tắt logic hoạt động:
1. Đọc discards.json, vivid_candidates.json và các dòng của file cache.
2. Duyệt qua từng dòng của file cache:
   - Nhận diện chunk_index qua thẻ META_CHUNK.
   - Nhận diện thẻ META vivid. Nếu dòng body ngay dưới khớp với một item trong discards.json (qua chunk_index và body_fragment), thay thế body đó bằng [NOT_FOUND].
3. Ghi đè file cache một cách an toàn (atomic write) thông qua file tạm .tmp.
4. Xây dựng curation log đầy đủ trạng thái KEEP/DISCARD cho tất cả các vivid candidates rồi xuất ra file JSON.
5. Xác định đường dẫn tuyệt đối của các sealing scripts (extract_metadata.py và generate_baseline.py) rồi gọi chúng tuần tự qua subprocess.run.
"""

import sys
import re
import json
import argparse
import os
import subprocess

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

def update_cache_file(cache_file_path, discards):
    """
    Cập nhật các body vivid bị loại bỏ thành [NOT_FOUND] trong file cache.
    Trả về danh sách các vivid body thực tế đã bị loại bỏ thành công để đối chiếu log.
    """
    if not os.path.exists(cache_file_path):
        print(f"❌ File cache không tồn tại: {cache_file_path}")
        sys.exit(1)

    with open(cache_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated_lines = []
    current_chunk_index = -1
    
    # Tập hợp các discards để theo dõi trạng thái xử lý
    discards_matched = []
    
    i = 0
    total_lines = len(lines)
    
    while i < total_lines:
        line = lines[i]
        
        # 1. Nhận dạng chunk index hiện tại
        if "META_CHUNK:" in line:
            pattern_chunk = r'\*?\*?META_CHUNK:\*?\*?\s*(.*?)(?=\n|$)'
            match_chunk = re.search(pattern_chunk, line)
            if match_chunk:
                chunk_meta = extract_pairs(match_chunk.group(1))
                current_chunk_index = int(chunk_meta.get("CHUNK_index", -1))
        
        # 2. Nhận dạng thẻ META vivid
        is_vivid_meta = False
        if "META_" in line and "content_type=vivid_" in line:
            is_vivid_meta = True
            
        updated_lines.append(line)
        
        # Nếu dòng hiện tại là thẻ META vivid và còn dòng tiếp theo
        if is_vivid_meta and i + 1 < total_lines:
            next_line = lines[i + 1]
            next_line_stripped = next_line.strip()
            
            # Chỉ xử lý nếu body hiện tại không phải [NOT_FOUND]
            if next_line_stripped and next_line_stripped != "[NOT_FOUND]":
                matched_discard = None
                
                # Tìm trong discards xem có trùng khớp chunk_index và body_fragment không
                for disc in discards:
                    chunk_idx = int(disc.get("chunk_index", -1))
                    fragment = disc.get("body_fragment", "").strip()
                    
                    if chunk_idx == current_chunk_index and fragment:
                        # Khớp fragment với body thực tế (sử dụng startswith hoặc tìm kiếm chuỗi con)
                        if next_line_stripped.startswith(fragment) or fragment in next_line_stripped:
                            matched_discard = disc
                            break
                
                if matched_discard:
                    # Thay thế dòng tiếp theo bằng [NOT_FOUND] (giữ nguyên thụt lề đầu dòng ban đầu)
                    indent = next_line[:len(next_line) - len(next_line.lstrip())]
                    updated_lines.append(f"{indent}[NOT_FOUND]\n")
                    
                    # Ghi nhận thông tin khớp
                    matched_discard["matched_original_body"] = next_line_stripped
                    discards_matched.append(matched_discard)
                    i += 2  # Nhảy qua dòng body cũ đã được thay thế
                    continue
            
        i += 1

    # Atomic write: ghi file tạm trước rồi ghi đè
    tmp_file_path = cache_file_path + ".tmp"
    try:
        with open(tmp_file_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        # Thay thế an toàn
        if os.path.exists(cache_file_path):
            os.remove(cache_file_path)
        os.rename(tmp_file_path, cache_file_path)
    except Exception as e:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
        print(f"❌ Lỗi ghi file cache: {e}")
        sys.exit(1)

    return discards_matched

def write_curation_log(log_path, candidates, discards_matched):
    """
    Tạo và ghi file log curation dựa trên danh sách candidates ban đầu và các discards thực tế.
    """
    book_name = candidates.get("book_name", "Unknown Book")
    total_evaluated = candidates.get("total_vivids", 0)
    
    # Tạo map để tra cứu nhanh các discards đã khớp
    discard_map = {}
    for dm in discards_matched:
        key = (dm.get("chunk_index"), dm.get("matched_original_body"))
        discard_map[key] = dm

    details = []
    discard_count = 0
    keep_count = 0

    for chunk in candidates.get("chunks", []):
        chunk_idx = chunk.get("chunk_index", -1)
        for vivid in chunk.get("vivids", []):
            vivid_body = vivid.get("body", "").strip()
            vivid_type = vivid.get("vivid_type", "")
            parent = vivid.get("parent", "")
            
            key = (chunk_idx, vivid_body)
            if key in discard_map:
                dm = discard_map[key]
                details.append({
                    "chunk_index": chunk_idx,
                    "type": vivid_type,
                    "parent": parent,
                    "original_text": vivid_body,
                    "disqualifier": dm.get("disqualifier", "UNKNOWN"),
                    "scores": None,
                    "total": None,
                    "verdict": "DISCARD",
                    "reason": dm.get("reason", "Discarded by curator.")
                })
                discard_count += 1
            else:
                details.append({
                    "chunk_index": chunk_idx,
                    "type": vivid_type,
                    "parent": parent,
                    "original_text": vivid_body,
                    "disqualifier": "NONE",
                    "scores": None,
                    "total": None,
                    "verdict": "KEEP",
                    "reason": "Passed all filters"
                })
                keep_count += 1

    log_data = {
        "book": book_name,
        "total_vivids_evaluated": total_evaluated,
        "kept": keep_count,
        "discarded": discard_count,
        "details": details
    }

    # Ghi file log
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return keep_count, discard_count

def run_sealing(cache_file_path, run_folder):
    """
    Gọi tuần tự các scripts extract_metadata.py và generate_baseline.py để niêm phong dữ liệu.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Tính toán đường dẫn tuyệt đối của các sealing scripts
    extractor_script = os.path.abspath(os.path.join(script_dir, '..', '..', 'book-extractor', 'scripts', 'extract_metadata.py'))
    baseline_script = os.path.abspath(os.path.join(script_dir, '..', '..', 'book-extractor', 'scripts', 'generate_baseline.py'))
    
    # Các file đích trong run folder
    parsed_metadata_json = os.path.abspath(os.path.join(run_folder, 'parsed_metadata.json'))
    pipeline_report_md = os.path.abspath(os.path.join(run_folder, 'pipeline_report.md'))
    
    print(f"🚀 Bắt đầu gọi sealing scripts...")
    
    # Chuẩn bị môi trường với UTF-8 encoding để tránh các script con bị crash Unicode trên Windows
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # 1. Chạy extract_metadata.py
    if not os.path.exists(extractor_script):
        print(f"❌ Không tìm thấy script: {extractor_script}")
        return False
        
    cmd_extract = [
        sys.executable,
        extractor_script,
        os.path.abspath(cache_file_path),
        "--output_json",
        parsed_metadata_json
    ]
    
    print(f"   [1/2] Đang chạy: python {os.path.basename(extractor_script)}...")
    res_extract = subprocess.run(cmd_extract, capture_output=True, text=True, errors='replace', env=env)
    if res_extract.returncode != 0:
        print(f"❌ Chạy extract_metadata.py thất bại! Mã thoát: {res_extract.returncode}")
        print(f"   Chi tiết lỗi:\n{res_extract.stderr}")
        return False
    else:
        print(f"   ✅ Trích xuất metadata thành công -> {os.path.basename(parsed_metadata_json)}")
        
    # 2. Chạy generate_baseline.py
    if not os.path.exists(baseline_script):
        print(f"❌ Không tìm thấy script: {baseline_script}")
        return False
        
    cmd_baseline = [
        sys.executable,
        baseline_script,
        parsed_metadata_json,
        os.path.abspath(cache_file_path),
        "--report",
        pipeline_report_md
    ]
    
    print(f"   [2/2] Đang chạy: python {os.path.basename(baseline_script)}...")
    res_baseline = subprocess.run(cmd_baseline, capture_output=True, text=True, errors='replace', env=env)
    if res_baseline.returncode != 0:
        print(f"❌ Chạy generate_baseline.py thất bại! Mã thoát: {res_baseline.returncode}")
        print(f"   Chi tiết lỗi:\n{res_baseline.stderr}")
        return False
    else:
        print(f"   ✅ Tạo báo cáo baseline thành công -> {os.path.basename(pipeline_report_md)}")
        
    return True

def main():
    parser = argparse.ArgumentParser(description="Áp dụng lọc vivid, ghi log curation và tự động chạy các sealing scripts.")
    parser.add_argument("--discards", required=True, help="Đường dẫn tới file JSON chứa danh sách vivid bị loại bỏ")
    parser.add_argument("--candidates", required=True, help="Đường dẫn tới file JSON candidates vivid ban đầu")
    parser.add_argument("--cache_file", required=True, help="Đường dẫn tới file cache của sách (.md)")
    parser.add_argument("--run_folder", required=True, help="Đường dẫn tới thư mục lưu trữ của lượt chạy hiện tại (run folder)")

    args = parser.parse_args()

    # Đường dẫn tuyệt đối
    discards_path = os.path.abspath(args.discards)
    candidates_path = os.path.abspath(args.candidates)
    cache_path = os.path.abspath(args.cache_file)
    run_dir = os.path.abspath(args.run_folder)

    # 1. Kiểm tra đầu vào bắt buộc
    if not os.path.exists(discards_path):
        print(f"❌ File discards không tồn tại: {discards_path}")
        sys.exit(1)
        
    if not os.path.exists(candidates_path):
        print(f"❌ File candidates không tồn tại: {candidates_path}")
        print("   Vui lòng chạy extract_vivids.py trước.")
        sys.exit(1)

    # 2. Đọc dữ liệu JSON
    try:
        with open(discards_path, 'r', encoding='utf-8') as f:
            discards = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file discards.json: {e}")
        sys.exit(1)
        
    if not isinstance(discards, list):
        print("❌ Định dạng discards.json không hợp lệ, bắt buộc là một danh sách JSON (array).")
        sys.exit(1)

    try:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file candidates.json: {e}")
        sys.exit(1)

    print(f"🧹 Đang áp dụng {len(discards)} quyết định loại bỏ vào file cache...")
    discards_matched = update_cache_file(cache_path, discards)
    
    # Cảnh báo nếu có discards không khớp được trong file cache
    if len(discards_matched) < len(discards):
        unmatched_count = len(discards) - len(discards_matched)
        print(f"⚠️ Cảnh báo: Có {unmatched_count} quyết định discard không thể khớp với vivid nào trong file cache!")
        
        # Chỉ ra các discard không khớp
        matched_fragments = [d.get("body_fragment") for d in discards_matched]
        for d in discards:
            frag = d.get("body_fragment")
            if frag not in matched_fragments:
                print(f"   - Không khớp: Chunk {d.get('chunk_index')} | fragment: '{frag}'")

    # 3. Ghi file log curation
    log_path = os.path.join(run_dir, "vivid_curation_log.json")
    print(f"📝 Đang tổng hợp kết quả curation log...")
    kept, discarded = write_curation_log(log_path, candidates, discards_matched)

    # 4. Kích hoạt các sealing scripts
    sealing_success = run_sealing(cache_path, run_dir)

    # 5. In báo cáo tổng thể
    print("\n📊 BÁO CÁO KẾT QUẢ CURATION:")
    print(f"   Tổng số vivid đánh giá: {candidates.get('total_vivids', 0)}")
    print(f"   Giữ lại (KEEP): {kept}")
    print(f"   Loại bỏ (DISCARD): {discarded}")
    print(f"✅ Đã cập nhật file cache: {cache_path}")
    print(f"✅ Đã ghi curation log: {log_path}")
    
    if sealing_success:
        print("✅ Niêm phong dữ liệu hoàn tất thành công (Sealing Completed).")
        sys.exit(0)
    else:
        print("❌ Quá trình niêm phong dữ liệu (Sealing) gặp lỗi. Vui lòng kiểm tra log lỗi phía trên.")
        sys.exit(1)

if __name__ == "__main__":
    main()
