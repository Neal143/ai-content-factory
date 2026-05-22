"""
TÊN SCRIPT: append_cache.py
VAI TRÒ: Append data_chunk từ raw file vào cache file (vault).
         Xử lý: extract, inject warning, chống duplicate, append.
KHI NÀO SỬ DỤNG: Agent gọi sau khi Gate pass hoặc fallback trong vòng lặp Bước 2 (SKILL.md).
                  Thay thế việc Agent tự đọc/ghi file cache trực tiếp.
CÁCH XỬ LÝ:
  1. Đọc raw file → extract tất cả <data_chunk>...</data_chunk>.
  2. Parse CHUNK_index từ mỗi data_chunk.
  3. Inject warning flags nếu có (--warnings).
  4. Dedup: xóa chunk cũ cùng CHUNK_index khỏi cache (bao gồm heading Normalizer).
  5. Append data_chunk mới vào cuối cache file.

KHÔNG LÀM:
  ❌ Gọi NLM (Agent gọi CLI trực tiếp)
  ❌ Cập nhật ledger (Agent làm)
  ❌ Chạy normalizer (post_mine làm)
  ❌ Chạy gate_checker (Agent gọi riêng)

OUTPUT: stdout summary + cache file updated.
"""

import re
import os
import sys
import json


# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def extract_data_chunks(raw_content):
    """
    Extract tất cả <data_chunk>...</data_chunk> từ raw content.
    Returns: list of chunk content strings (không bao gồm tag bọc ngoài).
    """
    return re.findall(r'<data_chunk>(.*?)</data_chunk>', raw_content, re.DOTALL)


def parse_chunk_index(chunk_content):
    """
    Parse CHUNK_index=N từ chunk content.
    Returns: int hoặc 0 nếu không tìm thấy.
    """
    match = re.search(r'CHUNK_index=(\d+)', chunk_content)
    if match:
        return int(match.group(1))
    return 0


def inject_warnings(chunk_content, warnings):
    """
    Chèn cờ warning vào đỉnh chunk (trước META_CHUNK:).

    Args:
        chunk_content: nội dung bên trong <data_chunk>
        warnings: list of warning flag strings

    Returns: chunk_content đã inject warnings.
    """
    if not warnings:
        return chunk_content

    warning_lines = '\n'.join(f'> [!warning] {w}' for w in warnings)

    # Tìm vị trí META_CHUNK: để chèn trước
    meta_pos = chunk_content.find('META_CHUNK:')
    if meta_pos != -1:
        # Tìm đầu dòng chứa META_CHUNK
        line_start = chunk_content.rfind('\n', 0, meta_pos)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1  # Bỏ qua ký tự \n

        before = chunk_content[:line_start]
        after = chunk_content[line_start:]
        return before + warning_lines + '\n' + after
    else:
        # Không tìm thấy META_CHUNK → chèn đầu chunk
        return warning_lines + '\n' + chunk_content


def strip_chunk_from_cache(cache_content, chunk_index):
    """
    Xóa chunk cũ có cùng CHUNK_index khỏi cache content.
    Bao gồm:
      - <data_chunk>...</data_chunk> chứa CHUNK_index=N
      - Heading `## Chunk N: ...` + summary line `> 🎯 ...` (nếu đã qua Normalizer)

    Returns: (new_content, was_stripped: bool)
    """
    # Strip <data_chunk> chứa CHUNK_index=N
    pattern = re.compile(
        r'<data_chunk>(?:(?!</data_chunk>).)*?CHUNK_index=' + str(chunk_index) + r'\b.*?</data_chunk>',
        re.DOTALL
    )
    new_content, count = pattern.subn('', cache_content)

    if count == 0:
        # Thử fallback BLOCK_index (source NLM chưa re-upload)
        pattern_block = re.compile(
            r'<data_chunk>(?:(?!</data_chunk>).)*?BLOCK_index=' + str(chunk_index) + r'\b.*?</data_chunk>',
            re.DOTALL
        )
        new_content, count = pattern_block.subn('', new_content)

    if count > 0:
        # Xóa heading Normalizer: ## Chunk N: ...\n> 🎯 ...\n
        heading_pattern = re.compile(
            r'## Chunk ' + str(chunk_index) + r':.*?\n(?:>.*?\n)?',
            re.MULTILINE
        )
        new_content = heading_pattern.sub('', new_content)

        # Dọn blank lines thừa
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)

    return new_content, count > 0


def append_cache(raw_file, cache_file, warnings=None):
    """
    Main entry point: extract, inject, dedup, append.

    Args:
        raw_file: path tới chunk_NN_raw.txt
        cache_file: path tới vault cache file
        warnings: list of warning flag strings hoặc None

    Returns: True nếu thành công
    """
    print(f"\n{'='*60}")
    print(f"  APPEND CACHE")
    print(f"  Raw:   {raw_file}")
    print(f"  Cache: {cache_file}")
    if warnings:
        print(f"  Warnings: {warnings}")
    print(f"{'='*60}\n")

    # ── Validate inputs ──
    if not os.path.isfile(raw_file):
        print(f"  ❌ ERROR: Raw file not found: {raw_file}")
        return False

    if not os.path.isfile(cache_file):
        print(f"  ❌ ERROR: Cache file not found: {cache_file}")
        return False

    # ── Validate agent gate log exists (clean path only) ──
    # Enforcement: Agent PHẢI ghi chunk_NN_agent_gate.json TRƯỚC KHI gọi append.
    # Ngăn Agent bypass Gate [8] mà vẫn append chunk vào cache.
    # CHỈ áp dụng khi KHÔNG có --warnings (clean path = đã qua Bước ④).
    # Khi có --warnings, Agent đang ở fallback path (Gate [3-6] FAIL) hoặc
    # FALLBACK [8] — quality issue đã được acknowledge, không cần gate log.
    if not warnings:
        raw_dir = os.path.dirname(raw_file)
        raw_basename = os.path.basename(raw_file)
        # chunk_01_raw.txt → chunk_01_agent_gate.json
        agent_gate_file = os.path.join(
            raw_dir,
            raw_basename.replace('_raw.txt', '_agent_gate.json').replace('_raw.json', '_agent_gate.json')
        )
        if not os.path.isfile(agent_gate_file):
            print(f"  ❌ ERROR: Agent gate log not found: {agent_gate_file}")
            print(f"  Agent MUST write chunk_NN_agent_gate.json before calling append_cache.")
            print(f"  (Use --warnings flag for fallback paths that skip Gate [8])")
            return False

    # ── Read raw file ──
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # ── Extract data_chunks ──
    chunks = extract_data_chunks(raw_content)
    if not chunks:
        print(f"  ❌ ERROR: No <data_chunk> found in {raw_file}")
        return False

    print(f"  Found {len(chunks)} data_chunk(s) in raw file")

    # ── Read cache ──
    with open(cache_file, 'r', encoding='utf-8') as f:
        cache_content = f.read()

    # ── Process each chunk ──
    appended_indices = []

    for chunk_content in chunks:
        chunk_index = parse_chunk_index(chunk_content)
        if chunk_index == 0:
            print(f"  ⚠️ WARNING: Could not parse CHUNK_index, using 0")

        # Inject warnings
        if warnings:
            chunk_content = inject_warnings(chunk_content, warnings)

        # Dedup: strip old chunk with same index
        cache_content, was_stripped = strip_chunk_from_cache(cache_content, chunk_index)
        if was_stripped:
            print(f"  🔄 Stripped old chunk {chunk_index} from cache (dedup)")

        # Append
        # Đảm bảo cache kết thúc bằng 2 newlines trước chunk mới
        cache_content = cache_content.rstrip('\n') + '\n\n'
        cache_content += f'<data_chunk>\n{chunk_content.strip()}\n</data_chunk>\n'

        appended_indices.append(chunk_index)

    # ── Write cache ──
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(cache_content)

    # ── Summary ──
    warning_str = f" (warnings: {','.join(warnings)})" if warnings else ""
    print(f"  ✅ Appended chunk(s) {appended_indices} to cache{warning_str}")
    print(f"{'='*60}\n")

    return True


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python append_cache.py <raw_file> <cache_file> [--warnings \"FLAG1,FLAG2\"]")
        print('Example: python append_cache.py ".extraction_runs/run/chunk_05_raw.txt" "vault/02-sources/books/Book.md"')
        print('Example: python append_cache.py "chunk_05_raw.txt" "Book.md" --warnings "MISSING_TAGS,INCOMPLETE_CONTENT"')
        sys.exit(1)

    raw_file = sys.argv[1]
    cache_file = sys.argv[2]

    if not os.path.isabs(raw_file):
        raw_file = os.path.abspath(raw_file)
    if not os.path.isabs(cache_file):
        cache_file = os.path.abspath(cache_file)

    # Parse --warnings
    warning_list = None
    if '--warnings' in sys.argv:
        w_idx = sys.argv.index('--warnings')
        if w_idx + 1 < len(sys.argv):
            warning_list = [w.strip() for w in sys.argv[w_idx + 1].split(',') if w.strip()]

    success = append_cache(raw_file, cache_file, warnings=warning_list)
    sys.exit(0 if success else 1)
