"""
TÊN SCRIPT: init_ledger.py
VAI TRÒ: Tự động tạo miner_progress.yaml từ thông tin META_BOOK trong cache file.
         Thay thế việc Agent tự viết YAML thủ công.
KHI NÀO SỬ DỤNG: Agent gọi ở đầu Bước 2 (sau Mapper Validation Gate pass).
CÁCH XỬ LÝ:
  1. Đọc cache file → parse book_name và total_chunks từ META_BOOK.
  2. Generate YAML chuẩn với N chunks PENDING.
  3. Ghi file vào [run_folder]/miner_progress.yaml.
  4. In JSON stdout summary.

KHÔNG LÀM:
  ❌ Gọi NLM
  ❌ Ghi đè ledger đã tồn tại (exit(1) nếu file đã có)
  ❌ Cập nhật ledger (dùng update_ledger.py)
  ❌ Validate cache file (dùng prepare_mapper.py)

OUTPUT: JSON stdout — {created, path, total_chunks, book_name}.
"""

import os
import re
import sys
import json
import yaml
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def parse_meta_book(cache_content):
    """
    Parse META_BOOK line từ cache file content.
    Trả về dict với các trường: book_name, author, year, topics, total_chunks.
    """
    meta_match = re.search(r'^META_BOOK:\s*(.+)$', cache_content, re.MULTILINE)
    if not meta_match:
        return None

    meta_str = meta_match.group(1).strip()
    result = {}

    # Parse key=value pairs separated by |
    for pair in meta_str.split('|'):
        pair = pair.strip()
        if '=' in pair:
            key, val = pair.split('=', 1)
            result[key.strip()] = val.strip()

    return result


def init_ledger(run_folder, cache_file, notebook_id):
    """
    Tạo miner_progress.yaml từ thông tin META_BOOK trong cache file.
    Returns: dict kết quả (JSON-serializable).
    """
    ledger_path = os.path.join(run_folder, 'miner_progress.yaml')

    # ── Guard: không ghi đè ledger đã tồn tại ──
    if os.path.isfile(ledger_path):
        return {
            "created": False,
            "error": f"Ledger đã tồn tại: {ledger_path}. Dùng Resume Protocol thay vì tạo mới.",
            "path": ledger_path
        }

    # ── Validate inputs ──
    if not os.path.isfile(cache_file):
        return {"created": False, "error": f"Cache file not found: {cache_file}"}

    # ── Đọc cache file và parse META_BOOK ──
    with open(cache_file, 'r', encoding='utf-8') as f:
        content = f.read()

    meta = parse_meta_book(content)
    if not meta:
        return {"created": False, "error": "META_BOOK not found in cache file"}

    book_name = meta.get('book_name', '')
    total_chunks_str = meta.get('total_chunks') or meta.get('total_blocks')
    if not total_chunks_str:
        return {"created": False, "error": "total_chunks not found in META_BOOK"}

    try:
        total_chunks = int(total_chunks_str)
    except ValueError:
        return {"created": False, "error": f"total_chunks is not a number: {total_chunks_str}"}

    if total_chunks < 1:
        return {"created": False, "error": f"total_chunks must be >= 1, got {total_chunks}"}

    # ── Generate ledger YAML ──
    now = datetime.now(timezone.utc).isoformat()

    chunks = {}
    for i in range(1, total_chunks + 1):
        chunks[i] = {
            'status': 'PENDING',
            'error_code': None,
            'retry_count': 0,
            'updated_at': None
        }

    ledger = {
        'book_name': book_name,
        'notebook_id': notebook_id,
        'total_chunks': total_chunks,
        'mapper_completed': True,
        'last_updated': now,
        'chunks': chunks
    }

    # ── Ghi file ──
    os.makedirs(run_folder, exist_ok=True)
    with open(ledger_path, 'w', encoding='utf-8') as f:
        yaml.dump(ledger, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return {
        "created": True,
        "path": ledger_path,
        "total_chunks": total_chunks,
        "book_name": book_name
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python init_ledger.py <run_folder> <cache_file> <notebook_id>")
        print('Example: python init_ledger.py ".extraction_runs/book_2026-04-15" "vault/02-sources/books/Book.md" "abc123"')
        sys.exit(1)

    run_folder = sys.argv[1]
    cache_file = sys.argv[2]
    notebook_id = sys.argv[3]

    if not os.path.isabs(cache_file):
        cache_file = os.path.abspath(cache_file)

    result = init_ledger(run_folder, cache_file, notebook_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result.get("created") else 1)
