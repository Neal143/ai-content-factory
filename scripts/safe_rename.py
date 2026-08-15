"""
safe_rename.py
Last update: 15/08/2026 (GMT+7)
Vai tro: Library & CLI tool de rename file an toan trong Content Factory.
Su dung khi: Can rename file (.md, .yaml) kem cap nhat toan bo references (wikilink & plain text).
Output: File da duoc doi ten va cac reference duoc cap nhat (hoac tra ve data neu import nhu thu vien).
Tom tat logic: Quet toan bo Content Factory tru cac thu muc loai tru. Dung word-boundary regex de replace old_name thanh new_name dam bao khong bi false positive.
"""

import os
import sys
import re
import argparse
import json

EXCLUDE_DIRS = {'.agents', '.git', '.save-data', '__pycache__', '.obsidian', '_DLQ', 'recalibrate_runs', '.curation_temp'}
SCAN_EXTENSIONS = {'.md', '.yaml', '.yml'}

def collect_files_in_scope(scan_root):
    """
    Tra ve danh sach duong dan tuyet doi cua tat ca file trong scope.
    Duyet os.walk(scan_root), skip thu muc co ten trong EXCLUDE_DIRS,
    chi lay file co extension trong SCAN_EXTENSIONS.
    """
    files_in_scope = []
    for root, dirs, files in os.walk(scan_root):
        # Skip excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SCAN_EXTENSIONS:
                files_in_scope.append(os.path.abspath(os.path.join(root, file)))
    return files_in_scope

def replace_refs(scan_root, old_name, new_name, dry_run=False):
    """
    Quet toan bo scan_root (tru EXCLUDE_DIRS), tim va thay the
    old_name → new_name trong tat ca file .md/.yaml.
    
    Su dung word-boundary regex de dam bao chi replace khi old_name
    xuat hien nhu mot token hoan chinh (khong phai substring cua slug khac).
    
    Pattern: (?<![a-zA-Z0-9_-])old_name(?![a-zA-Z0-9_-])
    
    Vi du ket qua:
      [[old-name]]     → [[new-name]]     (bounded by [ ])
      old-name.md      → new-name.md      (bounded by . )
      "old-name"       → "new-name"       (bounded by " ")
      longer-old-name  → KHONG thay doi   (lookahead chan)
    
    Args:
        scan_root: Duong dan thu muc goc (thuong la Content Factory/)
        old_name: Ten file cu (khong co extension)
        new_name: Ten file moi (khong co extension)
        dry_run: Neu True, chi report khong ghi file
    
    Returns:
        list[dict]: [{"file": path, "count": N}, ...]
    """
    files = collect_files_in_scope(scan_root)
    # Regex with negative lookbehind and lookahead to ensure word boundaries
    escaped_old = re.escape(old_name)
    pattern = re.compile(r'(?<![a-zA-Z0-9_-])' + escaped_old + r'(?![a-zA-Z0-9_-])')
    
    results = []
    
    for filepath in files:
        try:
            # Read with utf-8-sig to handle BOM fallback
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            matches = pattern.findall(content)
            count = len(matches)
            
            if count > 0:
                new_content = pattern.sub(new_name, content)
                if not dry_run:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                results.append({"file": filepath, "count": count})
                
        except Exception as e:
            print(f"[ERR] Loi doc/ghi file {filepath}: {e}", file=sys.stderr)
            
    return results

def _find_physical_file(scan_root, filename):
    """
    Tim file vat ly theo basename.
    """
    files = collect_files_in_scope(scan_root)
    for filepath in files:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        if basename == filename:
            return filepath
    return None

def _cmd_rename(args):
    old_name = args.old_name
    new_name = args.new_name
    scan_root = args.scan_root
    dry_run = args.dry_run

    if not old_name or not new_name:
        print(json.dumps({"status": "ERR", "reason": "old-name va new-name khong duoc rong"}))
        sys.exit(1)
        
    if any(c in old_name or c in new_name for c in ['/', '\\', '[[', ']]']):
        print(json.dumps({"status": "ERR", "reason": "old-name va new-name khong duoc chua ky tu cấm (/, \\, [[, ]])"}))
        sys.exit(1)

    if old_name == new_name:
        print(json.dumps({"status": "SKIP", "reason": "No change needed"}))
        sys.exit(0)

    old_filepath = _find_physical_file(scan_root, old_name)
    if not old_filepath:
        print(json.dumps({"status": "ERR", "reason": f"Khong tim thay file cu: {old_name}"}))
        sys.exit(1)

    new_filepath_check = _find_physical_file(scan_root, new_name)
    if new_filepath_check:
        print(json.dumps({"status": "ERR", "reason": f"File moi da ton tai: {new_filepath_check}"}))
        sys.exit(1)

    # Replace references
    ref_results = replace_refs(scan_root, old_name, new_name, dry_run=dry_run)
    total_files = len(ref_results)
    total_replacements = sum(r['count'] for r in ref_results)

    report = {
        "status": "SUCCESS",
        "old_name": old_name,
        "new_name": new_name,
        "file_renamed": old_filepath,
        "references_updated": ref_results,
        "total_files_updated": total_files,
        "total_replacements": total_replacements
    }
    
    if total_files == 0:
        report["warning"] = "No references found"

    if not dry_run:
        new_filepath = os.path.join(os.path.dirname(old_filepath), new_name + os.path.splitext(old_filepath)[1])
        try:
            os.rename(old_filepath, new_filepath)
            report["file_renamed"] = new_filepath
        except Exception as e:
            print(json.dumps({"status": "ERR", "reason": f"Loi doi ten file vat ly: {e}"}))
            sys.exit(2)

    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rename file in Content Factory and update references safely.")
    parser.add_argument('--old-name', required=True, help="Ten file cu (khong co extension)")
    parser.add_argument('--new-name', required=True, help="Ten file moi (khong co extension)")
    parser.add_argument('--scan-root', default=".", help="Thu muc goc de quet (default: current directory)")
    parser.add_argument('--dry-run', action='store_true', help="Chi mo phong, khong ghi file hoac doi ten")
    
    args = parser.parse_args()
    _cmd_rename(args)
