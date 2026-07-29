# -*- coding: utf-8 -*-
"""
TEN SCRIPT: migrate_source_link_to_wikilink.py
VAI TRO: Chuyen source_link tu Markdown link sang Wikilink / Raw path
"""
import os
import re
import argparse

def migrate_links(vault_root, dry_run=False):
    target_dirs = [
        "01-Atomic/Insights", "01-Atomic/Solutions", "01-Atomic/Concepts",
        "01-Atomic/Data-Points", "01-Atomic/Quotes", "01-Atomic/Stories",
        "01-Atomic/Audiences"
    ]
    
    updated = 0
    skipped = 0
    
    # Regex de tim source_link trong YAML frontmatter (bat ky format nao)
    # Match: source_link: "[text](path)" hoac source_link: '[text](path)' hoac source_link: [text](path)
    link_pattern = re.compile(r'^source_link:\s*["\']?\[([^\]]+)\]\(([^)]+)\)["\']?', re.MULTILINE)
    
    for d in target_dirs:
        dir_path = os.path.join(vault_root, d)
        if not os.path.isdir(dir_path):
            continue
            
        for filename in os.listdir(dir_path):
            if not filename.endswith(".md") or filename.startswith("_"):
                continue
                
            filepath = os.path.join(dir_path, filename)
            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                continue
                
            match = link_pattern.search(content)
            if not match:
                skipped += 1
                continue
                
            display_text = match.group(1)
            link_path = match.group(2)
            
            # Xac dinh format moi
            new_val = ""
            if "02-sources/books/" in link_path:
                new_val = f'"[[{display_text}]]"'
            elif "personas/" in link_path:
                new_val = f'"{link_path}"'
            elif "#^" in link_path:
                # Trich xuat ten file va block id
                # VD: ../../00-Inbox/Processed/Stories.md#^block_id -> Stories#^block_id
                parts = link_path.split("/")[-1] # Stories.md#^block_id
                parts = parts.replace(".md", "") # Stories#^block_id
                new_val = f'"[[{parts}]]"'
            else:
                skipped += 1
                continue
                
            # Thay the
            new_content = link_pattern.sub(f'source_link: {new_val}', content, count=1)
            
            if not dry_run:
                # Ép lưu UTF-8 with BOM theo rule global
                with open(filepath, "w", encoding="utf-8-sig") as f:
                    f.write(new_content)
            
            updated += 1
            
    return updated, skipped

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    print(f"MIGRATING SOURCE LINKS (dry_run={args.dry_run})...")
    u, s = migrate_links(args.vault_root, args.dry_run)
    print(f"Updated: {u}")
    print(f"Skipped/Unmatched: {s}")
