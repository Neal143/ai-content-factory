"""
TÊN SCRIPT: patch_source_metadata.py
LAST UPDATE: 03/06/2026 (GMT+7)
VAI TRÒ: Khắc dấu (Patch) metadata toàn vẹn (source_id, topic_ids, audience_filename) vào file Markdown gốc.
OUTPUT: File Markdown nguồn được ghi đè metadata an toàn bằng atomic write.
TÓM TẮT LOGIC:
  1. Tự sinh source_id chuẩn từ book_name thông qua hàm slugify_vi y hệt atomizer.
  2. Tạo bộ từ điển (Dictionary Mapping) ánh xạ topic và audience cho từng cấp độ Sách & Chunk để chống râu ông nọ cắm cằm bà kia.
  3. Ghi đè vào các thẻ RESOLVED_BOOK_META và RESOLVED_CHUNK_META.
"""

import os
import re
import json
import yaml
import argparse
import unicodedata
import sys

sys.stdout.reconfigure(encoding='utf-8')

def slugify_vi(text):
    text = text.lower()
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    text = text.replace('_', ' ')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    slug = text.strip('-')
    return slug if slug else "untitled"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-folder', required=True)
    args = parser.parse_args()
    
    run_folder = args.run_folder
    
    # Đọc blackboard
    bb_path = os.path.join(run_folder, "00-blackboard.yaml")
    with open(bb_path, 'r', encoding='utf-8') as f:
        bb = yaml.safe_load(f)
    
    cache_file = bb.get("cache_file")
    if not cache_file or not os.path.exists(cache_file):
        print(f"File {cache_file} khong ton tai.")
        return

    # Hàm hỗ trợ tìm kiếm file trong cả thư mục gốc và thư mục con (hỗ trợ kiến trúc session mới)
    def find_file(root_dir, filename):
        for dirpath, _, filenames in os.walk(root_dir):
            if filename in filenames:
                return os.path.join(dirpath, filename)
        return None

    # Khởi tạo từ điển
    book_topics = []
    chunk_topic_map = {}
    
    # Đọc resolved_topics.json (Định dạng: Dict of Lists)
    topics_path = find_file(run_folder, "resolved_topics.json")
    if topics_path:
        with open(topics_path, 'r', encoding='utf-8') as f:
            topics_data = json.load(f)
            book_topics = topics_data.get("book", [])
            for key, t_ids in topics_data.items():
                if key != "book" and key.isdigit():
                    chunk_topic_map[int(key)] = t_ids

    book_audience = ""
    chunk_audience_map = {}
    
    # Đọc audience_decision_map.json (Định dạng: List of Dicts)
    aud_path = find_file(run_folder, "audience_decision_map.json")
    if aud_path:
        with open(aud_path, 'r', encoding='utf-8') as f:
            aud_data = json.load(f)
            for item in aud_data:
                if item.get("scope") == "book":
                    book_audience = item.get("audience_filename", "")
                else:
                    ci = item.get("chunk_index")
                    if ci is not None:
                        chunk_audience_map[ci] = item.get("audience_filename", "")

    # Đọc file markdown
    with open(cache_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Xử lý cấp Sách
    book_match = re.search(r'META_BOOK:.*?book_name=(.*?)\s*\|', content)
    if not book_match:
        print("Khong tim thay META_BOOK.")
        return
    
    book_name = book_match.group(1).strip()
    source_id = slugify_vi(book_name)
    
    # Chèn RESOLVED_BOOK_META
    book_meta_str = f"RESOLVED_BOOK_META: source_id=[{source_id}] | topic_ids={json.dumps(book_topics, ensure_ascii=False)} | audience_filename={book_audience}"
    
    # Xóa TẤT CẢ các dòng RESOLVED_BOOK_META cũ ở bất kỳ đâu (trước hay sau)
    content = re.sub(r'^RESOLVED_BOOK_META:.*?(?:\r?\n|$)', '', content, flags=re.MULTILINE)
    
    # Chèn mới ngay dưới META_BOOK
    content = re.sub(r'(^META_BOOK:.*?)(?=\r?\n|$)', r'\1\n' + book_meta_str, content, flags=re.MULTILINE)

    # Xử lý cấp Chunk
    def chunk_replacer(match):
        meta_chunk_line = match.group(0)
        idx_match = re.search(r'CHUNK_index=(\d+)', meta_chunk_line)
        if idx_match:
            idx = int(idx_match.group(1))
            # Hợp nhất topic của Sách và topic riêng của Chunk, loại bỏ trùng lặp
            t_ids = list(set(book_topics + chunk_topic_map.get(idx, [])))
            a_name = chunk_audience_map.get(idx, "")
            resolved_line = f"RESOLVED_CHUNK_META: source_id=[{source_id}] | topic_ids={json.dumps(t_ids, ensure_ascii=False)} | audience_filename={a_name}"
            return meta_chunk_line + "\n" + resolved_line
        return meta_chunk_line

    # Xóa dòng RESOLVED_CHUNK_META cũ
    content = re.sub(r'\nRESOLVED_CHUNK_META:.*?(?=\n|$)', '', content)
    # Chèn mới
    content = re.sub(r'META_CHUNK:.*?CHUNK_index=\d+.*', chunk_replacer, content)

    # Ghi Atomic
    tmp_file = cache_file + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_file, cache_file)
    print(f"Da dong dau metadata thanh cong vao {cache_file}")

if __name__ == "__main__":
    main()
