"""
TÊN SCRIPT: clean_audiences.py
VAI TRÒ: Script ngắn hạn dọn dẹp YAML frontmatter bị corrupt trong Audience files.
KHI NÀO SỬ DỤNG: Chạy 1 lần trước khi re-atomize để khôi phục khả năng parse YAML.
OUTPUT: Audience files với frontmatter sạch (xóa vivid_circumstances + dòng rác 🔥).

TÓM TẮT LOGIC:
  1. Duyệt tất cả file .md trong thư mục Audiences
  2. Tách frontmatter (giữa 2 dấu ---)
  3. Trong vùng frontmatter: xóa key vivid_circumstances + dòng rác * 🔥
  4. Ghi lại file
  5. Xóa file .tmp tồn đọng
"""

import os
import re
import sys

def clean_audience_file(filepath):
    """Dọn dẹp 1 file Audience bị corrupt YAML."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Normalize CRLF → LF
    content = content.replace('\r\n', '\n')
    
    # Tách frontmatter và body
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return False, "Không tìm thấy frontmatter"
    
    fm_text = fm_match.group(1)
    body = content[fm_match.end():]
    original_fm = fm_text
    
    # Xóa toàn bộ key vivid_circumstances và giá trị kéo dài nhiều dòng
    # Pattern: bắt đầu bằng vivid_circumstances: rồi mọi thứ cho đến key tiếp theo
    fm_text = re.sub(
        r'^vivid_circumstances:.*?(?=^\S|\Z)',
        '',
        fm_text,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Xóa dòng rác * 🔥 ... nằm ngoài key YAML hợp lệ
    fm_text = re.sub(r'^\*\s*🔥.*$\n?', '', fm_text, flags=re.MULTILINE)
    
    # Xóa dòng rác - 🔥 ... nằm ngoài key hợp lệ
    fm_text = re.sub(r'^-\s*🔥.*$\n?', '', fm_text, flags=re.MULTILINE)
    
    # Xóa dòng trống thừa liên tiếp trong frontmatter
    fm_text = re.sub(r'\n{3,}', '\n\n', fm_text)
    fm_text = fm_text.strip()
    
    if fm_text == original_fm.strip():
        return False, "Không cần sửa"
    
    # Ráp lại và ghi file
    new_content = f'---\n{fm_text}\n---{body}'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, "Đã dọn dẹp"


def main():
    if len(sys.argv) < 2:
        print("Usage: python clean_audiences.py <audiences_dir>")
        sys.exit(1)
    
    audiences_dir = sys.argv[1]
    if not os.path.isdir(audiences_dir):
        print(f"Error: Thư mục không tồn tại: {audiences_dir}")
        sys.exit(1)
    
    cleaned = 0
    skipped = 0
    tmp_removed = 0
    
    for filename in sorted(os.listdir(audiences_dir)):
        filepath = os.path.join(audiences_dir, filename)
        
        # Xóa file .tmp tồn đọng
        if filename.endswith('.tmp'):
            os.remove(filepath)
            tmp_removed += 1
            print(f"  🗑️ Xóa .tmp: {filename}")
            continue
        
        # Chỉ xử lý file .md (bỏ qua .gitkeep, _audience_index.yaml, etc.)
        if not filename.endswith('.md'):
            continue
        
        ok, msg = clean_audience_file(filepath)
        if ok:
            cleaned += 1
            print(f"  ✅ {filename}: {msg}")
        else:
            skipped += 1
    
    print(f"\nKết quả: {cleaned} file đã dọn, {skipped} file không cần sửa, {tmp_removed} file .tmp đã xóa")


if __name__ == "__main__":
    main()
