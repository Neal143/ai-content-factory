# -*- coding: utf-8 -*-
"""
Tên file: backfill-topics.py
Last update: 27/05/2026 00:45 (GMT+7)
Vai trò: Script Python thực hiện backfill topics đúng cho toàn bộ các file nguyên tố GI_ atoms.
Sử dụng khi nào: Chạy một lần tại Phase 2 để sửa lỗi topics cho Good Inside atoms trong vault.
Output: Cập nhật trực tiếp trường topics trong frontmatter của toàn bộ file GI_ atoms.
Tóm tắt logic hoạt động:
  1. Đọc atomizer_context.json để lấy book_topics và chunk_topics_map.
  2. Đọc extraction_baseline.csv, áp dụng slugify_vi và quy tắc đặt tên file của atomizer.py để ánh xạ từng filename sang chunk_index tương ứng.
  3. Quét 6 thư mục con của vault/01-Atomic/ để tìm các file có prefix GI_.
  4. Đối với mỗi file GI_, tra cứu chunk_index, gộp book_topics và chunk_topics để tạo danh sách topics mới.
  5. Sửa đổi an toàn frontmatter bằng cách chỉ thay thế trường topics, bảo tồn hoàn toàn vivid data và body Markdown.
"""

# ==========================================
# NHÓM 1: CÁC THƯ VIỆN HỆ THỐNG
# ==========================================
import os
import re
import csv
import json
import sys
import unicodedata
import argparse

# Đảm bảo in tiếng Việt có dấu đúng mã hóa trên terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# NHÓM 2: HÀM SLUGIFY TIẾNG VIỆT & TÊN FILE
# ==========================================
def slugify_vi(text):
    """
    Chuyển text tiếng Việt thành slug ASCII-hyphenated.
    Sao chép nguyên bản từ atomizer.py L52-71 để đảm bảo tính nhất quán 100%.
    """
    text = text.lower()
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    text = text.replace('_', ' ')  # Underscore → space
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    slug = text.strip('-')
    return slug if slug else "untitled"

def get_expected_filename(category, raw_id, chunk_idx, acr="GI"):
    """
    Sinh filename từ baseline CSV row theo quy tắc của atomizer.py L185-230.
    """
    if category == "insight":
        slug = slugify_vi(raw_id)
        return f"{acr}_{slug}.md"
        
    elif category == "knowledge":
        slug = slugify_vi(raw_id)
        return f"{acr}_{slug}.md"
        
    elif category == "quote":
        # baseline CSV quote format: thường là 'unknown' hoặc tên speaker
        slug = slugify_vi(raw_id)
        return f"{acr}_quote-{slug}-{chunk_idx}.md"
        
    elif category == "evidence":
        # baseline CSV evidence format: thường là 'unknown' hoặc keyword
        slug = slugify_vi(raw_id)
        return f"{acr}_data-{slug}-{chunk_idx}.md"
        
    elif category == "story":
        # baseline CSV story format: protagonist-core_event (ví dụ: Đứa con út (younger son)-unknown)
        parts = raw_id.split("-", 1)
        protagonist = parts[0]
        core_event = parts[1] if len(parts) > 1 else ""
        
        if core_event and core_event != "unknown":
            slug = slugify_vi(f"{protagonist}-{core_event}")
        else:
            slug = slugify_vi(protagonist)
            
        return f"{acr}_story-{slug}-{chunk_idx}.md"
        
    return f"{acr}_unknown-{chunk_idx}.md"

# ==========================================
# NHÓM 3: LOGIC CHÍNH XỬ LÝ BACKFILL
# ==========================================
def build_filename_to_chunk_map(csv_path, acronym="GI"):
    """
    Đọc extraction_baseline.csv và tạo mapping {filename -> chunk_index}.
    """
    mapping = {}
    if not os.path.exists(csv_path):
        print(f"[ERR] Khong tim thay file baseline CSV tai: {csv_path}")
        return mapping
        
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("section") != "atom":
                continue
                
            chunk = row.get("chunk")
            category = row.get("category")
            raw_id = row.get("id")
            
            # Đồng nhất category
            if category in ("solution", "concept"):
                category = "knowledge"
                
            filename = get_expected_filename(category, raw_id, chunk, acronym)
            mapping[filename] = chunk
            
    return mapping

def backfill_topics_in_vault(vault_dir, acronym, csv_map, context_data, dry_run=False):
    """
    Quét qua các file atom trong vault, cập nhật trường topics từ context_data.
    """
    book_topics = context_data.get("book_topics", [])
    chunk_topics_map = context_data.get("chunk_topics_map", {})
    
    # 6 thư mục nguyên tố DIKW
    sub_dirs = ["Insights", "Solutions", "Concepts", "Stories", "Quotes", "Data-Points"]
    updated_count = 0
    skipped_count = 0
    
    print("\n--- BAT DAU TIEN TRINH QUET VA UPDATE VAULT ---")
    
    for sub in sub_dirs:
        target_dir = os.path.join(vault_dir, sub)
        if not os.path.exists(target_dir):
            continue
            
        for filename in os.listdir(target_dir):
            # Chỉ xử lý các file có prefix tương ứng (ví dụ: GI_)
            if not filename.startswith(acronym + "_") or not filename.endswith(".md"):
                continue
                
            filepath = os.path.join(target_dir, filename)
            
            # Tra cứu chunk_index của file từ CSV mapping hoặc trích xuất từ hậu tố tên file
            chunk_idx = csv_map.get(filename)
            if not chunk_idx:
                # Thử trích xuất từ hậu tố tên file bằng regex (áp dụng cho story, quote, data-point)
                m = re.search(r"-(\d+)\.md$", filename)
                if m:
                    chunk_idx = m.group(1)
                    
            if not chunk_idx:
                print(f"[WARN] Khong tim thay mapping chunk cho file: {filename} (Bo qua)")
                skipped_count += 1
                continue
                
            # Tính toán topics mới = book_topics + chunk_topics (deduplicated)
            chunk_topics = chunk_topics_map.get(str(chunk_idx), [])
            new_topics = list(dict.fromkeys(book_topics + chunk_topics))
            
            # Đọc nội dung file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Tách frontmatter bằng regex
            match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
            if not match:
                print(f"[ERR] Khong parse duoc frontmatter cho file: {filename}")
                continue
                
            frontmatter_str = match.group(1)
            body_str = content[match.end():]
            
            # Sửa đổi hoặc chèn trường topics vào frontmatter
            lines = frontmatter_str.split('\n')
            new_lines = []
            has_topics = False
            
            for line in lines:
                line_strip = line.strip()
                if line_strip.startswith("topics:"):
                    has_topics = True
                    # Replace bằng topics mới
                    topics_json = json.dumps(new_topics, ensure_ascii=False)
                    new_lines.append(f"topics: {topics_json}")
                else:
                    new_lines.append(line)
                    
            # Nếu chưa có topics trong frontmatter (trường hợp hiếm gặp), chèn vào dòng đầu tiên
            if not has_topics:
                topics_json = json.dumps(new_topics, ensure_ascii=False)
                new_lines.insert(1, f"topics: {topics_json}")
                
            new_frontmatter = "---\n" + "\n".join(new_lines) + "\n---\n"
            new_content = new_frontmatter + body_str
            
            # Ghi file nếu không ở chế độ dry_run
            if not dry_run:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[OK] Updated {sub}/{filename} -> Topics: {new_topics}")
            else:
                print(f"[DRY-RUN] Would update {sub}/{filename} -> Topics: {new_topics}")
                
            updated_count += 1
            
    print(f"\n[SUMMARY] Hoan thanh: Da update {updated_count} files, Bo qua {skipped_count} files.")

# ==========================================
# NHÓM 4: CLI ENTRYPOINT
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="Backfill topics đúng cho Good Inside atoms trong vault")
    parser.add_argument("--context", required=True, help="Đường dẫn đến file atomizer_context.json")
    parser.add_argument("--baseline", required=True, help="Đường dẫn đến file extraction_baseline.csv")
    parser.add_argument("--vault", required=True, help="Đường dẫn đến thư mục vault/01-Atomic")
    parser.add_argument("--prefix", default="GI", help="Acronym/Prefix của file (ví dụ: GI)")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm hiển thị kết quả, không ghi file")
    
    args = parser.parse_args()
    
    # 1. Đọc atomizer_context.json
    if not os.path.exists(args.context):
        print(f"[ERR] Khong tim thay context tai: {args.context}")
        sys.exit(1)
        
    with open(args.context, 'r', encoding='utf-8') as f:
        context_data = json.load(f)
        
    # 2. Build mapping từ baseline CSV
    csv_map = build_filename_to_chunk_map(args.baseline, args.prefix)
    print(f"[INFO] Da load map tu CSV. So luong mappings tim thay: {len(csv_map)}")
    
    # 3. Tiến hành backfill
    backfill_topics_in_vault(args.vault, args.prefix, csv_map, context_data, args.dry_run)

if __name__ == "__main__":
    main()
