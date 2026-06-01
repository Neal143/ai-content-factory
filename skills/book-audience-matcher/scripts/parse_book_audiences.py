"""
parse_book_audiences.py
=======================
Mục đích:
    Parse file sách thô (tuân thủ schema raw-book-structure.md) để bóc tách
    toàn bộ câu JTBD thô của Book Audience và Chunk Audiences.
    Được gọi bởi skill `book-audience-matcher` trong Giai đoạn 1 (Parse & JTBD Calibration).

    Lý do dùng script thay vì để LLM tự parse:
    - Chống ảo giác: regex không bịa dữ liệu
    - Đảm bảo không bỏ sót chunk khi sách có N lớn (50+ chunks)

Input:
    File sách thô tại vault/02-sources/books/[Tên Sách].md
    (Phải tuân thủ schema: .agent/skills/book-extractor/references/raw-book-structure.md)

Output JSON:
    {
        "book": "<câu JTBD thô cấp sách>" | null,
        "chunks": [
            { "chunk_index": N, "chunk_name": "...", "jtbd_raw": "..." },
            ...
        ]
    }
    Các chunk có [NO_JTBD_FOUND] bị bỏ qua tự động.

Cách chạy:
    # Chỉ in kết quả ra terminal:
    python parse_book_audiences.py vault/02-sources/books/ten-sach.md

    # Xuất kết quả ra file JSON:
    python parse_book_audiences.py vault/02-sources/books/ten-sach.md --output_json temp_audiences.json
"""

import sys
import re
import json
import argparse


def parse_book_audiences(filepath):
    """
    Parse file sách thô (tuân thủ raw-book-structure.md) để lấy:
    - Book-level JTBD từ META_BOOK_AUDIENCE trong header
    - Chunk-level JTBD từ META_CHUNK_AUDIENCE trong mỗi <data_chunk>

    Trả về dict:
    {
        "book": "<câu JTBD thô cấp sách>" | None,
        "chunks": [
            { "chunk_index": N, "chunk_name": "...", "jtbd_raw": "..." },
            ...
        ]
    }
    Các chunk có [NO_JTBD_FOUND] bị bỏ qua.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {"book": None, "chunks": []}

    # 1. Extract META_BOOK_AUDIENCE từ header (trước <data_chunk> đầu tiên)
    header = content.split('<data_chunk>')[0]
    m = re.search(r'META_BOOK_AUDIENCE:\s*book_audience=(.+)', header)
    if m:
        result["book"] = m.group(1).strip()

    # 2. Extract từng data_chunk
    chunks = re.findall(r'<data_chunk>(.*?)</data_chunk>', content, re.DOTALL)
    for chunk in chunks:
        # Quét và Cách ly Rác (Warning Isolation)
        if '> [!warning]' in chunk:
            chunk_match = re.search(r'CHUNK_index=(\d+)', chunk)
            b_idx = chunk_match.group(1) if chunk_match else "?"
            print(f"⚠️ System: Cách ly (Skip) thành công Chunk {b_idx} do phát hiện cờ > [!warning].")
            continue

        # Bỏ qua chunk không có JTBD
        if '[NO_JTBD_FOUND]' in chunk:
            continue

        chunk_idx = re.search(r'CHUNK_index=(\d+)', chunk)
        chunk_name = re.search(r'CHUNK=([^|`\n]+)', chunk)
        audience = re.search(r'META_CHUNK_AUDIENCE[*\s:`]*chunk_audience=([^`\n]+)', chunk)

        if not audience:
            continue

        result["chunks"].append({
            "chunk_index": int(chunk_idx.group(1)) if chunk_idx else None,
            "chunk_name": chunk_name.group(1).strip() if chunk_name else None,
            "jtbd_raw": audience.group(1).strip()
        })

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse multi-chunk JTBD audiences từ file sách thô (raw-book-structure.md schema)"
    )
    parser.add_argument('input_file', help='Đường dẫn đến file sách thô (vault/02-sources/books/...md)')
    parser.add_argument('--output_json', help='Đường dẫn xuất file JSON kết quả')
    args = parser.parse_args()

    if not __import__('os').path.exists(args.input_file):
        print(f"❌ Lỗi: File không tồn tại: {args.input_file}")
        sys.exit(1)

    data = parse_book_audiences(args.input_file)

    if args.output_json:
        out_dir = __import__('os').path.dirname(__import__('os').path.abspath(args.output_json))
        if out_dir:
            __import__('os').makedirs(out_dir, exist_ok=True)
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã xuất JSON ra: {args.output_json}")

    print(f"✅ Book audience : {'found → ' + data['book'][:60] + '...' if data['book'] else 'NOT FOUND'}")
    print(f"✅ Chunk audiences: {len(data['chunks'])} chunk hợp lệ (bỏ qua [NO_JTBD_FOUND])")
    if data['chunks']:
        for b in data['chunks']:
            print(f"   Chunk {b['chunk_index']:>2}: {b['jtbd_raw'][:70]}...")
