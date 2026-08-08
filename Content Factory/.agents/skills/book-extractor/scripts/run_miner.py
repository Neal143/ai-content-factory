"""
Tên file: run_miner.py
Last update: 08/08/2026 18:20 (GMT+7)
Vai trò: Tự động chạy Phase 2 Content extraction.
Được sử dụng khi: Chạy Phase 2 trong loop Bước 2.
Output: Lưu kết quả vào session_1/chunk_NN_raw.txt.
Tóm tắt logic: Đọc progress.yaml, cache, jtbd_gate.json -> Ghép query -> Gọi NLM -> Lưu file.
"""
import sys, os, yaml, json, subprocess, re

def run_miner(run_folder, chunk_index, cache_file):
    chunk_idx = int(chunk_index)
    chunk_nn = str(chunk_idx).zfill(2)
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
    # Tim audience, evidence
    gate_file = os.path.join(run_folder, "session_1", "jtbd_raw", f"chunk_{chunk_nn}_jtbd_gate.json")
    with open(gate_file, 'r', encoding='utf-8') as f:
        g_data = json.load(f)
    audience = g_data.get('audience', '')
    evidence = g_data.get('evidence', '')
    
    query = (f'Tham chiếu file prompt-miner-v4.md, hãy trích xuất CHÍNH XÁC Content Chunk sau: '
             f'Chunk {chunk_idx}: {chunk_name}. Ghi chú: Sử dụng Audience: "{audience}" '
             f'và Evidence: "{evidence}" để làm ngữ cảnh xác định Insight và Knowledge.')
             
    res = subprocess.run(['nlm', 'notebook', 'query', nb_id, query, '--json'], capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"NLM ERROR: {res.stderr}")
        return False
    try:
        ans = json.loads(res.stdout).get('answer', '')
    except:
        ans = res.stdout
    out_file = os.path.join(run_folder, "session_1", f"chunk_{chunk_nn}_raw.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(ans)
    print(f"SUCCESS: Saved Content to {os.path.basename(out_file)}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python run_miner.py <run_folder> <chunk_index> <cache_file>")
        sys.exit(1)
    sys.exit(0 if run_miner(sys.argv[1], sys.argv[2], sys.argv[3]) else 1)
