"""
Tên file: cascade_merge.py
Last update: 14/07/2026 15:46 (GMT+7)
Vai trò: Xử lý các side-effect (cập nhật file YAML và file Markdown Atom) khi merge topic hoặc audience.
Được sử dụng khi: Skill vc-topic-dedup hoặc vc-audience-curator ra quyết định merge và được submit.
Output: Cập nhật topic_map.yaml hoặc _audience_index.yaml và cập nhật frontmatter các file Atoms liên quan.
Tóm tắt logic hoạt động: Chạy cascade merge cho Topics (cộng dồn insight, đổi reference) hoặc Audiences (reparenting, redirect).
"""

import os
import sys
import re
import argparse
import json
import codecs
import yaml

def _read_md_file(filepath):
    try:
        with codecs.open(filepath, 'r', encoding='utf-8-sig') as f:
            return f.read()
    except Exception as e:
        print(json.dumps({"error": f"Loi doc file {filepath}: {e}"}))
        return None

def _write_md_file(filepath, content):
    try:
        with codecs.open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(content)
        return True
    except Exception as e:
        print(json.dumps({"error": f"Loi ghi file {filepath}: {e}"}))
        return False

def merge_topic(args):
    # Doc topic map
    if not os.path.exists(args.topic_map):
        print(json.dumps({"error": f"File khong ton tai: {args.topic_map}"}))
        sys.exit(1)
        
    with open(args.topic_map, 'r', encoding='utf-8') as f:
        topic_map = yaml.safe_load(f) or {}
        
    # Tim survivor va loser
    topics = topic_map.get('topics', [])
    loser_entry = None
    survivor_entry = None
    
    for t in topics:
        if t.get('id') == args.loser_id:
            loser_entry = t
        if t.get('id') == args.survivor_id:
            survivor_entry = t
            
    if not loser_entry or not survivor_entry:
        print(json.dumps({"error": "Khong tim thay loser_id hoac survivor_id trong topic_map"}))
        sys.exit(1)
        
    # Poka-Yoke: Cung pillar
    loser_prefix = args.loser_id.split('_')[0]
    survivor_prefix = args.survivor_id.split('_')[0]
    if loser_prefix != survivor_prefix:
        print(json.dumps({"error": "Khong the merge cross-pillar (khac prefix)"}))
        sys.exit(1)
        
    # Cong don belongs_to_audience va aliases
    survivor_audiences = set(survivor_entry.get('belongs_to_audience', []))
    survivor_audiences.update(loser_entry.get('belongs_to_audience', []))
    survivor_entry['belongs_to_audience'] = sorted(list(survivor_audiences))
    
    survivor_aliases = survivor_entry.get('aliases', [])
    if args.loser_id not in survivor_aliases:
        survivor_aliases.insert(0, args.loser_id)
    loser_label = loser_entry.get('label', '')
    if loser_label and loser_label not in survivor_aliases:
        survivor_aliases.insert(0, loser_label)
        
    # Gioi han FIFO max 5 aliases
    survivor_entry['aliases'] = survivor_aliases[:5]
    
    # Xoa loser entry
    topics.remove(loser_entry)
    
    # Ghi lai topic_map (neu khong phai dry-run)
    if not args.dry_run:
        with open(args.topic_map, 'w', encoding='utf-8') as f:
            yaml.dump(topic_map, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
    # Quet tat ca atoms
    updated_files = []
    for root, _, files in os.walk(args.vault_root):
        if '_DLQ' in root or 'Audiences' in root:
            continue
        for file in files:
            if not file.endswith('.md'):
                continue
            
            filepath = os.path.join(root, file)
            content = _read_md_file(filepath)
            if not content:
                continue
                
            # Parse frontmatter
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                continue
                
            frontmatter_text = match.group(1)
            
            # De dam bao an toan, tim kiem dong chua "- loser_id"
            lines = frontmatter_text.split('\n')
            new_lines = []
            has_changes = False
            has_survivor = any(f"- {args.survivor_id}" in l for l in lines)
            
            for line in lines:
                if f"- {args.loser_id}" in line:
                    has_changes = True
                    if not has_survivor:
                        # Thay the
                        new_lines.append(line.replace(f"- {args.loser_id}", f"- {args.survivor_id}"))
                        has_survivor = True
                    else:
                        # Bo qua (xoa dong)
                        pass
                else:
                    new_lines.append(line)
                    
            if has_changes:
                new_frontmatter = '\n'.join(new_lines)
                new_content = content.replace(f"---\n{frontmatter_text}\n---", f"---\n{new_frontmatter}\n---", 1)
                if not args.dry_run:
                    _write_md_file(filepath, new_content)
                updated_files.append(filepath)
                
    result = {
        "action": "merge-topic",
        "loser": args.loser_id,
        "survivor": args.survivor_id,
        "files_updated": len(updated_files),
        "topic_map_updated": not args.dry_run
    }
    print(json.dumps(result))


def merge_audience(args):
    # Doc audience index
    if not os.path.exists(args.audience_index):
        print(json.dumps({"error": f"File khong ton tai: {args.audience_index}"}))
        sys.exit(1)
        
    with open(args.audience_index, 'r', encoding='utf-8') as f:
        aud_index = yaml.safe_load(f) or {}
        
    audiences = aud_index.get('audiences', [])
    loser_entry = None
    survivor_entry = None
    
    # Auto-mapping: Lookup file_ref neu LLM truyen vao ID (Anti-Fragile)
    for a in audiences:
        if a.get('id') == args.loser_file:
            ref = a.get('file_ref', '')
            args.loser_file = ref.replace('[[', '').replace(']]', '')
        if a.get('id') == args.survivor_file:
            ref = a.get('file_ref', '')
            args.survivor_file = ref.replace('[[', '').replace(']]', '')

    # Auto-Swap Protected Personas
    protected_audiences = []
    personas_dir = os.path.join(args.vault_root, "..", "..", "personas")
    if os.path.exists(personas_dir):
        for root, _, files in os.walk(personas_dir):
            if 'audience.yaml' in files:
                try:
                    with open(os.path.join(root, 'audience.yaml'), 'r', encoding='utf-8') as f:
                        p_data = yaml.safe_load(f) or {}
                        pref = p_data.get('file_ref', '')
                        if pref:
                            protected_audiences.append(pref.replace('[[', '').replace(']]', '').replace('.md', ''))
                except:
                    pass

    if args.loser_file in protected_audiences:
        if args.survivor_file in protected_audiences:
            print(json.dumps({"error": "Ca hai file deu la Persona Audience (protected), khong the merge!"}))
            sys.exit(1)
        # Swap
        args.loser_file, args.survivor_file = args.survivor_file, args.loser_file

    # Format link
    loser_link = f"[[{args.loser_file}]]"
    survivor_link = f"[[{args.survivor_file}]]"
    
    for a in audiences:
        if a.get('file_ref') == loser_link:
            loser_entry = a
        if a.get('file_ref') == survivor_link:
            survivor_entry = a
            
    if not loser_entry or not survivor_entry:
        print(json.dumps({"error": "Khong tim thay loser_file hoac survivor_file"}))
        sys.exit(1)
        
    if loser_entry == survivor_entry:
        print(json.dumps({"error": "Khong the tu merge (loser == survivor)"}))
        sys.exit(1)
        
    # Aliases
    survivor_aliases = survivor_entry.get('aliases', [])
    if args.loser_file not in survivor_aliases:
        survivor_aliases.insert(0, args.loser_file)
    survivor_entry['aliases'] = survivor_aliases[:5]
    
    # Update parent_audience cho cac con cua loser
    for a in audiences:
        parents = a.get('parent_audience', [])
        if loser_link in parents:
            if survivor_link not in parents:
                parents.append(survivor_link)
            parents.remove(loser_link)
            a['parent_audience'] = parents
            
    # Xoa loser entry
    audiences.remove(loser_entry)
    
    if not args.dry_run:
        with open(args.audience_index, 'w', encoding='utf-8') as f:
            yaml.dump(aud_index, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
    # Xoa file markdown loser_file.md
    loser_filepath = os.path.join(args.vault_root, 'Audiences', f"{args.loser_file}.md")
    if not args.dry_run and os.path.exists(loser_filepath):
        try:
            os.remove(loser_filepath)
        except Exception as e:
            print(json.dumps({"error": f"Loi xoa file vat ly: {str(e)}"}))
            sys.exit(1)

    # Cap nhat aliases vao file vat ly cua survivor
    survivor_filepath = os.path.join(args.vault_root, 'Audiences', f"{args.survivor_file}.md")
    if not args.dry_run and os.path.exists(survivor_filepath):
        sv_content = _read_md_file(survivor_filepath)
        if sv_content:
            loser_alias_str = f"- {args.loser_file}"
            if loser_alias_str not in sv_content:
                if re.search(r'^aliases:', sv_content, flags=re.MULTILINE):
                    sv_content = re.sub(r'^(aliases:.*?)(?:\r?\n)', f'\\1\n{loser_alias_str}\n', sv_content, count=1, flags=re.MULTILINE)
                    # Chuan hoa neu truoc do la aliases: []
                    sv_content = sv_content.replace('aliases: []\n', 'aliases:\n')
                    sv_content = sv_content.replace('aliases: []\r\n', 'aliases:\r\n')
                elif sv_content.startswith("---\n") or sv_content.startswith("---\r\n"):
                    sv_content = re.sub(r'^---(\r?\n)', f'---\\1aliases:\\1{loser_alias_str}\\1', sv_content, count=1)
                _write_md_file(survivor_filepath, sv_content)
            
    # Quet va cap nhat tham chieu
    updated_files = []
    
    # 1. Quet topic_map.yaml
    if os.path.exists(args.topic_map):
        with open(args.topic_map, 'r', encoding='utf-8') as f:
            topic_map = yaml.safe_load(f) or {}
            
        topics = topic_map.get('topics', [])
        has_tm_changes = False
        for t in topics:
            aud_refs = t.get('belongs_to_audience', [])
            if loser_link in aud_refs:
                has_tm_changes = True
                if survivor_link not in aud_refs:
                    aud_refs.append(survivor_link)
                aud_refs.remove(loser_link)
                t['belongs_to_audience'] = aud_refs
                
        if has_tm_changes and not args.dry_run:
            with open(args.topic_map, 'w', encoding='utf-8') as f:
                yaml.dump(topic_map, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
    # 2. Quet cac file markdown (Insights, Concepts, Solutions, Audiences)
    for root, _, files in os.walk(args.vault_root):
        if '_DLQ' in root:
            continue
        for file in files:
            if not file.endswith('.md'):
                continue
            filepath = os.path.join(root, file)
            content = _read_md_file(filepath)
            if not content:
                continue
                
            # Thay the noi dung
            if loser_link in content:
                new_content = content.replace(loser_link, survivor_link)
                if not args.dry_run:
                    _write_md_file(filepath, new_content)
                updated_files.append(filepath)
                
    result = {
        "action": "merge-audience",
        "loser": args.loser_file,
        "survivor": args.survivor_file,
        "files_updated": len(updated_files),
        "audience_index_updated": not args.dry_run
    }
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cascade merge cho topics va audiences")
    parser.add_argument('--action', choices=['merge-topic', 'merge-audience'], required=True)
    parser.add_argument('--loser-id', help="Topic ID bi xoa")
    parser.add_argument('--survivor-id', help="Topic ID giu lai")
    parser.add_argument('--loser-file', help="Audience file bi xoa")
    parser.add_argument('--survivor-file', help="Audience file giu lai")
    parser.add_argument('--topic-map', help="Duong dan topic_map.yaml")
    parser.add_argument('--audience-index', help="Duong dan _audience_index.yaml")
    parser.add_argument('--vault-root', help="Thu muc goc vault", required=True)
    parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    if args.action == 'merge-topic':
        if not all([args.loser_id, args.survivor_id, args.topic_map]):
            print(json.dumps({"error": "Thieu tham so cho merge-topic"}))
            sys.exit(1)
        merge_topic(args)
    else:
        if not all([args.loser_file, args.survivor_file, args.audience_index, args.topic_map]):
            print(json.dumps({"error": "Thieu tham so cho merge-audience"}))
            sys.exit(1)
        merge_audience(args)
