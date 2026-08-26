"""
render_audience_canvas.py
Last update: 25/08/2026 23:25 (GMT+7)
Vai tro: Micro-renderer chuyên trách kết xuất Sơ đồ Phân cấp & Tiến trình Độc giả JTBD ra định dạng Obsidian Canvas (audience-hierarchy.canvas) với kiến trúc Phân Tầng Đa Cấp (Cascading Multi-Level Groups).
Su dung khi: Được gọi tự động bởi Orchestrator generate_coverage_preview.py trong pipeline Live-Sync.
Output: File vault/03-Content/Content Plan/audience-hierarchy.canvas chuẩn JSON UTF-8.
Tom tat logic hoat dong:
  1. Load & Phân loại: Nạp dữ liệu audiences từ Vault hoặc data_context, phân loại thành Big Audience, Level 1 (con của Big) và Level 2+ (con của Little).
  2. Bố cục Level 1: Áp dụng Bottom Row Priority để xếp các thẻ có con cấp dưới ở hàng đáy của Group 1.
  3. Bố cục Level 2+: Sinh Khung Group riêng biệt cho từng nhánh con ở tầng dưới, căn chính trực theo thẻ cha.
  4. Cạnh ngữ nghĩa: Cạnh Đáy (bottom -> top) là Phả Hệ màu xanh lá (4); Cạnh Bên (right -> left) là Job Step màu tím (6). Không dùng nhãn chữ để giữ sơ đồ thanh thoát.
  5. Smart Merge: Đọc và bảo toàn 100% tọa độ và màu sắc tùy chỉnh của người dùng từ Canvas cũ.
"""

import os
import sys
import json
import re
import math
from collections import defaultdict

# -------------------------------------------------------------
# NHÓM 1: CẤU HÌNH HÌNH HỌC & MÀU SẮC CHUẨN (CANVAS_CONFIG)
# -------------------------------------------------------------
CANVAS_CONFIG = {
    # Kích thước thẻ
    "CARD_W": 540,
    "CARD_H": 460,
    "BIG_CARD_W": 640,
    "BIG_CARD_H": 420,
    
    # Khoảng cách lưới
    "GAP_X": 220,       # Khoảng cách ngang giữa 2 thẻ (đảm bảo độ dài mũi tên)
    "GAP_Y": 100,       # Khoảng cách dọc giữa các hàng thẻ
    "COLS": 5,          # Số cột tối đa cho lưới Level 1
    
    # Tọa độ khởi đầu
    "START_X": 100,
    "START_Y": 620,
    "BIG_START_X": 1200,
    "BIG_START_Y": 50,
    
    # Đệm và phân tầng Khung Group
    "PADDING_X": 60,
    "PADDING_Y": 80,
    "TIER_GAP": 160,    # Khoảng cách dọc giữa các tầng Group
    "MOTHER_OFFSET_Y": 150, # Khoảng cách từ Thẻ Mẹ tới đỉnh Khung Group
    
    # Bảng màu chuẩn Obsidian Canvas
    "COLOR_BIG": "1",        # Đỏ: Big Audience
    "COLOR_LITTLE": "4",     # Xanh lá: Little Audience
    "COLOR_GROUP_L1": "4",   # Xanh lá: Khung Group Level 1
    "COLOR_GROUP_L2": "5",   # Cyan: Khung Group Level 2+
    "COLOR_EDGE_PHẢ_HỆ": "4",# Xanh lá: Mũi tên Mẹ - Con
    "COLOR_EDGE_JOB_STEP": "6" # Tím: Mũi tên Tiến trình Job Step
}

# -------------------------------------------------------------
# NHÓM 2: CÁC HÀM TIỆN ÍCH & TRÍCH XUẤT VĂN BẢN
# -------------------------------------------------------------
def extract_slug_from_node_text(node_text):
    """Trích xuất slug Audience từ wikilink [[slug]] trong nội dung Text Node hoặc Group Label."""
    if not node_text:
        return None
    match = re.search(r'\[\[(.*?)\]\]', str(node_text))
    return match.group(1).strip() if match else None

def generate_node_text(aud_data, level_str):
    """Sinh nội dung Markdown hiển thị bên trong Text Node của Canvas."""
    base = aud_data.get("base", "")
    performer = aud_data.get("performer", "N/A")
    main_job = aud_data.get("main_job", "N/A")
    circumstance = aud_data.get("circumstance", "N/A")
    matched_topics = aud_data.get("matched_topics", [])
    
    if level_str == "big":
        header_title = "## 🎯 BIG AUDIENCE (Hạt nhân chiến lược)"
        tag = "`#big`"
    else:
        header_title = "## 👥 LITTLE AUDIENCE"
        tag = "`#little`"
        
    lines = [
        header_title,
        f"### [[{base}]]",
        f"{tag} • **Performer:** {performer}",
        f"**Main Job:** {main_job}",
        f"**Circumstance:** *{circumstance}*",
        "",
        "---",
        "#### 📌 Topics & Insights:"
    ]
    
    if matched_topics:
        for t in matched_topics:
            t_id = t.get("id", "")
            t_label = t.get("label", t_id)
            lines.append(f"- **{t_label}** (`{t_id}`)")
    else:
        lines.append("- *(Chưa có topic liên kết)*")
        
    return "\n".join(lines)

# -------------------------------------------------------------
# NHÓM 3: NẠP DỮ LIỆU VAULT & PHÂN TÍCH CANVAS CŨ (SMART MERGE)
# -------------------------------------------------------------
def load_vault_audiences(factory_root):
    """Quét và nạp danh sách Audience Markdown files từ thư mục Vault khi data_context rỗng."""
    audiences = {}
    aud_dir = os.path.join(factory_root, "vault", "01-Atomic", "Audiences")
    if not os.path.exists(aud_dir):
        return audiences
        
    for fname in os.listdir(aud_dir):
        if fname.endswith(".md") and not fname.startswith("_"):
            base = fname[:-3]
            fpath = os.path.join(aud_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8-sig", errors="ignore") as f:
                    txt = f.read()
                lvl = "big" if ("level: 'big'" in txt or 'level: "big"' in txt or 'level: big' in txt) else "little"
                
                parents = []
                next_steps = []
                p_match = re.search(r"parent_audience:\s*\n((?:\s+-\s+.*)+)", txt)
                if p_match:
                    for line in p_match.group(1).split("\n"):
                        clean_p = re.sub(r"^\s*-\s*['\"]?\[\[?([^\]'\"]+)\]?\]?['\"]?", r"\1", line).strip()
                        if clean_p:
                            parents.append(clean_p)
                            
                n_match = re.search(r"next_job_step:\s*\n((?:\s+-\s+.*)+)", txt)
                if n_match:
                    for line in n_match.group(1).split("\n"):
                        clean_n = re.sub(r"^\s*-\s*['\"]?\[\[?([^\]'\"]+)\]?\]?['\"]?", r"\1", line).strip()
                        if clean_n:
                            next_steps.append(clean_n)

                audiences[base] = {
                    "base": base,
                    "level": lvl,
                    "title": base,
                    "parents": parents,
                    "next_steps": next_steps
                }
            except Exception:
                pass
    return audiences

def parse_existing_canvas(existing_canvas_path):
    """Đọc file Canvas hiện tại trên đĩa để lập chỉ mục các node/group cũ phục vụ Smart Merge."""
    nodes_by_slug = {}
    groups_by_slug = {}
    if not existing_canvas_path or not os.path.exists(existing_canvas_path):
        return nodes_by_slug, groups_by_slug
        
    try:
        with open(existing_canvas_path, "r", encoding="utf-8") as f:
            old_canvas = json.load(f)
            for node in old_canvas.get("nodes", []):
                n_type = node.get("type", "text")
                if n_type == "text":
                    slug = extract_slug_from_node_text(node.get("text", ""))
                    if slug:
                        nodes_by_slug[slug] = node
                elif n_type == "group":
                    slug = extract_slug_from_node_text(node.get("label", ""))
                    if slug:
                        groups_by_slug[slug] = node
    except Exception as e:
        print(f"  [WARN] Khong the doc file Canvas cu de Smart Merge: {e}")
        
    return nodes_by_slug, groups_by_slug

# -------------------------------------------------------------
# NHÓM 4: PHÂN RÃ CÂY PHẢ HỆ ĐA TẦNG (HIERARCHY PARTITIONING)
# -------------------------------------------------------------
def partition_audience_tree(audiences, big_slug):
    """
    Phân rã toàn bộ Audiences thành:
      - big_audiences: Danh sách Big Audiences.
      - sorted_level_1: Little Audiences con của Big (Leaf xếp trên, Branching xếp ở hàng đáy).
      - children_by_parent: Map quan hệ cha-con đa cấp.
      - little_audiences: Danh sách toàn bộ Little Audiences.
    """
    big_audiences = []
    little_audiences = []
    
    for base, aud in audiences.items():
        lvl = aud.get("level", "little")
        if lvl == "big":
            big_audiences.append(aud)
        else:
            little_audiences.append(aud)
            
    children_by_parent = defaultdict(list)
    independent_audiences = []

    for aud in little_audiences:
        parents = aud.get("parents", [])
        clean_parents = []
        if parents:
            for p in parents:
                cp = p.replace("[[", "").replace("]]", "").strip()
                if cp:
                    clean_parents.append(cp)
                    children_by_parent[cp].append(aud)
        
        # Chỉ khi khai báo cha rõ ràng mới đưa vào cây phả hệ
        if not clean_parents:
            independent_audiences.append(aud)

    # Lọc các thẻ con trực tiếp của Big Audience (Level 1)
    level_1_audiences = list(children_by_parent.get(big_slug, []))

    # Xác định các thẻ trong Level 1 mà bản thân nó lại có con (Branching Parents)
    branching_slugs_in_level_1 = set()
    for aud in level_1_audiences:
        s = aud["base"]
        if s in children_by_parent and len(children_by_parent[s]) > 0:
            branching_slugs_in_level_1.add(s)

    # Tách Level 1: Leaf ở trên, Branching ở Hàng Đáy (Bottom Row Priority)
    leaf_auds = [a for a in level_1_audiences if a["base"] not in branching_slugs_in_level_1]
    branching_auds = [a for a in level_1_audiences if a["base"] in branching_slugs_in_level_1]
    sorted_level_1 = leaf_auds + branching_auds
    
    return big_audiences, sorted_level_1, children_by_parent, little_audiences, independent_audiences

# -------------------------------------------------------------
# NHÓM 5: TÍNH TOÁN BỐ CỤC HÌNH HỌC (GRID & BOUNDING BOX)
# -------------------------------------------------------------
def compute_bounding_box(node_list, pad_x=60, pad_y=80):
    """Tính toán Bounding Box ôm trọn danh sách các node con."""
    if not node_list:
        return 50, 550, 2000, 1000
    min_x = min(n["x"] for n in node_list)
    min_y = min(n["y"] for n in node_list)
    max_right = max(n["x"] + n["width"] for n in node_list)
    max_bottom = max(n["y"] + n["height"] for n in node_list)
    
    gx = min_x - pad_x
    gy = min_y - pad_y
    gw = max_right - gx + pad_x
    gh = max_bottom - gy + pad_y
    return gx, gy, gw, gh

def layout_card_nodes(audience_list, base_x, base_y, cols, existing_nodes_by_slug, created_slugs):
    """Bố trí danh sách thẻ Audience theo lưới cột đều đặn với Smart Merge."""
    nodes = []
    node_id_map = {}
    
    card_w = CANVAS_CONFIG["CARD_W"]
    card_h = CANVAS_CONFIG["CARD_H"]
    gap_x = CANVAS_CONFIG["GAP_X"]
    gap_y = CANVAS_CONFIG["GAP_Y"]
    
    for idx, aud in enumerate(audience_list):
        slug = aud["base"]
        created_slugs.add(slug)
        l_text = generate_node_text(aud, "little")
        
        row = idx // cols
        col = idx % cols
        default_x = base_x + col * (card_w + gap_x)
        default_y = base_y + row * (card_h + gap_y)
        
        old_color = CANVAS_CONFIG["COLOR_LITTLE"]
        node_id = f"node_aud_{slug}"
        if slug in existing_nodes_by_slug:
            old_n = existing_nodes_by_slug[slug]
            node_id = old_n.get("id", node_id)
            old_color = old_n.get("color", old_color)

        l_node = {
            "id": node_id,
            "type": "text",
            "text": l_text,
            "x": default_x,
            "y": default_y,
            "width": card_w,
            "height": card_h,
            "color": old_color
        }
        nodes.append(l_node)
        node_id_map[slug] = node_id
        
    return nodes, node_id_map

# -------------------------------------------------------------
# NHÓM 6: CORE CANVAS BUILDER (KẾT HỢP TOÀN BỘ CÁC MODULE)
# -------------------------------------------------------------
def build_canvas_data(data_context, existing_canvas_path):
    """Xây dựng cấu trúc JSON Canvas hoàn chỉnh kết hợp thuật toán Phân Tầng Đa Cấp và Smart Merge."""
    audiences = dict(data_context.get("audiences", {}))
    if not audiences:
        audiences = load_vault_audiences(data_context.get("factory_root", "."))
    
    # 1. Đọc Canvas cũ để bảo toàn tọa độ của người dùng
    existing_nodes_by_slug, existing_groups_by_slug = parse_existing_canvas(existing_canvas_path)

    # 2. Xác định Big Audience Slug
    big_slug = "cha-me_thiet-lap-nen-tang-phat-trien-cho-con_khi-sap-co-con-hoac-dang-nuoi-con-tu-0-7-tuoi-tai-viet-nam"
    for base, aud in audiences.items():
        if aud.get("level") == "big":
            big_slug = base
            break

    # 3. Phân rã cây phả hệ đa tầng
    big_audiences, sorted_level_1, children_by_parent, little_audiences, independent_audiences = partition_audience_tree(audiences, big_slug)

    nodes = []
    edges = []
    node_id_by_slug = {}
    created_slugs = set()

    # 4. Layout Big Audience (Đặt ở đỉnh)
    big_root_node_id = "node_big_root"
    if big_audiences:
        big_aud = big_audiences[0]
        b_slug = big_aud["base"]
        b_text = generate_node_text(big_aud, "big")
        
        old_big_id = big_root_node_id
        old_big_color = CANVAS_CONFIG["COLOR_BIG"]
        if b_slug in existing_nodes_by_slug:
            old_n = existing_nodes_by_slug[b_slug]
            old_big_id = old_n.get("id", big_root_node_id)
            old_big_color = old_n.get("color", old_big_color)

        big_node = {
            "id": old_big_id,
            "type": "text",
            "text": b_text,
            "x": CANVAS_CONFIG["BIG_START_X"],
            "y": CANVAS_CONFIG["BIG_START_Y"],
            "width": CANVAS_CONFIG["BIG_CARD_W"],
            "height": CANVAS_CONFIG["BIG_CARD_H"],
            "color": old_big_color
        }
        nodes.append(big_node)
        node_id_by_slug[b_slug] = big_node["id"]
        big_root_node_id = big_node["id"]

    # 5. Layout Level 1 (5 cột)
    l1_nodes, l1_id_map = layout_card_nodes(
        sorted_level_1,
        CANVAS_CONFIG["START_X"],
        CANVAS_CONFIG["START_Y"],
        CANVAS_CONFIG["COLS"],
        existing_nodes_by_slug,
        created_slugs
    )
    nodes.extend(l1_nodes)
    node_id_by_slug.update(l1_id_map)

    # 6. Xây dựng Khung Group 1 (Level 1) & Căn Chính Trực Big Audience
    calc_gx, calc_gy, calc_gw, calc_gh = compute_bounding_box(
        l1_nodes, 
        CANVAS_CONFIG["PADDING_X"], 
        CANVAS_CONFIG["PADDING_Y"]
    )

    if big_audiences:
        group_1_center_x = calc_gx + calc_gw / 2
        big_node["x"] = group_1_center_x - big_node["width"] / 2
        big_node["y"] = calc_gy - big_node["height"] - CANVAS_CONFIG["MOTHER_OFFSET_Y"]

    group_1_id = "group_little_audiences"
    group_1_label = f"📦 NHÓM CON (Little Audiences): [[{big_slug}]]"

    if len(sorted_level_1) > 1:
        old_g1_id = group_1_id
        old_g1_color = CANVAS_CONFIG["COLOR_GROUP_L1"]
        if big_slug in existing_groups_by_slug:
            old_g = existing_groups_by_slug[big_slug]
            old_g1_id = old_g.get("id", group_1_id)
            old_g1_color = old_g.get("color", old_g1_color)

        group_1_node = {
            "id": old_g1_id,
            "type": "group",
            "label": group_1_label,
            "x": calc_gx,
            "y": calc_gy,
            "width": calc_gw,
            "height": calc_gh,
            "color": old_g1_color
        }
        nodes.insert(0, group_1_node)

        # Mũi tên dọc từ Big Node -> Khung Group 1
        edges.append({
            "id": "edge_root_to_group",
            "fromNode": big_root_node_id,
            "fromSide": "bottom",
            "toNode": group_1_node["id"],
            "toSide": "top",
            "color": CANVAS_CONFIG["COLOR_EDGE_PHẢ_HỆ"]
        })
    elif len(sorted_level_1) == 1:
        single_child_id = node_id_by_slug.get(sorted_level_1[0]["base"])
        if single_child_id:
            edges.append({
                "id": "edge_root_to_single_child",
                "fromNode": big_root_node_id,
                "fromSide": "bottom",
                "toNode": single_child_id,
                "toSide": "top",
                "color": CANVAS_CONFIG["COLOR_EDGE_PHẢ_HỆ"]
            })

    # 7. Xây dựng các Khung Group Level 2+ (Tầng dưới, căn chính trực theo thẻ cha)
    current_tier_y = calc_gy + calc_gh + CANVAS_CONFIG["TIER_GAP"]
    sub_group_idx = 1
    
    card_w = CANVAS_CONFIG["CARD_W"]
    card_h = CANVAS_CONFIG["CARD_H"]
    gap_x = CANVAS_CONFIG["GAP_X"]
    gap_y = CANVAS_CONFIG["GAP_Y"]

    for p_slug, child_list in children_by_parent.items():
        if p_slug == big_slug or not child_list:
            continue
            
        parent_card_node_id = node_id_by_slug.get(p_slug)
        parent_card = next((n for n in nodes if n.get("id") == parent_card_node_id), None)
        parent_center_x = (parent_card.get("x", 100) + parent_card.get("width", card_w) / 2) if parent_card else 500
                
        sub_group_id = f"group_sub_{p_slug[:20]}_{sub_group_idx}"
        sub_group_label = f"📦 NHÓM CON (Little Audiences): [[{p_slug}]]"
        
        uncreated_children = [c for c in child_list if c["base"] not in created_slugs]
        if not uncreated_children:
            continue

        sub_leaf = [c for c in uncreated_children if c["base"] not in children_by_parent or len(children_by_parent[c["base"]]) == 0]
        sub_branching = [c for c in uncreated_children if c["base"] in children_by_parent and len(children_by_parent[c["base"]]) > 0]
        sorted_sub_children = sub_leaf + sub_branching

        total_sub_cards = len(sorted_sub_children)
        sub_cols = min(total_sub_cards, CANVAS_CONFIG["COLS"])
        sub_rows = math.ceil(total_sub_cards / sub_cols) if sub_cols > 0 else 1
        sub_block_w = sub_cols * (card_w + gap_x) - gap_x
        sub_calc_gw = sub_block_w + 120
        sub_calc_gh = sub_rows * (card_h + gap_y) - gap_y + 140

        sub_calc_gx = parent_center_x - sub_calc_gw / 2
        sub_calc_gy = current_tier_y

        sub_nodes, sub_id_map = layout_card_nodes(
            sorted_sub_children,
            sub_calc_gx + 60,
            sub_calc_gy + 80,
            sub_cols,
            existing_nodes_by_slug,
            created_slugs
        )
        nodes.extend(sub_nodes)
        node_id_by_slug.update(sub_id_map)

        if total_sub_cards > 1:
            old_sg_id = sub_group_id
            old_sg_color = CANVAS_CONFIG["COLOR_GROUP_L2"]
            if p_slug in existing_groups_by_slug:
                old_sg = existing_groups_by_slug[p_slug]
                old_sg_id = old_sg.get("id", sub_group_id)
                old_sg_color = old_sg.get("color", old_sg_color)

            sub_group_node = {
                "id": old_sg_id,
                "type": "group",
                "label": sub_group_label,
                "x": sub_calc_gx,
                "y": sub_calc_gy,
                "width": sub_calc_gw,
                "height": sub_calc_gh,
                "color": old_sg_color
            }
            nodes.insert(1, sub_group_node)

            if parent_card_node_id:
                edges.append({
                    "id": f"edge_pha_he_sub_{sub_group_idx}",
                    "fromNode": parent_card_node_id,
                    "fromSide": "bottom",
                    "toNode": sub_group_node["id"],
                    "toSide": "top",
                    "color": CANVAS_CONFIG["COLOR_EDGE_PHẢ_HỆ"]
                })
            current_tier_y += sub_calc_gh + CANVAS_CONFIG["TIER_GAP"]
        elif total_sub_cards == 1:
            single_sub_child_id = node_id_by_slug.get(sorted_sub_children[0]["base"])
            if parent_card_node_id and single_sub_child_id:
                edges.append({
                    "id": f"edge_pha_he_sub_single_{sub_group_idx}",
                    "fromNode": parent_card_node_id,
                    "fromSide": "bottom",
                    "toNode": single_sub_child_id,
                    "toSide": "top",
                    "color": CANVAS_CONFIG["COLOR_EDGE_PHẢ_HỆ"]
                })
            current_tier_y += card_h + CANVAS_CONFIG["TIER_GAP"]
            
        sub_group_idx += 1

    # 7b. Layout các thẻ Audience độc lập (không có liên kết cha) ở tầng dưới cùng, KHÔNG CÓ KHUNG GROUP
    if independent_audiences:
        uncreated_indep = [c for c in independent_audiences if c["base"] not in created_slugs]
        if uncreated_indep:
            indep_cols = min(len(uncreated_indep), CANVAS_CONFIG["COLS"])
            indep_rows = math.ceil(len(uncreated_indep) / indep_cols) if indep_cols > 0 else 1
            indep_nodes, indep_id_map = layout_card_nodes(
                uncreated_indep,
                CANVAS_CONFIG["START_X"],
                current_tier_y,
                indep_cols,
                existing_nodes_by_slug,
                created_slugs
            )
            nodes.extend(indep_nodes)
            node_id_by_slug.update(indep_id_map)
            current_tier_y += indep_rows * (card_h + gap_y) + CANVAS_CONFIG["TIER_GAP"]

    # 8. Sinh Cạnh Tiến Trình Ngang (Job Steps giữa các Audiences)
    edge_idx = 1
    for aud in little_audiences:
        from_slug = aud["base"]
        from_node_id = node_id_by_slug.get(from_slug)
        if not from_node_id:
            continue
            
        next_steps = aud.get("next_steps", [])
        for to_slug in next_steps:
            to_node_id = node_id_by_slug.get(to_slug)
            if to_node_id and to_node_id != from_node_id:
                edges.append({
                    "id": f"edge_job_step_{edge_idx}",
                    "fromNode": from_node_id,
                    "fromSide": "right",
                    "toNode": to_node_id,
                    "toSide": "left",
                    "color": CANVAS_CONFIG["COLOR_EDGE_JOB_STEP"]
                })
                edge_idx += 1

    return {
        "nodes": nodes,
        "edges": edges
    }

# -------------------------------------------------------------
# NHÓM 7: ENTRY POINT RENDER FUNCTION
# -------------------------------------------------------------
def render(data_context):
    """Entry point được gọi bởi generate_coverage_preview.py."""
    factory_root = data_context.get("factory_root")
    if not factory_root:
        print("[ERR] render_audience_canvas: Thieu factory_root trong data_context.")
        return False
        
    output_dir = os.path.join(factory_root, "vault", "03-Content", "Content Plan")
    os.makedirs(output_dir, exist_ok=True)
    canvas_path = os.path.join(output_dir, "audience-hierarchy.canvas")
    
    try:
        canvas_json_data = build_canvas_data(data_context, canvas_path)
        
        # Atomic write
        tmp_path = canvas_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(canvas_json_data, f, ensure_ascii=False, indent=2)
            
        os.replace(tmp_path, canvas_path)
        print(f"  [OK] Đã xuất Audience Canvas (Cascading Multi-Level): {os.path.relpath(canvas_path, factory_root)}")
        return True
    except Exception as e:
        print(f"  [ERR] Loi khi xuat Audience Canvas: {e}")
        return False
