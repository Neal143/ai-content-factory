"""
TÊN SCRIPT: next_chunk.py
VAI TRÒ: Xác định chunk tiếp theo cần mine — deterministic, không phụ thuộc Agent.
         Đọc ledger + TOC_MASTER, trả JSON chứa chunk info + lệnh CLI sẵn dùng.
KHI NÀO SỬ DỤNG: Agent gọi ở đầu mỗi vòng lặp Bước ① (SKILL.md).
                  Thay thế việc Agent tự đọc ledger + cache file thủ công.
CÁCH XỬ LÝ:
  1. Đọc miner_progress.yaml → tìm chunk PENDING có index nhỏ nhất.
  2. Đọc cache file → parse TOC_MASTER → lấy canonical name cho chunk đó.
  3. In JSON ra stdout cho Agent dùng trực tiếp.

KHÔNG LÀM:
  ❌ Gọi NLM
  ❌ Cập nhật ledger
  ❌ Gọi gate_checker hay append_cache

OUTPUT: JSON stdout — Agent đọc và dùng trực tiếp các trường trong output.
"""

import os
import re
import sys
import json
import yaml

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def find_next_chunk(ledger_path, cache_path):
    """
    Xác định chunk PENDING tiếp theo từ ledger + TOC_MASTER.

    Returns: dict chứa chunk info hoặc {"done": true} nếu hết chunk.
    """
    # ── Validate inputs ──
    if not os.path.isfile(ledger_path):
        return {"error": f"Ledger not found: {ledger_path}"}
    if not os.path.isfile(cache_path):
        return {"error": f"Cache file not found: {cache_path}"}

    # ── Read ledger ──
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = yaml.safe_load(f)

    book_name = ledger.get('book_name', '')
    notebook_id = ledger.get('notebook_id', '')
    total_chunks = ledger.get('total_chunks', 0)
    chunks = ledger.get('chunks', {})

    # ── Tìm chunk PENDING nhỏ nhất ──
    pending = []
    done_count = 0
    fatal_count = 0
    for key, info in chunks.items():
        idx = int(key)
        status = info.get('status', 'PENDING')
        if status == 'PENDING':
            pending.append(idx)
        elif status == 'DONE':
            done_count += 1
        elif status == 'FATAL':
            fatal_count += 1

    if not pending:
        return {
            "done": True,
            "book_name": book_name,
            "total_chunks": total_chunks,
            "done_count": done_count,
            "fatal_count": fatal_count,
            "message": "Không còn chunk PENDING. Sẵn sàng chạy post_mine.py (Bước 3)."
        }

    next_idx = min(pending)
    chunk_nn = str(next_idx).zfill(2)

    # ── Parse TOC_MASTER từ cache file ──
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_content = f.read()

    toc_map = {}
    toc_match = re.search(r'TOC_MASTER[:\*\s]*\n(.*?)(?:\n\n\n|\Z|<!--)', cache_content, re.DOTALL)
    if toc_match:
        toc_body = toc_match.group(1)
        for m in re.finditer(r'(?:[-*]\s*)?Chunk\s+(\d+):\s*(.+?)(?:\r?\n|$)', toc_body):
            toc_map[int(m.group(1))] = m.group(2).strip()

    chunk_name = toc_map.get(next_idx, f"Unknown Chunk {next_idx}")

    # ── Derive paths ──
    run_folder = os.path.dirname(ledger_path)
    raw_file = os.path.join(run_folder, f"chunk_{chunk_nn}_raw.txt")
    gate_script = ".agent/skills/book-extractor/scripts/gate_checker.py"
    append_script = ".agent/skills/book-extractor/scripts/append_cache.py"

    return {
        "done": False,
        "book_name": book_name,
        "notebook_id": notebook_id,
        "chunk_index": next_idx,
        "chunk_nn": chunk_nn,
        "chunk_name": chunk_name,
        "raw_file": raw_file,
        "cache_file": cache_path,
        "progress": f"{done_count}/{total_chunks} done, {len(pending)} pending, {fatal_count} fatal",
        "cli_nlm_query": (
            f'nlm notebook query {notebook_id} '
            f'"Tham chiếu file prompt-miner-v4.md, hãy trích xuất CHÍNH XÁC '
            f'Content Chunk sau: Chunk {next_idx}: {chunk_name}." --json'
        ),
        "cli_gate_checker": (
            f'python {gate_script} '
            f'"{raw_file}" {next_idx} "{chunk_name}" '
            f'--cache "{cache_path}"'
        ),
        "cli_append_cache": (
            f'python {append_script} '
            f'"{raw_file}" "{cache_path}"'
        )
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python next_chunk.py <ledger_path> <cache_path>")
        print('Example: python next_chunk.py ".extraction_runs/book_2026-04-15/miner_progress.yaml" "vault/02-sources/books/Book.md"')
        sys.exit(1)

    ledger_path = sys.argv[1]
    cache_path = sys.argv[2]

    if not os.path.isabs(ledger_path):
        ledger_path = os.path.abspath(ledger_path)
    if not os.path.isabs(cache_path):
        cache_path = os.path.abspath(cache_path)

    result = find_next_chunk(ledger_path, cache_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("error"):
        sys.exit(1)
    elif result.get("done"):
        sys.exit(0)
    else:
        sys.exit(0)
