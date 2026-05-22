"""
TÊN SCRIPT: write_audience_files.py
VAI TRÒ: Tạo file Audience vật lý (.md) và cập nhật _audience_index.yaml.
         Nhận 2 nguồn dữ liệu: Decision Map (action/filename/level/parent)
         và Calibrated JTBD (performer/main_job/circumstance/aliases).
         Script join 2 nguồn bằng chunk_index (integer) hoặc scope="book".
KHI NÀO SỬ DỤNG: Giai đoạn 3 của book-audience-matcher.
INPUT:  --decision-map (JSON), --calibrated-jtbd (JSON), --vault-root (path)
OUTPUT: File .md trong vault/01-Atomic/Audiences/, entries mới trong _audience_index.yaml

TÓM TẮT LOGIC:
  1. Đọc 2 file JSON đầu vào
  2. Join Decision Map với Calibrated JTBD bằng chunk_index/scope
  3. Validate: 7 field bắt buộc cho mỗi entry create
  4. Extract dashboard template từ audience-structure.md
  5. Tạo file .md (PyYAML frontmatter + dashboard body)
  6. Cập nhật _audience_index.yaml (full re-serialize bằng PyYAML)
  7. Báo cáo tóm tắt
"""

import os
import sys
import re
import json
import yaml
import argparse


# ────────────────────────────────────────────────────────────────
# Nhóm 1: Join — Ghép 2 nguồn dữ liệu bằng chunk_index/scope
# ────────────────────────────────────────────────────────────────

def join_data(decision_map, calibrated_jtbd):
    """Ghép Decision Map với Calibrated JTBD.

    Join logic (dùng field scope + chunk_index):
    - scope="book": match calibrated JTBD entry có scope="book"
    - scope="chunk": match calibrated JTBD entry có chunk_index=N
      Nếu Agent quên chunk_index cho chunk → KeyError → fail loud
      (không silent match nhầm vào book)

    Returns: list các entry đã merge đầy đủ (chỉ action=create).
    Fail loud nếu join thất bại cho bất kỳ entry create nào.
    """
    # Build lookup từ calibrated JTBD
    book_jtbd = None
    chunk_lookup = {}  # chunk_index (int) → jtbd entry
    for jtbd in calibrated_jtbd:
        if jtbd.get("scope") == "book":
            book_jtbd = jtbd
        else:
            idx = jtbd.get("chunk_index")
            if idx is not None:
                chunk_lookup[idx] = jtbd

    # Join từng entry create trong Decision Map (array)
    merged = []
    for entry in decision_map:
        if entry.get("action") != "create":
            continue

        scope = entry.get("scope")

        # Tìm JTBD tương ứng — phân nhánh bằng scope, không bằng null check
        if scope == "book":
            jtbd = book_jtbd
            if jtbd is None:
                sys.exit("❌ Entry scope=book nhưng không tìm thấy calibrated JTBD scope=book")
        elif scope == "chunk":
            chunk_index = entry["chunk_index"]  # KeyError nếu thiếu → fail loud
            jtbd = chunk_lookup.get(chunk_index)
            if jtbd is None:
                sys.exit(f"❌ Entry chunk_index={chunk_index} nhưng không tìm thấy calibrated JTBD tương ứng")
        else:
            sys.exit(f"❌ Entry có scope không hợp lệ: '{scope}' (cần 'book' hoặc 'chunk')")

        # Merge 2 nguồn
        merged.append({
            "audience_filename": entry["audience_filename"],
            "audience_level": entry["audience_level"],
            "parent_audience": entry.get("parent_audience", []),
            "audience_Job_performer": jtbd["audience_Job_performer"],
            "audience_main_job": jtbd["audience_main_job"],
            "audience_circumstance": jtbd["audience_circumstance"],
            "aliases": jtbd.get("aliases", []),
        })

    return merged


# ────────────────────────────────────────────────────────────────
# Nhóm 2: Validation — Kiểm tra entry đã merge
# ────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    "audience_filename", "audience_level", "parent_audience",
    "audience_Job_performer", "audience_main_job",
    "audience_circumstance", "aliases",
]
VALID_LEVELS = {"big", "little", "micro"}

def validate_entries(entries):
    """Validate tất cả entry đã merge. Fail-fast nếu lỗi."""
    errors = []
    for i, entry in enumerate(entries):
        label = entry.get("audience_filename", f"entry_{i}")
        for field in REQUIRED_FIELDS:
            if field not in entry:
                errors.append(f"'{label}': thiếu field '{field}'")
        level = entry.get("audience_level", "")
        if level not in VALID_LEVELS:
            errors.append(f"'{label}': audience_level='{level}' không hợp lệ")
        if not isinstance(entry.get("parent_audience"), list):
            errors.append(f"'{label}': parent_audience phải là mảng")
        if not isinstance(entry.get("aliases"), list):
            errors.append(f"'{label}': aliases phải là mảng")
    if errors:
        print("❌ VALIDATION FAILED:")
        for e in errors:
            print(f"   {e}")
        sys.exit(1)


# ────────────────────────────────────────────────────────────────
# Nhóm 3: Extract template từ audience-structure.md
# ────────────────────────────────────────────────────────────────

def load_dashboard_template(skill_root):
    """Đọc dashboard template từ audience-structure.md (DRY — single source of truth).

    Extract nội dung trong code fence ```markdown ... ``` ở Section 3.
    Fail loud nếu không tìm thấy.
    """
    template_path = os.path.join(skill_root, "references", "audience-structure.md")
    if not os.path.isfile(template_path):
        sys.exit(f"❌ Không tìm thấy: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(
        r'## 3\. Khung Dashboard.*?````markdown\n(.*?)````',
        content, re.DOTALL
    )
    if not match:
        sys.exit("❌ Không extract được dashboard template từ audience-structure.md")

    return match.group(1)


# ────────────────────────────────────────────────────────────────
# Nhóm 4: Tạo file Audience .md
# ────────────────────────────────────────────────────────────────

def build_frontmatter(entry):
    """Sinh YAML frontmatter từ entry đã merge. PyYAML serialize — 100% YAML hợp lệ."""
    fm = {
        "audience_level": entry["audience_level"],
        "audience_Job_performer": entry["audience_Job_performer"],
        "audience_main_job": entry["audience_main_job"],
        "audience_circumstance": entry["audience_circumstance"],
        "vivid_circumstances": [],
        "vivid_circumstances_reserve": [],
        "parent_audience": entry["parent_audience"],
        "aliases": entry["aliases"],
    }
    yaml_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---"


def write_audience_file(entry, audiences_dir, dashboard_template):
    """Tạo 1 file Audience .md. Skip nếu đã tồn tại. Atomic write."""
    filename = entry["audience_filename"]
    if not filename.endswith(".md"):
        filename += ".md"
    filepath = os.path.join(audiences_dir, filename)

    if os.path.exists(filepath):
        print(f"  ⏭️ SKIP (đã tồn tại): {filename}")
        return False

    frontmatter = build_frontmatter(entry)

    # Thay placeholder trong dashboard template
    body = dashboard_template.replace("[Job_performer]", entry["audience_Job_performer"])
    body = body.replace("[Main_job]", entry["audience_main_job"])
    body = body.replace("[Circumstance]", entry["audience_circumstance"])

    content = f"{frontmatter}\n{body}\n"

    # Atomic write
    tmp_path = filepath + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, filepath)

    print(f"  ✅ Tạo: {filename}")
    return True


# ────────────────────────────────────────────────────────────────
# Nhóm 5: Cập nhật _audience_index.yaml (full re-serialize)
# ────────────────────────────────────────────────────────────────

def update_audience_index(entries, index_path):
    """Cập nhật _audience_index.yaml.

    Logic:
    1. Đọc file, tách header comments khỏi body YAML
    2. Parse body bằng PyYAML
    3. Dedup by id — skip entry đã tồn tại
    4. Append entries mới
    5. Full re-serialize body bằng PyYAML
    6. Ghép header + body, atomic write
    """
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tách header (comment lines + dòng trống ở đầu)
    lines = content.split("\n")
    header_lines = []
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
            body_start = i + 1
        else:
            break
    header = "\n".join(header_lines)
    body = "\n".join(lines[body_start:])

    # Parse body
    data = yaml.safe_load(body) or {}
    audience_list = data.get("audiences", [])
    if not isinstance(audience_list, list):
        audience_list = []

    existing_ids = {e.get("id") for e in audience_list}

    # Append entries mới
    added = 0
    for entry in entries:
        entry_id = entry["audience_filename"].replace("-", "_")
        if entry_id in existing_ids:
            print(f"  ⏭️ INDEX SKIP (đã tồn tại): {entry_id}")
            continue

        index_entry = {
            "id": entry_id,
            "file_ref": f"[[{entry['audience_filename']}]]",
            "audience_level": entry["audience_level"],
            "audience_Job_performer": entry["audience_Job_performer"],
            "audience_main_job": entry["audience_main_job"],
            "audience_circumstance": entry["audience_circumstance"],
            "parent_audience": entry["parent_audience"],
            "aliases": entry["aliases"],
        }
        audience_list.append(index_entry)
        existing_ids.add(entry_id)
        added += 1

    if added == 0:
        print("  ℹ️ Không có entry mới cần thêm vào index.")
        return 0

    data["audiences"] = audience_list
    new_body = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    new_content = header + "\n" + new_body

    # Atomic write
    tmp_path = index_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    os.replace(tmp_path, index_path)

    print(f"  ✅ Index cập nhật: +{added} entries")
    return added


# ────────────────────────────────────────────────────────────────
# Nhóm 6: Main
# ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Tạo file Audience vật lý và cập nhật _audience_index.yaml"
    )
    parser.add_argument("--decision-map", required=True,
                        help="Path tới audience_decision_map.json")
    parser.add_argument("--calibrated-jtbd", required=True,
                        help="Path tới jtbd_calibrated.json")
    parser.add_argument("--vault-root", required=True,
                        help="Path tới vault root")
    args = parser.parse_args()

    # ── Bước 1: Đọc inputs ──
    for path, name in [(args.decision_map, "decision-map"), (args.calibrated_jtbd, "calibrated-jtbd")]:
        if not os.path.isfile(path):
            sys.exit(f"❌ Không tìm thấy file: {path}")

    with open(args.decision_map, "r", encoding="utf-8") as f:
        decision_map = json.load(f)
    with open(args.calibrated_jtbd, "r", encoding="utf-8") as f:
        calibrated_jtbd = json.load(f)

    # ── Bước 2: Join 2 nguồn dữ liệu ──
    merged = join_data(decision_map, calibrated_jtbd)
    if not merged:
        print("ℹ️ Không có entry action=create. Không tạo file.")
        sys.exit(0)

    # ── Bước 3: Validate ──
    validate_entries(merged)

    # ── Bước 4: Load dashboard template ──
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_template = load_dashboard_template(skill_root)

    # ── Bước 5: Kiểm tra thư mục đích ──
    audiences_dir = os.path.join(args.vault_root, "01-Atomic", "Audiences")
    if not os.path.isdir(audiences_dir):
        sys.exit(f"❌ Thư mục không tồn tại: {audiences_dir}")
    index_path = os.path.join(audiences_dir, "_audience_index.yaml")
    if not os.path.isfile(index_path):
        sys.exit(f"❌ Không tìm thấy index: {index_path}")

    # ── Bước 6: Tạo file .md ──
    print(f"\n📂 Tạo file Audience ({len(merged)} entries create):")
    created = skipped = 0
    for entry in merged:
        if write_audience_file(entry, audiences_dir, dashboard_template):
            created += 1
        else:
            skipped += 1

    # ── Bước 7: Cập nhật index ──
    print(f"\n📋 Cập nhật _audience_index.yaml:")
    added = update_audience_index(merged, index_path)

    # ── Bước 8: Báo cáo ──
    print(f"\n{'='*40}")
    print(f"✅ Hoàn tất!")
    print(f"  File tạo mới: {created}")
    print(f"  File skip:    {skipped}")
    print(f"  Index thêm:   {added}")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    main()
