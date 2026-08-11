import re, os, sys, argparse

def format_cache_content(content):
    
    # 1. OVERVIEW HEADING
    # GI: "### 1. TẦNG 1: TỔNG QUAN CUỐN SÁCH"
    # BTRB: "#### [1] TẦNG 1: TỔNG QUAN CUỐN SÁCH"
    # WBC: "**TẦNG 1: TỔNG QUAN CUỐN SÁCH**"
    content = re.sub(
        r'^#{1,4}\s*(?:\[?\d+\]?\.?\s*)?(?:TẦNG 1:\s*)?TỔNG QUAN CUỐN SÁCH\s*$',
        '## TỔNG QUAN CUỐN SÁCH ^book-overview',
        content, count=1, flags=re.MULTILINE
    )
    content = re.sub(
        r'^\*\*(?:TẦNG 1:\s*)?TỔNG QUAN CUỐN SÁCH\*\*\s*$',
        '## TỔNG QUAN CUỐN SÁCH ^book-overview',
        content, count=1, flags=re.MULTILINE
    )
    
    # 2. XÓA TOC HEADING (giữ nội dung bên dưới)
    # GI: "### 3. TẦNG 2: MỤC LỤC CONTENT CHUNK (TOC)"
    # BTRB: "#### [2] MỤC LỤC CONTENT CHUNK (TOC)"
    # WBC: không có TOC heading → regex không match → an toàn
    content = re.sub(
        r'^#{1,4}\s*(?:\[?\d+\]?\.?\s*)?(?:TẦNG 2:\s*)?MỤC LỤC.*$',
        '',
        content, count=1, flags=re.MULTILINE
    )
    
    # 3. XÓA SEPARATOR --- giữa overview và chunks (GI dòng 36)
    # Chỉ xóa --- nằm TRƯỚC <!-- HEADER_END --> hoặc trước ## Chunk
    # Dùng cách an toàn: tìm vị trí HEADER_END hoặc Chunk đầu, xóa --- trước đó
    content = re.sub(
        r'\n---\n(\s*\n)*(?=<!--\s*HEADER_END|##\s+Chunk)',
        '\n\n',
        content, count=1
    )
    
    # 4. ĐẢM BẢO <!-- HEADER_END -->
    if '<!-- HEADER_END -->' not in content:
        # Chèn trước ## Chunk đầu tiên
        content = re.sub(
            r'(^|\n)(## Chunk )',
            r'\1<!-- HEADER_END -->\n\n\2',
            content, count=1
        )
    
    return content

def format_cache(cache_file):
    with open(cache_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    content = format_cache_content(content)
    
    tmp = cache_file + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, cache_file)
    print(f"Formatted: {cache_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-file", required=True)
    args = parser.parse_args()
    format_cache(args.cache_file)
