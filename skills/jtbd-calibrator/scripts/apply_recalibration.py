# ── TEN SCRIPT: apply_recalibration.py ──
# Last update: 15/08/2026 (GMT+7)
# Vai tro: Ap dung JTBD da recalibrate vao vault.
# Su dung khi: Sau khi jtbd-calibrator hoan thanh mode re-calibrate.
# Output: Audience files updated/renamed, _audience_index.yaml updated,
#         topic_map.yaml updated, recalibration_report.json.
# Tom tat logic:
#   Phase 1: Build change_map + conflict check
#   Phase 2: Dry-run report
#   Phase 3: Backup
#   Phase 4: In-memory batch update + write + rename
#   Phase 5: Verification scan
#   Phase 6: Write report JSON
#   Phase 7: Summary

import os
import sys
import argparse
import json
import re
import shutil
from datetime import datetime
import yaml
import unicodedata


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def slugify_vi(text):
    """Chuyen text tieng Viet thanh slug ASCII-hyphenated."""
    text = text.lower()
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    text = text.replace('_', ' ')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    slug = text.strip('-')
    return slug if slug else "untitled"


def derive_filename(performer, main_job, circumstance):
    """Derive audience filename tu 3 JTBD fields."""
    return f"{slugify_vi(performer)}_{slugify_vi(main_job)}_{slugify_vi(circumstance)}"


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(path, content):
    """Atomic write: tmp + rename."""
    tmp_path = path + ".tmp"
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_path, path)


def backup_file(file_path, backup_dir, vault_root):
    """Copy file vao backup dir, giu nguyen relative path."""
    if not os.path.exists(file_path):
        return
    rel_path = os.path.relpath(file_path, vault_root)
    dest_path = os.path.join(backup_dir, rel_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(file_path, dest_path)


# ══════════════════════════════════════════════════════════════
# MAIN LOGIC
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Apply re-calibrated JTBD to vault")
    parser.add_argument('--recalibrated-json', required=True, help="Path to jtbd_recalibrated.json")
    parser.add_argument('--vault-root', required=True, help="Path to vault root")
    parser.add_argument('--work-dir', required=True, help="Path to work_dir (backup + report)")
    parser.add_argument('--dry-run', action='store_true', help="Preview only, no writes")
    args = parser.parse_args()

    # ── Doc input ──
    with open(args.recalibrated_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    atomic_dir = os.path.join(args.vault_root, '01-Atomic')
    audiences_dir = os.path.join(atomic_dir, 'Audiences')
    index_path = os.path.join(audiences_dir, '_audience_index.yaml')
    personas_dir = os.path.join(os.path.dirname(args.vault_root.rstrip('/\\')), 'personas')
    backup_dir = os.path.join(args.work_dir, 'backup')

    # Map original_filename -> entry
    updates = {}
    for entry in data:
        if 'original_filename' in entry:
            updates[entry['original_filename']] = entry

    # ════════════════════════════════════════════
    # PHASE 1: Build change_map + Conflict check
    # ════════════════════════════════════════════
    change_map = []
    for orig_fn, entry in updates.items():
        new_fn = derive_filename(
            entry['audience_Job_performer'],
            entry['audience_main_job'],
            entry['audience_circumstance']
        )
        change_map.append({
            "original_filename": orig_fn,
            "new_filename": new_fn,
            "has_rename": new_fn != orig_fn,
            "entry": entry,
        })

    # Conflict check A: Uniqueness giua cac new_filename trong batch
    new_fns = [cm["new_filename"] for cm in change_map]
    seen = {}
    for cm in change_map:
        nf = cm["new_filename"]
        if nf in seen:
            print(f"CONFLICT: Entries '{seen[nf]}' va '{cm['original_filename']}' cung derive thanh '{nf}'. Dung truoc khi thay doi.")
            sys.exit(1)
        seen[nf] = cm["original_filename"]

    # Conflict check B: Conflict voi existing files khong trong batch
    existing_audience_files = set()
    for f in os.listdir(audiences_dir):
        if f.endswith('.md') and f != '_audience_index.yaml':
            existing_audience_files.add(f[:-3])  # bo .md

    original_fns_set = set(updates.keys())
    for cm in change_map:
        nf = cm["new_filename"]
        if cm["has_rename"] and nf in existing_audience_files and nf not in original_fns_set:
            print(f"CONFLICT: '{nf}' da ton tai (khong thuoc batch recalibrate). Dung.")
            sys.exit(1)

    # ════════════════════════════════════════════
    # PHASE 2: Dry-run Report
    # ════════════════════════════════════════════
    rename_count = sum(1 for cm in change_map if cm["has_rename"])
    update_count = len(change_map) - rename_count

    print(f"\nDRY-RUN REPORT")
    print(f"{'='*55}")
    print(f"Entries: {len(change_map)} total, {rename_count} can rename, {update_count} chi update noi dung\n")
    print(f"{'#':<4} {'Original (rut gon)':<40} {'Rename?':<8}")
    print(f"{'-'*4} {'-'*40} {'-'*8}")
    for i, cm in enumerate(change_map, 1):
        orig_short = cm["original_filename"][:38] + ".." if len(cm["original_filename"]) > 40 else cm["original_filename"]
        rename_flag = "YES" if cm["has_rename"] else "skip"
        print(f"{i:<4} {orig_short:<40} {rename_flag:<8}")

    print(f"\nBackup se luu tai: {backup_dir}/")
    print(f"{'='*55}\n")

    if args.dry_run:
        print("DRY-RUN mode. Khong ghi file. Thoat.")
        sys.exit(0)

    # ════════════════════════════════════════════
    # PHASE 3: Backup
    # ════════════════════════════════════════════
    os.makedirs(backup_dir, exist_ok=True)

    # Backup _audience_index.yaml
    backup_file(index_path, backup_dir, args.vault_root)

    # Backup audience .md files trong change_map
    for cm in change_map:
        md_path = os.path.join(audiences_dir, f"{cm['original_filename']}.md")
        backup_file(md_path, backup_dir, args.vault_root)

    # Backup topic_map.yaml (neu ton tai)
    if os.path.isdir(personas_dir):
        for persona_name in os.listdir(personas_dir):
            tm = os.path.join(personas_dir, persona_name, 'topic_map.yaml')
            if os.path.isfile(tm):
                backup_file(tm, backup_dir, os.path.dirname(args.vault_root.rstrip('/\\')))

    print(f"BACKUP hoan tat tai: {backup_dir}/")

    # ════════════════════════════════════════════
    # PHASE 4: Apply — In-memory batch update + Write
    # ════════════════════════════════════════════

    # Buoc 4a: Read ALL affected files vao memory
    file_contents = {}

    for cm in change_map:
        path = os.path.join(audiences_dir, f"{cm['original_filename']}.md")
        if os.path.exists(path):
            file_contents[path] = read_file(path)

    # Doc _audience_index.yaml
    file_contents[index_path] = read_file(index_path)

    # Doc tat ca .md files trong 01-Atomic/ (de replace wikilinks)
    for root, _, files in os.walk(atomic_dir):
        if '_DLQ' in root or 'recalibrate_runs' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                fpath = os.path.join(root, f)
                if fpath not in file_contents:
                    file_contents[fpath] = read_file(fpath)

    # Doc topic_map.yaml (neu ton tai)
    topic_map_paths = []
    if os.path.isdir(personas_dir):
        for persona_name in os.listdir(personas_dir):
            tm = os.path.join(personas_dir, persona_name, 'topic_map.yaml')
            if os.path.isfile(tm):
                topic_map_paths.append(tm)
                file_contents[tm] = read_file(tm)

    # Mo rong scope: doc them cac file .md/.yaml khac trong Content Factory/
    # (bo sung nhung file chua co trong file_contents)
    _scripts_dir = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))
    if _scripts_dir not in sys.path:
        sys.path.insert(0, _scripts_dir)
    from safe_rename import collect_files_in_scope

    _cf_root = os.path.normpath(os.path.abspath(
        os.path.join(args.vault_root, '..')))
    _existing_abs = {os.path.normpath(os.path.abspath(k)) for k in file_contents}
    for _fpath in collect_files_in_scope(_cf_root):
        _abs = os.path.normpath(os.path.abspath(_fpath))
        if _abs not in _existing_abs:
            file_contents[_fpath] = read_file(_fpath)
            _existing_abs.add(_abs)

    # Buoc 4b: Update frontmatter + heading trong audience files (in-memory)
    for cm in change_map:
        path = os.path.join(audiences_dir, f"{cm['original_filename']}.md")
        if path not in file_contents:
            continue
        content = file_contents[path]
        entry = cm["entry"]

        # Update 3 single-line fields bang regex
        content = re.sub(r'^(audience_main_job:)\s*.*$',
                         rf'\1 {entry["audience_main_job"]}', content, count=1, flags=re.MULTILINE)
        content = re.sub(r'^(audience_circumstance:)\s*.*$',
                         rf'\1 {entry["audience_circumstance"]}', content, count=1, flags=re.MULTILINE)
        content = re.sub(r'^(audience_Job_performer:)\s*.*$',
                         rf'\1 {entry["audience_Job_performer"]}', content, count=1, flags=re.MULTILINE)

        # Update aliases (multi-line field) bang regex block replacement
        calibrated_aliases = entry.get("aliases", [])
        if calibrated_aliases:
            new_aliases_block = "aliases:\n" + "\n".join(f"- {a}" for a in calibrated_aliases)
        else:
            new_aliases_block = "aliases: []"
        content = re.sub(r'^aliases:.*?(?=^\w|^---)',
                         new_aliases_block + "\n", content, count=1, flags=re.MULTILINE | re.DOTALL)

        # Update heading
        performer = entry["audience_Job_performer"]
        main_job = entry["audience_main_job"]
        circumstance = entry["audience_circumstance"]
        new_heading = f"# \U0001f3af {performer} muon {main_job} {circumstance}"
        if re.search(r'^# \U0001f3af ', content, re.MULTILINE):
            content = re.sub(r'^# \U0001f3af .*$', new_heading, content, count=1, flags=re.MULTILINE)

        file_contents[path] = content

    # Buoc 4c: Build global rename map + Replace wikilinks (in-memory)
    rename_map = {}
    for cm in change_map:
        if cm["has_rename"]:
            rename_map[f"[[{cm['original_filename']}]]"] = f"[[{cm['new_filename']}]]"

    ref_update_count = 0
    for fpath in list(file_contents.keys()):
        content = file_contents[fpath]
        changed = False
        for old_link, new_link in rename_map.items():
            if old_link in content:
                content = content.replace(old_link, new_link)
                changed = True
                ref_update_count += 1
        if changed:
            file_contents[fpath] = content

    # Buoc 4d: Update _audience_index.yaml (in-memory)
    idx_content = file_contents[index_path]
    idx_lines = idx_content.split('\n')
    body_start = 0
    for i, line in enumerate(idx_lines):
        if line.startswith('#') or line.strip() == '':
            body_start = i + 1
        else:
            break
    header = '\n'.join(idx_lines[:body_start])
    body = '\n'.join(idx_lines[body_start:])

    index_data = yaml.safe_load(body) or {}
    for aud in index_data.get('audiences', []):
        file_ref = aud.get('file_ref', '')
        match = re.search(r'\[\[(.*?)\]\]', file_ref)
        if match:
            fn = match.group(1)
            # Reverse lookup: fn might be the new filename (wikilinks already replaced)
            orig_fn = next((cm["original_filename"] for cm in change_map
                           if cm["new_filename"] == fn or cm["original_filename"] == fn), fn)
            if orig_fn in updates:
                entry = updates[orig_fn]
                # Derive correct current filename (post-rename)
                current_fn = next((cm["new_filename"] for cm in change_map
                                  if cm["original_filename"] == orig_fn), orig_fn)
                aud.pop('id', None)
                aud['file_ref'] = f"[[{current_fn}]]"
                aud['audience_Job_performer'] = entry['audience_Job_performer']
                aud['audience_main_job'] = entry['audience_main_job']
                aud['audience_circumstance'] = entry['audience_circumstance']
                aud['aliases'] = entry['aliases']

    new_body = yaml.dump(index_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    file_contents[index_path] = header + ('\n' if header else '') + new_body

    # Buoc 4e: Update topic_map.yaml (in-memory) — id replacement
    for tm_path in topic_map_paths:
        if tm_path in file_contents:
            content = file_contents[tm_path]
            for cm in change_map:
                if cm["has_rename"]:
                    old_id = cm["original_filename"].replace('-', '_')
                    new_id = cm["new_filename"].replace('-', '_')
                    content = content.replace(f"audience_id: {old_id}", f"audience_id: {new_id}")
                    content = content.replace(cm["original_filename"], cm["new_filename"])
            file_contents[tm_path] = content

    # Buoc 4f: Write ALL files to disk
    for path, content in file_contents.items():
        write_file(path, content)

    # Buoc 4g: Rename physical files
    for cm in change_map:
        if cm["has_rename"]:
            old_path = os.path.join(audiences_dir, f"{cm['original_filename']}.md")
            new_path = os.path.join(audiences_dir, f"{cm['new_filename']}.md")
            if os.path.exists(old_path):
                os.rename(old_path, new_path)

    # ════════════════════════════════════════════
    # PHASE 5: Verification
    # ════════════════════════════════════════════
    existing_files = set()
    for f in os.listdir(audiences_dir):
        if f.endswith('.md'):
            existing_files.add(f[:-3])

    broken_links = []
    for root, _, files in os.walk(atomic_dir):
        if '_DLQ' in root or 'recalibrate_runs' in root:
            continue
        for f in files:
            if not f.endswith('.md'):
                continue
            fpath = os.path.join(root, f)
            content = read_file(fpath)
            for match in re.finditer(r'\[\[(.*?)\]\]', content):
                link_target = match.group(1)
                # Chi check cac wikilinks tro toi Audiences dir
                if any(cm["new_filename"] == link_target or cm["original_filename"] == link_target
                       for cm in change_map):
                    if link_target not in existing_files:
                        broken_links.append({
                            "file": os.path.relpath(fpath, args.vault_root),
                            "broken_link": f"[[{link_target}]]"
                        })

    if broken_links:
        print(f"\nVERIFICATION FAILED: {len(broken_links)} broken wikilinks phat hien:")
        for bl in broken_links[:10]:
            print(f"   File: {bl['file']}, Link: {bl['broken_link']}")
        print(f"Rollback: copy files tu {backup_dir}/ ve vault/01-Atomic/Audiences/")
        verification_status = "FAILED"
    else:
        print("VERIFICATION PASSED (0 broken wikilinks)")
        verification_status = "PASSED"

    # ════════════════════════════════════════════
    # PHASE 6: Write report
    # ════════════════════════════════════════════
    report = {
        "timestamp": datetime.now().isoformat(),
        "backup_path": backup_dir,
        "total_entries": len(change_map),
        "renamed": rename_count,
        "content_only": update_count,
        "verification": verification_status,
        "changes": []
    }
    for cm in change_map:
        entry = cm["entry"]
        report["changes"].append({
            "original_filename": cm["original_filename"],
            "new_filename": cm["new_filename"],
            "new_main_job": entry["audience_main_job"],
            "new_circumstance": entry["audience_circumstance"],
            "renamed": cm["has_rename"]
        })

    report_path = os.path.join(args.work_dir, "recalibration_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ════════════════════════════════════════════
    # PHASE 7: Summary
    # ════════════════════════════════════════════
    print(f"\n{'='*55}")
    print(f"RECALIBRATION APPLIED")
    print(f"  Entries processed : {len(change_map)}")
    print(f"  Renamed           : {rename_count}")
    print(f"  Content-only      : {update_count}")
    print(f"  Refs updated      : {ref_update_count} occurrences")
    print(f"  Verification      : {verification_status}")
    print(f"  Backup            : {backup_dir}")
    print(f"  Report            : {report_path}")
    print(f"{'='*55}")


if __name__ == '__main__':
    main()
