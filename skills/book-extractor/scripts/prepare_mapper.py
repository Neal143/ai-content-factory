"""
TÊN SCRIPT: prepare_mapper.py
VAI TRÒ: Chuyển đổi dữ liệu thô (JSON) từ NotebookLM thành khung sườn Markdown chuẩn,
         sau đó chạy 4-point Mapper Validation Gate.
KHI NÀO SỬ DỤNG: Dùng ở Bước 1.5 (Mapper Validation Gate) của skill book-extractor.
CÁCH XỬ LÝ:
  1. Đọc mapper_raw.md → clean META tags (strip markdown formatting).
  2. Ghi file xương sống vào vault/02-sources/books/[Tên Sách].md.
  3. Chạy 4-point validation:
     [1] HEADER COMPLETE: META_BOOK (5 trường), META_BOOK_AUDIENCE (JTBD), Tổng quan (1.1→1.8)
     [2] TOC INTEGRITY: Đếm Chunk trong TOC_MASTER = total_chunks
     [3] FORMAT: META lines là plaintext (không ** hay `)
     [4] SENTINEL: <!-- HEADER_END --> tồn tại sau TOC_MASTER
  4. In JSON verdict ra stdout.

KHÔNG LÀM:
  ❌ Gọi NLM
  ❌ Tự sửa lỗi validation (Agent quyết định hành động dựa trên verdict)
  ❌ Tạo ledger

OUTPUT: JSON stdout — verdict với passed/failed + chi tiết từng check.
"""


import re
import sys
import os
import json


def prepare_mapper(run_folder, book_name):
    """
    Phase 1: Clean mapper raw text và ghi file xương sống vào vault.
    Returns: path tới cache file đã ghi.
    """
    mapper_raw_path = os.path.join(os.path.abspath(run_folder), 'session_1', 'mapper_raw.md')
    vault_path = os.path.join('vault', '02-sources', 'books', f"{book_name}.md")

    print(f"Preparing mapper for: {book_name}")
    print(f"Reading from: {mapper_raw_path}")

    with open(mapper_raw_path, 'r', encoding='utf-8-sig') as f:
        raw_content = f.read()

    # CLI nlm notebook query trả plain text trực tiếp (Agent đã extract answer)
    text = raw_content

    # ── Clean META_BOOK and META_BOOK_AUDIENCE ──
    def clean_meta(match):
        val = match.group(2).replace('`', '').strip()
        return f"{match.group(1)}: {val}"

    text = re.sub(r'(?:\*\s*)?\*\*(META_BOOK(?:_AUDIENCE)?):\*\*(?:\s*`?)(.*?)(?:`?)$', clean_meta, text, flags=re.MULTILINE)
    text = text.replace('**META_BOOK:**', 'META_BOOK:')

    # ── Ensure directory exists and write ──
    os.makedirs(os.path.dirname(vault_path), exist_ok=True)

    with open(vault_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"Saved cleanly to {vault_path}")
    return vault_path


def validate_mapper(cache_file):
    """
    Phase 2: Chạy 4-point Mapper Validation Gate trên file cache đã ghi.
    Returns: dict kết quả validation (JSON-serializable).
    """
    with open(cache_file, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = {}
    failed = []

    # ── [1] HEADER COMPLETE ──
    header_issues = []

    # Check META_BOOK có đủ 5 trường bắt buộc
    meta_match = re.search(r'^META_BOOK:\s*(.+)$', content, re.MULTILINE)
    if meta_match:
        meta_str = meta_match.group(1)
        required_fields = ['book_name', 'author', 'year', 'topics', 'total_chunks']
        # Hỗ trợ legacy field name total_blocks
        if 'total_blocks' in meta_str and 'total_chunks' not in meta_str:
            required_fields = ['book_name', 'author', 'year', 'topics', 'total_blocks']
        missing_meta = [f for f in required_fields if f'{f}=' not in meta_str]
        if missing_meta:
            header_issues.append(f"META_BOOK thiếu trường: {', '.join(missing_meta)}")
    else:
        header_issues.append("META_BOOK không tồn tại")

    # Check META_BOOK_AUDIENCE có JTBD
    audience_match = re.search(r'^META_BOOK_AUDIENCE:\s*(.+)$', content, re.MULTILINE)
    if audience_match:
        audience_str = audience_match.group(1)
        if 'Người' not in audience_str:
            header_issues.append("META_BOOK_AUDIENCE không chứa JTBD (thiếu 'Người')")
    else:
        header_issues.append("META_BOOK_AUDIENCE không tồn tại")

    # Check Tổng quan 1.1 → 1.8
    required_sections = ['1.1', '1.2', '1.3', '1.4', '1.5', '1.6', '1.7', '1.8']
    missing_sections = [s for s in required_sections if f'**{s}.' not in content and f'**{s} ' not in content]
    if missing_sections:
        header_issues.append(f"Tổng quan thiếu mục: {', '.join(missing_sections)}")

    checks['header_complete'] = {
        'pass': len(header_issues) == 0,
        'detail': '; '.join(header_issues) if header_issues else ''
    }
    if header_issues:
        failed.append('header_complete')

    # ── [2] TOC INTEGRITY ──
    # Parse total_chunks từ META_BOOK
    total_chunks = 0
    if meta_match:
        tc_match = re.search(r'total_(?:chunks|blocks)\s*=\s*(\d+)', meta_match.group(1))
        if tc_match:
            total_chunks = int(tc_match.group(1))

    # Đếm số Chunk N: trong TOC_MASTER
    toc_section = re.search(r'TOC_MASTER[:\*\s]*\n(.*?)(?:\n\n\n|\Z|<!--)', content, re.DOTALL)
    toc_count = 0
    if toc_section:
        toc_count = len(re.findall(r'Chunk\s+\d+:', toc_section.group(1)))

    toc_pass = (total_chunks > 0 and toc_count == total_chunks)
    checks['toc_integrity'] = {
        'pass': toc_pass,
        'total_chunks': total_chunks,
        'toc_count': toc_count
    }
    if not toc_pass:
        failed.append('toc_integrity')

    # ── [3] FORMAT ──
    format_issues = []
    if meta_match:
        meta_line = meta_match.group(0)
        if '**' in meta_line or '`' in meta_line:
            format_issues.append("META_BOOK chứa markdown formatting (** hoặc `)")
    if audience_match:
        audience_line = audience_match.group(0)
        if '**' in audience_line or '`' in audience_line:
            format_issues.append("META_BOOK_AUDIENCE chứa markdown formatting (** hoặc `)")

    checks['format_clean'] = {
        'pass': len(format_issues) == 0,
        'detail': '; '.join(format_issues) if format_issues else ''
    }
    if format_issues:
        failed.append('format_clean')

    # ── [4] SENTINEL ──
    sentinel_exists = '<!-- HEADER_END -->' in content
    checks['sentinel_exists'] = {'pass': sentinel_exists}
    if not sentinel_exists:
        failed.append('sentinel_exists')

    # ── Build verdict (chỉ cho failed checks) ──
    verdict = {}
    if 'header_complete' in failed:
        detail = checks['header_complete']['detail']
        verdict['header_complete'] = f"NLM bổ sung: {detail}"
    if 'toc_integrity' in failed:
        verdict['toc_integrity'] = f"DỪNG báo User: TOC count mismatch (expected={total_chunks}, found={toc_count})"
    if 'format_clean' in failed:
        verdict['format_clean'] = "Agent strip markdown formatting trong cache file, chạy lại script"
    if 'sentinel_exists' in failed:
        verdict['sentinel_exists'] = "Agent chèn <!-- HEADER_END --> vào đúng vị trí (sau TOC_MASTER)"

    result = {
        'passed': len(failed) == 0,
        'checks': checks,
        'cache_file': cache_file,
        'total_chunks': total_chunks,
        'failed': failed
    }
    if verdict:
        result['verdict'] = verdict

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python prepare_mapper.py <run_folder> <book_name>")
        print("Example: python prepare_mapper.py .extraction_runs/the-whole-brain-child_2026-04-11 \"The Whole-Brain Child\"")
        sys.exit(1)

    run_folder = sys.argv[1]
    book_name = sys.argv[2]

    # Phase 1: Clean + ghi file
    cache_file = prepare_mapper(run_folder, book_name)

    # Phase 2: Validate
    result = validate_mapper(cache_file)

    # Output JSON verdict
    print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result['passed'] else 1)
