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
import urllib.parse
import subprocess

EXCLUDE_DIRS = {'.agents', '.git', '.save-data', '__pycache__', '.obsidian', '_DLQ'}
SCAN_EXTENSIONS = {'.md', '.yaml', '.yml'}

def collect_files_in_scope(scan_root):
    """
    Tra ve danh sach duong dan tuyet doi cua tat ca file trong scope.
    Duyet os.walk(scan_root), skip thu muc co ten trong EXCLUDE_DIRS,
    chi lay file co extension trong SCAN_EXTENSIONS.
    """
    files_in_scope = []
    for root, dirs, files in os.walk(scan_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SCAN_EXTENSIONS:
                files_in_scope.append(os.path.abspath(os.path.join(root, file)))
    return files_in_scope

def replace_refs(scan_root, old_name, new_name, dry_run=False):
    """
    Quet toan bo scan_root (tru EXCLUDE_DIRS), tim va thay the
    old_name -> new_name trong tat ca file .md/.yaml.
    Ho tro ca dang raw va URL-encoded (%20).
    """
    files = collect_files_in_scope(scan_root)
    escaped_old = re.escape(old_name)
    pattern = re.compile(r'(?<![a-zA-Z0-9_-])' + escaped_old + r'(?![a-zA-Z0-9_-])')
    
    old_encoded = urllib.parse.quote(old_name)
    new_encoded = urllib.parse.quote(new_name)
    has_encoded = (old_encoded != old_name)
    
    results = []
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read()
            
            modified = False
            new_content = content
            
            matches = pattern.findall(new_content)
            count = len(matches)
            if count > 0:
                new_content = pattern.sub(new_name, new_content)
                modified = True
                
            if has_encoded and old_encoded in new_content:
                encoded_count = new_content.count(old_encoded)
                count += encoded_count
                new_content = new_content.replace(old_encoded, new_encoded)
                modified = True
                
            if modified:
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
    sync_only = getattr(args, 'sync_only', False)

    if not old_name or not new_name:
        print(json.dumps({"status": "ERR", "reason": "old-name va new-name khong duoc rong"}))
        sys.exit(1)
        
    if any(c in old_name or c in new_name for c in ['/', '\\', '[[', ']]']):
        print(json.dumps({"status": "ERR", "reason": "old-name va new-name khong duoc chua ky tu cam (/, \\, [[, ]])"}))
        sys.exit(1)

    if old_name == new_name:
        print(json.dumps({"status": "SKIP", "reason": "No change needed"}))
        sys.exit(0)

    old_filepath = None
    if not sync_only:
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
        "sync_only": sync_only,
        "references_updated": ref_results,
        "total_files_updated": total_files,
        "total_replacements": total_replacements
    }

    if not dry_run and not sync_only and old_filepath:
        new_filepath = os.path.join(os.path.dirname(old_filepath), new_name + os.path.splitext(old_filepath)[1])
        try:
            os.rename(old_filepath, new_filepath)
            report["file_renamed"] = new_filepath
        except Exception as e:
            print(json.dumps({"status": "ERR", "reason": f"Loi doi ten file vat ly: {e}"}))
            sys.exit(2)

    # Trigger artifact refresh if available in scratch/
    scratch_dir = os.path.expanduser(r"~\.gemini\antigravity-ide\brain\56331815-b28b-4fcf-a1c4-9b5a429978cd\scratch")
    if os.path.exists(scratch_dir):
        preview_script = os.path.join(scratch_dir, "generate_merged_preview.py")
        canvas_script = os.path.join(scratch_dir, "generate_radial_canvas.py")
        if os.path.exists(preview_script):
            try:
                subprocess.run([sys.executable, preview_script], cwd=scratch_dir, capture_output=True)
            except Exception:
                pass
        if os.path.exists(canvas_script):
            try:
                subprocess.run([sys.executable, canvas_script], cwd=scratch_dir, capture_output=True)
            except Exception:
                pass

    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rename file in Content Factory and update references safely.")
    parser.add_argument('--old-name', required=True, help="Ten file cu (khong co extension)")
    parser.add_argument('--new-name', required=True, help="Ten file moi (khong co extension)")
    parser.add_argument('--scan-root', default=".", help="Thu muc goc de quet (default: current directory)")
    parser.add_argument('--dry-run', action='store_true', help="Chi mo phong, khong ghi file hoac doi ten")
    parser.add_argument('--sync-only', action='store_true', help="Chi cap nhat references, khong doi ten file vat ly")
    
    args = parser.parse_args()
    _cmd_rename(args)
