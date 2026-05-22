"""
TÊN SCRIPT: audit_cache.py
VAI TRÒ: POKA-YOKE cuối cùng + Mining Report — chạy quality gates per-chunk trên
          file vault đã normalize, đọc ledger thống kê DONE/SKIPPED/FATAL, xuất
          báo cáo tổng hợp (Bước 4 trong SKILL.md).

KHI NÀO SỬ DỤNG:
  1. Sau khi vòng lặp Miner hoàn thành — kiểm tra chất lượng tổng thể toàn bộ file.
  2. Khi run bị crash giữa chừng — xác định chunks nào cần re-mine trước resume.
  3. Sau khi edit tay file cache trong Obsidian — validate structural integrity.
  4. Trước khi chạy downstream skill (book-audience-matcher, book-parser) —
     POKA-YOKE gate cuối cùng, đảm bảo không có chunk lỗi lọt xuống.

CÁCH XỬ LÝ:
  1. Parse file vault: tách từng ## Chunk N: heading + <data_chunk> content.
  2. Chạy Gate [1] (length) + Gates [2]-[6] (quality_gate module) trên mỗi chunk.
  3. Phân loại: PASS / WARN (Gate [6] optional) / FAIL (structural errors).
  4. Nếu có --ledger: đọc miner_progress.yaml → thống kê DONE/SKIPPED/FATAL + warnings.
  5. Xuất báo cáo chunk-by-chunk + SUMMARY + Mining Stats + hướng dẫn hành động cụ thể.

KHÔNG LÀM: Không sửa file vault. Không cập nhật ledger. Không gọi NLM.
           Chỉ đọc và báo cáo.

CÁCH DÙNG:
  cd "d:\\AI\\AI content factory"
  python .agent/skills/book-extractor/scripts/audit_cache.py "vault/02-sources/books/Book.md" --ledger ".extraction_runs/book_2026-04-15/miner_progress.yaml"
"""

import re
import os
import sys
import yaml
from datetime import datetime

# Import shared gate logic — không duplicate
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from quality_gate import run_deterministic_gates

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def parse_chunks_from_cache(filepath: str) -> list:
    """
    Đọc file vault và tách từng <data_chunk> cùng heading bên ngoài.

    Pattern tìm kiếm:
      ## Chunk N: [Tên Chunk]
      (bất kỳ text nào — dòng summary)
      <data_chunk>
        [nội dung chunk]
      </data_chunk>

    Returns: list of (chunk_index: int, chunk_name: str, chunk_content: str)
    Nếu không tìm thấy heading nhưng có data_chunk → vẫn parse với index từ CHUNK_index=.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if '<!-- HEADER_END -->' not in content:
        print("  [WARNING] HEADER_END sentinel missing — file may be corrupt.")

    chunks = []

    # Match: ## Chunk N: [Name]\n...<data_chunk>...</data_chunk>
    pattern = re.compile(
        r'##\s+Chunk\s+(\d+):\s*(.+?)\n.*?<data_chunk>(.*?)</data_chunk>',
        re.DOTALL
    )
    for m in pattern.finditer(content):
        chunks.append((int(m.group(1)), m.group(2).strip(), m.group(3).strip()))

    # Fallback: tìm data_chunk không có heading (miner chưa qua normalizer)
    if not chunks:
        chunks = re.findall(r'<data_chunk>(.*?)</data_chunk>', content, re.DOTALL)
        for chunk in chunks:
            idx_match = re.search(r'CHUNK_index=(\d+)', chunk)
            name_match = re.search(r'CHUNK=([^|\n`\r]+)', chunk)
            idx = int(idx_match.group(1)) if idx_match else 0
            name = name_match.group(1).strip() if name_match else "Unknown"
            chunks.append((idx, name, chunk.strip()))

    return sorted(chunks, key=lambda x: x[0])


def audit_cache(filepath: str, ledger_path: str = None, report_path: str = None):
    """
    Main entry point: chạy quality gate trên từng chunk, xuất báo cáo.
    Nếu ledger_path được cung cấp, thêm phần Mining Stats vào report.
    """
    print(f"\n{'='*60}")
    print(f"  CACHE AUDIT + MINING REPORT")
    print(f"  File: {filepath}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if not os.path.isfile(filepath):
        print(f"[FATAL] File not found: {filepath}")
        sys.exit(1)

    chunks = parse_chunks_from_cache(filepath)
    if not chunks:
        print("[FATAL] No <data_chunk> chunks found. File empty or malformed.")
        sys.exit(1)

    print(f"  Chunks found: {len(chunks)}\n")

    results = {"PASS": [], "WARN": [], "FAIL": []}

    for idx, name, chunk in chunks:
        # Gate [1]: length check
        if len(chunk) < 200:
            if 'SKIPPED_SHORT_CONTENT' in chunk:
                label = "⏭️ SKIP "
                detail = "Acknowledged skip (retry 2 lần, vẫn < 200 chars)"
                results.setdefault("SKIP", []).append(idx)
            else:
                label = "❌ FAIL "
                detail = "Gate [1]: Content < 200 chars"
                results["FAIL"].append(idx)
        else:
            # Gates [2]-[6]: deterministic check
            gate_result = run_deterministic_gates(chunk, f"Chunk {idx}: {name}", idx)

            if gate_result.passed:
                label = "✅ PASS "
                detail = ""
                results["PASS"].append(idx)
            elif gate_result.failed_gates == ["[6]"]:
                # Section optional missing → WARNING (không phải FATAL)
                label = "⚠️  WARN "
                detail = f"Gates {gate_result.failed_gates}: {gate_result.detail}"
                results["WARN"].append(idx)
            else:
                # MISSING_TAGS hoặc MISMATCH → FAIL
                label = "❌ FAIL "
                detail = f"Gates {gate_result.failed_gates}: {gate_result.detail}"
                results["FAIL"].append(idx)

        display_name = name[:50] + ("..." if len(name) > 50 else "")
        print(f"  Chunk {str(idx).rjust(2)} {label} — \"{display_name}\"")
        if detail:
            print(f"           {detail}")

    # Summary
    total = len(chunks)
    print(f"\n{'─'*60}")
    print(f"  SUMMARY")
    print(f"{'─'*60}")
    print(f"  ✅ PASS    : {len(results['PASS'])} / {total}")

    warn_str = f"  ⚠️  WARNING : {len(results['WARN'])} / {total}"
    if results['WARN']:
        warn_str += f"   → chunks: {results['WARN']}"
    print(warn_str)

    skip_str = f"  ⏭️ SKIPPED : {len(results.get('SKIP', []))} / {total}"
    if results.get('SKIP'):
        skip_str += f"   → chunks: {results['SKIP']}"
    print(skip_str)

    fail_str = f"  ❌ FAIL    : {len(results['FAIL'])} / {total}"
    if results['FAIL']:
        fail_str += f"   → chunks: {results['FAIL']}"
    print(fail_str)

    # Actionable recommendations
    print()
    if results['FAIL']:
        print(f"  [ACTION REQUIRED]")
        print(f"  Re-mine chunks: {results['FAIL']}")
        print(f"  → Set status=PENDING in miner_progress.yaml")
        print(f"  → Re-mine via CLI nlm notebook query + gate_checker.py")
    if results['WARN']:
        print(f"  [REVIEW RECOMMENDED]")
        print(f"  Optional content warnings in chunks: {results['WARN']}")
        print(f"  → Kiểm tra section ③④⑤ — cần nội dung hoặc [NOT_FOUND]")
    if not results['FAIL'] and not results['WARN']:
        print(f"  [OK] Cache is clean. Safe to run downstream skills.")

    # ── Mining Stats (from ledger) ──
    if ledger_path and os.path.isfile(ledger_path):
        print(f"\n{'─'*60}")
        print(f"  MINING STATS")
        print(f"{'─'*60}")
        with open(ledger_path, 'r', encoding='utf-8') as f:
            ledger = yaml.safe_load(f)
        chunks_data = ledger.get('chunks', {})
        status_counts = {"DONE": 0, "SKIPPED": 0, "FATAL": 0, "PENDING": 0}
        warning_chunks = {}
        for cid, info in chunks_data.items():
            st = info.get('status', 'PENDING')
            status_counts[st] = status_counts.get(st, 0) + 1
            ec = info.get('error_code')
            if ec:
                warning_chunks.setdefault(ec, []).append(cid)

        total_ledger = sum(status_counts.values())
        print(f"  📊 Total chunks (ledger): {total_ledger}")
        print(f"  ✅ DONE: {status_counts['DONE']}")
        print(f"  ⏭️ SKIPPED: {status_counts['SKIPPED']}")
        print(f"  ❌ FATAL: {status_counts['FATAL']}")
        if status_counts['PENDING'] > 0:
            print(f"  ⏳ PENDING: {status_counts['PENDING']}")
        if warning_chunks:
            for wtype, wchunks in warning_chunks.items():
                print(f"  ⚠️ {wtype}: chunks {wchunks}")

    # Ghi pipeline_report.md — audit_cache là script ĐẦU TIÊN trong luồng, dùng mode 'w' để tạo mới
    if report_path:
        with open(report_path, 'w', encoding='utf-8') as rf:
            rf.write(f"# Pipeline Report: DIKW Extraction\n\n")
            rf.write(f"## 1. book-extractor (Mining & Quality Gates)\n")
            rf.write(f"- Tổng chunks: {total}\n")
            rf.write(f"- PASS: {len(results['PASS'])} | WARN: {len(results['WARN'])} | FAIL: {len(results['FAIL'])}\n")
            if results['FAIL']:
                rf.write(f"- ❌ Chunks FAIL: {results['FAIL']}\n")

    print(f"\n{'='*60}\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:   python audit_cache.py <path-to-cache-file> [--ledger <ledger-path>]")
        print('Example: python audit_cache.py "vault/02-sources/books/Book.md" --ledger ".extraction_runs/book_2026-04-15/miner_progress.yaml"')
        sys.exit(1)

    fp = sys.argv[1]
    if not os.path.isabs(fp):
        fp = os.path.abspath(fp)

    # Parse --ledger arg
    ledger_path = None
    if '--ledger' in sys.argv:
        l_idx = sys.argv.index('--ledger')
        if l_idx + 1 < len(sys.argv):
            ledger_path = sys.argv[l_idx + 1]
            if not os.path.isabs(ledger_path):
                ledger_path = os.path.abspath(ledger_path)

    # Parse --report arg
    report_path = None
    if '--report' in sys.argv:
        r_idx = sys.argv.index('--report')
        if r_idx + 1 < len(sys.argv):
            report_path = sys.argv[r_idx + 1]
            if not os.path.isabs(report_path):
                report_path = os.path.abspath(report_path)

    audit_cache(fp, ledger_path=ledger_path, report_path=report_path)
