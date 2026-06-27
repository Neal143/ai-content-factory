# -*- coding: utf-8 -*-
"""
Ten file: generate_insights.py
Last update: 26/06/2026 15:16 (GMT+7)
Vai tro: Script Python tao file vat ly cho cac Insight tu cuoc phong van Persona.
Khi nao dung: Chay tu command line hoac duoc goi tu workflow khi tao Insight.
Output: Cac file Markdown cua Insight trong thu muc vault dau ra (01-Atomic/Insights) voi Schema B.
Tom tat logic hoat dong:
  1. Doc file JSON payload chua mang cac insight.
  2. Doc file template.md co san.
  3. Lap qua tung insight trong payload, sinh slug tieng Viet khong dau cho ten file tu headline.
  4. Giai quyet trung ten file bang cach them hau to so tang dan (-2, -3,...).
  5. Dinh dang truong topics thanh JSON array string tuong thich voi YAML.
  6. Thay the cac placeholder trong template bang du lieu insight (bao gom ca topics).
  7. Ghi noi dung ra file vat ly.
  8. (Moi) Neu co --username: cap nhat file_ref va file_link trong pillars.yaml (thay PENDING + backfill).
  
Che do --backfill-only: Chi chay buoc 8 (khong tao file .md), dung de them file_link cho du lieu cu.
"""

# ==========================================
# NHOM 1: CAC THU VIEN HE THONG
# ==========================================
import sys
import json
import os
import re
import unicodedata
from datetime import datetime
from urllib.parse import quote

# ==========================================
# NHOM 2: HAM TRO GIUP (HELPERS)
# ==========================================
def slugify(value):
    """
    Chuyen doi chuoi tieng Viet co dau thanh slug khong dau, chu thuong, noi bang gach ngang.
    Xu ly dac biet ky tu 'd' va 'D' vi unicodedata normalize khong tu chuyen sang ASCII 'd'.
    """
    value = str(value).replace('d', 'd').replace('D', 'd')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value).strip('-')
    return value

def backfill_pillars(username, slug_map, workspace_root):
    """
    Cap nhat file_ref va file_link trong pillars.yaml.
    Xu ly 2 truong hop:
      1. PENDING_N placeholder (flow moi) -> thay bang gia tri that
      2. file_ref co san nhung thieu file_link (backfill du lieu cu) -> chen file_link
    
    Args:
        username: Ten Persona (VD: "Neal")
        slug_map: dict {index: final_slug} (VD: {0: "so-ai-thay-the", 1: "muon-lam-cha-me"})
        workspace_root: Duong dan tuyet doi den thu muc Content Factory
    """
    pillars_path = os.path.join(workspace_root, "personas", username, "pillars.yaml")
    if not os.path.exists(pillars_path):
        print(f"[WARN] Khong tim thay: {pillars_path}")
        return
    
    with open(pillars_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    insights_dir = os.path.join(workspace_root, "vault", "01-Atomic", "Insights")
    original_content = content  # Luu ban goc de so sanh
    
    # === BUOC 1: Thay the PENDING_N placeholder (flow moi) ===
    # Thu tu QUAN TRONG: thay "[[PENDING_N]]" TRUOC, roi "PENDING_N" SAU
    for idx, slug in slug_map.items():
        abs_path = os.path.join(insights_dir, f"{slug}.md").replace("\\", "/")
        encoded_path = quote(abs_path, safe=':/')  # Encode spaces thanh %20 de VS Code nhan dung URI
        content = content.replace(f'"[[PENDING_{idx}]]"', f'"[[{slug}]]"')
        content = content.replace(f'"PENDING_{idx}"', f'"file:///{encoded_path}"')
    
    # === BUOC 2: Backfill file_link cho du lieu cu (thieu file_link) ===
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        # Tim dong file_ref co gia tri that (khong phai PENDING)
        m = re.match(r'^(\s*)file_ref:\s*"\[\[([^\]]+)\]\]"', line)
        if m and 'PENDING_' not in line:
            indent = m.group(1)
            slug = m.group(2)
            # Kiem tra dong tiep theo co phai file_link khong
            next_line = lines[i + 1] if i + 1 < len(lines) else ''
            if 'file_link:' not in next_line:
                abs_path = os.path.join(insights_dir, f"{slug}.md").replace("\\", "/")
                encoded_path = quote(abs_path, safe=':/')  # Encode spaces thanh %20
                new_lines.append(f'{indent}file_link: "file:///{encoded_path}"')
    content = '\n'.join(new_lines)
    
    # Chi ghi file khi co thay doi
    if content != original_content:
        with open(pillars_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Da cap nhat pillars.yaml cho [{username}]")
    else:
        print(f"[INFO] pillars.yaml [{username}] khong can cap nhat")

def backfill_audience(username, workspace_root):
    """
    Reverse Lookup: Tim file Audience vat ly trong vault/01-Atomic/Audiences/
    bang cach so khop 3 truong JTBD voi Frontmatter cua file .md.
    Neu tim thay, tu dong ghi file_ref va file_link vao audience.yaml.
    Luon ghi de gia tri hien tai de dam bao chinh xac 100%.
    
    Args:
        username: Ten Persona (VD: "Neal")
        workspace_root: Duong dan tuyet doi den thu muc Content Factory
    """
    audience_yaml_path = os.path.join(workspace_root, "personas", username, "audience.yaml")
    audiences_dir = os.path.join(workspace_root, "vault", "01-Atomic", "Audiences")
    
    if not os.path.exists(audience_yaml_path):
        print(f"[WARN] Khong tim thay: {audience_yaml_path}")
        return
    if not os.path.exists(audiences_dir):
        print(f"[WARN] Khong tim thay thu muc: {audiences_dir}")
        return
    
    with open(audience_yaml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # === BUOC 1: Doc 3 truong JTBD tu audience.yaml ===
    jp = re.search(r'audience_Job_performer:\s*"([^"]*)"', content)
    mj = re.search(r'audience_main_job:\s*"([^"]*)"', content)
    ac = re.search(r'audience_circumstance:\s*"([^"]*)"', content)
    
    if not all([jp, mj, ac]):
        print(f"[WARN] audience.yaml [{username}] thieu truong JTBD, bo qua")
        return
    
    target_jp = jp.group(1)
    target_mj = mj.group(1)
    target_ac = ac.group(1)
    
    # === BUOC 2: Quet vault/01-Atomic/Audiences/ tim file khop JTBD ===
    matched_file = None
    for fname in os.listdir(audiences_dir):
        if not fname.endswith('.md') or fname.startswith('_'):
            continue
        fpath = os.path.join(audiences_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Parse Frontmatter (giua 2 dau ---)
        fm_match = re.match(r'^---\s*\n(.*?)\n---', md_content, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        
        # So khop 3 truong JTBD
        fm_jp = re.search(r'audience_Job_performer:\s*"([^"]*)"', fm)
        fm_mj = re.search(r'audience_main_job:\s*"([^"]*)"', fm)
        fm_ac = re.search(r'audience_circumstance:\s*"([^"]*)"', fm)
        
        if (fm_jp and fm_mj and fm_ac and
            fm_jp.group(1) == target_jp and
            fm_mj.group(1) == target_mj and
            fm_ac.group(1) == target_ac):
            matched_file = fname
            break
    
    if not matched_file:
        print(f"[WARN] Khong tim thay file Audience khop JTBD trong {audiences_dir}")
        return
    
    # === BUOC 3: Sinh file_ref va file_link ===
    slug = os.path.splitext(matched_file)[0]
    abs_path = os.path.join(audiences_dir, matched_file).replace("\\", "/")
    encoded_path = quote(abs_path, safe=':/')
    file_ref_value = f'"[[{slug}]]"'
    file_link_value = f'"file:///{encoded_path}"'
    
    # === BUOC 4: Ghi vao audience.yaml (luon ghi de) ===
    lines = content.split('\n')
    new_lines = []
    has_file_ref = any(line.strip().startswith('file_ref:') for line in lines)
    inserted = False
    
    for line in lines:
        stripped = line.strip()
        # Neu da co truong cu -> ghi de gia tri moi
        if stripped.startswith('file_ref:'):
            new_lines.append(f'file_ref: {file_ref_value}')
            continue
        if stripped.startswith('file_link:'):
            new_lines.append(f'file_link: {file_link_value}')
            continue
        new_lines.append(line)
        # Neu chua co truong nao -> chen sau audience_circumstance
        if not inserted and not has_file_ref and 'audience_circumstance:' in line:
            new_lines.append(f'file_ref: {file_ref_value}')
            new_lines.append(f'file_link: {file_link_value}')
            inserted = True
    
    new_content = '\n'.join(new_lines)
    if new_content != content:
        with open(audience_yaml_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[OK] Da cap nhat audience.yaml [{username}] voi file_ref va file_link")
    else:
        print(f"[INFO] audience.yaml [{username}] khong can cap nhat")

# ==========================================
# NHOM 3: LOGIC CHINH XU LY GENERATE INSIGHTS
# ==========================================
def generate_insights(payload_path, template_path, output_dir, target_audience, username=None):
    """
    Doc payload JSON, parse tung insight, render qua template va ghi file vat ly.
    Neu co username, tu dong cap nhat file_ref va file_link trong pillars.yaml.
    """
    # Doc payload tu file JSON
    with open(payload_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
        
    # Doc template Markdown
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
        
    # Tao thu muc dau ra neu chua co
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Ho tro ca 2 dinh dang: array truc tiep hoac object {"insights": [...]}
    if isinstance(payload, list):
        insights_list = payload
    else:
        insights_list = payload.get("insights", [])

    slug_map = {}  # Map: index -> final_slug (sau khi xu ly trung ten)

    for idx, item in enumerate(insights_list):
        insight_type = item.get("insight_type", "insight")
        headline = item.get("headline", "Untitled")
        raw_payload = item.get("raw_payload", "")
        llm_explain = item.get("llm_explain", "")
        
        # Doc truong topics (bo sung cho Schema B)
        topics = item.get("topics", [])
        
        # Sinh ten file tu headline
        slug = slugify(headline)
        filename = f"{slug}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Xu ly chong trung ten file bang cach them hau to so tang dan (-2, -3, ...)
        if os.path.exists(filepath):
            i = 2
            while os.path.exists(os.path.join(output_dir, f"{slug}-{i}.md")):
                i += 1
            filename = f"{slug}-{i}.md"
            filepath = os.path.join(output_dir, filename)
        
        # Luu slug cuoi cung (ke ca hau to dedup) de backfill pillars.yaml
        final_slug = os.path.splitext(filename)[0]
        slug_map[idx] = final_slug
        
        # Format list topics thanh chuoi JSON array tuong thich tot voi YAML
        topics_yaml = json.dumps(topics, ensure_ascii=False)
        
        # Thuc hien thay the cac bien trong template
        file_content = template.replace("{{type}}", str(insight_type).upper())\
                               .replace("{{date}}", today)\
                               .replace("{{name}}", headline)\
                               .replace("{{topics}}", topics_yaml)\
                               .replace("{{target_audience}}", target_audience)\
                               .replace("{{raw_payload}}", raw_payload)\
                               .replace("{{llm_explain}}", llm_explain)
                               
        # Ghi noi dung da render ra file vat ly
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        print(f"[OK] Da tao file: {filepath}")

    # Sau khi tao xong tat ca file, cap nhat pillars.yaml + audience.yaml
    if username:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
        if slug_map:
            backfill_pillars(username, slug_map, workspace_root)
        backfill_audience(username, workspace_root)

# ==========================================
# NHOM 4: KHOI CHAY SCRIPT TU COMMAND LINE (CLI ENTRYPOINT)
# ==========================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tao file Insight vat ly tu JSON payload")
    parser.add_argument("--payload", required=False, default=None, help="Duong dan den file JSON payload")
    parser.add_argument("--template", required=False, default=None, help="Duong dan den template insight.md")
    parser.add_argument("--output", required=False, default=None, help="Thu muc dau ra (vd: 01-Atomic/Insights)")
    parser.add_argument("--audience", required=False, default=None, help="Chuoi dinh danh Big Audience")
    parser.add_argument("--username", required=False, default=None, help="Ten Persona (VD: Neal). Neu co, script se cap nhat file_ref va file_link trong pillars.yaml")
    parser.add_argument("--backfill-only", action="store_true", help="Chi chay backfill pillars.yaml (them file_link), khong tao file .md")
    
    args = parser.parse_args()
    
    if args.backfill_only:
        # Che do backfill: chi them file_link cho du lieu cu, khong tao file
        if not args.username:
            parser.error("--username bat buoc khi dung --backfill-only")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
        backfill_pillars(args.username, {}, workspace_root)
        backfill_audience(args.username, workspace_root)
    else:
        # Che do binh thuong: tao file + backfill (neu co username)
        if not all([args.payload, args.template, args.output, args.audience]):
            parser.error("--payload, --template, --output, --audience bat buoc khi khong dung --backfill-only")
        generate_insights(args.payload, args.template, args.output, args.audience, args.username)
