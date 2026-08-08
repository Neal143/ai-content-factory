"""
Tên file: run_jtbd.py
Last update: 08/08/2026 18:20 (GMT+7)
Vai trò: Tự động chạy Phase 1 JTBD extraction.
Được sử dụng khi: Chạy Phase 1 trong loop Bước 2.
Output: Lưu kết quả vào session_1/jtbd_raw/chunk_NN_jtbd.txt.
Tóm tắt logic: Đọc progress.yaml & cache -> Ghép query -> Gọi NLM -> Lưu file.
"""
import sys, os, yaml, json, subprocess, re

def run_jtbd(run_folder, chunk_index, cache_file):
    chunk_idx = int(chunk_index)
    ledger_path = os.path.join(run_folder, "session_1", "miner_progress.yaml")
    with open(ledger_path, 'r', encoding='utf-8') as f:
        nb_id = yaml.safe_load(f).get('notebook_id', '')
    with open(cache_file, 'r', encoding='utf-8') as f:
        c_text = f.read()
    # Tim chunk_name
    toc_match = re.search(r'TOC_MASTER[:\*\s]*\n(.*?)(?:\n\n\n|\Z|<!--)', c_text, re.DOTALL)
    chunk_name = ""
    if toc_match:
        for m in re.finditer(r'(?:[-*]\s*)?Chunk\s+(\d+):\s*(.+?)(?:\r?\n|$)', toc_match.group(1)):
            if int(m.group(1)) == chunk_idx:
                chunk_name = m.group(2).strip()
                break
    # Tim book_audience
    aud_match = re.search(r'^META_BOOK_AUDIENCE:\s*(.+)$', c_text, re.MULTILINE)
    book_audience = aud_match.group(1).strip() if aud_match else ""
    if not chunk_name or not book_audience:
        print("ERROR: Missing chunk_name or book_audience in cache")
        return False
    query = f"Tham chiếu file prompt-jtbd-chunk-v1.md, hãy xác định JTBD audience cho Chunk {chunk_idx}: {chunk_name}. JTBD cấp sách: {book_audience}."
    res = subprocess.run(['nlm', 'notebook', 'query', nb_id, query, '--json'], capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"NLM ERROR: {res.stderr}")
        return False
    try:
        ans = json.loads(res.stdout).get('answer', '')
    except:
        ans = res.stdout
    chunk_nn = str(chunk_idx).zfill(2)
    out_dir = os.path.join(run_folder, "session_1", "jtbd_raw")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"chunk_{chunk_nn}_jtbd.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(ans)
    print(f"SUCCESS: Saved JTBD to {os.path.basename(out_file)}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python run_jtbd.py <run_folder> <chunk_index> <cache_file>")
        sys.exit(1)
    sys.exit(0 if run_jtbd(sys.argv[1], sys.argv[2], sys.argv[3]) else 1)
