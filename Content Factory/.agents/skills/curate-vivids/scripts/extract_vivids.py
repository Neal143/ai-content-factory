# -*- coding: utf-8 -*-
"""
Tên file: extract_vivids.py
Last update: 28/05/2026 21:50 (GMT+7)
Vai trò: Trích xuất các candidates vivid hoạt động (active) từ file cache của sách kèm theo đầy đủ ngữ cảnh của chunk (JTBD, insight cha, knowledges cha).
Được sử dụng khi nào: Bước 2.2 của Core Skill Phase 2 (Curate Vivids).
Output: Một file JSON chứa cấu trúc các candidates vivid và ngữ cảnh tương ứng để agent đánh giá.
Tóm tắt logic hoạt động:
1. Đọc file cache sách bằng UTF-8.
2. Quét book metadata để lấy tên sách.
3. Tách nội dung thành các chunk nhỏ qua thẻ <data_chunk>.
4. Bỏ qua các chunk có cờ cảnh báo '> [!warning]'.
5. Parse từng chunk bằng regex split tương tự extract_metadata.py, phân loại thẻ META để trích xuất JTBD, insight cha, knowledges cha và các active vivids (bỏ qua [NOT_FOUND]).
6. Tổng hợp dữ liệu và ghi ra file JSON kết quả.
"""

import sys
import re
import json
import argparse
import os

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

def main():
    parser = argparse.ArgumentParser(description="Trích xuất candidates vivid và ngữ cảnh từ file cache markdown.")
    parser.add_argument("cache_file", help="Đường dẫn tới file cache của sách (.md)")
    parser.add_argument("--output", required=True, help="Đường dẫn lưu file JSON output candidates")
    
    args = parser.parse_args()

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

    # In báo cáo kết quả
    print(f"✅ Trích xuất hoàn tất: {output_data['total_vivids']} vivids từ {len(output_data['chunks'])} chunks.")
    print(f"   Phân bổ: {vivid_stats['vivid_circumstance']} circumstance, {vivid_stats['vivid_insight']} insight, {vivid_stats['vivid_knowledge']} knowledge.")
    if skipped_warnings_count > 0:
        print(f"   Bỏ qua: {skipped_warnings_count} chunks (warning isolation).")
    print(f"   Output: {output_path}")

if __name__ == "__main__":
    main()
