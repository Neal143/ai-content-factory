# -*- coding: utf-8 -*-
"""
Tên file: generate_insights.py
Last update: 27/05/2026 00:20 (GMT+7)
Vai trò: Script Python tạo file vật lý cho các Insight từ cuộc phỏng vấn Persona.
Được sử dụng khi nào: Chạy từ command line hoặc được gọi từ workflow khi tạo Insight.
Output: Các file Markdown của Insight trong thư mục vault đầu ra (01-Atomic/Insights) với Schema B mới.
Tóm tắt logic hoạt động:
  1. Đọc file JSON payload chứa mảng các insight.
  2. Đọc file template.md có sẵn.
  3. Lặp qua từng insight trong payload, sinh slug tiếng Việt không dấu cho tên file từ headline.
  4. Giải quyết trùng tên file bằng cách thêm hậu tố số tăng dần (-2, -3,...).
  5. Định dạng trường topics thành JSON array string tương thích với YAML.
  6. Thay thế các placeholder trong template bằng dữ liệu insight (bao gồm cả topics).
  7. Ghi nội dung ra file vật lý.
"""

# ==========================================
# NHÓM 1: CÁC THƯ VIỆN HỆ THỐNG
# ==========================================
import sys
import json
import os
import re
import unicodedata
from datetime import datetime

# ==========================================
# NHÓM 2: HÀM TRỢ GIÚP (HELPERS)
# ==========================================
def slugify(value):
    """
    Chuyển đổi chuỗi tiếng Việt có dấu thành slug không dấu, chữ thường, nối bằng gạch ngang.
    Xử lý đặc biệt ký tự 'đ' và 'Đ' vì unicodedata normalize không tự chuyển sang ASCII 'd'.
    """
    value = str(value).replace('đ', 'd').replace('Đ', 'd')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value).strip('-')
    return value

# ==========================================
# NHÓM 3: LOGIC CHÍNH XỬ LÝ GENERATE INSIGHTS
# ==========================================
def generate_insights(payload_path, template_path, output_dir, target_audience):
    """
    Đọc payload JSON, parse từng insight, render qua template và ghi file vật lý.
    """
    # Đọc payload từ file JSON
    with open(payload_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)
        
    # Đọc template Markdown
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
        
    # Tạo thư mục đầu ra nếu chưa có
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Ho tro ca 2 dinh dang: array truc tiep hoac object {"insights": [...]}
    if isinstance(payload, list):
        insights_list = payload
    else:
        insights_list = payload.get("insights", [])

    for item in insights_list:
        insight_type = item.get("insight_type", "insight")
        headline = item.get("headline", "Untitled")
        raw_payload = item.get("raw_payload", "")
        llm_explain = item.get("llm_explain", "")
        
        # Đọc trường topics (mới bổ sung cho Schema B)
        topics = item.get("topics", [])
        
        # Sinh tên file từ headline
        slug = slugify(headline)
        filename = f"{slug}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Xử lý chống trùng tên file bằng cách thêm hậu tố số tăng dần (-2, -3, ...)
        if os.path.exists(filepath):
            i = 2
            while os.path.exists(os.path.join(output_dir, f"{slug}-{i}.md")):
                i += 1
            filename = f"{slug}-{i}.md"
            filepath = os.path.join(output_dir, filename)
        
        # Format list topics thành chuỗi JSON array tương thích tốt với YAML (ví dụ: ["nao_bo", "cam_xuc"])
        topics_yaml = json.dumps(topics, ensure_ascii=False)
        
        # Thực hiện thay thế các biến trong template
        file_content = template.replace("{{type}}", str(insight_type).upper())\
                               .replace("{{date}}", today)\
                               .replace("{{name}}", headline)\
                               .replace("{{topics}}", topics_yaml)\
                               .replace("{{target_audience}}", target_audience)\
                               .replace("{{raw_payload}}", raw_payload)\
                               .replace("{{llm_explain}}", llm_explain)
                               
        # Ghi nội dung đã render ra file vật lý
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        print(f"[OK] Da tao file: {filepath}")

# ==========================================
# NHÓM 4: KHỞI CHẠY SCRIPT TỪ COMMAND LINE (CLI ENTRYPOINT)
# ==========================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tạo file Insight vật lý từ JSON payload")
    parser.add_argument("--payload", required=True, help="Đường dẫn đến file JSON payload")
    parser.add_argument("--template", required=True, help="Đường dẫn đến template insight.md")
    parser.add_argument("--output", required=True, help="Thư mục đầu ra (vd: 01-Atomic/Insights)")
    parser.add_argument("--audience", required=True, help="Chuỗi định danh Big Audience (Ví dụ: [Job_performer]_[Main_job]_[Circumstances])")
    
    args = parser.parse_args()
    generate_insights(args.payload, args.template, args.output, args.audience)
