"""
Tên file: run_mapper.py
Last update: 08/08/2026 18:20 (GMT+7)
Vai trò: Đọc 00-blackboard.yaml, tự gọi NLM sinh Tổng quan và Mục lục sách.
Được sử dụng khi: Chạy Bước 1 (The Mapper) trong SKILL.md.
Output: Lưu kết quả NLM vào session_1/mapper_raw.md.
Tóm tắt logic: Đọc YAML -> Ghép câu lệnh query -> subprocess gọi NLM -> lưu JSON answer.
"""
import sys, os, yaml, json, subprocess

def run_mapper(run_folder):
    bb_path = os.path.join(run_folder, "00-blackboard.yaml")
    if not os.path.isfile(bb_path):
        print(f"ERROR: Cannot find {bb_path}")
        return False
    with open(bb_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    book_name = data.get('book_name')
    nb_id = data.get('notebook_id')
    if not book_name or not nb_id:
        print("ERROR: book_name or notebook_id missing in 00-blackboard.yaml")
        return False
    query = f"Chỉ tham chiếu DUY NHẤT file prompt-mapper-v4.md (TUYỆT ĐỐI BỎ QUA prompt-miner-v4.md). Nhiệm vụ của bạn là đóng vai MAPPER, sinh Tổng quan (META_BOOK, META_BOOK_AUDIENCE) và Bảng Mục Lục (TOC_MASTER) chia thành các CHUNK cho sách {book_name}. BẮT BUỘC trả về ĐÚNG cấu trúc có trong prompt-mapper-v4.md. Không trả về data_chunk."
    print("Calling NLM...")
    res = subprocess.run(['nlm', 'notebook', 'query', nb_id, query, '--json'], capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0:
        print(f"NLM ERROR: {res.stderr}")
        return False
    try:
        ans = json.loads(res.stdout).get('answer', '')
    except:
        ans = res.stdout
    session_dir = os.path.join(run_folder, "session_1")
    os.makedirs(session_dir, exist_ok=True)
    out_file = os.path.join(session_dir, "mapper_raw.md")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(ans)
    print(f"SUCCESS: Saved to mapper_raw.md")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_mapper.py <run_folder>")
        sys.exit(1)
    sys.exit(0 if run_mapper(sys.argv[1]) else 1)
