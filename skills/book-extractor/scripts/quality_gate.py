"""
TÊN SCRIPT: quality_gate.py
VAI TRÒ: Shared module — Deterministic Quality Gate Validator.
          Thực thi Gates [2]-[7] bằng Regex thuần, không cần LLM.
          Gate [8] cần LLM judge — do Agent thực thi per-chunk (Semantic Score).

KHI NÀO SỬ DỤNG:
  - Được import bởi gate_checker.py (validate raw text Agent đã lưu từ CLI)
  - Được import bởi post_mine.py (Phase 2.5 content integrity audit)
  - Được import bởi audit_cache.py (validate file vault bất kỳ lúc)

CÁCH XỬ LÝ:
  Gate [2] CORRECT_CHUNK:  CHUNK= trong response phải khớp tên chunk yêu cầu.
                           Fuzzy match (lowercase + strip) để tránh false positive.
                           Fail → needs_retry=True (retry ngay, không check tiếp).
  Gate [3] HAS_AUDIENCE:   Có META_CHUNK_AUDIENCE hoặc [NO_JTBD_FOUND].
  Gate [4] HAS_INSIGHT:    Có insight_type= VÀ insight_name=.
  Gate [5] HAS_KNOWLEDGE:  Có knowledge_type=, stance=, supports_insight=.
  Gate [6] HAS_OPTIONAL:   Section ③④ phải có marker HOẶC [NOT_FOUND].
                           Gates [3-6] thu thập tất cả failures trước khi return.
  Gate [7] LINK_INTEGRITY:  Chiều 1: supports_insight= khớp insight_name= (Exact Match).
                            Chiều 2: supports_knowledge= khớp knowledge_name= (Exact Match).
                            Cả 2 chiều: normalize_dikw_names() đã chạy trước ở gate_checker (Shift-Left).

KHÔNG LÀM: Không đọc/ghi file. Không gọi NLM. Không import từ script khác.
OUTPUT: GateResult — data object chứa verdict và hướng xử lý cho caller.
"""

import re
import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class GateResult:
    """
    Kết quả của một lần chạy quality gate.
    Caller (gate_checker.py, audit_cache.py) dùng các field này để quyết định hành động.
    """
    passed: bool
    failed_gates: List[str] = field(default_factory=list)
    error_code: Optional[str] = None
    needs_retry: bool = False       # True → retry NLM cùng prompt gốc (max 2 lần)
    needs_supplement: bool = False  # True → gửi supplement query bổ sung field thiếu
    detail: str = ""                # Mô tả human-readable cho log và report


def build_toc_map_from_cache(cache_file: str) -> dict:
    """
    Đọc cache file, parse TOC_MASTER, trả về dict {chunk_index: canonical_name}.
    Dùng cho Gate [2] để cross-reference tên chunk thay vì tin Agent.
    """
    toc_map = {}
    if not cache_file or not os.path.isfile(cache_file):
        return toc_map
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
        toc_match = re.search(r'TOC_MASTER[:\*\s]*\n(.*?)(?:\n\n\n|\Z|<!--)', content, re.DOTALL)
        if not toc_match:
            return toc_map
        toc_body = toc_match.group(1)
        for m in re.finditer(r'(?:[-*]\s*)Chunk\s+(\d+):\s*(.+?)(?:\r?\n|$)', toc_body):
            idx = int(m.group(1))
            toc_map[idx] = m.group(2).strip()
    except Exception:
        pass
    return toc_map


def check_gate_2(answer: str, expected_chunk_name: str, chunk_index: int = 0, cache_file: str = None) -> GateResult:
    """
    Gate [2] CORRECT_CHUNK: Giá trị CHUNK= trong response phải khớp tên chunk yêu cầu.

    Logic 2 lớp:
    1. Nếu có cache_file → parse TOC_MASTER, lấy canonical name cho chunk_index
       → so sánh CHUNK= với canonical name (KHÔNG tin Agent).
    2. Nếu không có cache_file → fallback so sánh với expected_chunk_name (từ Agent).

    Fuzzy match (lowercase + strip) để tránh false positive.
    Fail → needs_retry=True (data sai chunk, không check tiếp).
    """
    match = re.search(r'CHUNK\s*=\s*([^|\n`\r]+)', answer)
    if not match:
        return GateResult(
            passed=False, failed_gates=["[2]"],
            error_code="MISMATCH", needs_retry=True,
            detail="Không tìm thấy trường CHUNK= trong response."
        )

    found = match.group(1).strip().lower()

    # ── Lớp 1: Cross-reference với TOC_MASTER (ưu tiên) ──
    # Lấy tên canonical từ TOC, không phụ thuộc vào Agent truyền đúng hay sai.
    canonical_name = None
    if cache_file and chunk_index > 0:
        toc_map = build_toc_map_from_cache(cache_file)
        canonical_name = toc_map.get(chunk_index)

    # Chọn expected: ưu tiên canonical từ TOC, fallback Agent-provided
    if canonical_name:
        expected = canonical_name.strip().lower()
        source = "TOC_MASTER"
    else:
        expected = expected_chunk_name.strip().lower()
        source = "Agent-provided"

    # Fuzzy: expected là substring của found, hoặc ngược lại
    if expected not in found and found not in expected:
        return GateResult(
            passed=False, failed_gates=["[2]"],
            error_code="MISMATCH", needs_retry=True,
            detail=(
                f"CHUNK mismatch (vs {source}): "
                f"expected='{canonical_name or expected_chunk_name}' | "
                f"found='{match.group(1).strip()}'"
            )
        )

    return GateResult(passed=True)


def check_gate_345(answer: str) -> GateResult:
    """
    Gate [3] HAS_AUDIENCE:  Có META_CHUNK_AUDIENCE hoặc [NO_JTBD_FOUND].
    Gate [4] HAS_INSIGHT:    Có insight_type= VÀ insight_name=.
    Gate [5] HAS_KNOWLEDGE: Có knowledge_type=, knowledge_name=, stance=, supports_insight=.

    Thu thập tất cả failures (không short-circuit) để supplement query
    có thể yêu cầu bổ sung đúng tất cả fields còn thiếu trong một lần.
    """
    failed = []

    # Gate [3]: HAS_AUDIENCE
    # PASS nếu 1 trong 2:
    #   (1) chunk_audience= tồn tại, giá trị không rỗng
    #   (2) META_CHUNK_AUDIENCE: tồn tại, giá trị [NO_JTBD_FOUND]
    audience_match = re.search(r'chunk_audience\s*=\s*(.+)', answer)
    has_audience = (audience_match and audience_match.group(1).strip())
    has_no_jtbd = bool(re.search(r'META_CHUNK_AUDIENCE:\s*`?\[NO_JTBD_FOUND\]', answer))
    if not has_audience and not has_no_jtbd:
        failed.append("[3]")

    # Gate [4]
    if not re.search(r'insight_type\s*=', answer) or \
       not re.search(r'insight_name\s*=', answer):
        failed.append("[4]")

    # Gate [5]
    if not re.search(r'knowledge_type\s*=', answer) or \
       not re.search(r'knowledge_name\s*=', answer) or \
       not re.search(r'stance\s*=', answer) or \
       not re.search(r'supports_insight\s*=', answer):
        failed.append("[5]")

    if failed:
        return GateResult(
            passed=False, failed_gates=failed,
            error_code="MISSING_TAGS", needs_supplement=True,
            detail=f"Thiếu trường bắt buộc tại Gates {', '.join(failed)}"
        )

    return GateResult(passed=True)


def check_gate_6(answer: str) -> GateResult:
    """
    Gate [6] HAS_OPTIONAL_MARKERS: Section ③④ phải có marker HOẶC [NOT_FOUND].

    Không được bỏ trống hoàn toàn — đây là vi phạm protocol prompt-miner-v4.
    Check sự HIỆN DIỆN của marker hoặc placeholder, không check nội dung.
    (Nội dung rỗng sau marker được phát hiện ở post_mine.py Phase 2.5.)

    FIX B1: [NOT_FOUND] được anchor vào section context (③/④)
    thay vì match global — tránh false positive cross-section.

    ⑤ Quote: KHÔNG CHECK — optional, không enforce.
    """
    missing = []

    # Section ③: shocking_fact hoặc evidence hoặc [NOT_FOUND] sau marker ③
    has_s3_content = bool(re.search(r'content_type\s*=\s*(?:shocking_fact|evidence)', answer))
    has_s3_notfound = bool(re.search(r'(?:③[^\n]*\[NOT_FOUND\]|META_EVIDENCE:\s*\[NOT_FOUND\])', answer))
    if not has_s3_content and not has_s3_notfound:
        missing.append("③ Evidence/Shocking fact")

    # Section ④: story hoặc case_study hoặc [NOT_FOUND] sau marker ④
    has_s4_content = bool(re.search(r'content_type\s*=\s*(?:story|case_study)', answer))
    has_s4_notfound = bool(re.search(r'(?:④[^\n]*\[NOT_FOUND\]|META_STORY:\s*\[NOT_FOUND\])', answer))
    if not has_s4_content and not has_s4_notfound:
        missing.append("④ Story/Case Study")

    # ⑤ Quote — KHÔNG CHECK (optional, không enforce)

    if missing:
        return GateResult(
            passed=False, failed_gates=["[6]"],
            error_code=None, needs_supplement=True,
            detail=f"Thiếu section: {', '.join(missing)}"
        )

    return GateResult(passed=True)


def check_gate_7(answer: str) -> GateResult:
    """Gate [7] LINK INTEGRITY (Script hóa hoàn toàn):
    Chiều 1: supports_insight= phải khớp insight_name=.
    Chiều 2: supports_knowledge= phải khớp knowledge_name=.
    Dữ liệu đã qua normalize_dikw_names() ở gate_checker → dùng Exact Match.
    """
    orphans = []

    # Chiều 1: Insight
    insight_names = {
        m.group(1).strip().lower()
        for m in re.finditer(r'insight_name\s*=\s*([^|"\n`\r]+)', answer)
    }
    supports_insight = {
        m.group(1).strip().lower()
        for m in re.finditer(r'supports_insight\s*=\s*([^|"\n`\r]+)', answer)
    }
    if insight_names:
        for si in (supports_insight - insight_names):
            orphans.append(f"insight:{si}")

    # Chiều 2: Knowledge
    knowledge_names = {
        m.group(1).strip().lower()
        for m in re.finditer(r'knowledge_name\s*=\s*([^|"\n`\r]+)', answer)
    }
    supports_knowledge = {
        m.group(1).strip().lower()
        for m in re.finditer(r'supports_knowledge\s*=\s*([^|"\n`\r]+)', answer)
    }
    if knowledge_names:
        for sk in (supports_knowledge - knowledge_names):
            orphans.append(f"knowledge:{sk}")

    if orphans:
        return GateResult(
            passed=False, failed_gates=["[7]"],
            error_code="LINK_ERROR", needs_supplement=True,
            detail=f"Orphan FK: {orphans}"
        )
    return GateResult(passed=True)


def run_deterministic_gates(answer: str, chunk_name: str, chunk_index: int, cache_file: str = None) -> GateResult:
    """
    Entry point chính. Chạy Gates [2]-[7] theo thứ tự đúng.

    Thứ tự xử lý:
    1. Gate [2]: fail → return ngay (data sai chunk, không check tiếp).
    2. Gate [3][4][5]: collect tất cả failures.
    3. Gate [6]: collect failures.
    4. Gate [7]: Link integrity (Insight & Knowledge).
    5. Merge tất cả, return GateResult tổng hợp.

    Lưu ý:
    - Gate [1] (length check) xử lý trong gate_checker.py trước khi gọi hàm này.
    - Gate [8] (Semantic Score) do Agent đánh giá per-chunk — không script hóa tại đây.
    """
    # Gate [2] — sai chunk → retry ngay
    g2 = check_gate_2(answer, chunk_name, chunk_index=chunk_index, cache_file=cache_file)
    if not g2.passed:
        return g2

    # Gate [3][4][5] — thiếu trường bắt buộc
    g345 = check_gate_345(answer)

    # Gate [6] — section optional bị bỏ qua hoàn toàn
    g6 = check_gate_6(answer)

    # Gate [7] — link integrity
    g7 = check_gate_7(answer)

    # Merge
    all_failed = g345.failed_gates + g6.failed_gates + g7.failed_gates
    if not all_failed:
        return GateResult(passed=True)

    # Xác định error_code ưu tiên: LINK > MISSING_TAGS > INCOMPLETE
    if g7.failed_gates:
        primary_error = "LINK_ERROR"
    elif g345.failed_gates:
        primary_error = "MISSING_TAGS"
    else:
        primary_error = None

    combined_detail = " | ".join(filter(None, [g345.detail, g6.detail, g7.detail]))

    return GateResult(
        passed=False,
        failed_gates=all_failed,
        error_code=primary_error,
        needs_retry=False,
        needs_supplement=g345.needs_supplement or g6.needs_supplement or g7.needs_supplement,
        detail=combined_detail
    )
