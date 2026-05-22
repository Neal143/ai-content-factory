import sys
import json
import os
import re
import unicodedata
from datetime import datetime

def slugify(value):
    """
    Chuyển đổi chuỗi tiếng Việt có dấu thành slug không dấu, chữ thường, gạch ngang.
    Xử lý đặc biệt: 'đ' -> 'd' (ký tự không có ASCII equivalent).
    """
    value = str(value).replace('đ', 'd').replace('Đ', 'd')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value).strip('-')
    return value

def generate_insights(payload_path, template_path, output_dir, target_audience):
    with open(payload_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
        
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
        
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    for item in payload.get("insights", []):
        insight_type = item.get("insight_type", "insight")
        headline = item.get("headline", "Untitled")
        raw_payload = item.get("raw_payload", "")
        llm_explain = item.get("llm_explain", "")
        
        slug = slugify(headline)
        filename = f"{slug}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Chống trùng tên file
        if os.path.exists(filepath):
            i = 2
            while os.path.exists(os.path.join(output_dir, f"{slug}-{i}.md")):
                i += 1
            filename = f"{slug}-{i}.md"
            filepath = os.path.join(output_dir, filename)
        
        # Replace variables
        file_content = template.replace("{{type}}", str(insight_type).upper())\
                               .replace("{{date}}", today)\
                               .replace("{{name}}", headline)\
                               .replace("{{target_audience}}", target_audience)\
                               .replace("{{raw_payload}}", raw_payload)\
                               .replace("{{llm_explain}}", llm_explain)
                               
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        print(f"[OK] Da tao file: {filepath}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo file Insight vật lý từ JSON payload")
    parser.add_argument("--payload", required=True, help="Đường dẫn đến file JSON payload")
    parser.add_argument("--template", required=True, help="Đường dẫn đến template insight.md")
    parser.add_argument("--output", required=True, help="Thư mục đầu ra (vd: 01-Atomic/Insights)")
    parser.add_argument("--audience", required=True, help="Chuỗi định danh Big Audience (Ví dụ: [Job_performer]_[Main_job]_[Circumstances])")
    
    args = parser.parse_args()
    generate_insights(args.payload, args.template, args.output, args.audience)
