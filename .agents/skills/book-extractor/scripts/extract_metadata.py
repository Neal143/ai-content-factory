import sys
import re
import json
import argparse
import os

def parse_book_file(content):
    metadata = {
        "book": {},
        "chunks": []
    }
    
    def extract_pairs(target_dict, match_group):
        pairs = match_group.split('|')
        for pair in pairs:
            if '=' in pair:
                k, v = pair.split('=', 1)
                target_dict[k.strip()] = v.strip()

    # 1. Quét Book Meta
    pattern_book = r'\*?\*?META_BOOK:\*?\*?\s*(.*?)(?=\n|$)'
    match_book = re.search(pattern_book, content)
    if match_book:
        extract_pairs(metadata["book"], match_book.group(1))

    # 2. Tách các data chunks
    chunk_pattern = r'<data_chunk>([\s\S]*?)</data_chunk>'
    chunks = re.finditer(chunk_pattern, content)
    
    skipped_warnings = []

    for chunk_match in chunks:
        chunk_content = chunk_match.group(1)

        # Warning Isolation — skip chunk có cờ warning
        if '> [!warning]' in chunk_content:
            chunk_match = re.search(r'CHUNK_index=(\d+)', chunk_content)
            b_idx = chunk_match.group(1) if chunk_match else "?"
            skipped_warnings.append(b_idx)
            print(f"⚠️ Cách ly Chunk {b_idx}: phát hiện cờ > [!warning], skip.")
            continue

        chunk_data = {
            "chunk": {},
            "audience": {},
            "items": []
        }
        
        # Lấy META_CHUNK
        pattern_chunk = r'\*?\*?META_CHUNK:\*?\*?\s*(.*?)(?=\n|$)'
        match_chunk = re.search(pattern_chunk, chunk_content)
        if match_chunk:
            extract_pairs(chunk_data["chunk"], match_chunk.group(1))
            
        # Lấy META_CHUNK_AUDIENCE — dùng finditer để duyệt tất cả thẻ,
        # nhưng chỉ lấy metadata audience (chunk_audience/book_audience) cho chunk_data.
        # Thẻ vivid_circumstance sẽ được bảo tồn cho bước split bên dưới.
        pattern_audience = r'\*?\*?META_CHUNK_AUDIENCE:\*?\*?\s*(.*?)(?=\n|$)'
        for aud_match in re.finditer(pattern_audience, chunk_content):
            aud_str = aud_match.group(1).strip()
            if aud_str == "[NO_JTBD_FOUND]":
                chunk_data["audience"]["jtbd"] = aud_str
            elif "chunk_audience=" in aud_str or "book_audience=" in aud_str:
                extract_pairs(chunk_data["audience"], aud_str)
                
        # Làm sạch thẻ meta chunk ở header (CHỈ xóa META_CHUNK, KHÔNG xóa META_CHUNK_AUDIENCE)
        clean_chunk = chunk_content
        clean_chunk = re.sub(pattern_chunk, '', clean_chunk)
        clean_chunk = re.sub(r'^\s*SKIPPED_BY_AI\s*', '', clean_chunk, flags=re.MULTILINE)
        
        # Cắt items — thêm CHUNK_AUDIENCE để vivid_circumstance thành item riêng
        pattern_meta = r'\*?\*?META_(?:INSIGHT|KNOWLEDGE|EVIDENCE|STORY|QUOTE|CHUNK_AUDIENCE):\*?\*?\s*(.*?)(?=\n|$)'
        parts = re.split(pattern_meta, clean_chunk)
        
        # parts[0] là text trước thẻ META đầu tiên
        intro_text = parts[0].strip()
        if intro_text:
            chunk_data["items"].append({
                "meta": {},
                "body_text": intro_text
            })
            
        for i in range(1, len(parts), 2):
            meta_str = parts[i]
            text_body = parts[i+1].strip() if i+1 < len(parts) else ""
            
            # Clean trailing structural headers that bleed into the body text
            text_body = re.sub(r'\n*^\s*[-*]*\s*[①②③④⑤].*$', '', text_body, flags=re.MULTILINE | re.DOTALL)
            text_body = re.sub(r'\n+\s*[-*]*\s*\*{0,2}🔥.*$', '', text_body, flags=re.MULTILINE | re.DOTALL)
            text_body = text_body.strip()
            
            item_meta = {}
            extract_pairs(item_meta, meta_str)
            
            # Sentinel filter: bỏ item có body là [NOT_FOUND] hoặc [NO_JTBD_FOUND]
            # Miner viết [NOT_FOUND] khi section không có dữ liệu thực
            # Item không có nội dung → giữ lại chỉ gây rác hạ nguồn
            if text_body in ('[NOT_FOUND]', '[NO_JTBD_FOUND]'):
                continue
            
            chunk_data["items"].append({
                "meta": item_meta,
                "body_text": text_body
            })
            
        metadata["chunks"].append(chunk_data)
        
    metadata["skipped_warnings"] = skipped_warnings
    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strict Metadata Regex Extraction Tool (Chunk-Aware)")
    parser.add_argument('input_file', help='Đường dẫn tới file Markdown thô')
    parser.add_argument('--output_json', help='Đường dẫn xuất file JSON Metadata')
    # Loại bỏ --output_clean vì giờ text đã được bind vĩnh viễn với item
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File không tồn tại: {args.input_file}")
        sys.exit(1)
        
    with open(args.input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    meta = parse_book_file(content)
    
    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
            
    print(f"✅ Hoàn tất bóc tách Regex! Tách thành công {len(meta['chunks'])} chunks.")
    if meta.get('skipped_warnings'):
        print(f"⚠️ Cách ly {len(meta['skipped_warnings'])} chunk(s) do cờ warning: Chunk {', '.join(meta['skipped_warnings'])}")

