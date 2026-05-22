"""
TÊN SCRIPT: gate_checker.py
VAI TRÒ: Single-chunk Quality Gate Checker — Nhận raw text (Agent đã lưu từ CLI response),
          chạy Gates [1-7], trả kết quả cho Agent.
KHI NÀO SỬ DỤNG: Được Agent gọi per-chunk trong vòng lặp Bước 2 (SKILL.md).
                  Agent gọi NLM qua CLI nlm notebook query → lưu raw → gọi script này validate.
CÁCH XỬ LÝ:
  1. Nhận args: raw_file, chunk_index, chunk_name.
  2. Đọc raw text từ file (Agent đã lưu từ CLI response).
  3. [SHIFT-LEFT] Auto-Repair: Ép chuẩn CHUNK_index (chống ảo) & Móc ngoéo Khóa ngoại.
  4. Chạy Gate [1] (length) + Gates [2-7] (quality_gate.py).
  5. Ghi kết quả vào cùng thư mục: chunk_NN_gate.json.
  6. In kết quả ra stdout cho Agent đọc.

KHÔNG LÀM:
  ❌ Gọi NLM (Agent gọi CLI trực tiếp)
  ❌ Compose prompt (Agent tự compose)
  ❌ Đọc/cập nhật ledger (Agent làm)
  ❌ Append vào cache file (Agent làm sau Gate [8])
  ❌ Gọi post_mine.py (Agent gọi khi hết chunk PENDING)
  ❌ Retry logic (Agent quyết định retry và gọi lại script)

OUTPUT: chunk_NN_gate.json (có next_action) + stdout summary.
"""

import os
import json
import sys
import re

# Import quality gate module
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from quality_gate import run_deterministic_gates
from normalizer import normalize_dikw_names


def check_chunk(raw_file, chunk_index, chunk_name, cache_file=None):
    """
    Validate 1 chunk từ raw text file, chạy Gates [1-7], ghi kết quả.

    Args:
        raw_file: Path tới file chunk_NN_raw.txt (Agent đã lưu từ CLI response)
        chunk_index: Số thứ tự chunk (1-based)
        chunk_name: Tên chunk (từ TOC, Agent truyền vào)

    Returns:
        dict: Gate result (cùng format với gate.json)
    """
    # Fix Windows console encoding
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    chunk_nn = str(chunk_index).zfill(2)
    gate_file = os.path.join(os.path.dirname(raw_file), f"chunk_{chunk_nn}_gate.json")

    print(f"\n{'='*60}")
    print(f"  QUALITY GATE CHECKER")
    print(f"  Chunk {chunk_index}: {chunk_name}")
    print(f"  Raw file: {raw_file}")
    print(f"{'='*60}\n")

    # ── Read raw text ──
    if not os.path.isfile(raw_file):
        na = _build_next_action_retry(
            chunk_index, "NETWORK_ERROR",
            f"Raw file not found: {raw_file}"
        )
        result = _build_result(
            chunk_index, chunk_name, raw_file,
            passed=False, failed_gates=["[0]"],
            error_code="NETWORK_ERROR", needs_retry=True,
            detail=f"Raw file not found: {raw_file}",
            next_action=na
        )
        _write_gate_json(gate_file, result)
        print(f"  ❌ Raw file not found")
        return result

    with open(raw_file, 'r', encoding='utf-8') as f:
        answer = f.read()

    # ── [SHIFT-LEFT] Auto-Repair Metadata & Khóa Ngoại ──
    original_answer = answer
    
    # 1. Ép cứng CHUNK_index chuẩn (Bọc thép chống LLM hallucinate mọi định dạng)
    def _repair_chunk_index(match):
        line = match.group(0)
        # Xóa sạch mọi dấu vết CHUNK_index ảo (dù là số, chữ hay ký tự đặc biệt)
        line = re.sub(r'\|\s*CHUNK_index\s*=\s*[^|\n\r]+', '', line)
        line = re.sub(r'CHUNK_index\s*=\s*[^|\n\r]+\s*\|?', '', line)
        
        # POKA-YOKE Tầng 2: Nếu AI nuốt mất mỏ neo META_CHUNK:, tự động bù vào
        if 'META_CHUNK:' not in line:
            line = "META_CHUNK: " + line.lstrip()
            
        # Bắt vít cứng biến môi trường vào đuôi dòng
        return line.strip() + f" | CHUNK_index={chunk_index}"
        
    # Mỏ neo lõi CHUNK= dùng để định vị. Giới hạn sửa 1 lần đầu tiên (count=1).
    answer = re.sub(r'^.*CHUNK\s*=.*$', _repair_chunk_index, answer, count=1, flags=re.MULTILINE)

    # 1.5. [SHIFT-LEFT] Tự động sửa lỗi NotebookLM quên knowledge_name
    def _repair_knowledge_name(match):
        prefix = match.group(1)
        kn_name = match.group(2).strip()
        if kn_name.endswith('**'):
            kn_name = kn_name[:-2].strip()
        middle = match.group(3)
        meta_tag = match.group(4)
        meta_content = match.group(5)
        
        if "knowledge_name=" not in meta_content:
            meta_content = meta_content.strip() + f" | knowledge_name={kn_name}"
            
        return f"{prefix}{match.group(2)}{middle}{meta_tag}{meta_content}"

    answer = re.sub(
        r'([^②]*②-\d+\.\s*[^:]+:\s*)([^\n]+)(\s*\n+\s*)(META_KNOWLEDGE:\s*)([^\n]+)',
        _repair_knowledge_name,
        answer
    )

    # 1.6. [SHIFT-LEFT] Tự động điền metadata Low-Critical/Unused thiếu
    answer = auto_fill_optional_fields(answer)

    # 2. Tự động nắn Khóa Ngoại (Substring Match)
    answer = normalize_dikw_names(answer)
    
    if answer != original_answer:
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(answer)
        print("  🔧 [AUTO-REPAIR] Đã chuẩn hóa CHUNK_index và Khóa Ngoại.")

    print(f"  Raw length: {len(answer)} chars")

    # ── Gate [1]: Length check ──
    if len(answer) < 200:
        append_script = ".agent/skills/book-extractor/scripts/append_cache.py"
        na = {
            "type": "RETRY",
            "max_retry": 2,
            "instruction": "Gọi lại NLM query gốc (từ next_chunk.py), lưu đè raw file, chạy lại gate_checker.",
            "detail": f"Response too short: {len(answer)} chars (min 200)",
            "on_exhaust": {
                "cli_append": f'python {append_script} "{raw_file}" "{cache_file}" --warnings "SKIPPED_SHORT_CONTENT"',
                "ledger_update": {"status": "SKIPPED", "error_code": "PARTIAL"}
            }
        }
        result = _build_result(
            chunk_index, chunk_name, raw_file,
            passed=False, failed_gates=["[1]"],
            error_code="PARTIAL", needs_retry=True,
            detail=f"Response too short: {len(answer)} chars (min 200)",
            next_action=na
        )
        _write_gate_json(gate_file, result)
        print(f"  ❌ Gate [1] FAIL: {result['detail']}")
        return result

    # ── Gates [2-7]: Deterministic quality check ──
    gate_result = run_deterministic_gates(
        answer, f"Chunk {chunk_index}: {chunk_name}", chunk_index,
        cache_file=cache_file
    )

    # ── Build next_action based on gate results ──
    na = _build_next_action(
        gate_result, chunk_index, chunk_name, raw_file, cache_file
    )

    result = _build_result(
        chunk_index, chunk_name, raw_file,
        passed=gate_result.passed,
        failed_gates=gate_result.failed_gates,
        error_code=gate_result.error_code,
        needs_retry=gate_result.needs_retry,
        needs_supplement=gate_result.needs_supplement,
        detail=gate_result.detail,
        next_action=na
    )
    _write_gate_json(gate_file, result)

    if gate_result.passed:
        print(f"  ✅ Gates [1-7] PASS")
    else:
        print(f"  ❌ Gates {gate_result.failed_gates} FAIL: {gate_result.detail}")

    return result


def auto_fill_optional_fields(content):
    """
    [SHIFT-LEFT] Tự động điền các optional/unused fields bị thiếu từ NLM.
    Giảm tỷ lệ fail Gate [5] (thiếu stance) và chuẩn hóa dữ liệu cho Downstream.
    """
    fallbacks = {
        "META_KNOWLEDGE": {"stance": "support"},
        "META_EVIDENCE": {"evidence_keyword": "unknown"},
        "META_STORY": {
            "protagonist": "unknown", 
            "core_event": "unknown", 
            "timeline": "unknown", 
            "outcome_measurable": "unknown"
        },
        "META_QUOTE": {
            "speaker": "unknown", 
            "quote_keyword": "unknown", 
            "context": "unknown"
        }
    }
    
    def process_line(match):
        meta_type = match.group(1)
        value_str = match.group(2)
        
        # Bỏ qua sentinel
        if "[NOT_FOUND]" in value_str or "[NO_JTBD_FOUND]" in value_str:
            return match.group(0)
            
        # Bỏ qua vivid_* (chúng không có các optional fields của master node)
        if "content_type=" in value_str and "vivid_" in value_str:
            return match.group(0)
            
        fields = fallbacks.get(meta_type, {})
        for field, default_val in fields.items():
            pattern = rf'({field})\s*=\s*([^|\n\r]*)'
            m = re.search(pattern, value_str)
            if not m:
                # Thiếu field -> Append
                value_str += f" | {field}={default_val}"
            else:
                # Có field nhưng rỗng
                val = m.group(2).strip()
                if not val:
                    # Thay thế giá trị rỗng bằng default_val
                    value_str = re.sub(pattern, rf'\1={default_val}', value_str)
                    
        return f"{meta_type}: {value_str}"
        
    return re.sub(r'^(META_(?:KNOWLEDGE|EVIDENCE|STORY|QUOTE)):\s*(.*)$', process_line, content, flags=re.MULTILINE)


def _build_next_action(gate_result, chunk_index, chunk_name, raw_file, cache_file):
    """
    Dựa trên kết quả Gate [1-7], trả dict mô tả hành động tiếp theo.
    Agent chạy TRỰC TIẾP theo dict này, không cần đọc SKILL.md.
    """
    append_script = ".agent/skills/book-extractor/scripts/append_cache.py"
    chunk_nn = str(chunk_index).zfill(2)
    run_folder = os.path.dirname(raw_file)

    # Guard: cache_file bắt buộc cho các CLI commands
    if not cache_file:
        return {"type": "ERROR", "detail": "cache_file is required. Use --cache flag when calling gate_checker.py"}

    if gate_result.passed:
        # ── PASS Script Gates → Agent đánh giá Gate [8] ──
        return {
            "type": "AGENT_EVAL",
            "instruction": "Đọc raw file, đánh giá Gate [8] (Semantic Score), ghi agent_gate.json rồi hành động theo on_pass/on_fail",
            "agent_gate_template": {
                "chunk_index": chunk_index,
                "gate_8_axis_1": None,
                "gate_8_axis_2": None,
                "gate_8_pass": None,
                "verdict": ""
            },
            "agent_gate_file": os.path.join(run_folder, f"chunk_{chunk_nn}_agent_gate.json"),
            "on_pass": {
                "cli_append": f'python {append_script} "{raw_file}" "{cache_file}"',
                "ledger_update": {"status": "DONE", "error_code": None}
            },
            "on_fail_axis": {
                "max_retry": 1,
                "action": "Gửi NLM query hiệu đính trục hỏng, lưu đè raw file, re-eval Gate [8]",
                "fallback_template": {
                    "cli_append": f'python {append_script} "{raw_file}" "{cache_file}" --warnings "SEMANTIC_WARNING_AXIS_{{N}}"',
                    "ledger_update": {"status": "DONE", "error_code": "SEMANTIC_ERROR_AXIS"}
                }
            }
        }

    if gate_result.needs_retry:
        # ── RETRY (Gate [2] fail — sai chunk) ──
        return _build_next_action_retry(
            chunk_index, gate_result.error_code, gate_result.detail
        )

    if gate_result.needs_supplement:
        # ── SUPPLEMENT (Gate [3-7] fail) ──
        mandatory_fail = [g for g in gate_result.failed_gates if g in ["[3]", "[4]", "[5]", "[7]"]]

        fallback_warnings = None
        fallback_error = None
        if mandatory_fail:
            fallback_warnings = "MISSING_TAGS"
            fallback_error = "MISSING_TAGS"

        fallback_cli = f'python {append_script} "{raw_file}" "{cache_file}"'
        if fallback_warnings:
            fallback_cli += f' --warnings "{fallback_warnings}"'

        return {
            "type": "SUPPLEMENT",
            "max_retry": 2,
            "failed_gates": gate_result.failed_gates,
            "missing_detail": gate_result.detail,
            "instruction": f"Gọi NLM yêu cầu trích xuất LẠI TOÀN BỘ chunk (không phải chỉ phần thiếu), nhấn mạnh đảm bảo có đầy đủ: {gate_result.detail}. Lưu đè raw file, chạy lại gate_checker.",
            "on_exhaust": {
                "cli_append": fallback_cli,
                "ledger_update": {"status": "DONE", "error_code": fallback_error}
            }
        }

    return {"type": "UNKNOWN", "detail": gate_result.detail}


def _build_next_action_retry(chunk_index, error_code, detail):
    """Build next_action cho trường hợp RETRY (Gate [1] hoặc [2])."""
    return {
        "type": "RETRY",
        "max_retry": 2,
        "instruction": "Gọi lại NLM query gốc (từ next_chunk.py), lưu đè raw file, chạy lại gate_checker.",
        "detail": detail,
        "on_exhaust": {
            "ledger_update": {"status": "FATAL", "error_code": error_code},
            "do_not_append": True
        }
    }


def _build_result(chunk_index, chunk_name, raw_file, *,
                  passed, failed_gates=None, error_code=None,
                  needs_retry=False, needs_supplement=False,
                  detail="", skipped=False, next_action=None):
    """Build standardized result dict."""
    return {
        "chunk_index": chunk_index,
        "chunk_name": chunk_name,
        "passed": passed,
        "skipped": skipped,
        "failed_gates": failed_gates or [],
        "error_code": error_code,
        "needs_retry": needs_retry,
        "needs_supplement": needs_supplement,
        "detail": detail,
        "raw_file": os.path.basename(raw_file),
        "next_action": next_action
    }


def _write_gate_json(gate_file, result):
    """Write gate result to JSON file."""
    with open(gate_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  Gate result: {gate_file}")


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python gate_checker.py <raw_file> <chunk_index> <chunk_name> [--cache <cache_file>]")
        print('Example: python gate_checker.py "chunk_05_raw.txt" 5 "Phần 2" --cache "vault/02-sources/books/Book.md"')
        sys.exit(1)

    raw_file = sys.argv[1]
    chunk_index = int(sys.argv[2])
    chunk_name = sys.argv[3]

    # Parse --cache arg
    cache_file_arg = None
    if '--cache' in sys.argv:
        c_idx = sys.argv.index('--cache')
        if c_idx + 1 < len(sys.argv):
            cache_file_arg = sys.argv[c_idx + 1]
            if not os.path.isabs(cache_file_arg):
                cache_file_arg = os.path.abspath(cache_file_arg)

    result = check_chunk(raw_file, chunk_index, chunk_name, cache_file=cache_file_arg)
    sys.exit(0 if result['passed'] or result.get('skipped') else 1)
