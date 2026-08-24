"""
generate_coverage_preview.py
Last update: 18/08/2026 22:30 (GMT+7)
Vai tro: Script me (Orchestrator & Data Aggregator) thu thap, chuan hoa toan bo du lieu Ma tran phu tri thuc tu Vault & Persona, sau do dieu phoi cac Renderer Modules con xuat file.
Su dung khi:
  - Duoc goi boi factory-sync Obsidian plugin (khi vault co file sua/tao/xoa hoac layout ready).
  - Duoc goi boi safe_rename.py sau khi doi ten file xong de refresh toan bo artifacts.
  - Chay doc lap qua CLI: python generate_coverage_preview.py [--factory-root <path>]
Output:
  - Goi renderers.render_coverage_markdown -> vault/03-Content/Content Plan/audience-knowledge-coverage-preview.md.
Tom tat logic hoat dong:
  1. Tu dong phat hien Workspace Root va Persona dang hoat dong trong personas/ (0% hardcode).
  2. Doc va chuan hoa toan bo du lieu Audiences (kem aliases, parents, level), Topics tu topic_map.yaml va Insights, Knowledges, Evidences, va Production Log.
  3. Dong goi thanh Data Context chuan va truyen cho cac Renderer Modules con thuc thi.
"""

import os
import sys
import re
import yaml
import argparse

# Dam bao UTF-8 I/O tren Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Them thu muc hien tai vao sys.path de import renderers de dang
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from renderers import render_coverage_markdown
from renderers import render_vault_health

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
# CORE DATA COLLECTOR & AGGREGATOR
# -------------------------------------------------------------
def collect_coverage_data(factory_root):
    vault_dir = os.path.join(factory_root, "vault")
    persona_dir = get_active_persona_dir(factory_root)
    
    if not persona_dir or not os.path.exists(persona_dir):
        print(f"[ERR] Khong tim thay thu muc Persona trong: {os.path.join(factory_root, 'personas')}")
        return None

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

    # 1. Load Audiences Index Aliases
    index_aliases_map = {}
    if os.path.exists(aud_index_path):
        try:
            with open(aud_index_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                idx_yaml = yaml.safe_load(f)
                if isinstance(idx_yaml, dict) and "audiences" in idx_yaml:
                    for a_item in idx_yaml["audiences"]:
                        f_ref = clean_ref(a_item.get("file_ref", ""))
                        a_aliases = a_item.get("aliases") or []
                        if f_ref:
                            index_aliases_map.setdefault(f_ref, set()).update(a_aliases + [f_ref])
        except Exception:
            pass

    # 2. Load Topics from topic_map.yaml
    topics = []
    topic_label_map = {}
    if os.path.exists(topic_map_path):
        try:
            with open(topic_map_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                t_yaml = yaml.safe_load(f)
                if isinstance(t_yaml, dict):
                    topics = t_yaml.get("topics", [])
                    topic_label_map = {t["id"]: t.get("label", t["id"]) for t in topics}
        except Exception:
            pass

    tm_aud_to_topic = {}
    for t in topics:
        t_id = t.get("id")
        t_label = t.get("label", t_id)
        t_auds = t.get("belongs_to_audience", [])
        if isinstance(t_auds, str):
            t_auds = [t_auds]
        for a in t_auds:
            tm_aud_to_topic.setdefault(clean_ref(a), []).append({"id": t_id, "label": t_label})

    # 3. Load Insights & map topic associations per audience
    insights = {}
    aud_topic_ins_map = {} # aud -> set(topic_ids)
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
                    "audiences": aud_list,
                    "source_type": fm.get("source_type", ""),
                    "insight_type": fm.get("insight_type") or fm.get("subtype") or "-",
                    "created": fm.get("created", "N/A")
                }
                for a in aud_list:
                    for t in t_list:
                        aud_topic_ins_map.setdefault(a, set()).add(t)

    # 4. Load Audience Files & match topics comprehensively
    audiences = {}
    if os.path.exists(aud_dir):
        for fname in sorted(os.listdir(aud_dir)):
            if fname.endswith(".md") and not fname.startswith("_"):
                base = fname[:-3]
                fpath = os.path.join(aud_dir, fname)
                fm = parse_frontmatter(fpath)
                
                raw_parents = fm.get("parent_audience") or []
                if isinstance(raw_parents, str):
                    raw_parents = [raw_parents]
                parents = [clean_ref(p) for p in raw_parents if clean_ref(p)]
                
                level = str(fm.get("audience_level", "little")).lower()
                performer = fm.get("audience_Job_performer", "Cha mẹ")
                main_job = fm.get("audience_main_job", "")
                circumstance = fm.get("audience_circumstance", "")
                aliases = list(fm.get("aliases") or [])
                
                if base in index_aliases_map:
                    aliases.extend(list(index_aliases_map[base]))
                
                candidates = set([base, fname] + aliases)
                
                # Match from topic_map.yaml
                matching_topics = []
                for c in candidates:
                    if c in tm_aud_to_topic:
                        matching_topics.extend(tm_aud_to_topic[c])
                
                # Match from Insights
                for c in candidates:
                    if c in aud_topic_ins_map:
                        for t_id in aud_topic_ins_map[c]:
                            matching_topics.append({
                                "id": t_id,
                                "label": topic_label_map.get(t_id, t_id)
                            })
                        
                unique_topics = []
                seen_t = set()
                for t in matching_topics:
                    if t["id"] not in seen_t:
                        seen_t.add(t["id"])
                        unique_topics.append(t)

                audiences[base] = {
                    "base": base,
                    "filename": fname,
                    "level": level,
                    "parents": parents,
                    "performer": performer,
                    "main_job": main_job,
                    "circumstance": circumstance,
                    "aliases": list(candidates),
                    "matched_topics": unique_topics
                }

    # 5. Load Production Log
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

    # 6. Load Knowledges (Concepts & Solutions)
    knowledges = {}
    for d_path, k_type in [(con_dir, "concept"), (sol_dir, "solution")]:
        if os.path.exists(d_path):
            for fname in os.listdir(d_path):
                if fname.endswith(".md"):
                    fpath = os.path.join(d_path, fname)
                    fm = parse_frontmatter(fpath)
                    base = fname[:-3]
                    raw_sup = fm.get("supports_insight") or fm.get("supports_to_insight") or []
                    if isinstance(raw_sup, str):
                        raw_sup = [raw_sup]
                    sup_ins = [clean_ref(x) for x in raw_sup]
                    raw_topics = fm.get("topics") or []
                    if isinstance(raw_topics, str):
                        raw_topics = [raw_topics]
                    t_list = [clean_ref(t) for t in raw_topics if clean_ref(t)]
                    knowledges[base] = {
                        "filename": fname,
                        "type": k_type,
                        "topics": t_list,
                        "supports_insight": sup_ins,
                        "source_type": fm.get("source_type", ""),
                        "subtype": fm.get("subtype") or "-",
                        "created": fm.get("created", "N/A")
                    }

    # 7. Load Evidences (Quotes, Stories, Data-Points)
    evidences = {}
    for d_path, e_type in [(quo_dir, "quote"), (sto_dir, "story"), (dat_dir, "data_point")]:
        if os.path.exists(d_path):
            for fname in os.listdir(d_path):
                if fname.endswith(".md"):
                    fpath = os.path.join(d_path, fname)
                    fm = parse_frontmatter(fpath)
                    base = fname[:-3]
                    supp_k = [clean_ref(x) for x in (fm.get("supports_knowledge") or [])]
                    raw_topics = fm.get("topics") or []
                    if isinstance(raw_topics, str):
                        raw_topics = [raw_topics]
                    t_list = [clean_ref(t) for t in raw_topics if clean_ref(t)]
                    evidences[base] = {
                        "filename": fname,
                        "type": e_type,
                        "topics": t_list,
                        "supports_knowledge": supp_k,
                        "source_type": fm.get("source_type", ""),
                        "subtype": fm.get("subtype") or "-",
                        "created": fm.get("created", "N/A")
                    }

    return {
        "factory_root": factory_root,
        "persona_dir": persona_dir,
        "persona_name": persona_name,
        "audiences": audiences,
        "topics": topics,
        "aud_to_topics": tm_aud_to_topic,
        "insights": insights,
        "knowledges": knowledges,
        "evidences": evidences,
        "prod_counts": prod_counts
    }

# -------------------------------------------------------------
# ORCHESTRATION PIPELINE
# -------------------------------------------------------------
def run_pipeline(factory_root=None):
    root = get_factory_root(factory_root)
    data_context = collect_coverage_data(root)
    if not data_context:
        return False
    
    # 1. Render Markdown Preview Table
    success_md = render_coverage_markdown.render(data_context)
    
    # 2. Render Vault Health Dashboard
    success_health = render_vault_health.render(data_context)
    
    return success_md and success_health

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coverage Engine Orchestrator")
    parser.add_argument("--factory-root", default=None, help="Path to Content Factory root directory")
    args = parser.parse_args()
    
    success = run_pipeline(args.factory_root)
    sys.exit(0 if success else 1)
