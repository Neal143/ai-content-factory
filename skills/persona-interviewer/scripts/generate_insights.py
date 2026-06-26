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

    # Sau khi tao xong tat ca file, cap nhat pillars.yaml neu co username
    if username and slug_map:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
        backfill_pillars(username, slug_map, workspace_root)

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
    else:
        # Che do binh thuong: tao file + backfill (neu co username)
        if not all([args.payload, args.template, args.output, args.audience]):
            parser.error("--payload, --template, --output, --audience bat buoc khi khong dung --backfill-only")
        generate_insights(args.payload, args.template, args.output, args.audience, args.username)
