import os
import sys
import json
import uuid
import yaml
import codecs
import argparse
import shutil
import subprocess

"""
Ten file: prepare_curation_batches.py
Last update: 13/07/2026 09:38 (GMT+7)
Vai tro: Quan ly batch cho 3 curation skills (auto-tagger, atom-dedup, atom-linker).
         Co che anti-cheat: submit-and-validate + content isolation (embed atom content vao batch).
Su dung khi: Goi tu cac skill auto-tagger, atom-dedup, atom-linker.
Output:
  - batch_manifest.json (trang thai batch, KHONG chua atoms)
  - batch_XX.json (atoms tung batch, co batch_key + atoms_content)
  - current_batch.json (batch hien tai cho Agent doc)
  - results_temp.json (template cho Agent dien ket qua)
  - {skill}_log.json (ket qua tich luy)
Tom tat logic:
  - --init: Chia atoms thanh batch files, ghi manifest (co skill type)
  - --get-next: Copy batch hien tai + sinh template results_temp.json
  - --submit: Validate ket qua + execute (ghi vault) + mark done
  - --status: Hien thi tien trinh
"""

# === NHOM 0: Constants & Helpers ===

EXCLUDED_DIRS = ["_DLQ", "Audiences"]
PLACEHOLDER = "[ĐIỀN VÀO ĐÂY"
SESSION_BATCH_LIMIT = 5

SKILL_NAME_MAP = {
    "tag": "auto-tagger",
    "dedup": "atom-dedup",
    "align": "atom-linker",
    "vc-topic-dedup": "vc-topic-dedup",
    "vc-audience-curator": "vc-audience-curator"
}

def _read_manifest(output_dir):
    """Doc manifest, tra ve dict hoac None"""
    path = os.path.join(output_dir, "batch_manifest.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_manifest(output_dir, manifest):
    """Ghi manifest"""
    path = os.path.join(output_dir, "batch_manifest.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

def _read_json(path):
    """Doc file JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_json(path, data):
    """Ghi file JSON"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _print_skill_summary(output_dir, skill):
    """In summary cua skill sau khi tat ca batch da xu ly xong.
    Goi tu get_next() khi tat ca batch = done."""
    log_names = {"tag": "tag_log.json", "dedup": "dedup_log.json", "align": "align_log.json"}
    log_name = log_names.get(skill)
    if not log_name:
        return
    log_file = os.path.join(output_dir, log_name)
    if not os.path.exists(log_file):
        return

    entries = _read_json(log_file)
    if not entries:
        return

    print(f"\n===== {skill.upper()} SUMMARY =====")

    if skill == "tag":
        tagged = sum(1 for e in entries if e.get("action") == "tagged")
        skipped = sum(1 for e in entries if e.get("action") == "skipped")
        print(f"Total: {len(entries)} atoms | Tagged: {tagged} | Skipped: {skipped}")

    elif skill == "dedup":
        merged = [e for e in entries if e.get("decision") == "merge"]
        passed = sum(1 for e in entries if e.get("decision") == "pass")
        print(f"Total: {len(entries)} atoms | Passed: {passed} | Merged: {len(merged)}")
        for m in merged:
            loser = m["atom_path"] if m.get("survivor") != m["atom_path"] else m.get("merge_with", "?")
            survivor_path = m.get("survivor", "?")
            print(f"  {os.path.basename(loser)} -> {os.path.basename(survivor_path)}")

    elif skill == "align":
        linked = sum(1 for e in entries if e.get("decision") == "linked")
        orphaned_list = [e for e in entries if e.get("decision") == "orphan"]
        cloned = sum(1 for e in entries if e.get("decision") == "cloned")
        print(f"Total: {len(entries)} atoms | Linked: {linked} | Orphaned: {len(orphaned_list)} | Cloned: {cloned}")
        for o in orphaned_list:
            print(f"  [ORPHAN] {os.path.basename(o['atom_path'])}")

    elif skill in ["vc-topic-dedup", "vc-audience-curator"]:
        print(f"Total: {len(entries)} decisions processed.")

    print("=" * 35)


def _append_log(log_path, entries):
    """Append entries vao file log (tao moi neu chua co)"""
    existing = []
    if os.path.exists(log_path):
        existing = _read_json(log_path)
    existing.extend(entries)
    _write_json(log_path, existing)

def _parse_frontmatter(content):
    """Tach frontmatter va body tu noi dung markdown.
    Tra ve (frontmatter_str, body_str) hoac (None, content) neu khong co."""
    if not content.startswith("---"):
        return None, content
    # Tim vi tri dong --- thu 2
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return None, content
    # Tim het dong ---
    newline_after = content.find("\n", end_idx)
    if newline_after == -1:
        fm_str = content[3:end_idx].strip()
        return fm_str, ""
    fm_str = content[3:end_idx].strip()
    body = content[newline_after + 1:]
    return fm_str, body

def _write_md_file(path, frontmatter_dict, body):
    """Ghi file markdown voi YAML frontmatter va body, encoding UTF-8 BOM.
    - keywords: flow-style list [a, b, c] (1 dong, giu kieu list cho downstream)
    - description va cac truong khac: khong xuong dong (width=10000)"""
    fm = dict(frontmatter_dict)

    # Tach keywords ra de format rieng (flow-style)
    keywords = fm.pop("keywords", None)

    fm_str = yaml.dump(
        fm,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000
    ).strip()

    # Append keywords dang flow-style list
    if keywords is not None:
        if isinstance(keywords, list) and len(keywords) > 0:
            kw_items = ", ".join(str(k) for k in keywords)
            fm_str += f"\nkeywords: [{kw_items}]"
        elif isinstance(keywords, str) and keywords:
            fm_str += f"\nkeywords: {keywords}"

    content = f"---\n{fm_str}\n---\n{body}"
    with codecs.open(path, 'w', 'utf-8-sig') as f:
        f.write(content)

def _read_md_file(path):
    """Doc file markdown, tra ve (frontmatter_dict, body_str)"""
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    fm_str, body = _parse_frontmatter(content)
    if fm_str is None:
        return {}, body
    fm_dict = yaml.safe_load(fm_str) or {}
    return fm_dict, body


def init_meta_dedup_batches(skill, meta_source, batch_size, output_dir):
    """Khoi tao batch cho vc-topic-dedup hoac vc-audience-curator"""
    if not os.path.exists(meta_source):
        print(f"Khong tim thay {meta_source}")
        sys.exit(1)
        
    with open(meta_source, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
        
    os.makedirs(output_dir, exist_ok=True)
    batches_meta = []
    
    if skill == "vc-topic-dedup":
        topics = data.get('topics', [])
        groups = {}
        for t in topics:
            prefix = t.get('id', '').split('_')[0]
            groups.setdefault(prefix, []).append(t)
            
        batch_id = 1
        for prefix, items in groups.items():
            for i in range(0, len(items), batch_size):
                chunk = items[i:i+batch_size]
                # Anti-hallucination: Xoa aliases khoi batch de LLM khong nham lan
                for item in chunk:
                    item.pop("aliases", None)
                batch_file = os.path.join(output_dir, f"batch_{batch_id:02d}.json")
                _write_json(batch_file, {
                    "batch_id": batch_id,
                    "pillar_prefix": prefix,
                    "items": chunk,
                    "anchors": []
                })
                batches_meta.append({"id": batch_id, "status": "pending"})
                batch_id += 1
                
    elif skill == "vc-audience-curator":
        audiences = data.get('audiences', [])
        batch_id = 1
        for i in range(0, len(audiences), batch_size):
            chunk = audiences[i:i+batch_size]
            # Anti-hallucination: Xoa aliases khoi batch de LLM khong nham lan
            for item in chunk:
                item.pop("aliases", None)
            batch_file = os.path.join(output_dir, f"batch_{batch_id:02d}.json")
            _write_json(batch_file, {
                "batch_id": batch_id,
                "items": chunk,
                "anchors": []
            })
            batches_meta.append({"id": batch_id, "status": "pending"})
            batch_id += 1
            
    manifest = {
        "skill": skill,
        "batch_size": batch_size,
        "meta_source": meta_source,
        "anchors": [],
        "batches": batches_meta
    }
    _write_manifest(output_dir, manifest)
    print(f"Initialized {len(batches_meta)} batches cho {skill}")

def _validate_meta_dedup(entries):
    """Validation meta dedup decisions"""
    return True, ""

def _execute_meta_dedup(entries, output_dir):
    """Execute meta dedup bang subprocess goi cascade_merge.py"""
    manifest = _read_manifest(output_dir)
    skill = manifest.get("skill")
    meta_source = manifest.get("meta_source", "vault/01-Atomic/Topics/topic_map.yaml")
    script_path = os.path.join(".agents", "scripts", "cascade_merge.py")
    
    for entry in entries:
        if entry.get("action") == "merge":
            loser = entry.get("loser_id") or entry.get("loser_file")
            survivor = entry.get("survivor_id") or entry.get("survivor_file")
            
            if loser:
                loser = loser.replace("[[", "").replace("]]", "").replace(".md", "")
            if survivor:
                survivor = survivor.replace("[[", "").replace("]]", "").replace(".md", "")

            if skill == "vc-topic-dedup":
                cmd = [sys.executable, script_path, "--action", "merge-topic", "--loser-id", loser, "--survivor-id", survivor, "--topic-map", meta_source, "--vault-root", "vault/01-Atomic"]
            else:
                cmd = [sys.executable, script_path, "--action", "merge-audience", "--loser-file", loser, "--survivor-file", survivor, "--audience-index", meta_source, "--topic-map", "vault/01-Atomic/Topics/topic_map.yaml", "--vault-root", "vault/01-Atomic"]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"[ERR] Cascade merge failed for {loser}: {res.stderr}")
                sys.exit(1)
            else:
                try:
                    out_data = json.loads(res.stdout)
                    if "error" in out_data:
                        print(f"[ERR] Cascade merge error logic for {loser}: {out_data['error']}")
                        sys.exit(1)
                    # Dong bo Auto-Swap vao Log de bao cao hien thi dung
                    if "loser" in out_data:
                        if skill != "vc-topic-dedup": entry["loser_file"] = out_data["loser"]
                        else: entry["loser_id"] = out_data["loser"]
                    if "survivor" in out_data:
                        if skill != "vc-topic-dedup": entry["survivor_file"] = out_data["survivor"]
                        else: entry["survivor_id"] = out_data["survivor"]
                except Exception as e:
                    print(f"[ERR] Cascade merge output invalid JSON for {loser}: {e}\nSTDOUT: {res.stdout}")
                    sys.exit(1)
            
    log_name = "topic_dedup_log.json" if skill == "vc-topic-dedup" else "audience_curator_log.json"
    _append_log(os.path.join(output_dir, log_name), entries)


# === NHOM 1: INIT ===

def _load_atoms_from_file(file_path):
    """Doc danh sach atom paths tu file.
    Ho tro .json (array) va .txt (1 path/dong)."""
    if not os.path.exists(file_path):
        print(f"[ERR] Atoms file khong ton tai: {file_path}")
        sys.exit(1)
    
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(p).strip() for p in data if str(p).strip()]
        else:
            print(f"[ERR] JSON file phai chua array, nhan {type(data).__name__}")
            sys.exit(1)
    else:
        # .txt hoac bat ky: 1 path/dong
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]


def init_batches(atoms_list, batch_size, output_dir, skill):
    """Chia atoms thanh batch files, ghi manifest.
    atoms_list: list cac duong dan atom (da parse)."""
    os.makedirs(output_dir, exist_ok=True)

    # Loc bo _DLQ, Audiences
    atoms = [
        a for a in atoms_list
        if not any(excl in a.replace("\\", "/") for excl in EXCLUDED_DIRS)
    ]
    skipped = len(atoms_list) - len(atoms)
    if skipped > 0:
        print(f"[SKIP] {skipped} atom(s) excluded (_DLQ or Audiences)")

    # Edge case: 0 atoms sau filter
    if len(atoms) == 0:
        manifest = {
            "skill": skill,
            "total_atoms": 0,
            "batch_size": batch_size,
            "batches": []
        }
        _write_manifest(output_dir, manifest)
        print("[INFO] 0 atoms sau filter - khong co batch nao.")
        return

    # Chia batch va ghi tung batch file rieng (embed content)
    batches_meta = []
    actual_atom_count = 0
    for i in range(0, len(atoms), batch_size):
        batch_id = (i // batch_size) + 1
        batch_key = uuid.uuid4().hex[:8]
        batch_atoms = atoms[i:i + batch_size]

        # Doc content cua tung atom
        atoms_with_content = []
        for atom_path in batch_atoms:
            if os.path.exists(atom_path):
                fm_dict, body = _read_md_file(atom_path)
                # Dam bao JSON-serializable (convert date/datetime sang string)
                fm_safe = json.loads(json.dumps(fm_dict, default=str))
                atoms_with_content.append({
                    "atom_path": atom_path,
                    "frontmatter": fm_safe,
                    "body": body.strip()
                })
            else:
                print(f"[WARN] File khong ton tai, skip: {atom_path}")

        if len(atoms_with_content) == 0:
            continue

        batch_file_data = {
            "batch_id": batch_id,
            "batch_key": batch_key,
            "atoms": [a["atom_path"] for a in atoms_with_content],
            "atoms_content": atoms_with_content
        }
        batch_path = os.path.join(output_dir, f"batch_{batch_id:02d}.json")
        _write_json(batch_path, batch_file_data)

        actual_atom_count += len(atoms_with_content)
        batches_meta.append({
            "id": batch_id,
            "status": "pending",
            "atom_count": len(atoms_with_content)
        })

    # Manifest KHONG chua danh sach atoms (chong data leakage)
    manifest = {
        "skill": skill,
        "total_atoms": actual_atom_count,
        "batch_size": batch_size,
        "batches": batches_meta
    }
    _write_manifest(output_dir, manifest)
    print(f"Initialized {len(batches_meta)} batches ({actual_atom_count} atoms) in {output_dir}")


# === NHOM 2: GET-NEXT ===

def _generate_template(batch_data, skill, output_dir):
    """Sinh file results_temp.json voi placeholder cho Agent dien"""
    atoms = batch_data.get("atoms", [])
    batch_key = batch_data.get("batch_key", "")
    items = batch_data.get("items", [])

    if skill == "tag":
        results = [{
            "atom_path": a,
            "action": f"{PLACEHOLDER}: tagged | skipped]",
            "description": f"{PLACEHOLDER}: 1 cau 30-50 tu tieng Viet]",
            "keywords": [f"{PLACEHOLDER}: 8-11 tu khoa khong trung]"],
            "reasoning": f"{PLACEHOLDER}: Giai thich — LLM-CAPTCHA]"
        } for a in atoms]

    elif skill == "dedup":
        results = [{
            "atom_path": a,
            "decision": f"{PLACEHOLDER}: pass | merge]",
            "merge_with": f"{PLACEHOLDER} neu merge: duong dan atom trung lap]",
            "survivor": f"{PLACEHOLDER} neu merge: duong dan atom giu lai]",
            "enriched_content": f"{PLACEHOLDER} neu merge: noi dung body da merge cho survivor]",
            "reasoning": f"{PLACEHOLDER}: Giai thich quyet dinh — LLM-CAPTCHA]"
        } for a in atoms]

    elif skill == "align":
        results = [{
            "atom_path": a,
            "decision": f"{PLACEHOLDER}: linked | orphan | cloned]",
            "parent_path": f"{PLACEHOLDER} neu linked/cloned: duong dan parent atom]",
            "link_type": f"{PLACEHOLDER} neu linked/cloned: insight | knowledge]",
            "audience": f"{PLACEHOLDER} neu linked: audience id]",
            "clone_targets": [f"{PLACEHOLDER} neu cloned: danh sach audience ids, toi da 3]"],
            "reasoning": f"{PLACEHOLDER}: Giai thich quyet dinh — LLM-CAPTCHA]"
        } for a in atoms]

    elif skill == "vc-topic-dedup":
        results = [
            {"action": "[ĐIỀN VÀO ĐÂY: keep | merge]", "topic_id": "[ĐIỀN VÀO ĐÂY: neu keep thi dien id, neu merge thi xoa dong nay]", "loser_id": "[ĐIỀN VÀO ĐÂY: neu merge]", "survivor_id": "[ĐIỀN VÀO ĐÂY: neu merge]"} 
            for _ in items
        ]
    elif skill == "vc-audience-curator":
        results = [
            {"action": "[ĐIỀN VÀO ĐÂY: keep | merge]", "audience_file": "[ĐIỀN VÀO ĐÂY: neu keep thi dien id, neu merge thi xoa dong nay]", "loser_file": "[ĐIỀN VÀO ĐÂY: neu merge]", "survivor_file": "[ĐIỀN VÀO ĐÂY: neu merge]"} 
            for _ in items
        ]

    if skill in ["vc-topic-dedup", "vc-audience-curator"]:
        template = {"decisions": results}
    else:
        template = {"batch_key": batch_key, "results": results}
        
    template_path = os.path.join(output_dir, "results_temp.json")
    _write_json(template_path, template)


def get_next(output_dir):
    """Lay batch tiep theo cho Agent xu ly"""
    manifest = _read_manifest(output_dir)
    if manifest is None:
        print("ALL_DONE")
        return

    skill = manifest.get("skill", "tag")

    for batch_meta in manifest.get("batches", []):
        if batch_meta["status"] == "pending":
            batch_id = batch_meta["id"]
            batch_file = os.path.join(output_dir, f"batch_{batch_id:02d}.json")

            if not os.path.exists(batch_file):
                print(f"[ERR] Khong tim thay file {batch_file}")
                return

            batch_data = _read_json(batch_file)

            # Copy sang current_batch.json
            current_path = os.path.join(output_dir, "current_batch.json")
            _write_json(current_path, batch_data)

            # Sinh template
            _generate_template(batch_data, skill, output_dir)

            total = len(manifest.get("batches", []))
            print(f"Batch {batch_id}/{total} san sang.")
            print(f"Dien ket qua vao {output_dir}/results_temp.json roi goi --submit.")
            return

    _print_skill_summary(output_dir, skill)
    print("ALL_DONE")


# === NHOM 3: VALIDATION ===

def _check_placeholder(data, path=""):
    """Kiem tra de quy xem con placeholder nao khong"""
    if isinstance(data, str):
        if PLACEHOLDER in data:
            return f"Con placeholder tai {path}: '{data[:60]}...'"
    elif isinstance(data, list):
        for i, item in enumerate(data):
            err = _check_placeholder(item, f"{path}[{i}]")
            if err:
                return err
    elif isinstance(data, dict):
        for k, v in data.items():
            err = _check_placeholder(v, f"{path}.{k}")
            if err:
                return err
    return None


def _validate_tag(entries):
    """Validate ket qua auto-tagger"""
    for i, e in enumerate(entries):
        action = e.get("action", "")
        if action not in ("tagged", "skipped"):
            return False, f"Entry {i}: action phai la 'tagged' hoac 'skipped', nhan '{action}'"

        if action == "tagged":
            desc = e.get("description", "")
            kw = e.get("keywords", [])
            reasoning = e.get("reasoning", "")

            word_count = len(desc.split())
            if word_count < 30 or word_count > 50:
                return False, f"Entry {i}: description phai 30-50 tu, hien co {word_count} tu"

            if not isinstance(kw, list) or len(kw) < 8 or len(kw) > 11:
                return False, f"Entry {i}: keywords phai la mang 8-11 items, hien co {len(kw) if isinstance(kw, list) else 0}"

            kw_lower = [k.lower() for k in kw]
            if len(set(kw_lower)) != len(kw_lower):
                return False, f"Entry {i}: keywords co tu khoa trung lap"

            for k in kw:
                if len(k.strip()) < 2:
                    return False, f"Entry {i}: keyword '{k}' qua ngan (< 2 ky tu)"

            if len(reasoning) < 15:
                return False, f"Entry {i}: reasoning phai >= 15 ky tu"

        elif action == "skipped":
            # Verify file thuc su da co metadata
            atom_path = e.get("atom_path", "")
            if os.path.exists(atom_path):
                fm, _ = _read_md_file(atom_path)
                has_desc = bool(fm.get("description"))
                has_kw = bool(fm.get("keywords")) and len(fm.get("keywords", [])) > 0
                if not (has_desc and has_kw):
                    return False, f"Entry {i}: action='skipped' nhung file {atom_path} chua co description hoac keywords"

    return True, ""


def _validate_dedup(entries):
    """Validate ket qua atom-dedup"""
    for i, e in enumerate(entries):
        decision = e.get("decision", "")
        if decision not in ("pass", "merge"):
            return False, f"Entry {i}: decision phai la 'pass' hoac 'merge', nhan '{decision}'"

        if decision == "merge":
            merge_with = e.get("merge_with", "")
            survivor = e.get("survivor", "")
            enriched = e.get("enriched_content", "")
            reasoning = e.get("reasoning", "")

            if not os.path.exists(merge_with):
                return False, f"Entry {i}: merge_with '{merge_with}' khong ton tai tren disk"

            atom_path = e.get("atom_path", "")
            if survivor not in (atom_path, merge_with):
                return False, f"Entry {i}: survivor phai la atom_path hoac merge_with"

            if len(enriched.strip()) < 50:
                return False, f"Entry {i}: enriched_content phai >= 50 ky tu"

            if len(reasoning) < 15:
                return False, f"Entry {i}: reasoning phai >= 15 ky tu"

        elif decision == "pass":
            reasoning = e.get("reasoning", "")
            if len(reasoning) < 15:
                return False, f"Entry {i}: reasoning phai >= 15 ky tu"

    return True, ""


def _validate_align(entries):
    """Validate ket qua atom-linker"""
    for i, e in enumerate(entries):
        decision = e.get("decision", "")
        if decision not in ("linked", "orphan", "cloned"):
            return False, f"Entry {i}: decision phai la 'linked', 'orphan', hoac 'cloned', nhan '{decision}'"

        reasoning = e.get("reasoning", "")
        if len(reasoning) < 15:
            return False, f"Entry {i}: reasoning phai >= 15 ky tu"

        if decision in ("linked", "cloned"):
            parent = e.get("parent_path", "")
            link_type = e.get("link_type", "")

            if not os.path.exists(parent):
                return False, f"Entry {i}: parent_path '{parent}' khong ton tai tren disk"

            if link_type not in ("insight", "knowledge"):
                return False, f"Entry {i}: link_type phai la 'insight' hoac 'knowledge'"

        if decision == "linked":
            audience = e.get("audience", "")
            if not audience.strip():
                return False, f"Entry {i}: audience khong duoc rong"

        if decision == "cloned":
            targets = e.get("clone_targets", [])
            if not isinstance(targets, list) or len(targets) < 1 or len(targets) > 3:
                return False, f"Entry {i}: clone_targets phai la mang 1-3 items"
            for t in targets:
                if not t.strip():
                    return False, f"Entry {i}: clone_targets chua item rong"

    return True, ""


# === NHOM 4: EXECUTION ===

def _execute_tag(entries, output_dir):
    """Ghi description + keywords vao YAML frontmatter cua tung atom"""
    for e in entries:
        if e.get("action") != "tagged":
            continue

        atom_path = e["atom_path"]
        if not os.path.exists(atom_path):
            print(f"[WARN] File {atom_path} khong ton tai, bo qua")
            continue

        fm, body = _read_md_file(atom_path)
        fm["description"] = e["description"]
        fm["keywords"] = e["keywords"]
        _write_md_file(atom_path, fm, body)

    # Append vao log
    log_path = os.path.join(output_dir, "tag_log.json")
    _append_log(log_path, entries)
    print(f"[TAG] Da ghi metadata cho {sum(1 for e in entries if e.get('action') == 'tagged')} atom(s)")


def _get_protected_atoms():
    protected = []
    personas_dir = os.path.join(os.getcwd(), "personas")
    if os.path.exists(personas_dir):
        for root, _, files in os.walk(personas_dir):
            if 'pillars.yaml' in files:
                try:
                    with open(os.path.join(root, 'pillars.yaml'), 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f) or {}
                        for p_val in data.values():
                            if isinstance(p_val, dict) and 'insights' in p_val:
                                for insight in p_val['insights']:
                                    ref = insight.get('file_ref', '')
                                    if ref:
                                        protected.append(ref.replace('[[', '').replace(']]', ''))
                except:
                    pass
    return protected

def _execute_dedup(entries, output_dir):
    """Thuc thi merge cho cac entry decision=merge"""
    protected_atoms = _get_protected_atoms()
    merge_count = 0
    for e in entries:
        if e.get("decision") != "merge":
            continue

        atom_path = e["atom_path"]
        merge_with = e["merge_with"]
        survivor = e["survivor"]

        # Safety check: file co the da bi xoa boi entry truoc trong cung batch
        if not os.path.exists(atom_path) or not os.path.exists(merge_with):
            print(f"[SKIP] File da bi xu ly boi entry truoc trong batch, bo qua: {atom_path}")
            continue

        loser = atom_path if survivor != atom_path else merge_with

        # AUTO-SWAP logic for protected insights
        loser_base = os.path.basename(loser).replace('.md', '')
        survivor_base = os.path.basename(survivor).replace('.md', '')

        if loser_base in protected_atoms:
            if survivor_base in protected_atoms:
                print(f"[ERR] Both atoms {loser_base} and {survivor_base} are Core Insights. Cannot merge.")
                sys.exit(1)
            print(f"[AUTO-SWAP] {loser_base} is protected. Swapping survivor.")
            survivor, loser = loser, survivor
            e["survivor"] = survivor

        # Buoc 1: Redirect links (an toan nhat — neu crash, chi link bi doi)
        subprocess.run([
            sys.executable, ".agents/scripts/patch-semantics.py",
            "--action", "redirect",
            "--old-target", loser,
            "--new-target", survivor
        ], check=False)

        # Buoc 2: Enrich survivor (giu frontmatter, thay body)
        fm, _ = _read_md_file(survivor)
        _write_md_file(survivor, fm, e["enriched_content"])

        # Buoc 3: Xoa loser
        if os.path.exists(loser):
            os.remove(loser)
            print(f"[MERGE] {os.path.basename(loser)} -> {os.path.basename(survivor)}")

        merge_count += 1

    # Append vao log
    log_path = os.path.join(output_dir, "dedup_log.json")
    _append_log(log_path, entries)
    print(f"[DEDUP] Da merge {merge_count} cap atom(s)")


def _execute_align(entries, output_dir):
    """Thuc thi link/orphan/clone cho cac entry"""
    pending_reframes = []

    for e in entries:
        atom_path = e["atom_path"]
        decision = e["decision"]

        if decision == "linked":
            subprocess.run([
                sys.executable, ".agents/scripts/patch-semantics.py",
                "--action", "add",
                "--source", atom_path,
                "--target", e["parent_path"],
                "--link-type", e["link_type"]
            ], check=False)
            print(f"[LINK] {os.path.basename(atom_path)} -> {os.path.basename(e['parent_path'])}")

        elif decision == "orphan":
            if os.path.exists(atom_path):
                fm, body = _read_md_file(atom_path)
                fm["status"] = "orphan"
                _write_md_file(atom_path, fm, body)
                print(f"[ORPHAN] {os.path.basename(atom_path)}")

        elif decision == "cloned":
            # Link ban goc truoc
            subprocess.run([
                sys.executable, ".agents/scripts/patch-semantics.py",
                "--action", "add",
                "--source", atom_path,
                "--target", e["parent_path"],
                "--link-type", e["link_type"]
            ], check=False)

            # Tao clone cho moi audience
            basename = os.path.splitext(os.path.basename(atom_path))[0]
            parent_dir = os.path.dirname(atom_path)

            for aud_id in e.get("clone_targets", []):
                clone_name = f"{basename}__{aud_id}.md"
                clone_path = os.path.join(parent_dir, clone_name).replace("\\", "/")
                shutil.copy2(atom_path, clone_path)

                subprocess.run([
                    sys.executable, ".agents/scripts/patch-semantics.py",
                    "--action", "add",
                    "--source", clone_path,
                    "--target", e["parent_path"],
                    "--link-type", e["link_type"]
                ], check=False)

                pending_reframes.append({
                    "clone_path": clone_path,
                    "source_path": atom_path,
                    "target_audience": aud_id
                })
                print(f"[CLONE] {clone_name} cho audience {aud_id}")

    # Ghi pending_reframe.json neu co clones
    if pending_reframes:
        reframe_path = os.path.join(output_dir, "pending_reframe.json")
        # Append vao file hien co (nhieu batch co the sinh clones)
        _append_log(reframe_path, pending_reframes)

    # Append vao log
    log_path = os.path.join(output_dir, "align_log.json")
    _append_log(log_path, entries)
    linked = sum(1 for e in entries if e["decision"] == "linked")
    orphaned = sum(1 for e in entries if e["decision"] == "orphan")
    cloned = sum(1 for e in entries if e["decision"] == "cloned")
    print(f"[ALIGN] linked={linked}, orphan={orphaned}, cloned={cloned}")


# === NHOM 5: SUBMIT ===

def submit_results(output_dir, results_file):
    """Validate va execute ket qua tu Agent"""
    manifest = _read_manifest(output_dir)
    if manifest is None:
        print("[ERR] Khong tim thay manifest")
        sys.exit(1)

    skill = manifest.get("skill", "tag")

    # Doc current batch
    current_path = os.path.join(output_dir, "current_batch.json")
    if not os.path.exists(current_path):
        print("[ERR] Khong tim thay current_batch.json. Hay goi --get-next truoc.")
        sys.exit(1)

    batch_data = _read_json(current_path)
    batch_id = batch_data["batch_id"]
    
    is_meta_dedup = skill in ["vc-topic-dedup", "vc-audience-curator"]
    if is_meta_dedup:
        expected_key = None
        expected_atoms = [item["id"] for item in batch_data.get("items", [])]
    else:
        expected_key = batch_data.get("batch_key")
        expected_atoms = batch_data.get("atoms", [])

    # Doc results
    try:
        results_data = _read_json(results_file)
    except Exception as e:
        print(f"[ERR] Loi doc results file: {e}")
        sys.exit(1)

    entries = results_data.get("results", []) if not is_meta_dedup else results_data.get("decisions", [])

    # === VALIDATE CHUNG ===

    # 1. Batch key
    if not is_meta_dedup and results_data.get("batch_key") != expected_key:
        print(f"FAIL: batch_key khong khop (expected={expected_key})")
        return

    # 2. Coverage
    if len(entries) != len(expected_atoms):
        print(f"FAIL: So entries ({len(entries)}) khac so atoms trong batch ({len(expected_atoms)})")
        return

    if is_meta_dedup:
        submitted_paths = [e.get("topic_id", e.get("loser_id", e.get("audience_file", e.get("loser_file", "")))) for e in entries]
    else:
        submitted_paths = [e.get("atom_path", "") for e in entries]
        
    for atom in expected_atoms:
        if atom not in submitted_paths:
            print(f"FAIL: Thieu entry cho atom: {atom}")
            return

    # 3. Placeholder check
    if not is_meta_dedup:
        placeholder_err = _check_placeholder(entries)
        if placeholder_err:
            print(f"FAIL: {placeholder_err}")
            return

    # === VALIDATE RIENG THEO SKILL ===
    validators = {
        "tag": _validate_tag,
        "dedup": _validate_dedup,
        "align": _validate_align,
        "vc-topic-dedup": _validate_meta_dedup,
        "vc-audience-curator": _validate_meta_dedup
    }
    validator = validators.get(skill)
    if not validator:
        print(f"[ERR] Skill '{skill}' khong hop le")
        sys.exit(1)

    ok, err_msg = validator(entries)
    if not ok:
        print(f"FAIL: {err_msg}")
        return

    # === EXECUTE ===
    executors = {
        "tag": _execute_tag,
        "dedup": _execute_dedup,
        "align": _execute_align,
        "vc-topic-dedup": _execute_meta_dedup,
        "vc-audience-curator": _execute_meta_dedup
    }
    executor = executors[skill]
    executor(entries, output_dir)

    # === MARK DONE ===
    for b in manifest["batches"]:
        if b["id"] == batch_id:
            b["status"] = "done"
            break
    _write_manifest(output_dir, manifest)

    # === CLEANUP ===
    if os.path.exists(current_path):
        os.remove(current_path)
    if os.path.exists(results_file):
        os.remove(results_file)

    print(f"PASS: Batch {batch_id} hoan tat.")

    # === SESSION_BREAK CHECK ===
    done_count = sum(1 for b in manifest["batches"] if b["status"] == "done")
    pending_count = sum(1 for b in manifest["batches"] if b["status"] == "pending")
    total = len(manifest["batches"])

    if pending_count > 0 and done_count % SESSION_BATCH_LIMIT == 0:
        skill_name = SKILL_NAME_MAP.get(skill, skill)

        # Doc pipeline context tu parent dir (neu co)
        parent_dir = os.path.dirname(output_dir.rstrip("/\\"))
        pipeline_ctx_path = os.path.join(parent_dir, "pipeline_context.json")
        pipeline_ctx = None
        if os.path.exists(pipeline_ctx_path):
            pipeline_ctx = _read_json(pipeline_ctx_path)

        print(f"\nSESSION_BREAK")
        print(f"Da xu ly {done_count}/{total} batches. Con {pending_count} batches.")
        print(f"Dung lai. Copy prompt ben duoi sang conversation moi:\n")
        print(f"---")

        if pipeline_ctx:
            mode = pipeline_ctx.get("mode", "?")
            atoms_file = pipeline_ctx.get("atoms_file", "?")
            root_dir = pipeline_ctx.get("root_output_dir", parent_dir)
            print(f"@vault-curator tiep tuc pipeline `{mode}`.")
            print(f"- Mode: {mode}")
            print(f"- Buoc hien tai: {skill} (doc SKILL {skill_name})")
            print(f"- Output dir skill: {output_dir}")
            print(f"- Root output dir: {root_dir}")
            print(f"- Atoms file: {atoms_file}")
            print(f"- Trang thai: {done_count}/{total} batches done")
            print(f"")
            print(f"Dua vao Mode: {mode}, doc AGENT.md routing logic de biet buoc tiep theo sau ALL_DONE.")
            print(f"Goi `--get-next --output-dir \"{output_dir}\"` va xu ly batch theo SKILL. Lap den khi ALL_DONE hoac SESSION_BREAK.")
        else:
            print(f"@vault-curator tiep tuc xu ly. Batch system da duoc khoi tao san.")
            print(f"- Skill: {skill} (doc SKILL {skill_name})")
            print(f"- Output dir: {output_dir}")
            print(f"- Trang thai: {done_count}/{total} batches done")
            print(f"")
            print(f"Goi `--get-next --output-dir \"{output_dir}\"` va xu ly batch theo SKILL. Lap den khi ALL_DONE hoac SESSION_BREAK.")

        print(f"---")


# === NHOM 6: STATUS ===

def print_status(output_dir):
    """Hien thi tien trinh batch"""
    manifest = _read_manifest(output_dir)
    if manifest is None:
        print("No manifest found.")
        return

    batches = manifest.get("batches", [])
    total_batches = len(batches)
    done_batches = sum(1 for b in batches if b["status"] == "done")
    total_atoms = manifest.get("total_atoms", 0)
    done_atoms = sum(b.get("atom_count", 0) for b in batches if b["status"] == "done")

    print(f"Skill: {manifest.get('skill', '?')}")
    print(f"Done: {done_batches}/{total_batches} batches ({done_atoms}/{total_atoms} atoms)")


# === NHOM 7: MAIN ===

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage curation batches (anti-cheat)")
    parser.add_argument('--init', action='store_true', help="Khoi tao batch")
    parser.add_argument('--get-next', action='store_true', help="Lay batch tiep theo")
    parser.add_argument('--submit', action='store_true', help="Submit ket qua (thay mark-done)")
    parser.add_argument('--status', action='store_true', help="Xem tien trinh")

    parser.add_argument('--skill', choices=['tag', 'dedup', 'align', 'vc-topic-dedup', 'vc-audience-curator'],
                        help="Loai skill (bat buoc cho --init)")
    parser.add_argument('--meta-source', type=str,
                        help="Duong dan den file topic_map hoac _audience_index")
    parser.add_argument('--atoms', type=str, default="",
                        help="Danh sach atom paths, phan tach bang dau phay")
    parser.add_argument('--atoms-file', type=str,
                        help="File chua danh sach atom paths (.json array hoac .txt 1 path/dong). Dung thay --atoms khi danh sach dai.")
    parser.add_argument('--batch-size', type=int, default=10)
    parser.add_argument('--results-file', type=str,
                        help="Duong dan file ket qua (bat buoc cho --submit)")
    parser.add_argument('--output-dir', type=str, required=True,
                        help="Thu muc luu trang thai batch")

    args = parser.parse_args()

    if args.init:
        if not args.skill:
            print("[ERR] --init requires --skill")
            sys.exit(1)
            
        if args.skill in ["vc-topic-dedup", "vc-audience-curator"]:
            if not getattr(args, 'meta_source', None):
                print("[ERR] --init cho skill nay requires --meta-source")
                sys.exit(1)
            init_meta_dedup_batches(args.skill, args.meta_source, args.batch_size, args.output_dir)
            sys.exit(0)
        # Chon nguon atoms: --atoms-file uu tien hon --atoms
        if args.atoms_file:
            atoms_list = _load_atoms_from_file(args.atoms_file)
        elif args.atoms:
            atoms_list = [a.strip() for a in args.atoms.split(',') if a.strip()]
        else:
            print("[ERR] --init requires --atoms or --atoms-file")
            sys.exit(1)
        init_batches(atoms_list, args.batch_size, args.output_dir, args.skill)
    elif args.get_next:
        get_next(args.output_dir)
    elif args.submit:
        if not args.results_file:
            print("[ERR] --submit requires --results-file")
            sys.exit(1)
        submit_results(args.output_dir, args.results_file)
    elif args.status:
        print_status(args.output_dir)
    else:
        parser.print_help()
