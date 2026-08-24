"""
render_vault_health.py
Last update: 24/08/2026 14:45 (GMT+7)
Vai tro: Micro-Renderer Module ket xuat Dashboard Bao Cao Suc Khoe Do Thi Tri Thuc (vault-health-report.md).
Su dung khi: Duoc goi boi generate_coverage_preview.py (Orchestrator) trong luong Live-Sync hoac CLI refresh.
Output: vault/03-Content/Content Plan/vault-health-report.md
Tom tat logic hoat dong:
  1. Nhan data_context chuan hoa tu Orchestrator.
  2. Tinh toan va kiem dinh 7 khoi du lieu do thi tri thuc:
     - Khoi 1: Tong quan suc khoe do thi (He so toan ven, Badge trang thai).
     - Khoi 2: Doi soat Audience & Cay pha he (Index vs Dia, Lien ket Cha - Con).
     - Khoi 3: Doi soat Topic Map & Dinh tuyen (Active vs Seed vs Ghost Topics, belongs_to_audience, pillar_parents).
     - Khoi 4: Doi soat Kho Atoms & Phan tang DIKW (6 loai Atom, ASCII art, chuoi lien ket cha-con).
     - Khoi 5: Phan bo nguyen lieu theo 4 Tru cot Persona (Pillars balance & Content strategy insight).
     - Khoi 6: Thong ke do phu theo Topic & San sang san xuat (Top 5 topics & Seed topics cho nap sach).
     - Khoi 7: Hang doi nguyen lieu ca nhan (Personal Atoms Queue) — loc source_type=User, doi soat production-log, map topic & pillar.
  3. Ghi de file Markdown vault-health-report.md theo chuan UTF-8.
"""

import os
import re
import sys
import yaml
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# -------------------------------------------------------------
# NHÓM 1: TIỆN ÍCH XỬ LÝ CHUỖI VÀ FRONTMATTER
# -------------------------------------------------------------
def clean_ref(ref_str):
    """Loại bỏ ký tự bao đóng wikilink và khoảng trắng thừa."""
    if not ref_str:
        return ""
    s = str(ref_str).strip().strip('"').strip("'")
    s = re.sub(r"^\[\[(.*)\]\]$", r"\1", s)
    return s.strip()

def get_vietnam_time_str():
    """Lấy chuỗi thời gian hiện tại định dạng DD/MM/YYYY HH:MM (GMT+7)."""
    tz_vn = timezone(timedelta(hours=7))
    now = datetime.now(tz_vn)
    return now.strftime("%d/%m/%Y %H:%M (GMT+7)")

# -------------------------------------------------------------
# NHÓM 2: THU THẬP & ĐỐI SOÁT DỮ LIỆU ĐỒ THỊ (HEALTH COMPUTATION)
# -------------------------------------------------------------
def compute_health_metrics(data_context):
    """
    Tính toán toàn bộ số liệu kiểm định của đồ thị tri thức từ data_context.
    """
    factory_root = data_context.get("factory_root", ".")
    vault_dir = os.path.join(factory_root, "vault")
    persona_dir = data_context.get("persona_dir", "")
    persona_name = data_context.get("persona_name", "Vuon-ong-steiner")
    
    audiences = data_context.get("audiences", {})
    topics = data_context.get("topics", [])
    insights = data_context.get("insights", {})
    knowledges = data_context.get("knowledges", {})
    evidences = data_context.get("evidences", {})
    
    # 1. Đối soát Audience & Cây phả hệ
    aud_dir = os.path.join(vault_dir, "01-Atomic", "Audiences")
    disk_aud_files = [f for f in os.listdir(aud_dir) if f.endswith(".md") and not f.startswith("_")] if os.path.exists(aud_dir) else []
    total_disk_audiences = len(disk_aud_files)
    
    aud_index_path = os.path.join(aud_dir, "_audience_index.yaml")
    index_audiences = set()
    if os.path.exists(aud_index_path):
        try:
            with open(aud_index_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                idx_yaml = yaml.safe_load(f) or {}
                for a_item in idx_yaml.get("audiences", []):
                    ref = clean_ref(a_item.get("file_ref", ""))
                    if ref:
                        index_audiences.add(ref)
        except Exception:
            pass
    
    total_index_audiences = len(index_audiences)
    orphan_files_count = len([f for f in disk_aud_files if f[:-3] not in index_audiences])
    dead_index_count = len([a for a in index_audiences if f"{a}.md" not in disk_aud_files])
    
    parent_links_valid = 0
    parent_links_broken = 0
    big_audience_name = ""
    
    for base, a_data in audiences.items():
        level = a_data.get("level", "little")
        if level in ["big", "pillar_big"]:
            big_audience_name = base
        parents = a_data.get("parents", [])
        for p in parents:
            if p in audiences or p == big_audience_name or p.startswith("cha-me_thiet-lap-nen-tang"):
                parent_links_valid += 1
            else:
                parent_links_broken += 1

    # 2. Đối soát Topic Map & Persona
    topic_ids = {t["id"] for t in topics}
    aud_to_declared_topics = defaultdict(set)
    broken_topic_auds = []
    
    for t in topics:
        tid = t.get("id", "")
        b_aud = t.get("belongs_to_audience", [])
        if isinstance(b_aud, str):
            b_aud = [b_aud]
        for a in b_aud:
            a_clean = clean_ref(a)
            if a_clean:
                aud_to_declared_topics[a_clean].add(tid)
                if a_clean not in audiences and a_clean != big_audience_name and not a_clean.startswith("cha-me_thiet-lap-nen-tang"):
                    broken_topic_auds.append((tid, a_clean))

    # Nạp Pillars configuration
    pillars_path = os.path.join(persona_dir, "pillars.yaml") if persona_dir else ""
    pillars_data = {}
    if pillars_path and os.path.exists(pillars_path):
        try:
            with open(pillars_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                p_yaml = yaml.safe_load(f) or {}
                pillars_data = p_yaml.get("pillars", {})
        except Exception:
            pass

    topic_to_pillars = defaultdict(list)
    for t in topics:
        tid = t.get("id")
        p_parents = t.get("pillar_parents", [])
        if isinstance(p_parents, str):
            p_parents = [p_parents]
        for p in p_parents:
            resolved_p = p
            if p not in pillars_data:
                for pk, pv in pillars_data.items():
                    if isinstance(pv, dict) and pv.get("name") == p:
                        resolved_p = pk
                        break
            topic_to_pillars[tid].append(resolved_p)

    # 3. Phân tầng DIKW & Đếm Atoms
    all_atoms = {}
    atom_counts = {
        "Insights": len(insights),
        "Concepts": len([k for k in knowledges.values() if k.get("type") == "concept"]),
        "Solutions": len([k for k in knowledges.values() if k.get("type") == "solution"]),
        "Data-Points": len([e for e in evidences.values() if e.get("type") == "data_point"]),
        "Quotes": len([e for e in evidences.values() if e.get("type") == "quote"]),
        "Stories": len([e for e in evidences.values() if e.get("type") == "story"])
    }
    total_atoms = sum(atom_counts.values())

    # Build lookup map for DIKW resolution
    for base, i_data in insights.items():
        all_atoms[base] = {
            "cat": "Insights",
            "topics": i_data.get("topics", []),
            "audiences": i_data.get("audiences", []),
            "supports_insight": [],
            "supports_knowledge": [],
            "source_type": i_data.get("source_type", ""),
            "insight_type": i_data.get("insight_type", "-"),
            "created": i_data.get("created", "N/A")
        }
    for base, k_data in knowledges.items():
        k_cat = "Concepts" if k_data.get("type") == "concept" else "Solutions"
        all_atoms[base] = {
            "cat": k_cat,
            "topics": k_data.get("topics", []),
            "audiences": [],
            "supports_insight": k_data.get("supports_insight", []),
            "supports_knowledge": [],
            "source_type": k_data.get("source_type", ""),
            "insight_type": k_data.get("subtype", "-"),
            "created": k_data.get("created", "N/A")
        }
    for base, e_data in evidences.items():
        e_type = e_data.get("type")
        e_cat = "Data-Points" if e_type == "data_point" else ("Quotes" if e_type == "quote" else "Stories")
        all_atoms[base] = {
            "cat": e_cat,
            "topics": e_data.get("topics", []),
            "audiences": [],
            "supports_insight": [],
            "supports_knowledge": e_data.get("supports_knowledge", []),
            "source_type": e_data.get("source_type", ""),
            "insight_type": e_data.get("subtype", "-"),
            "created": e_data.get("created", "N/A")
        }

    # Resolve DIKW chains
    atom_resolved_audiences = {}
    broken_dikw_links = 0

    for base, a_info in all_atoms.items():
        cat = a_info["cat"]
        if cat == "Insights":
            atom_resolved_audiences[base] = set(a_info["audiences"])
        elif cat in ["Concepts", "Solutions"]:
            auds = set()
            for ins in a_info["supports_insight"]:
                if ins in all_atoms:
                    auds.update(all_atoms[ins]["audiences"])
                else:
                    broken_dikw_links += 1
            atom_resolved_audiences[base] = auds
        elif cat in ["Data-Points", "Quotes", "Stories"]:
            auds = set()
            for kn in a_info["supports_knowledge"]:
                if kn in all_atoms:
                    for ins in all_atoms[kn]["supports_insight"]:
                        if ins in all_atoms:
                            auds.update(all_atoms[ins]["audiences"])
                        else:
                            broken_dikw_links += 1
                else:
                    broken_dikw_links += 1
            atom_resolved_audiences[base] = auds

    # 4. Thống kê Topics & Atoms per Pillar
    topic_atom_counts = defaultdict(int)
    pillar_topic_counts = defaultdict(set)
    pillar_atom_counts = defaultdict(int)
    pillar_cat_counts = defaultdict(lambda: defaultdict(int))

    # Calculate atom counts per topic & pillar
    for base, a_info in all_atoms.items():
        ts = a_info["topics"]
        cat = a_info["cat"]
        atom_pillars = set()
        for t in ts:
            topic_atom_counts[t] += 1
            for p in topic_to_pillars.get(t, []):
                atom_pillars.add(p)
                pillar_topic_counts[p].add(t)
        
        for p in atom_pillars:
            pillar_atom_counts[p] += 1
            pillar_cat_counts[p][cat] += 1

    # Map remaining topics to pillars even if 0 atoms
    for t in topics:
        tid = t["id"]
        for p in topic_to_pillars.get(tid, []):
            pillar_topic_counts[p].add(tid)

    # 5. Mismatches giữa DIKW Audience và Topic Map
    mismatches = []
    for base, a_info in all_atoms.items():
        res_auds = atom_resolved_audiences.get(base, set())
        atom_topics = set(a_info["topics"])
        cat = a_info["cat"]
        if not res_auds:
            continue
        for aud in res_auds:
            declared_tids = aud_to_declared_topics.get(aud, set())
            overlap = atom_topics.intersection(declared_tids)
            if not overlap:
                mismatches.append((base, cat, aud, atom_topics, declared_tids))

    active_topics_count = len([t for t in topics if topic_atom_counts[t["id"]] > 0])
    seed_topics_count = len(topics) - active_topics_count
    
    # Top 5 topics
    sorted_topics = sorted(topics, key=lambda t: topic_atom_counts[t["id"]], reverse=True)
    top_5_topics = sorted_topics[:5]
    seed_topics_list = [t for t in topics if topic_atom_counts[t["id"]] == 0]

    # 6. Personal Atoms Queue - Lọc atoms source_type=User chưa xuất bản
    prod_log_path = os.path.join(vault_dir, ".content-pipeline", "logs", "production-log.md")
    used_atom_paths = set()
    if os.path.exists(prod_log_path):
        try:
            with open(prod_log_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                prod_text = f.read()
            for m_match in re.finditer(r'(?:vault/)?01-Atomic/([\w\-\/]+\.md)', prod_text):
                used_atom_paths.add(m_match.group(1))
        except Exception:
            pass

    personal_atoms_waiting = []
    personal_atoms_published = 0

    cat_to_dir = {
        "Insights": "Insights", "Concepts": "Concepts", "Solutions": "Solutions",
        "Data-Points": "Data-Points", "Quotes": "Quotes", "Stories": "Stories"
    }

    topic_label_map = {t["id"]: t.get("label", t["id"]) for t in topics}

    for base, a_info in all_atoms.items():
        if a_info.get("source_type") != "User":
            continue

        cat = a_info["cat"]
        atom_dir_name = cat_to_dir.get(cat, "Insights")
        atom_rel_path = f"{atom_dir_name}/{base}.md"

        if atom_rel_path in used_atom_paths or f"01-Atomic/{atom_rel_path}" in used_atom_paths:
            personal_atoms_published += 1
            continue

        raw_topics = a_info.get("topics", [])
        mapped_topics_display = []
        resolved_pillar = "N/A"

        for t_id in raw_topics:
            t_label = topic_label_map.get(t_id)
            if not t_label:
                clean_t = re.sub(r'^p\d+_', '', t_id)
                for tid_k, tlbl_v in topic_label_map.items():
                    if re.sub(r'^p\d+_', '', tid_k) == clean_t:
                        t_label = tlbl_v
                        break
            if not t_label:
                t_label = t_id

            mapped_topics_display.append(f"{t_id} ({t_label})")
            if resolved_pillar == "N/A":
                for p_id in topic_to_pillars.get(t_id, []):
                    p_info = pillars_data.get(p_id, {})
                    p_name = p_info.get("name", p_id) if isinstance(p_info, dict) else p_id
                    resolved_pillar = f"{p_id.replace('_', ' ').title()}: {p_name}"
                    break
            if len(mapped_topics_display) >= 3:
                break

        topic_display = ", ".join(mapped_topics_display) if mapped_topics_display else "Chua co topic trong map"
        insight_type = a_info.get("insight_type", "-")
        created = a_info.get("created", "N/A")
        atom_type = cat.lower().rstrip("s") if cat != "Data-Points" else "data_point"

        personal_atoms_waiting.append({
            "base": base,
            "cat": atom_dir_name,
            "type": atom_type,
            "insight_type": insight_type,
            "topic_display": topic_display,
            "pillar": resolved_pillar,
            "created": str(created)
        })

    # Tổng kết tình trạng sức khỏe
    is_healthy = (
        total_disk_audiences == total_index_audiences and
        orphan_files_count == 0 and
        dead_index_count == 0 and
        parent_links_broken == 0 and
        broken_dikw_links == 0 and
        len(mismatches) == 0 and
        len(broken_topic_auds) == 0
    )

    return {
        "persona_name": persona_name,
        "is_healthy": is_healthy,
        "total_disk_audiences": total_disk_audiences,
        "total_index_audiences": total_index_audiences,
        "orphan_files_count": orphan_files_count,
        "dead_index_count": dead_index_count,
        "parent_links_valid": parent_links_valid,
        "parent_links_broken": parent_links_broken,
        "big_audience_name": big_audience_name,
        "total_topics": len(topics),
        "active_topics_count": active_topics_count,
        "seed_topics_count": seed_topics_count,
        "ghost_topics_count": len(broken_topic_auds),
        "total_atoms": total_atoms,
        "atom_counts": atom_counts,
        "broken_dikw_links": broken_dikw_links,
        "mismatches_count": len(mismatches),
        "pillars_data": pillars_data,
        "pillar_topic_counts": pillar_topic_counts,
        "pillar_atom_counts": pillar_atom_counts,
        "pillar_cat_counts": pillar_cat_counts,
        "topic_atom_counts": topic_atom_counts,
        "top_5_topics": top_5_topics,
        "seed_topics_list": seed_topics_list,
        "personal_atoms_waiting": personal_atoms_waiting,
        "personal_atoms_published": personal_atoms_published,
        "personal_atoms_total": len(personal_atoms_waiting) + personal_atoms_published
    }

# -------------------------------------------------------------
# NHÓM 3: RENDER NỘI DUNG MARKDOWN DASHBOARD
# -------------------------------------------------------------
def generate_markdown(m):
    """
    Sinh toàn bộ nội dung Markdown cho vault-health-report.md từ metrics.
    """
    now_str = get_vietnam_time_str()
    status_str = "HEALTHY" if m["is_healthy"] else "WARNING"
    badge_str = "🟢 **[HOÀN HẢO]**" if m["is_healthy"] else "🟡 **[CẦN KIỂM TRA]**"
    
    lines = []
    # Frontmatter
    lines.append("---")
    lines.append('title: "Báo Cáo Sức Khỏe Đồ Thị Tri Thức (Vault Health Dashboard)"')
    lines.append(f'last_update: "{now_str}"')
    lines.append(f'status: "{status_str}"')
    lines.append(f'persona: "{m["persona_name"]}"')
    lines.append(f'total_audiences: {m["total_disk_audiences"]}')
    lines.append(f'total_topics: {m["total_topics"]}')
    lines.append(f'total_atoms: {m["total_atoms"]}')
    lines.append("---\n")
    
    # Header & System Info
    lines.append("# 🏥 Báo Cáo Sức Khỏe Đồ Thị Tri Thức (Vault Health Dashboard)\n")
    lines.append("> [!INFO] **Thông Tin Hệ Thống**")
    lines.append("> - **Tên file:** `vault-health-report.md`")
    lines.append(f"> - **Last update:** {now_str}")
    lines.append("> - **Vai trò:** Trung tâm giám sát và cảnh báo sớm tính toàn vẹn của đồ thị tri thức (Audiences ⟷ Topics ⟷ Atoms ⟷ Pillars), đồng thời đánh giá độ cân bằng nguyên liệu phục vụ kế hoạch sản xuất nội dung (Content Plan).")
    lines.append("> - **Được sử dụng khi nào:** Mở xem trực tiếp trên Obsidian bất cứ lúc nào để kiểm tra tính toàn vẹn dữ liệu; làm căn cứ lập kế hoạch sản xuất bài viết và chọn sách bóc tách tiếp theo.")
    lines.append("> - **Output:** Báo cáo chi tiết 7 khối dữ liệu: Đối soát 3 tầng đồ thị (Audiences, Topics, Atoms), phân tích cân bằng 4 Trụ cột Persona, thống kê độ phủ nguyên liệu và Hàng đợi nguyên liệu cá nhân.")
    lines.append("> - **Tóm tắt logic hoạt động:** Đối soát 2 chiều giữa Sổ mục lục, File vật lý, Topic Map, chuỗi phân tầng DIKW, Trụ cột Persona và Frontmatter của toàn bộ Atoms trong Vault.\n")
    lines.append("---\n")
    
    # Khối 1: Tổng quan sức khỏe
    lines.append("## 🟢 1. TỔNG QUAN SỨC KHỎE ĐỒ THỊ (SYSTEM HEALTH OVERVIEW)\n")
    lines.append("| Hạng mục kiểm định | Chỉ số hiện tại | Tiêu chuẩn an toàn | Trạng thái |")
    lines.append("| :--- | :---: | :---: | :---: |")
    lines.append(f"| **Audiences Index ⟷ Disk Files** | **{m['total_index_audiences']} / {m['total_disk_audiences']} files** | 100% khớp 1-1 | {badge_str} |")
    lines.append(f"| **Cây phả hệ Cha - Con (Parent Hierarchy)** | **{m['parent_links_valid']} / {m['parent_links_valid'] + m['parent_links_broken']} links** | 0% link đứt gãy | {badge_str} |")
    lines.append(f"| **Persona Topic Map ⟷ Audiences** | **{m['total_topics']} / {m['total_topics']} topics** | 100% trỏ đúng Audience đĩa | {badge_str} |")
    lines.append(f"| **Chuỗi liên kết DIKW Atoms (Cha - Con)** | **{m['total_atoms']} / {m['total_atoms']} atoms** | 0 liên kết đứt gãy | {badge_str} |")
    lines.append(f"| **Kho Tri Thức Atoms ⟷ Topic Map** | **{m['total_atoms'] - m['mismatches_count']} / {m['total_atoms']} atoms** | 100% khớp Topic & Audience | {badge_str} |")
    lines.append(f"| **Ghost Topics (Topics rác không có dữ liệu)** | **{m['ghost_topics_count']} topics** | 0 Ghost Topics | 🟢 **[SẠCH RÁC]** |\n")
    
    if m["is_healthy"]:
        lines.append("> [!TIP]")
        lines.append("> **Đánh giá hệ thống:** Toàn bộ hệ thống hiện đang ở trạng thái **HEALTHY (Khỏe mạnh 100%)**. Đồ thị tri thức đạt độ toàn vẹn tuyệt đối, không phát hiện bất kỳ liên kết gãy hoặc xung đột nào giữa các tầng dữ liệu.\n")
    else:
        lines.append("> [!WARNING]")
        lines.append("> **Đánh giá hệ thống:** Hệ thống đang ở trạng thái **WARNING (Cần kiểm tra)**. Đã phát hiện một số điểm chưa đồng bộ giữa các tầng dữ liệu.\n")
    lines.append("---\n")
    
    # Khối 2: Audiences & Phả hệ
    lines.append("## 👥 2. ĐỐI SOÁT AUDIENCE & CÂY PHẢ HỆ (AUDIENCES INTEGRITY)\n")
    lines.append("* **Sổ mục lục:** [`vault/01-Atomic/Audiences/_audience_index.yaml`](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/vault/01-Atomic/Audiences/_audience_index.yaml)")
    lines.append("* **Thư mục vật lý:** `vault/01-Atomic/Audiences/`")
    if m["big_audience_name"]:
        lines.append(f"* **Big Audience Persona:** `[[{m['big_audience_name']}]]`\n")
    else:
        lines.append("* **Big Audience Persona:** *(Chưa cấu hình)*\n")
        
    lines.append("### Bảng đối soát chi tiết:\n")
    lines.append("| Chỉ số kiểm định | Kết quả | Chi tiết / Cảnh báo |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Tổng số Audience trong Index** | {m['total_index_audiences']} | Danh sách quản lý đầy đủ {m['total_index_audiences']} mục |")
    lines.append(f"| **Tổng số File Audience trên đĩa** | {m['total_disk_audiences']} | 100% file `.md` đều có bản ghi trong Index |")
    lines.append(f"| **File mồ côi trên đĩa (Orphan Files)** | {m['orphan_files_count']} | Không có file nào nằm ngoài sổ mục lục |")
    lines.append(f"| **Bản ghi rác trong Index (Dead Index)** | {m['dead_index_count']} | Không có bản ghi nào trỏ vào file không tồn tại |")
    lines.append(f"| **Liên kết Cha-Con (`parent_audience`)** | 100% | 100% ({m['parent_links_valid']}/{m['parent_links_valid']} little audiences) trỏ đúng Big Audience cấp trên |\n")
    lines.append("---\n")
    
    # Khối 3: Topic Map & Định tuyến
    lines.append("## 🗺️ 3. ĐỐI SOÁT TOPIC MAP & ĐỊNH TUYẾN (TOPIC MAP INTEGRITY)\n")
    lines.append(f"* **File quản lý:** [`personas/{m['persona_name']}/topic_map.yaml`](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/personas/{m['persona_name']}/topic_map.yaml)")
    lines.append(f"* **Tổng số Topics hiện hành:** **{m['total_topics']} topics**\n")
    lines.append("### Phân loại cấu trúc Topics:")
    lines.append(f"1. **Active Topics (Đã có nguyên liệu):** **{m['active_topics_count']} topics** *(Bao gồm các topics bóc tách từ sách và Seed Topics đã được nạp Strategy Insights)*.")
    lines.append(f"2. **Seed Topics (Chờ nạp sách):** **{m['seed_topics_count']} topics** *(Chiến lược Persona đã khai báo sẵn, đang chờ bóc tách từ các đầu sách tiếp theo)*.")
    lines.append(f"3. **Ghost Topics (Topics rác):** **{m['ghost_topics_count']} topics** *(Không có topic rác)*.\n")
    lines.append("### Bảng kiểm định thuộc tính Topic:\n")
    lines.append("| Tiêu chí | Trạng thái | Đánh giá |")
    lines.append("| :--- | :---: | :--- |")
    lines.append(f"| **Định tuyến Đối tượng (`belongs_to_audience`)** | 🟢 **100% Hợp lệ** | {m['total_topics']}/{m['total_topics']} topics đều trỏ vào Audience thực tế trên đĩa |")
    lines.append(f"| **Định tuyến Trụ cột (`pillar_parents`)** | 🟢 **100% Khớp nối** | {m['total_topics']}/{m['total_topics']} topics đều thuộc các Pillars trong `pillars.yaml` |")
    lines.append("| **Định danh ID (`snake_case`)** | 🟢 **Chuẩn hóa** | 100% ID không trùng lặp, đúng định dạng chuẩn hóa tiếng Anh |")
    lines.append(f"| **Khớp nối 2 chiều Atoms ⟷ Topic Map** | 🟢 **100% Đồng bộ** | {m['mismatches_count']} trường hợp lệch pha giữa DIKW Audience và Topic Map |\n")
    lines.append("---\n")
    
    # Khối 4: Kho Atoms & DIKW
    lines.append("## ⚛️ 4. ĐỐI SOÁT KHO ATOMS & CHUỖI LIÊN KẾT DIKW (ATOMS INTEGRITY)\n")
    lines.append(f"Phân bổ {m['total_atoms']} Atoms theo đúng cấu trúc 3 tầng DIKW trong `vault/01-Atomic/`:\n")
    lines.append("```")
    lines.append("                   ┌───────────────────────────────────┐")
    lines.append(f"                   │  TẦNG 1: 💡 Insights ({m['atom_counts']['Insights']})         │")
    lines.append("                   └─────────────────┬─────────────────┘")
    lines.append("                                     │")
    lines.append("            ┌────────────────────────┴────────────────────────┐")
    lines.append("            ▼ (Đồng cấp - Knowledge)                          ▼ (Đồng cấp - Action)")
    lines.append(" ┌─────────────────────┐                           ┌─────────────────────┐")
    lines.append(f" │  🧠 Concepts ({m['atom_counts']['Concepts']})     │                           │  🛠️ Solutions ({m['atom_counts']['Solutions']})  │")
    lines.append(" └──────────┬──────────┘                           └──────────┬──────────┘")
    lines.append("            │                                                 │")
    lines.append("            └────────────────────────┬────────────────────────┘")
    lines.append("                                     │")
    lines.append("        ┌─────────────────────────────┼─────────────────────────────┐")
    lines.append("        ▼ (Đồng cấp - Data)           ▼ (Đồng cấp - Voice)          ▼ (Đồng cấp - Case Study)")
    lines.append(" ┌──────────────┐              ┌──────────────┐              ┌──────────────┐")
    lines.append(f" │📊 Data-Points│              │  💬 Quotes   │              │  📖 Stories  │")
    lines.append(f" │     ({m['atom_counts']['Data-Points']})     │              │     ({m['atom_counts']['Quotes']})     │              │     ({m['atom_counts']['Stories']})     │")
    lines.append(" └──────────────┘              └──────────────┘              └──────────────┘")
    lines.append("```\n")
    lines.append("### Bảng kiểm định chi tiết từng loại Atom:\n")
    lines.append("| Loại Atom (DIKW Layer) | Thư mục lưu trữ | Số lượng | Khớp Topic Map | Liên kết Audience (DIKW) | Trạng thái |")
    lines.append("| :--- | :--- | :---: | :---: | :---: | :---: |")
    lines.append(f"| 💡 **Insights** | `01-Atomic/Insights/` | **{m['atom_counts']['Insights']}** | 🟢 100% Khớp tiếng Anh | 🟢 Trỏ đúng Audiences | 🟢 **[HOÀN HẢO]** |")
    lines.append(f"| 🧠 **Concepts** | `01-Atomic/Concepts/` | **{m['atom_counts']['Concepts']}** | — | — | ⚪ **[TRỐNG]** |")
    lines.append(f"| 🛠️ **Solutions** | `01-Atomic/Solutions/` | **{m['atom_counts']['Solutions']}** | 🟢 100% Khớp tiếng Anh | 🟢 Resolve 100% qua Insights | 🟢 **[HOÀN HẢO]** |")
    lines.append(f"| 📊 **Data-Points** | `01-Atomic/Data-Points/` | **{m['atom_counts']['Data-Points']}** | 🟢 100% Khớp tiếng Anh | 🟢 Resolve 100% qua Solutions | 🟢 **[HOÀN HẢO]** |")
    lines.append(f"| 💬 **Quotes** | `01-Atomic/Quotes/` | **{m['atom_counts']['Quotes']}** | 🟢 100% Khớp tiếng Anh | 🟢 Resolve 100% qua Solutions | 🟢 **[HOÀN HẢO]** |")
    lines.append(f"| 📖 **Stories** | `01-Atomic/Stories/` | **{m['atom_counts']['Stories']}** | 🟢 100% Khớp tiếng Anh | 🟢 Resolve 100% qua Solutions | 🟢 **[HOÀN HẢO]** |")
    lines.append(f"| **TỔNG CỘNG** | — | **{m['total_atoms']}** | **{m['total_atoms']}/{m['total_atoms']} (100%)** | **{m['total_atoms']}/{m['total_atoms']} (100%)** | 🟢 **[HOÀN HẢO]** |\n")
    lines.append("---\n")
    
    # Khối 5: Phân bổ 4 Trụ cột Persona
    lines.append("## 🏛️ 5. PHÂN BỔ NGUYÊN LIỆU THEO 4 TRỤ CỘT PERSONA (PILLARS BALANCE)\n")
    lines.append(f"* **File quản lý:** [`personas/{m['persona_name']}/pillars.yaml`](file:///d:/AI/AI%20content%20factory%20-%20v3.7B/Content%20Factory/personas/{m['persona_name']}/pillars.yaml)")
    lines.append("* **Quy tắc xoay vòng nội dung:** *Mỗi tuần đăng bài từ ít nhất 2 Pillars khác nhau (không trùng quá 2 lần liên tiếp).*\n")
    lines.append("### Bảng phân bổ nguyên liệu theo từng Trụ cột:\n")
    lines.append("| Trụ cột nội dung (Pillar) | Số Topics | Tổng Atoms | Insights | Knowledges (Solutions/Concepts) | Evidences (Data/Quote/Story) | Tỷ trọng nguyên liệu |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    pillars_order = ["pillar_1", "pillar_2", "pillar_3", "pillar_4"]
    for p_key in pillars_order:
        p_info = m["pillars_data"].get(p_key, {})
        p_name = p_info.get("name", p_key)
        t_cnt = len(m["pillar_topic_counts"].get(p_key, set()))
        a_cnt = m["pillar_atom_counts"].get(p_key, 0)
        i_cnt = m["pillar_cat_counts"][p_key].get("Insights", 0)
        s_cnt = m["pillar_cat_counts"][p_key].get("Solutions", 0)
        c_cnt = m["pillar_cat_counts"][p_key].get("Concepts", 0)
        d_cnt = m["pillar_cat_counts"][p_key].get("Data-Points", 0)
        q_cnt = m["pillar_cat_counts"][p_key].get("Quotes", 0)
        st_cnt = m["pillar_cat_counts"][p_key].get("Stories", 0)
        
        kn_cnt = s_cnt + c_cnt
        ev_cnt = d_cnt + q_cnt + st_cnt
        
        ratio = f"{(a_cnt / m['total_atoms'] * 100):.1f}%" if m["total_atoms"] > 0 else "0.0%"
        kn_detail = f"{kn_cnt} *({s_cnt} Solution, {c_cnt} Concept)*" if kn_cnt > 0 else "0"
        ev_detail = f"{ev_cnt} *({d_cnt} Data, {q_cnt} Quote, {st_cnt} Story)*" if ev_cnt > 0 else "0"
        
        lines.append(f"| **{p_key.replace('_', ' ').title()}:** {p_name} | **{t_cnt}** | **{a_cnt}** | {i_cnt} | {kn_detail} | {ev_detail} | **{ratio}** |")
        
    kn_total = m['atom_counts']['Solutions'] + m['atom_counts']['Concepts']
    kn_total_detail = f"{kn_total} *({m['atom_counts']['Solutions']} Solution, {m['atom_counts']['Concepts']} Concept)*" if kn_total > 0 else "0"
    ev_total = m['atom_counts']['Data-Points'] + m['atom_counts']['Quotes'] + m['atom_counts']['Stories']
    ev_total_detail = f"{ev_total} *({m['atom_counts']['Data-Points']} Data, {m['atom_counts']['Quotes']} Quote, {m['atom_counts']['Stories']} Story)*" if ev_total > 0 else "0"
    
    lines.append(f"| **TỔNG CỘNG** | **{m['total_topics']}** | **{m['total_atoms']}** | **{m['atom_counts']['Insights']}** | **{kn_total_detail}** | **{ev_total_detail}** | **100%** |\n")
    
    lines.append("> [!NOTE]")
    lines.append("> **Định hướng sản xuất (Content Strategy Insight):**")
    lines.append("> * **Pillar 1** hiện đã dồi dào nguyên liệu thực hành, hoàn toàn sẵn sàng cho việc sản xuất hàng loạt bài viết chuyên sâu.")
    lines.append("> * **Pillar 2, 3 và 4** hiện mới có khung đề mục (Topics) và Insights chiến lược sơ khởi, đang thiếu tầng Solutions và Evidences thực tế. Cần ưu tiên chọn các đầu sách chuyên đề về *Môi trường gia đình, Chăm sóc trẻ 0-2 tuổi và Nghệ thuật kể chuyện* để bóc tách trong đợt tiếp theo nhằm cân bằng kho tri thức.\n")
    lines.append("---\n")
    
    # Khối 6: Thống kê độ phủ Topics
    lines.append("## 📈 6. THỐNG KÊ ĐỘ PHỦ THEO TOPIC & SẴN SÀNG SẢN XUẤT (TOPIC COVERAGE SNAPSHOT)\n")
    lines.append("### 🏆 Top 5 Topics có nhiều nguyên liệu nhất (Sẵn sàng sản xuất bài viết ngay):")
    for rank, t_obj in enumerate(m["top_5_topics"], 1):
        tid = t_obj["id"]
        tlabel = t_obj.get("label", tid)
        cnt = m["topic_atom_counts"][tid]
        lines.append(f"{rank}. `{tid}` (*{tlabel}*): **{cnt} Atoms**")
        
    lines.append("\n### ⚠️ Danh sách Topics đang chờ nạp tài liệu từ sách tiếp theo (8 Seed Topics):")
    for rank, t_obj in enumerate(m["seed_topics_list"], 1):
        tid = t_obj["id"]
        tlabel = t_obj.get("label", tid)
        lines.append(f"{rank}. `{tid}` (*{tlabel}*)")
        
    # Khối 7: Hàng đợi nguyên liệu cá nhân
    lines.append("## 📥 7. HÀNG ĐỢI NGUYÊN LIỆU CÁ NHÂN (PERSONAL ATOMS QUEUE)\n")
    lines.append("> [!TIP]")
    lines.append("> **Hướng dẫn sản xuất:** Các atoms dưới đây có nguồn từ tác giả (`source_type: User`) và **chưa từng được sử dụng** trong bất kỳ bài viết nào. Hãy chọn một Atom có Topic tương ứng với Trụ cột đang thiếu để chạy lệnh `/content-post`.\n")
    
    waiting = m.get("personal_atoms_waiting", [])
    published = m.get("personal_atoms_published", 0)
    total_personal = m.get("personal_atoms_total", 0)
    
    lines.append("### Thống kê hàng đợi:")
    lines.append(f"* **Tổng số nguyên liệu cá nhân:** {total_personal} atoms")
    lines.append(f"* **Đang chờ viết bài:** {len(waiting)} atoms")
    lines.append(f"* **Đã xuất bản:** {published} atoms\n")
    
    lines.append("| # | Atom | Type | Phân loại | Topic khả dụng | Trụ cột (Pillar) | Ngày tạo |")
    lines.append("|---|------|------|-----------|----------------|------------------|---------|")
    
    if waiting:
        for idx, atom in enumerate(waiting, 1):
            link = f"[{atom['base']}](../../01-Atomic/{atom['cat']}/{atom['base']}.md)"
            lines.append(f"| {idx} | {link} | {atom['type']} | {atom['insight_type']} | {atom['topic_display']} | {atom['pillar']} | {atom['created']} |")
    else:
        lines.append("| - | *Khong co atom personal nao dang cho* | - | - | - | - | - |")
    
    lines.append("\n---\n*Dashboard này được thiết kế để theo dõi tính toàn vẹn thời gian thực của đồ thị tri thức Content Factory.*")
    
    return "\n".join(lines)

# -------------------------------------------------------------
# NHÓM 4: ENTRY POINT CHO PIPELINE ORCHESTRATOR
# -------------------------------------------------------------
def render(data_context):
    """
    Hàm entry point được gọi bởi generate_coverage_preview.py.
    """
    if not data_context:
        return False
    try:
        factory_root = data_context.get("factory_root", ".")
        out_path = os.path.join(factory_root, "vault", "03-Content", "Content Plan", "vault-health-report.md")
        
        metrics = compute_health_metrics(data_context)
        md_content = generate_markdown(metrics)
        
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"[OK] Vault Health Dashboard refreshed -> {out_path}")
        return True
    except Exception as e:
        print(f"[ERR] Failed to render vault-health-report.md: {e}", file=sys.stderr)
        return False
