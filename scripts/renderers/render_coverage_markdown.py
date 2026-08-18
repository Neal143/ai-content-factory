"""
render_coverage_markdown.py
Last update: 18/08/2026 22:30 (GMT+7)
Vai tro: Module renderer con chuyen trach dinh dang va xuat bang Ma tran phu tri thuc (Markdown).
Su dung khi: Duoc goi boi generate_coverage_preview.py (Script me / Orchestrator).
Output: File vault/03-Content/Content Plan/audience-knowledge-coverage-preview.md.
Tom tat logic:
  1. Nhan data_context da duoc chuan hoa tu Script me.
  2. Dinh dang bang Markdown voi day du 8 cot (STT, Audience, Level, Parent Audience, Topic, Posts Count, Insights, Concepts & Solutions, Evidences).
  3. Tao relative link URL encoded de click/hover popup trong Obsidian.
  4. Ghi ra file audience-knowledge-coverage-preview.md.
"""

import os
import sys
import urllib.parse

def render(data_context):
    factory_root = data_context["factory_root"]
    persona_name = data_context["persona_name"]
    audiences = data_context["audiences"]
    topics = data_context["topics"]
    aud_to_topics = data_context["aud_to_topics"]
    insights = data_context["insights"]
    knowledges = data_context["knowledges"]
    evidences = data_context["evidences"]
    prod_counts = data_context["prod_counts"]
    
    vault_dir = os.path.join(factory_root, "vault")
    aud_dir = os.path.join(vault_dir, "01-Atomic", "Audiences")
    out_dir = os.path.join(vault_dir, "03-Content", "Content Plan")
    os.makedirs(out_dir, exist_ok=True)
    out_md_path = os.path.join(out_dir, "audience-knowledge-coverage-preview.md")

    # Helper: format relative link
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
            for b_name, info in audiences.items():
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

    for base, aud_data in audiences.items():
        level = aud_data.get("level", "little")
        parents = aud_data.get("parents", [])
        parent_link = format_aud_link(parents[0]) if parents else "-"
        aud_link = format_aud_link(base)
        
        matching_topics = aud_data.get("matched_topics", [])
        if not matching_topics:
            matching_topics = [{"id": "-", "label": "-"}]

        for i, top in enumerate(matching_topics):
            t_id = top["id"]
            t_label = top["label"]
            
            posts_count = prod_counts.get(t_id, 0)
            
            # Map Insights
            ins_matched = []
            for ins_name, ins_data in insights.items():
                aud_match = any(c in aud_data["aliases"] for c in ins_data["audiences"])
                top_match = (t_id in ins_data["topics"]) if t_id != "-" else True
                if aud_match and top_match:
                    ins_matched.append(ins_name)
                elif aud_match and t_id != "-" and not ins_data["topics"]:
                    ins_matched.append(ins_name)
                    
            ins_count = len(set(ins_matched))
            
            # Map Knowledges (Concepts & Solutions)
            knowledges_matched = []
            for k_name, k_data in knowledges.items():
                if any(ins in ins_matched for ins in k_data["supports_insight"]):
                    knowledges_matched.append(k_name)
            k_count = len(set(knowledges_matched))
            
            # Map Evidences (Quotes, Stories, Data-Points)
            evidences_matched = []
            for e_name, e_data in evidences.items():
                if any(k in knowledges_matched for k in e_data["supports_knowledge"]):
                    evidences_matched.append(e_name)
            e_count = len(set(evidences_matched))
            
            t_display = f"`{t_id}` (*{t_label}*)" if t_id != "-" else "-"
            
            if i == 0:
                stt_display = f"**{aud_idx}**"
                aud_display = aud_link
                level_display = f"`{level}`"
                parent_display = parent_link
            else:
                stt_display = "-"
                aud_display = "-"
                level_display = "-"
                parent_display = "-"
            
            rows.append({
                "stt": stt_display,
                "aud_link": aud_display,
                "level": level_display,
                "parent_link": parent_display,
                "topic_display": t_display,
                "posts_count": str(posts_count),
                "ins_count": str(ins_count),
                "k_count": str(k_count),
                "e_count": str(e_count)
            })
            
        aud_idx += 1

    # Generate Markdown Table
    md_lines = []
    md_lines.append(f"# 📊 Ma Trận Phủ Kiến Thức Persona ({persona_name})\n")
    md_lines.append("<!--")
    md_lines.append("- File name: audience-knowledge-coverage-preview.md")
    md_lines.append("- Last update: Auto-generated by generate_coverage_preview.py")
    md_lines.append("- Vai tro: Bang preview ma tran phu tri thuc giua Audiences, Topics va cac Atoms.")
    md_lines.append("-->\n")
    md_lines.append("> [!NOTE]")
    md_lines.append(f"> - **Tổng số Audiences:** Đúng **{len(audiences)} Audiences** (đánh số thứ tự từ **1 đến {len(audiences)}** ở cột STT).")
    md_lines.append("> - **Mỗi dòng là 1 Topic:** Hiển thị số lượng bài viết, Insights, Concepts và Evidences.")
    md_lines.append("> - **Cột 2 & Cột 4:** Định dạng relative link để hover mở popup và chỉnh sửa trực tiếp nội dung trong Obsidian.\n")
    
    md_lines.append("| STT | Audience (Cột 1) | Level (Cột 2) | Parent Audience (Cột 3) | Topic (Cột 4) | Posts Count (Cột 5) | Insights (Cột 6) | Concepts & Solutions (Cột 7) | Evidences: Quotes, Stories, Data (Cột 8) |")
    md_lines.append("|:---:|---|:---:|---|---|:---:|:---:|:---:|:---:|")

    for r in rows:
        md_lines.append(
            f"| {r['stt']} | {r['aud_link']} | {r['level']} | {r['parent_link']} | {r['topic_display']} | {r['posts_count']} | {r['ins_count']} | {r['k_count']} | {r['e_count']} |"
        )

    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"[OK] Generated Coverage Markdown: {out_md_path} ({len(audiences)} Audiences, {len(rows)} Topic rows)")
    return True
