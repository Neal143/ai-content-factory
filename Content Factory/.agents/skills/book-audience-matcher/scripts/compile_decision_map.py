# ==============================================================================
# Tên file: compile_decision_map.py
# Last update: 30/05/2026 15:32 (GMT+7)
# Vai trò: Biên dịch kết quả batch decisions thành audience_decision_map.json chuẩn schema.
# Sử dụng khi: Giai đoạn 2 (Bước 2.4) của book-audience-matcher — sau khi toàn bộ batch đã qua validation.
# Output: file audience_decision_map.json (đúng schema của downstream).
# Tóm tắt logic hoạt động:
#   1. Đọc internal_map.json, collected_decisions.json và _audience_index.yaml.
#   2. Validate tính đầy đủ (completeness) của các UID được quyết định.
#   3. Thay thế tham chiếu UID nội bộ trong internal_parents sang audience_filename thực tế.
#   4. Ánh xạ từ chunk_mapping sang các quyết định và gộp phả hệ Parent.
#   5. Tự động tính toán Level dựa trên quy tắc DAG (Big -> Little -> Micro).
#   6. Kiểm tra cấu trúc output, sắp xếp và lưu ra file đích.
# ==============================================================================

import sys
import json
import argparse
import yaml

# ==============================================================================
# Nhóm 1: Các hàm helper tra cứu thông tin phả hệ và Index
# ==============================================================================
def get_existing_parents(audience_filename, index_data):
    """
    Tra cứu danh sách parent hiện có của một audience từ sổ tay _audience_index.yaml.
    """
    if not index_data or "audiences" not in index_data:
        return []
    
    # Chuẩn hóa tên file tìm kiếm (loại bỏ dấu ngoặc vuông nếu có)
    target_slug = audience_filename.strip("[]")
    
    for aud in index_data["audiences"]:
        file_ref = aud.get("file_ref", "")
        # So khớp slug tên file vật lý
        if file_ref.strip("[]") == target_slug:
            return aud.get("parent_audience", [])
            
    return []

def get_level(parent_ref, index_data):
    """
    Tra cứu cấp độ (Level) của parent từ sổ tay _audience_index.yaml.
    Nếu không tìm thấy, mặc định trả về 'big' (fallback an toàn).
    """
    if not index_data or "audiences" not in index_data:
        return "big"
        
    target_slug = parent_ref.strip("[]")
    
    for aud in index_data["audiences"]:
        file_ref = aud.get("file_ref", "")
        if file_ref.strip("[]") == target_slug:
            return aud.get("audience_level", "big")
            
    return "big"

# ==============================================================================
# Nhóm 2: Logic biên dịch chính
# ==============================================================================
def compile_map(internal_map_path, collected_decisions_path, index_path, output_path):
    """
    Đọc các nguồn dữ liệu, thực hiện Reference Substitution, tính Level, validate và ghi kết quả.
    """
    # 1. Đọc các file dữ liệu đầu vào
    try:
        with open(internal_map_path, 'r', encoding='utf-8') as f:
            internal_map = json.load(f)
    except Exception as e:
        sys.exit(f"❌ Không thể đọc file internal_map: {e}")

    try:
        with open(collected_decisions_path, 'r', encoding='utf-8') as f:
            collected_decisions = json.load(f)
    except Exception as e:
        sys.exit(f"❌ Không thể đọc file collected_decisions: {e}")

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = yaml.safe_load(f)
            if index_data is None:
                index_data = {"audiences": []}
    except Exception as e:
        sys.exit(f"❌ Không thể đọc file audience_index: {e}")

    chunk_mapping = internal_map.get("chunk_mapping", {})
    unique_audiences = internal_map.get("unique_audiences", [])

    # 2. Kiểm tra tính đầy đủ (Completeness Verification)
    all_uids = {ua["uid"] for ua in unique_audiences}
    decision_uids = {d["uid"] for d in collected_decisions}
    missing = all_uids - decision_uids
    if missing:
        sys.exit(f"❌ Thiếu decisions cho UIDs: {missing}")

    # 2b. Validate chunk_mapping: mọi UID trong chunk_mapping phải tồn tại trong unique_audiences
    chunk_mapping_uids = set(chunk_mapping.values())
    invalid_uids = chunk_mapping_uids - all_uids
    if invalid_uids:
        sys.exit(f"❌ chunk_mapping chứa UID không có trong unique_audiences: {invalid_uids}")

    # 3. Xây dựng bảng tra cứu nhanh từ UID -> Quyết định
    uid_decision = {d["uid"]: d for d in collected_decisions}
    unique_audiences_by_uid = {ua["uid"]: ua for ua in unique_audiences}

    # 4. Thực hiện Reference Substitution
    # LLM lưu internal_parents dạng UIDs, ta cần phân giải thành [[audience_filename]] thực tế của cha
    for ua in unique_audiences:
        resolved_parents = []
        for parent_uid in ua.get("internal_parents", []):
            if parent_uid in uid_decision:
                parent_decision = uid_decision[parent_uid]
                resolved_ref = f"[[{parent_decision['audience_filename']}]]"
                resolved_parents.append(resolved_ref)
            else:
                print(f"⚠️ Cảnh báo: Không tìm thấy parent UID {parent_uid} trong collected decisions")
        ua["_resolved_internal_parents"] = resolved_parents

    # 5. Phẳng hóa chunk_mapping sang mảng Decision Map
    decision_map = []
    for key, uid in chunk_mapping.items():
        decision = uid_decision[uid]
        ua = unique_audiences_by_uid[uid]

        # Phân loại theo hành động Merge hoặc Create để xử lý parent
        if decision["action"] == "create":
            # Tạo mới: phả hệ = parent nội bộ đã phân giải + parent ngoại biên được chỉ định từ LLM
            all_parents = ua.get("_resolved_internal_parents", []) + decision.get("external_parents", [])
        else:
            # Gộp: chỉ append các parent nội bộ mới phát sinh mà file cũ trong Index chưa có
            existing_parents = get_existing_parents(decision["audience_filename"], index_data)
            resolved_internal = ua.get("_resolved_internal_parents", [])
            new_internal = [p for p in resolved_internal if p not in existing_parents]
            all_parents = new_internal

        # 6. Tính toán cấp độ (Level) dựa trên cấu trúc DAG
        if decision["action"] == "create":
            if not all_parents:
                level = "big"
            else:
                # Tìm parent có thứ tự level cao nhất (big > little > micro)
                parent_levels = [get_level(p, index_data) for p in all_parents]
                rank = {"big": 0, "little": 1, "micro": 2}
                
                # min_level tương đương với level lớn nhất/root nhất (gần big nhất)
                min_level = min(parent_levels, key=lambda x: rank.get(x, 0))
                
                # Quy tắc tịnh tiến cấp độ kế cận:
                # - Nếu cha lớn nhất là 'big' -> con là 'little'
                # - Nếu cha lớn nhất là 'little' hoặc 'micro' -> con là 'micro'
                level = "little" if min_level == "big" else "micro"
        else:
            # Merge: Giữ nguyên level của file cũ (đã được LLM đọc và xác nhận từ Index)
            level = decision["audience_level"]

        # Định dạng output khớp 100% với schema downstream yêu cầu
        entry = {
            "scope": "book" if key == "book" else "chunk",
            "chunk_index": None if key == "book" else int(key),
            "action": decision["action"],
            "audience_filename": decision["audience_filename"],
            "audience_level": level,
            "parent_audience": all_parents
        }
        decision_map.append(entry)

    # 7. Xác thực cấu trúc đầu ra (Validation)
    required_fields = {"scope", "chunk_index", "action", "audience_filename", "audience_level", "parent_audience"}
    for idx, entry in enumerate(decision_map):
        missing_fields = required_fields - set(entry.keys())
        if missing_fields:
            sys.exit(f"❌ Quyết định thứ {idx} thiếu trường bắt buộc: {missing_fields}")

    # Sắp xếp danh sách đầu ra: Book trước, sau đó tới các Chunk có Index tăng dần
    decision_map.sort(key=lambda x: (0 if x["scope"] == "book" else 1, x["chunk_index"] or 0))

    # Ghi file JSON kết quả cuối cùng
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(decision_map, f, ensure_ascii=False, indent=2)
    except Exception as e:
        sys.exit(f"❌ Không thể ghi file output {output_path}: {e}")

    print(f"✅ Decision Map: {len(decision_map)} entries → {output_path}")

# ==============================================================================
# Nhóm 3: Nhận diện CLI và thực thi
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Biên dịch quyết định batch thành map hoàn chỉnh")
    parser.add_argument("--internal-map", type=str, required=True, help="Đường dẫn file internal_map.json")
    parser.add_argument("--collected-decisions", type=str, required=True, help="Đường dẫn file collected_decisions.json")
    parser.add_argument("--audience-index", type=str, required=True, help="Đường dẫn file _audience_index.yaml")
    parser.add_argument("--output", type=str, required=True, help="Đường dẫn file ghi kết quả")

    args = parser.parse_args()
    compile_map(args.internal_map, args.collected_decisions, args.audience_index, args.output)
