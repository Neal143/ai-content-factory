"""
generate_coverage_preview.py
Last update: 17/08/2026 20:55 (GMT+7)
Vai tro: Tu dong tao duy nhat bang Markdown preview audience-knowledge-coverage-preview.md.
Su dung khi: Chay tu dong khi co thay doi Atoms tren Obsidian hoac duoc goi boi safe_rename / factory-sync.
Output: File vault/03-Content/Content Plan/audience-knowledge-coverage-preview.md duoc cap nhat ngay lap tuc.
Tom tat logic: Tu dong phat hien Persona dang hoat dong trong personas/ (0% hardcode), tinh toan va xuat bang Markdown.
"""

import os
import sys
import re
import yaml
import urllib.parse
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# -------------------------------------------------------------
# DYNAMIC PATH & PERSONA DISCOVERY
# -------------------------------------------------------------
def get_factory_root(override_root=None):
    if override_root and os.path.exists(os.path.join(override_root, "vault")):
        return os.path.abspath(override_root)
    curr = os.path.dirname(os.path.abspath(__file__))
    while curr and os.path.dirname(curr) != curr:
        if os.path.exists(os.path.join(curr, "vault")) and os.path.exists(os.path.join(curr, "personas")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

def get_active_persona_dir(factory_root):
    personas_root = os.path.join(factory_root, "personas")
    if not os.path.exists(personas_root):
        return None
    subdirs = [
        d for d in os.listdir(personas_root)
        if os.path.isdir(os.path.join(personas_root, d)) and not d.startswith(('.', '_'))
    ]
    return os.path.join(personas_root, subdirs[0]) if subdirs else None

def clean_ref(ref_str):
    if not ref_str:
        return ""
    s = str(ref_str).strip()
    s = re.sub(r"^\[\[(.*)\]\]$", r"\1", s)
    return s.strip()

def parse_frontmatter(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            content = f.read()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                data = yaml.safe_load(parts[1])
                return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}

# -------------------------------------------------------------
# MAIN BUILD LOGIC
# -------------------------------------------------------------
def build_preview(factory_root):
    vault_dir = os.path.join(factory_root, "vault")
    persona_dir = get_active_persona_dir(factory_root)
    
    if not persona_dir or not os.path.exists(persona_dir):
        print(f"[ERR] Không tìm thấy thư mục Persona trong: {os.path.join(factory_root, 'personas')}")
        return False

    persona_name = os.path.basename(persona_dir)
    aud_dir = os.path.join(vault_dir, "01-Atomic", "Audiences")
    ins_dir = os.path.join(vault_dir, "01-Atomic", "Insights")
    con_dir = os.path.join(vault_dir, "01-Atomic", "Concepts")
    sol_dir = os.path.join(vault_dir, "01-Atomic", "Solutions")
    quo_dir = os.path.join(vault_dir, "01-Atomic", "Quotes")
    sto_dir = os.path.join(vault_dir, "01-Atomic", "Stories")
    dat_dir = os.path.join(vault_dir, "01-Atomic", "Data-Points")
    prod_log_path = os.path.join(vault_dir, ".content-pipeline", "logs", "production-log.md")
    topic_map_path = os.path.join(persona_dir, "topic_map.yaml")
    aud_index_path = os.path.join(aud_dir, "_audience_index.yaml")
    
    out_dir = os.path.join(vault_dir, "03-Content", "Content Plan")
    os.makedirs(out_dir, exist_ok=True)
    out_md_path = os.path.join(out_dir, "audience-knowledge-coverage-preview.md")

    # 1. Load Audiences Index
    audiences_index_data = []
    if os.path.exists(aud_index_path):
        try:
            with open(aud_index_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                idx_yaml = yaml.safe_load(f)
                if isinstance(idx_yaml, dict) and "audiences" in idx_yaml:
                    audiences_index_data = idx_yaml["audiences"]
        except Exception:
            pass

    # 2. Load Audiences Files
    aud_files = {}
    if os.path.exists(aud_dir):
        for fname in os.listdir(aud_dir):
            if fname.endswith(".md") and not fname.startswith("_"):
                base = fname[:-3]
                fpath = os.path.join(aud_dir, fname)
                fm = parse_frontmatter(fpath)
                parents = [clean_ref(p) for p in (fm.get("parent_audience") or [])]
                level = fm.get("audience_level", "little")
                aliases = fm.get("aliases") or []
                aud_files[base] = {
                    "parents": parents,
                    "level": level,
                    "aliases": aliases,
                    "filename": fname,
                    "rel_path": f"01-Atomic/Audiences/{fname}"
                }

    # 3. Load Topics
    topics = []
    if os.path.exists(topic_map_path):
        try:
            with open(topic_map_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                t_yaml = yaml.safe_load(f)
                if isinstance(t_yaml, dict):
                    topics = t_yaml.get("topics", [])
        except Exception:
            pass

    # 4. Load Production Log
    prod_counts = {}
    if os.path.exists(prod_log_path):
        try:
            with open(prod_log_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                prod_text = f.read()
            topic_matches = re.findall(r'-\s+\*\*Topic\*\*:\s*["\']?([^"\'\n\r]+)["\']?', prod_text)
            for t in topic_matches:
                t_clean = t.strip()
                prod_counts[t_clean] = prod_counts.get(t_clean, 0) + 1
        except Exception:
            pass

    # 5. Load Insights
    insights = {}
    if os.path.exists(ins_dir):
        for fname in os.listdir(ins_dir):
            if fname.endswith(".md"):
                fpath = os.path.join(ins_dir, fname)
                fm = parse_frontmatter(fpath)
                base = fname[:-3]
                t_list = fm.get("topics") or []
                aud_list = [clean_ref(a) for a in (fm.get("belongs_to_audience") or [])]
                insights[base] = {
                    "filename": fname,
                    "topics": t_list,
                    "audiences": aud_list
                }

    # 6. Load Knowledge (Concepts & Solutions)
    knowledges = {}
    for d_path in [con_dir, sol_dir]:
        if os.path.exists(d_path):
            for fname in os.listdir(d_path):
                if fname.endswith(".md"):
                    fpath = os.path.join(d_path, fname)
                    fm = parse_frontmatter(fpath)
                    base = fname[:-3]
                    supp_ins = [clean_ref(x) for x in (fm.get("supports_insight") or [])]
                    knowledges[base] = {"supports_insight": supp_ins}

    # 7. Load Evidences (Quotes, Stories, Data)
    evidences = {}
    for d_path in [quo_dir, sto_dir, dat_dir]:
        if os.path.exists(d_path):
            for fname in os.listdir(d_path):
                if fname.endswith(".md"):
                    fpath = os.path.join(d_path, fname)
                    fm = parse_frontmatter(fpath)
                    base = fname[:-3]
                    supp_k = [clean_ref(x) for x in (fm.get("supports_knowledge") or [])]
                    evidences[base] = {"supports_knowledge": supp_k}

    aud_to_topics = {}
    for t in topics:
        t_id = t.get("id")
        t_label = t.get("label", t_id)
        t_auds = t.get("belongs_to_audience", [])
        if isinstance(t_auds, str):
            t_auds = [t_auds]
        for a in t_auds:
            aud_to_topics.setdefault(clean_ref(a), []).append({"id": t_id, "label": t_label})

    def format_aud_link(aud_ref):
        if not aud_ref or aud_ref == "-":
            return "-"
        target_name = aud_ref
        if not target_name.endswith(".md"):
            target_name += ".md"
        
        matched_filename = None
        if os.path.exists(os.path.join(aud_dir, target_name)):
            matched_filename = target_name
        else:
            for b_name, info in aud_files.items():
                if aud_ref == b_name or aud_ref in info["aliases"] or aud_ref == info["filename"]:
                    matched_filename = info["filename"]
                    break
                    
        if matched_filename:
            base = matched_filename[:-3]
            encoded_file = urllib.parse.quote(matched_filename)
            return f"[{base}](../../01-Atomic/Audiences/{encoded_file})"
            
        encoded_ref = urllib.parse.quote(target_name)
        return f"[{aud_ref}](../../01-Atomic/Audiences/{encoded_ref})"

    rows = []
    aud_idx = 1
    aud_list_source = audiences_index_data if audiences_index_data else [{"id": k, "file_ref": k} for k in aud_files.keys()]

    for item in aud_list_source:
        file_ref = clean_ref(item.get("file_ref", item.get("id", "")))
        aud_id = clean_ref(item.get("id", ""))
        
        aud_name = file_ref if file_ref in aud_files else aud_id
        aud_data = aud_files.get(aud_name, aud_files.get(file_ref, {}))
        
        level = aud_data.get("level", item.get("audience_level", "little"))
        parents = aud_data.get("parents", [])
        if not parents:
            parent_raw = item.get("parent_audience", [])
            if isinstance(parent_raw, list):
                parents = [clean_ref(p) for p in parent_raw]
            elif parent_raw:
                parents = [clean_ref(parent_raw)]
                
        parent_link = format_aud_link(parents[0]) if parents else "-"
        aud_link = format_aud_link(aud_name)
        
        matching_topics = []
        candidates = set([file_ref, aud_id, aud_name])
        if aud_data.get("aliases"):
            candidates.update(aud_data["aliases"])
        if item.get("aliases"):
            candidates.update(item["aliases"])
            
        for c in candidates:
            if c in aud_to_topics:
                matching_topics.extend(aud_to_topics[c])
                
        unique_topics = []
        seen_t = set()
        for t in matching_topics:
            if t["id"] not in seen_t:
                seen_t.add(t["id"])
                unique_topics.append(t)
                
        if not unique_topics:
            rows.append({
                "stt": f"**{aud_idx}**",
                "audience": aud_link,
                "level": f"`{level}`",
                "parent": parent_link,
                "topic": "-",
                "posts": 0,
                "insights": 0,
                "knowledges": 0,
                "evidences": 0
            })
            aud_idx += 1
            continue

        for i, t in enumerate(unique_topics):
            t_id = t["id"]
            t_label = t["label"]
            t_display = f"`{t_id}` (*{t_label}*)"
            
            p_count = prod_counts.get(t_id, 0)
            ins_count = sum(1 for ins in insights.values() if t_id in ins.get("topics", []))
            
            ins_keys = [k for k, ins in insights.items() if t_id in ins.get("topics", [])]
            matched_k = [k for k, kn in knowledges.items() if any(i in kn.get("supports_insight", []) for i in ins_keys)]
            k_count = len(matched_k)
            
            e_count = sum(1 for ev in evidences.values() if any(k in ev.get("supports_knowledge", []) for k in matched_k))
            
            if i == 0:
                rows.append({
                    "stt": f"**{aud_idx}**",
                    "audience": aud_link,
                    "level": f"`{level}`",
                    "parent": parent_link,
                    "topic": t_display,
                    "posts": p_count,
                    "insights": ins_count,
                    "knowledges": k_count,
                    "evidences": e_count
                })
            else:
                rows.append({
                    "stt": "-",
                    "audience": "-",
                    "level": "-",
                    "parent": "-",
                    "topic": t_display,
                    "posts": p_count,
                    "insights": ins_count,
                    "knowledges": k_count,
                    "evidences": e_count
                })
        aud_idx += 1

    md_content = f"""# 📊 Ma Trận Phủ Kiến Thức Persona ({persona_name})

<!--
- File name: audience-knowledge-coverage-preview.md
- Last update: Auto-generated by generate_coverage_preview.py
- Vai tro: Bang preview ma tran phu tri thuc giua Audiences, Topics va cac Atoms.
-->

> [!NOTE]
> - **Tổng số Audiences:** Đúng **{aud_idx - 1} Audiences** (đánh số thứ tự từ **1 đến {aud_idx - 1}** ở cột STT).
> - **Mỗi dòng là 1 Topic:** Hiển thị số lượng bài viết, Insights, Concepts và Evidences.
> - **Cột 2 & Cột 4:** Định dạng relative link để hover mở popup và chỉnh sửa trực tiếp nội dung trong Obsidian.

| STT | Audience (Cột 1) | Level (Cột 2) | Parent Audience (Cột 3) | Topic (Cột 4) | Posts Count (Cột 5) | Insights (Cột 6) | Concepts & Solutions (Cột 7) | Evidences: Quotes, Stories, Data (Cột 8) |
|:---:|---|:---:|---|---|:---:|:---:|:---:|:---:|
"""
    for r in rows:
        md_content += f"| {r['stt']} | {r['audience']} | {r['level']} | {r['parent']} | {r['topic']} | {r['posts']} | {r['insights']} | {r['knowledges']} | {r['evidences']} |\n"

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[OK] Generated Markdown Table: {out_md_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Audience Knowledge Coverage Markdown Table.")
    parser.add_argument("--factory-root", default=None, help="Path to Content Factory root directory")
    args = parser.parse_args()
    
    root = get_factory_root(args.factory_root)
    build_preview(root)
