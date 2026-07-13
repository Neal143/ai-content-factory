import os
import re
import sys
import json
import argparse

"""
patch-semantics.py
Last update: 10/07/2026 (GMT+7)
Vai tro: Chot chan ky thuat (Poka-Yoke) cho moi thao tac ghi va sua supports_insight / supports_knowledge.
Khi nao su dung: Goi tu cac skill nhu atom-linker (add) va atom-dedup (redirect).
Output: Ghi vao file .md hoac tra ve loi.
Tom tat logic:
- Mode add: Kiem tra Audience Exact Match, Cycle Check, Type Hierarchy Check. Neu pass thi ghi file.
- Mode redirect: Tim va thay the target trong mang supports_* cua tat ca file.
"""

DAG_PARENT_MAP = {
    "solution": ["insight"],
    "concept": ["insight"],
    "story": ["solution", "concept"],
    "quote": ["solution", "concept"],
    "data_point": ["solution", "concept"]
}

def load_index(index_path):
    if not os.path.exists(index_path):
        print(f"[ERR] Không tìm thấy index tại {index_path}")
        sys.exit(1)
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_basename(path):
    return os.path.splitext(os.path.basename(path))[0]

def add_link_regex(file_path, link_type, target_basename):
    if not os.path.exists(file_path):
        print(f"[ERR] Không tìm thấy file {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.search(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not match:
        print(f"[ERR] Không tìm thấy frontmatter trong {file_path}")
        return False
        
    frontmatter = match.group(1)
    key = f"supports_{link_type}"
    new_link = f"  - \"[[{target_basename}]]\""
    
    if f"{key}:" in frontmatter:
        # Array exists, append to it
        pattern = re.compile(r'^' + key + r':.*?(\n[^\s].*|\Z)', re.MULTILINE | re.DOTALL)
        
        def repl(m):
            block = m.group(0)
            if m.group(1):
                return block[:-len(m.group(1))] + "\n" + new_link + m.group(1)
            else:
                return block + "\n" + new_link
        
        new_frontmatter = pattern.sub(repl, frontmatter)
    else:
        # Add key and array
        new_frontmatter = frontmatter + f"\n{key}:\n{new_link}"
        
    new_content = content.replace(frontmatter, new_frontmatter, 1)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def redirect_link_regex(file_path, old_target_basename, new_target_basename):
    if not os.path.exists(file_path):
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.search(r'^---\r?\n(.*?)\r?\n---', content, re.DOTALL)
    if not match:
        return False
        
    frontmatter = match.group(1)
    if old_target_basename not in frontmatter:
        return False
        
    new_frontmatter = frontmatter.replace(f"[[{old_target_basename}]]", f"[[{new_target_basename}]]")
    if new_frontmatter != frontmatter:
        new_content = content.replace(frontmatter, new_frontmatter, 1)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def check_cycle(index_data, target_path, source_path):
    edges_i = index_data.get('edges', {}).get('supports_insight', {})
    edges_k = index_data.get('edges', {}).get('supports_knowledge', {})
    
    visited = set()
    queue = [target_path]
    
    while queue:
        curr = queue.pop(0)
        if curr == source_path:
            return True
        if curr in visited:
            continue
        visited.add(curr)
        
        parents = edges_i.get(curr, []) + edges_k.get(curr, [])
        queue.extend(parents)
        
    return False

def cmd_add(args):
    index_data = load_index(args.index)
    nodes = index_data.get('nodes', {})
    
    source = nodes.get(args.source)
    target = nodes.get(args.target)
    
    if not source:
        print(f"[REJECT] Source {args.source} không có trong index")
        sys.exit(1)
    if not target:
        print(f"[REJECT] Target {args.target} không có trong index")
        sys.exit(1)
        
    # 1. Audience Exact Match
    src_aud = source.get('resolved_audience')
    tgt_aud = target.get('resolved_audience')
    
    if src_aud == "CONFLICT" or tgt_aud == "CONFLICT":
        print("[REJECT] Source hoặc Target có CONFLICT audience")
        sys.exit(1)
        
    if src_aud and tgt_aud:
        if src_aud.get('id') != tgt_aud.get('id'):
            print(f"[REJECT] Audience Mismatch: Source ({src_aud.get('id')}) != Target ({tgt_aud.get('id')})")
            sys.exit(1)
    elif src_aud or tgt_aud:
        print("[REJECT] Một bên có Audience, một bên không (mismatch)")
        sys.exit(1)
        
    # 2. Type Hierarchy Check
    src_type = source.get('type')
    tgt_type = target.get('type')
    allowed = DAG_PARENT_MAP.get(src_type, [])
    if tgt_type not in allowed:
        print(f"[REJECT] Type Invalid: {src_type} không thể trỏ tới {tgt_type}")
        sys.exit(1)
        
    # 3. DAG Cycle Check
    if check_cycle(index_data, args.target, args.source):
        print(f"[REJECT] DAG Cycle detected: Trỏ từ {args.source} tới {args.target} sẽ tạo vòng lặp")
        sys.exit(1)
        
    # All checks passed, patch file
    target_basename = get_basename(args.target)
    if add_link_regex(args.source, args.link_type, target_basename):
        print(f"[SUCCESS] Đã thêm liên kết vào {args.source}")
    else:
        print("[ERR] Lỗi ghi file")
        sys.exit(1)

def cmd_redirect(args):
    old_basename = get_basename(args.old_target)
    new_basename = get_basename(args.new_target)
    
    vault_dir = "vault/01-Atomic"
    updated_files = []
    
    for root, dirs, files in os.walk(vault_dir):
        for file in files:
            if not file.endswith('.md'):
                continue
            file_path = os.path.join(root, file)
            # normalize path separator for regex
            file_path = file_path.replace("\\", "/")
            if redirect_link_regex(file_path, old_basename, new_basename):
                updated_files.append(file_path)
                
    print(f"[SUCCESS] Đã chuyển hướng {len(updated_files)} file trỏ từ {old_basename} sang {new_basename}")
    for f in updated_files:
        print(f" - {f}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Poka-Yoke Guard for Semantic Links")
    parser.add_argument('--action', choices=['add', 'redirect'], required=True)
    
    # Add mode
    parser.add_argument('--source', help="Source atom path (for add)")
    parser.add_argument('--target', help="Target atom path (for add)")
    parser.add_argument('--link-type', choices=['insight', 'knowledge'], help="supports_ type (for add)")
    
    # Redirect mode
    parser.add_argument('--old-target', help="Old target atom path (for redirect)")
    parser.add_argument('--new-target', help="New target atom path (for redirect)")
    
    parser.add_argument('--index', default=".agents/assets/vault_index.json", help="Path to vault_index.json")
    
    args = parser.parse_args()
    
    if args.action == 'add':
        if not args.source or not args.target or not args.link_type:
            print("[ERR] --action add yêu cầu --source, --target, và --link-type")
            sys.exit(1)
        cmd_add(args)
    elif args.action == 'redirect':
        if not args.old_target or not args.new_target:
            print("[ERR] --action redirect yêu cầu --old-target và --new-target")
            sys.exit(1)
        cmd_redirect(args)
