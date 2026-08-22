"""
TEN SCRIPT: print_handoff.py
LAST UPDATE: 22/08/2026 22:00 (GMT+7)
VAI TRO: Module tien ich - In handoff prompt tu dong cho Book Extractor Pipeline.
SU DUNG KHI NAO: Duoc import boi cac script cuoi moi session (post_mine.py, apply_curation.py, verify_audiences.py, patch_source_metadata.py).
OUTPUT: In handoff prompt ra stdout voi cac gia tri thuc doc tu 00-blackboard.yaml.
TOM TAT LOGIC:
  1. Doc 00-blackboard.yaml tu run_folder -> lay book_name, notebook_id, run_folder, cache_file, slug.
  2. Chon template handoff tuong ung voi next_phase.
  3. Format template voi gia tri thuc va in ra stdout.
  4. Fail-safe: Neu blackboard khong ton tai hoac loi -> return im lang.
"""

import os
import sys
import yaml


# -- Template handoff cho tung transition --
# Noi dung lay nguyen van tu .agents/workflows/book-extractor.md
HANDOFF_TEMPLATES = {
    2: """**[Hệ thống] Handoff 1**
Workflow: `/book-extractor` (Phase 2)
Sách: {book_name} (ID: {notebook_id}) | Run: {run_folder} | Cache: {cache_file}
Trạng thái: Phase 1 PASS. `current_phase: 2`.
Yêu cầu:
1. Đọc `.agents\\workflows\\book-extractor.md`.
2. Nạp cấu hình từ `00-blackboard.yaml` trong {run_folder}.
3. Kích chạy **Bước 3.5 (Phase 2: Vivid Curation)** ngay lập tức.""",

    3: """**[Hệ thống] Handoff 2**
Workflow: `/book-extractor` (Phase 3)
Sách: {book_name} | Run: {run_folder} | Cache: {cache_file}
Trạng thái: Phase 2 PASS. `current_phase: 3`.
Yêu cầu:
1. Đọc `.agents\\workflows\\book-extractor.md`.
2. Nạp cấu hình từ `00-blackboard.yaml` trong {run_folder}.
3. Khởi chạy **Bước 5 (Phase 3: Audience Resolver)** ngay lập tức.""",

    4: """**[Hệ thống] Handoff 3**
Workflow: `/book-extractor` (Phase 4)
Sách: {book_name} | Run: {run_folder} | Cache: {cache_file}
Trạng thái: Phase 3 PASS. `current_phase: 4`.
Yêu cầu:
1. Đọc `.agents\\workflows\\book-extractor.md`.
2. Nạp cấu hình từ `00-blackboard.yaml` trong {run_folder}.
3. Khởi chạy **Bước 7 (Phase 4: Topic Gen & Atomize)** ngay lập tức.""",

    5: """**[Hệ thống] Handoff 4**
Workflow: `/book-extractor` (Phase 5: Vault Curation)
Sách: {book_name} | Run: {run_folder} | Slug: {slug}
Trạng thái: Phase 4 PASS. `current_phase: 5`.
Yêu cầu:
1. Đọc `.agents\\workflows\\book-extractor.md`.
2. Nạp cấu hình từ `00-blackboard.yaml` trong {run_folder}.
3. Khởi chạy **SESSION 5: VAULT CURATION** ngay lập tức.""",
}


def print_handoff(run_folder, next_phase):
    """
    Doc blackboard tu run_folder, in handoff prompt tuong ung voi next_phase.
    Fail-safe: Moi loi deu bi bat im lang, khong anh huong script goi.
    """
    # Dam bao UTF-8 stdout tren Windows
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    # Doc blackboard
    bb_path = os.path.join(run_folder, "00-blackboard.yaml")
    if not os.path.exists(bb_path):
        return

    with open(bb_path, 'r', encoding='utf-8') as f:
        bb = yaml.safe_load(f)

    if not bb or not isinstance(bb, dict):
        return

    # Lay template
    template = HANDOFF_TEMPLATES.get(next_phase)
    if not template:
        return

    # Format template voi gia tri thuc tu blackboard
    values = {
        "book_name":   bb.get("book_name", ""),
        "notebook_id": bb.get("notebook_id", ""),
        "run_folder":  bb.get("run_folder", ""),
        "cache_file":  bb.get("cache_file", ""),
        "slug":        bb.get("slug", ""),
    }

    handoff_text = template.format(**values)

    # In ra stdout voi separator ro rang
    sep = "=" * 54
    print(f"\n{sep}")
    print("[HANDOFF PROMPT] — Copy va gui cho User")
    print(sep)
    print(handoff_text)
    print(sep)
