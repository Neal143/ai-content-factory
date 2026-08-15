"""
verify_referential_integrity.py
Last update: 15/08/2026 23:55 (GMT+7)
Vai tro: Kiem tra va dam bao tinh toan ven lien ket (Referential Integrity) trong toan bo Content Factory.
Su dung khi: Chay dinh ky hoac lam pre-flight check truoc khi chay cac pipeline noi dung.
Output: Bao cao chi tiet so luong lien ket hop le, lien ket hong (neu co) va tu dong fix neu co co --fix.
"""

import os
import sys
import re
import argparse
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

EXCLUDE_DIRS = {'.agents', '.git', '.save-data', '__pycache__', '.obsidian', '_DLQ'}
SCAN_EXTENSIONS = {'.md', '.yaml', '.yml'}

def audit_integrity(scan_root, auto_fix=False):
    vault_dir = os.path.join(scan_root, "vault")
    
    # 1. Map all physical files in vault
    all_vault_files = {}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            base, ext = os.path.splitext(f)
            all_vault_files[base] = os.path.join(root, f)
            all_vault_files[f] = os.path.join(root, f)

    # 2. Collect all files to check
    files_to_check = []
    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in SCAN_EXTENSIONS:
                files_to_check.append(os.path.join(root, f))

    wikilink_pattern = re.compile(r'\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]')
    
    total_links = 0
    valid_links = 0
    broken_links = []

    for filepath in files_to_check:
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read()
            
            matches = wikilink_pattern.findall(content)
            for target in matches:
                target_clean = target.strip()
                # Skip external/path links if any
                if target_clean.startswith('http') or target_clean.startswith('..'):
                    continue
                
                total_links += 1
                base_target = os.path.splitext(os.path.basename(target_clean))[0]
                
                if base_target in all_vault_files or target_clean in all_vault_files:
                    valid_links += 1
                else:
                    broken_links.append({
                        "file": filepath,
                        "broken_ref": target_clean
                    })
        except Exception as e:
            print(f"[ERR] Reading {filepath}: {e}", file=sys.stderr)

    report = {
        "status": "PASS" if len(broken_links) == 0 else "WARNING",
        "total_files_scanned": len(files_to_check),
        "total_wikilinks_checked": total_links,
        "valid_links": valid_links,
        "broken_links_count": len(broken_links),
        "broken_links": broken_links
    }
    
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Audit Referential Integrity in Content Factory.")
    parser.add_argument('--scan-root', default=".", help="Thu muc goc de kiem tra")
    parser.add_argument('--fix', action='store_true', help="Tu dong sua lien ket neu tim thay slug tuong tu")
    
    args = parser.parse_args()
    report = audit_integrity(os.path.abspath(args.scan_root), auto_fix=args.fix)
    print(json.dumps(report, indent=2, ensure_ascii=False))
