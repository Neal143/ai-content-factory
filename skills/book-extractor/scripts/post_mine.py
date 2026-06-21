"""
TÊN SCRIPT: post_mine.py
VAI TRÒ: Mandatory Post-Loop Checkpoint — Kiểm tra toàn vẹn cấu trúc, audit chất lượng
         nội dung, tự động cách ly chunk lỗi (strip + reset PENDING), và chuẩn hóa
         định dạng trước khi sang Bước 4.
KHI NÀO SỬ DỤNG: Agent gọi sau khi vòng lặp Bước 2 kết thúc (không còn chunk PENDING).
CÁCH XỬ LÝ:
  1. Phase 1 (Sentinel Check & Recovery): Phục hồi thẻ <!-- HEADER_END --> nếu bị mất.
  2. Phase 2 (Chunk Count Validation): Đếm số chunk nội dung thực tế so với TOC.
  3. Phase 2.5 (Content Integrity Audit): Đếm warning flags + phát hiện marker có nhưng
     content rỗng → strip chunk lỗi khỏi cache + reset ledger về PENDING.
  4. Phase 3 (Normalization): Kích hoạt normalizer.py để chuẩn hóa định dạng.

KHÔNG LÀM:
  ❌ Gọi NLM (post_mine chỉ xử lý data tĩnh)
  ❌ Gọi gate_checker.py (Agent tự quyết định re-mine qua CLI nếu cần)

OUTPUT: Console log + file post_mine_report.txt trong run-folder. File vault được chuẩn hóa.
"""

import re
import os
import sys
import yaml
from datetime import datetime

# Fix Windows console encoding (cp1252 → UTF-8)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Import normalizer từ cùng thư mục
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from normalizer import normalize_file


# ── Utilities ──────────────────────────────────────────────────────────────────

def log(phase, status, message):
    """Print structured log line"""
    icon = {"OK": "✅", "RECOVERED": "🔧", "WARNING": "⚠️", "FATAL": "❌", "INFO": "ℹ️"}
    print(f"  [{phase}] {icon.get(status, '•')} {status}: {message}")


def find_run_folder(filepath):
    """Tim [run-folder] dua tren ten sach.
    Scan cac source-type subdirs (books/, videos/, ...) ben trong .extraction_runs/
    """
    search = filepath
    for _ in range(5):
        search = os.path.dirname(search)
        runs_dir = os.path.join(search, '.extraction_runs')
        if os.path.isdir(runs_dir):
            # Collect run folders tu tat ca source-type subdirs (books/, videos/, ...)
            all_run_folders = []
            for source_type in os.listdir(runs_dir):
                type_dir = os.path.join(runs_dir, source_type)
                if os.path.isdir(type_dir):
                    for f in os.listdir(type_dir):
                        full_path = os.path.join(type_dir, f)
                        if os.path.isdir(full_path):
                            all_run_folders.append(full_path)
            if all_run_folders:
                # Sort theo modification time — lay folder moi nhat
                all_run_folders.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return all_run_folders[0]
    print(f"  [WARNING] --run-folder not provided. Using heuristic discovery (non-deterministic).")
    print(f"  [WARNING] Recommend: python post_mine.py <file> --run-folder <folder>")
    return None


def strip_chunk_from_cache(filepath: str, chunk_index: int) -> bool:
    """
    Xóa chunk cụ thể khỏi cache file (theo CHUNK_index=).
    FIX A1: Ngăn duplicate khi re-mine — xóa chunk cũ trước khi append chunk mới.

    Returns: True nếu xóa thành công, False nếu không tìm thấy.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return False

    # Pattern: toàn bộ <data_chunk> chứa CHUNK_index=N
    pattern = re.compile(
        r'<data_chunk>(?:(?!</data_chunk>).)*?CHUNK_index=' + str(chunk_index) + r'\b.*?</data_chunk>',
        re.DOTALL
    )
    new_content, count = pattern.subn('', content)

    if count > 0:
        # Cũng xóa heading ## Chunk N: nếu có (do Normalizer N7 tạo)
        heading_pattern = re.compile(
            r'## Chunk ' + str(chunk_index) + r':.*?\n(?:>.*?\n)?',
            re.MULTILINE
        )
        new_content = heading_pattern.sub('', new_content)

        # Dọn blank lines thừa
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  [STRIP] Removed chunk {chunk_index} from cache ({count} data_chunk(s))")
        return True
    return False


def count_warning_flags(content: str) -> dict:
    """
    Đếm các cờ cảnh báo trong file cache để đưa vào report.
    Phục vụ: Phase 2.5 của post_mine() — đếm flags do Agent ghi vào.
    """
    return {
        "MISSING_TAGS":            len(re.findall(r'>\s*\[!warning\]\s*MISSING_TAGS', content)),
        "LINK_INTEGRITY_WARNING":  len(re.findall(r'LINK_INTEGRITY_WARNING', content)),
        "SEMANTIC_WARNING_AXIS_1": len(re.findall(r'SEMANTIC_WARNING_AXIS_1', content)),
        "SEMANTIC_WARNING_AXIS_2": len(re.findall(r'SEMANTIC_WARNING_AXIS_2', content)),
        "SEMANTIC_WARNING_AXIS_3": len(re.findall(r'SEMANTIC_WARNING_AXIS_3', content)),
    }


def detect_empty_content_after_markers(content: str, run_folder) -> list:
    """
    Phát hiện: marker tồn tại (content_type=...) nhưng dòng nội dung ngay sau rỗng.

    Ví dụ vi phạm:
        - **META_EVIDENCE:** content_type=shocking_fact | supports_knowledge=XYZ
        -           ← dòng trắng ngay lập tức (không có nội dung)

    Xử lý khi phát hiện:
    1. Thu thập CHUNK_index của các chunks bị nhễm.
    2. Cập nhật ledger: status=PENDING, error_code=INCOMPLETE_CONTENT.
       → Cho phép Agent re-mine qua CLI nlm notebook query.
    3. Trả về danh sách index để report.

    Returns: list of chunk indices bị phát hiện.
    """
    flagged_indices = []

    # Chỉ flag "rỗng" khi sau META tag + dòng trắng, dòng tiếp theo CŨNG là:
    # trống / section marker / kết thúc chunk — KHÔNG phải nội dung thật.
    # Tránh false positive khi NLM xuống dòng tự nhiên trước XML tags (VD: <situation>).
    empty_after_marker = re.compile(
        r'content_type=(?:shocking_fact|evidence|story|case_study|quote)'
        r'[^\n]*\n'            # META line
        r'(?:[ \t]*\n)+'       # 1+ dòng trắng
        r'(?=[ \t]*(?:\n|\Z|[③④⑤]|META_|</data_chunk>|\*{2}))',  # dòng tiếp = trống/marker/kết thúc
        re.MULTILINE
    )

    chunks = re.findall(r'<data_chunk>(.*?)</data_chunk>', content, re.DOTALL)
    for chunk in chunks:
        if empty_after_marker.search(chunk):
            idx_match = re.search(r'CHUNK_index=(\d+)', chunk)
            if idx_match:
                flagged_indices.append(int(idx_match.group(1)))

    # Xóa chunk lỗi khỏi cache trước khi reset ledger (FIX A1: ngăn duplicate)
    if flagged_indices:
        # Tìm cache file path từ run_folder
        cache_file = None
        if run_folder:
            ledger_path = os.path.join(os.path.abspath(run_folder), 'session_1', 'miner_progress.yaml')
            if os.path.isfile(ledger_path):
                try:
                    with open(ledger_path, 'r', encoding='utf-8') as f:
                        ledger_data = yaml.safe_load(f)
                    book_name = ledger_data.get('book_name', '')
                    if book_name:
                        cache_file = os.path.join('vault', '02-sources', 'books', f"{book_name}.md")
                        if not os.path.isabs(cache_file):
                            cache_file = os.path.abspath(cache_file)
                except Exception:
                    pass

        for idx in flagged_indices:
            if cache_file and os.path.isfile(cache_file):
                strip_chunk_from_cache(cache_file, idx)
            else:
                print(f"  [WARNING] Cannot strip chunk {idx} from cache — cache file not found")

    # Cập nhật ledger — reset PENDING để enable re-mine
    if flagged_indices and run_folder:
        ledger_path = os.path.join(os.path.abspath(run_folder), 'session_1', 'miner_progress.yaml')
        if os.path.isfile(ledger_path):
            try:
                with open(ledger_path, 'r', encoding='utf-8') as f:
                    ledger = yaml.safe_load(f)
                for idx in flagged_indices:
                    key = idx if idx in ledger.get('chunks', {}) else str(idx)
                    if key in ledger.get('chunks', {}):
                        ledger['chunks'][key]['status'] = 'PENDING'
                        ledger['chunks'][key]['error_code'] = 'INCOMPLETE_CONTENT'
                with open(ledger_path, 'w', encoding='utf-8') as f:
                    yaml.dump(ledger, f, allow_unicode=True)
            except Exception as e:
                print(f"  [WARNING] Could not update ledger: {e}")

    return flagged_indices


# ── Phase 1: Sentinel Check & Recovery ─────────────────────────────────────────

def check_and_recover_sentinel(content):
    """
    Kiểm tra <!-- HEADER_END --> sentinel.
    Nếu missing, tự động chèn vào đúng vị trí (sau TOC_MASTER, trước <data_chunk> đầu tiên).
    
    Returns: (modified_content, status)
        status: "SENTINEL_OK" | "SENTINEL_RECOVERED" | "FATAL"
    """
    SENTINEL = '<!-- HEADER_END -->'
    
    # Case 1: Sentinel đã tồn tại
    if SENTINEL in content:
        return content, "SENTINEL_OK"
    
    # Case 2: Sentinel bị mất — cần recovery
    # Tìm vị trí <data_chunk> đầu tiên
    first_chunk = re.search(r'^\s*<data_chunk>', content, re.MULTILINE)
    if not first_chunk:
        return content, "FATAL"
    
    # Chèn sentinel ngay trước <data_chunk> đầu tiên
    insert_pos = first_chunk.start()
    
    # Đảm bảo có dòng trống trước sentinel
    before = content[:insert_pos].rstrip('\n\r')
    after = content[insert_pos:]
    
    content = before + '\n\n' + SENTINEL + '\n\n' + after
    return content, "SENTINEL_RECOVERED"


# ── Phase 2: Chunk Count Validation ───────────────────────────────────────────

def validate_chunk_count(content):
    """
    Đếm số <data_chunk> trong file và so sánh với total_chunks từ META_BOOK hoặc TOC_MASTER.
    
    Returns: (expected, found, status)
        status: "CHUNK_COUNT_OK" | "CHUNK_COUNT_MISMATCH"
    """
    # Đếm data_chunk thực tế
    found = len(re.findall(r'<data_chunk>', content))
    
    # Tìm expected từ META_BOOK
    expected = None
    meta_match = re.search(r'total_chunks\s*=\s*(\d+)', content)
    if meta_match:
        expected = int(meta_match.group(1))
    
    # Fallback: đếm TOC entries
    if expected is None:
        toc_entries = re.findall(r'(?:[-*]\s*)Chunk\s+\d+:', content)
        if toc_entries:
            expected = len(toc_entries)
    
    if expected is None:
        return None, found, "CHUNK_COUNT_OK"  # Không có expected → skip validation
    
    if found == expected:
        return expected, found, "CHUNK_COUNT_OK"
    else:
        return expected, found, "CHUNK_COUNT_MISMATCH"


# ── Main Orchestrator ──────────────────────────────────────────────────────────

def post_mine(filepath, run_folder=None):
    """
    Main entry point. Chạy 3 phase:
    1. Sentinel Check & Recovery
    2. Chunk Count Validation
    3. Normalizer
    
    Returns: True nếu thành công, False nếu FATAL
    """
    print(f"\n{'='*60}")
    print(f"  POST-MINE ORCHESTRATOR")
    print(f"  File: {filepath}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    report_lines = []
    report_lines.append(f"POST-MINE REPORT")
    report_lines.append(f"File: {filepath}")
    report_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    report_lines.append(f"{'─'*40}")
    
    # ── Validate file exists ──
    if not os.path.isfile(filepath):
        log("INIT", "FATAL", f"File not found: {filepath}")
        print(f"\n❌ FATAL: File not found")
        return False
    
    # ── Validate file type ──
    # Rào chắn: post_mine chỉ xử lý file cache sách (.md).
    # Nếu Agent truyền nhầm YAML/JSON, dừng ngay ở đây
    # thay vì leak vào Phase 1 Sentinel Check rồi mới FATAL.
    if not filepath.endswith('.md'):
        log("INIT", "FATAL", f"Expected .md file, got: {os.path.basename(filepath)}")
        print(f"\n❌ FATAL: Not a markdown file")
        return False
    
    # ── Read file ──
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ── Validate content format ──
    # Rào chắn: File cache hợp lệ phải chứa META_BOOK (header) hoặc <data_chunk> (content).
    # Nếu cả 2 đều không có → đây không phải file cache sách.
    # Fail-fast ở đây giúp error message rõ ràng hơn
    # so với Phase 1 report "no <data_chunk> found".
    if '<data_chunk>' not in content and 'META_BOOK' not in content:
        log("INIT", "FATAL", f"File doesn't look like a book cache: {os.path.basename(filepath)}")
        print(f"\n❌ FATAL: Missing META_BOOK and <data_chunk> markers")
        return False
    
    # ── Phase 1: Sentinel ──
    print("── Phase 1: Sentinel Check ──")
    content, sentinel_status = check_and_recover_sentinel(content)
    
    if sentinel_status == "SENTINEL_OK":
        log("SENTINEL", "OK", "<!-- HEADER_END --> found in file")
        report_lines.append("Phase 1: SENTINEL_OK")
    elif sentinel_status == "SENTINEL_RECOVERED":
        log("SENTINEL", "RECOVERED", "<!-- HEADER_END --> was MISSING — auto-inserted before first <data_chunk>")
        # Write recovered content back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        report_lines.append("Phase 1: SENTINEL_RECOVERED (auto-inserted)")
    else:
        log("SENTINEL", "FATAL", "Cannot locate header boundary — no <data_chunk> found in file")
        report_lines.append("Phase 1: FATAL — no <data_chunk> found")
        print(f"\n❌ FATAL: Cannot locate header boundary")
        _write_report(filepath, report_lines, run_folder)
        return False
    
    # ── Phase 2: Chunk Count ──
    print("\n── Phase 2: Chunk Count Validation ──")
    expected, found, count_status = validate_chunk_count(content)
    
    if count_status == "CHUNK_COUNT_OK":
        if expected:
            log("CHUNKS", "OK", f"Chunk count matches: {found}/{expected}")
            report_lines.append(f"Phase 2: CHUNK_COUNT_OK ({found}/{expected})")
        else:
            log("CHUNKS", "INFO", f"Found {found} chunks (no expected count to validate against)")
            report_lines.append(f"Phase 2: CHUNK_COUNT_OK ({found} chunks, no expected)")
    else:
        log("CHUNKS", "WARNING", f"Chunk count MISMATCH: expected={expected}, found={found}")
        report_lines.append(f"Phase 2: CHUNK_COUNT_MISMATCH (expected={expected}, found={found})")

    # ── Phase 2.5: Content Integrity Audit ──
    print("\n── Phase 2.5: Content Integrity Audit ──")
    if not run_folder:
        run_folder = find_run_folder(filepath)

    # 2.5a: Đếm warning flags có sẵn (do Agent ghi)
    flags = count_warning_flags(content)
    has_flags = any(v > 0 for v in flags.values())
    for flag_name, count in flags.items():
        if count > 0:
            log("FLAGS", "WARNING", f"{flag_name}: {count} chunk(s)")
            report_lines.append(f"  WARNING {flag_name}: {count}")
    if not has_flags:
        log("FLAGS", "OK", "No warning flags detected")
        report_lines.append("  FLAGS: CLEAN")

    # 2.5b: Phát hiện marker có nhưng content rỗng + auto-reset ledger
    flagged = detect_empty_content_after_markers(content, run_folder)
    if flagged:
        log("CONTENT", "WARNING",
            f"Empty content after marker — chunks auto-reset to PENDING: {flagged}")
        report_lines.append(f"  EMPTY_CONTENT_CHUNKS (reset to PENDING): {flagged}")
        report_lines.append("  ACTION: Re-mine these chunks via CLI nlm notebook query + gate_checker.py.")
    else:
        log("CONTENT", "OK", "No empty-content-after-marker detected")
        report_lines.append("  EMPTY_CONTENT: CLEAN")
    
    # ── Phase 3: Normalizer ──
    print("\n── Phase 3: Normalizer ──")
    norm_result = normalize_file(filepath)

    if norm_result["success"]:
        log("NORMALIZER", "OK", "Normalization completed successfully")
        report_lines.append("Phase 3: NORMALIZER_OK")

        # Ghi whitelist stats vào report
        ws = norm_result.get("whitelist_stats", {})
        total_stripped = sum(ws.values())
        if total_stripped > 0:
            log("WHITELIST", "WARNING", f"Stripped {total_stripped} foreign field(s)")
            report_lines.append(f"  [WHITELIST] Stripped {total_stripped} foreign fields:")
            for key, count in sorted(ws.items(), key=lambda x: -x[1]):
                report_lines.append(f"    - {key}: {count}")
        else:
            log("WHITELIST", "OK", "No foreign fields detected")
            report_lines.append("  [WHITELIST]: CLEAN")
    else:
        log("NORMALIZER", "FATAL", "Normalizer failed — check normalizer output above")
        report_lines.append("Phase 3: NORMALIZER_FATAL")
        print(f"\n❌ FATAL: Normalizer failed")
        _write_report(filepath, report_lines, run_folder)
        return False
    
    # ── Summary ──
    _write_report(filepath, report_lines, run_folder)
    
    print(f"\n{'='*60}")
    print(f"  ✅ POST-MINE COMPLETE")
    print(f"{'='*60}\n")
    return True


def _write_report(filepath, lines, run_folder=None):
    """Write report to [run-folder]/session_1/post_mine_report.txt"""
    if not run_folder:
        run_folder = find_run_folder(filepath)
    if run_folder:
        session_dir = os.path.join(os.path.abspath(run_folder), 'session_1')
        os.makedirs(session_dir, exist_ok=True)
        report_path = os.path.join(session_dir, 'post_mine_report.txt')
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            log("REPORT", "OK", f"Report saved to {report_path}")
        except Exception as e:
            log("REPORT", "WARNING", f"Could not write report: {e}")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python post_mine.py <path_to_markdown_file> [--run-folder <run_folder>]")
        print('Example: python post_mine.py "vault/02-sources/books/Book.md" --run-folder ".extraction_runs/books/book_2026-04-11"')
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.isabs(filepath):
        filepath = os.path.abspath(filepath)

    # Parse --run-folder arg
    run_folder_arg = None
    if '--run-folder' in sys.argv:
        rf_idx = sys.argv.index('--run-folder')
        if rf_idx + 1 < len(sys.argv):
            run_folder_arg = sys.argv[rf_idx + 1]
            if not os.path.isabs(run_folder_arg):
                run_folder_arg = os.path.abspath(run_folder_arg)

    success = post_mine(filepath, run_folder=run_folder_arg)
    sys.exit(0 if success else 1)
