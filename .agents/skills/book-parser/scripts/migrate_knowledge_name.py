import sys
import re
import os

def migrate_file(filepath):
    """Inject knowledge_name từ ② headers vào META_KNOWLEDGE cho file cache cũ.
    
    Chỉ chạy 1 lần duy nhất cho các sách phân rã bằng prompt v3/v4 cũ chưa có field này.
    """
    if not os.path.exists(filepath):
        print(f"Error: {filepath} không tồn tại")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Tách từng <data_chunk>
    chunks = re.findall(r'(<data_chunk>.*?</data_chunk>)', content, re.DOTALL)
    if not chunks:
        print("Không tìm thấy <data_chunk> nào.")
        return

    modified = False

    for chunk_raw in chunks:
        chunk_new = chunk_raw

        # 1. Quét tìm tất cả các knowledge_name từ header ②
        # Regex match: ②-1. framework: knowledge_name
        header_names = []
        for line in chunk_raw.splitlines():
            line = line.strip()
            # Bắt dạng: *   **②-1. type: knowledge_name**  (cho phép prefix markdown)
            match = re.search(r'[②③][\-—]?\s*\d+[\.\s]+[^:]+:\s*(.+)', line)
            if match:
                kn = match.group(1).strip()
                # strip bold
                kn = kn.strip('*').strip()
                if kn:
                    header_names.append(kn)

        if not header_names:
            continue

        # 2. Tìm tất cả META_KNOWLEDGE non-vivid
        # Regex tìm dòng META_KNOWLEDGE không có chữ vivid
        mk_pattern = r'(\*?\*?META_KNOWLEDGE:\*?\*?\s*.*?)(?=\n|$)'
        mk_matches = list(re.finditer(mk_pattern, chunk_new))
        
        # Chỉ lấy cái non-vivid
        non_vivid_matches = []
        for match in mk_matches:
            if 'vivid' not in match.group(1):
                non_vivid_matches.append(match)

        # 3. Inject theo thứ tự (giả định 1 header tương ứng 1 META_KNOWLEDGE)
        for i, match in enumerate(non_vivid_matches):
            if i >= len(header_names):
                break # Không đủ header map

            old_str = match.group(1)
            # Kiểm tra xem đã có knowledge_name chưa
            if 'knowledge_name=' in old_str:
                continue

            name_to_inject = header_names[i]
            
            # Chèn sau knowledge_type=xxx |
            new_str = re.sub(
                r'(knowledge_type=[^|]+)\|', 
                rf'\1| knowledge_name={name_to_inject} |', 
                old_str, 
                count=1
            )
            
            if new_str != old_str:
                chunk_new = chunk_new.replace(old_str, new_str, 1)

        # Cập nhật content
        if chunk_new != chunk_raw:
            content = content.replace(chunk_raw, chunk_new)
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Đã chèn knowledge_name cho {filepath}")
        print("Tiếp theo: Hãy chạy normalizer.py trên file này để làm sạch.")
    else:
        print(f"⏭️ Không có gì thay đổi trong {filepath} (file đã có knowledge_name hoặc không tìm thấy header hợp lệ).")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Sử dụng: python migrate_knowledge_name.py <path_to_cache_md>")
        sys.exit(1)
    
    migrate_file(sys.argv[1])
