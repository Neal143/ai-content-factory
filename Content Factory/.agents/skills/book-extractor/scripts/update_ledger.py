"""
TÊN SCRIPT: update_ledger.py
VAI TRÒ: Atomic updater cho miner_progress.yaml — cập nhật trạng thái chunk
          mà không cần Agent tự edit YAML thủ công.
KHI NÀO SỬ DỤNG: Agent gọi ở bước ⑤ trong vòng lặp Miner (SKILL.md Bước 2).
                  Thay thế việc Agent tự mở/sửa/ghi file YAML.
CÁCH XỬ LÝ:
  1. Nhận args: ledger_path, chunk_index, status, [error_code].
  2. Đọc YAML → validate status/error_code → cập nhật chunk entry.
  3. Cập nhật last_updated top-level.
  4. Ghi YAML lại.
  5. In JSON summary ra stdout (bao gồm progress và milestone flag).

KHÔNG LÀM:
  ❌ Gọi NLM
  ❌ Gọi gate_checker hay append_cache
  ❌ Quyết định status (Agent/gate_checker quyết định, script chỉ ghi)

OUTPUT: JSON stdout summary + ledger file updated.

ERROR CODE REFERENCE (Trigger & Xử lý):
  DONE:                Chunk vượt qua 8-Point Gate → Lưu trữ, chuyển chunk tiếp theo.
  SKIPPED:             Response < 200 ký tự sau retry 2 lần (Gate [1]) → Append skeleton + warning.
  PARTIAL:             Kích thước chuỗi < 200 ký tự (Gate [1]) → Kích hoạt lại (max 2).
  MISMATCH:            Tên chunk không khớp chỉ định (Gate [2]) → Kích hoạt lại (max 2).
  MISSING_TAGS:        Khuyết thiếu trường cấu trúc (Gate [3][4][5]) → Phát lệnh truy vấn bổ sung → Rớt: Warning.
  LINK_ERROR:          Lỗi tham chiếu khóa ngoại (Gate [7]) → Yêu cầu đồng bộ → Rớt: Warning.
  SEMANTIC_ERROR_AXIS: Lỗi định lượng logic Trục 1/2/3 (Gate [8]) → Hiệu đính → Rớt: Warning.
  NETWORK_ERROR:       Gián đoạn kết nối → Kích hoạt lại (max 3).
  FATAL:               Vượt hạn mức retry cốt lõi (Gate [2]) → Không append chunk.
"""

import os
import sys
import json
import yaml
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Giá trị hợp lệ (Source of Truth — khớp với SKILL.md) ──
VALID_STATUSES = {"PENDING", "DONE", "SKIPPED", "FATAL"}
VALID_ERROR_CODES = {
    None, "PARTIAL", "MISMATCH", "MISSING_TAGS",
    "LINK_ERROR", "SEMANTIC_ERROR_AXIS", "NETWORK_ERROR"
}

# Milestone: in progress summary mỗi N chunks hoàn thành
MILESTONE_INTERVAL = 5


def update_ledger(ledger_path, chunk_index, status, error_code=None):
    """
    Cập nhật 1 chunk entry trong miner_progress.yaml.

    Args:
        ledger_path: Path tuyệt đối tới miner_progress.yaml.
        chunk_index: Số thứ tự chunk (1-based).
        status: Một trong VALID_STATUSES.
        error_code: Một trong VALID_ERROR_CODES hoặc None.

    Returns:
        dict: Summary JSON cho Agent đọc.
    """
    # ── Validate inputs ──
    if not os.path.isfile(ledger_path):
        return {"error": f"Ledger not found: {ledger_path}"}

    if status not in VALID_STATUSES:
        return {"error": f"Invalid status: '{status}'. Valid: {VALID_STATUSES}"}

    if error_code and error_code not in VALID_ERROR_CODES:
        return {"error": f"Invalid error_code: '{error_code}'. Valid: {VALID_ERROR_CODES}"}

    # ── Read ledger ──
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = yaml.safe_load(f)

    chunks = ledger.get('chunks', {})
    total_chunks = ledger.get('total_chunks', 0)
    now_iso = datetime.now(timezone.utc).isoformat()

    # ── Validate chunk exists ──
    chunk_key = chunk_index  # YAML key có thể là int hoặc str
    if chunk_key not in chunks and str(chunk_key) not in chunks:
        return {"error": f"Chunk {chunk_index} not found in ledger. Available: {list(chunks.keys())}"}

    # Normalize key (YAML đôi khi parse int key, đôi khi string)
    if chunk_key not in chunks:
        chunk_key = str(chunk_key)

    # ── Determine retry_count ──
    old_entry = chunks[chunk_key]
    old_status = old_entry.get('status', 'PENDING')
    old_retry = old_entry.get('retry_count', 0)

    # Nếu status không đổi (vẫn retry) → tăng retry_count
    # Nếu status thay đổi (PENDING → DONE) → giữ nguyên retry_count
    if status == old_status and status != 'DONE':
        new_retry = old_retry + 1
    else:
        new_retry = old_retry

    # ── Update chunk entry ──
    chunks[chunk_key] = {
        "status": status,
        "error_code": error_code,
        "retry_count": new_retry,
        "updated_at": now_iso
    }

    # ── Update top-level last_updated ──
    ledger['last_updated'] = now_iso

    # ── Write ledger ──
    with open(ledger_path, 'w', encoding='utf-8') as f:
        yaml.dump(ledger, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # ── Calculate progress ──
    done_count = 0
    fatal_count = 0
    pending_count = 0
    skipped_count = 0
    for key, info in chunks.items():
        s = info.get('status', 'PENDING')
        if s == 'DONE':
            done_count += 1
        elif s == 'FATAL':
            fatal_count += 1
        elif s == 'SKIPPED':
            skipped_count += 1
        elif s == 'PENDING':
            pending_count += 1

    # Milestone detection: mỗi MILESTONE_INTERVAL chunks done
    is_milestone = (done_count > 0 and done_count % MILESTONE_INTERVAL == 0)

    return {
        "updated_chunk": chunk_index,
        "status": status,
        "error_code": error_code,
        "progress": f"{done_count}/{total_chunks} done, {pending_count} pending, {fatal_count} fatal",
        "milestone": is_milestone
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python update_ledger.py <ledger_path> <chunk_index> <status> [error_code]")
        print('Example: python update_ledger.py "miner_progress.yaml" 5 DONE')
        print('Example: python update_ledger.py "miner_progress.yaml" 5 DONE MISSING_TAGS')
        print(f'\nValid statuses: {VALID_STATUSES}')
        print(f'Valid error_codes: {VALID_ERROR_CODES}')
        sys.exit(1)

    ledger_path = sys.argv[1]
    chunk_index = int(sys.argv[2])
    status = sys.argv[3]

    error_code = None
    if len(sys.argv) >= 5:
        error_code = sys.argv[4]
        if error_code.lower() == 'null' or error_code.lower() == 'none':
            error_code = None

    if not os.path.isabs(ledger_path):
        ledger_path = os.path.abspath(ledger_path)

    result = update_ledger(ledger_path, chunk_index, status, error_code)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("error"):
        sys.exit(1)
    else:
        sys.exit(0)
