"""
TÊN SCRIPT: generate_baseline.py
VAI TRÒ: Sinh file extraction_baseline.csv từ parsed_metadata.json.
          Đây là "Manifest" gốc — ghi lại TOÀN BỘ dữ liệu kỳ vọng với status=PENDING.
          Các skill hạ nguồn update status về DONE/MISSING/DLQ.
KHI NÀO SỬ DỤNG: Chạy ngay sau extract_metadata.py, trước book-audience-matcher.
INPUT:  parsed_metadata.json, [book].md (để đọc book-level audience)
OUTPUT: extraction_baseline.csv

TÓM TẮT LOGIC:
  1. Đọc parsed_metadata.json để lấy danh sách items theo chunk
  2. Đọc cache file để lấy book-level audience từ header
  3. Phân loại từng item theo DIKW (khớp với classify_dikw() trong atomizer.py)
  4. Ghi mỗi item thành 1 row CSV với status=PENDING
  5. Append tóm tắt vào pipeline_report.md (nếu có --report)
"""

import sys
import os
import csv
import re
import json

# Fieldnames cố định — tất cả script trong pipeline phải dùng đúng bộ này
FIELDNAMES = ['section', 'chunk', 'category', 'id', 'status']


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_baseline.py <parsed_metadata.json> <cache_book.md> [--report <report.md>]")
        sys.exit(1)

    metadata_path = sys.argv[1]
    cache_path    = sys.argv[2]

    # Parse --report arg (optional)
    report_path = None
    if '--report' in sys.argv:
        report_path = sys.argv[sys.argv.index('--report') + 1]

    # Đường dẫn output: cùng thư mục với metadata_json
    out_dir  = os.path.dirname(os.path.abspath(metadata_path))
    out_path = os.path.join(out_dir, 'extraction_baseline.csv')

    # ── Đọc inputs ──
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache_content = f.read()

    rows = []

    # ── Book-level audience ──
    # Đọc từ header (phần trước <data_chunk> đầu tiên)
    header = cache_content.split('<data_chunk>')[0]
    m = re.search(r'META_BOOK_AUDIENCE:\s*book_audience=(.+)', header)
    if m:
        book_aud = m.group(1).strip()
        rows.append({'section': 'audience', 'chunk': 'book',
                     'category': 'audience', 'id': book_aud, 'status': 'PENDING'})

    # ── Per-chunk data ──
    counts = {'audience': 0, 'atom': 0, 'vivid': 0}

    for chunk_data in data.get('chunks', []):
        chunk_meta = chunk_data.get('chunk', {})
        chunk_idx  = str(chunk_meta.get('CHUNK_index', '0'))
        aud_info   = chunk_data.get('audience', {})
        chunk_aud  = aud_info.get('chunk_audience', '').strip()

        # Chunk-level audience
        if chunk_aud and chunk_aud != '[NO_JTBD_FOUND]':
            rows.append({'section': 'audience', 'chunk': chunk_idx,
                         'category': 'audience', 'id': chunk_aud, 'status': 'PENDING'})
            counts['audience'] += 1

        for item in chunk_data.get('items', []):
            meta = item.get('meta', {})
            if not meta:
                continue
            ct = meta.get('content_type', '')
            kt = meta.get('knowledge_type', '')
            it = meta.get('insight_type', '')

            # ── Phân loại — PHẢI khớp với classify_dikw() trong atomizer.py ──

            # Vivid types
            if ct in ('vivid_circumstance', 'vivid_insight', 'vivid_knowledge'):
                if ct == 'vivid_insight':
                    vid = meta.get('supports_insight', '').strip()
                elif ct == 'vivid_knowledge':
                    vid = meta.get('supports_knowledge', '').strip()
                else:  # vivid_circumstance — ID = audience JTBD của chunk đó
                    vid = chunk_aud if chunk_aud != '[NO_JTBD_FOUND]' else ''
                if vid:
                    rows.append({'section': 'vivid', 'chunk': chunk_idx,
                                 'category': ct, 'id': vid, 'status': 'PENDING'})
                    counts['vivid'] += 1

            # Tầng 2: Insight
            elif it:
                vid = meta.get('insight_name', '').strip()
                if vid:
                    rows.append({'section': 'atom', 'chunk': chunk_idx,
                                 'category': 'insight', 'id': vid, 'status': 'PENDING'})
                    counts['atom'] += 1

            # Tầng 3: Knowledge (Solution + Concept gộp thành "knowledge" trong baseline)
            elif kt in ('principle', 'framework', 'mental_model', 'actionable_rule',
                        'typology', 'trend', 'concept', 'philosophy'):
                vid = meta.get('knowledge_name', '').strip()
                if vid:
                    rows.append({'section': 'atom', 'chunk': chunk_idx,
                                 'category': 'knowledge', 'id': vid, 'status': 'PENDING'})
                    counts['atom'] += 1

            # Tầng 4: Quote
            elif ct == 'quote':
                vid = meta.get('quote_keyword', '').strip()
                if vid:
                    rows.append({'section': 'atom', 'chunk': chunk_idx,
                                 'category': 'quote', 'id': vid, 'status': 'PENDING'})
                    counts['atom'] += 1

            # Tầng 4: Evidence (shocking_fact + evidence)
            elif ct in ('shocking_fact', 'evidence'):
                vid = meta.get('evidence_keyword', '').strip()
                if vid:
                    rows.append({'section': 'atom', 'chunk': chunk_idx,
                                 'category': 'evidence', 'id': vid, 'status': 'PENDING'})
                    counts['atom'] += 1

            # Tầng 4: Story (story + case_study)
            elif ct in ('story', 'case_study'):
                protagonist = meta.get('protagonist', '').strip()
                core_event  = meta.get('core_event', '').strip()
                # Dùng cùng logic với generate_filename() trong atomizer.py
                vid = f"{protagonist}-{core_event}" if core_event else protagonist
                if vid:
                    rows.append({'section': 'atom', 'chunk': chunk_idx,
                                 'category': 'story', 'id': vid, 'status': 'PENDING'})
                    counts['atom'] += 1

    # Sắp xếp: audience trước, atom giữa, vivid sau
    rows.sort(key=lambda r: (0 if r['section'] == 'audience' else 1))

    # ── Ghi CSV ──
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Baseline sinh xong: {out_path}")
    print(f"   Audiences: {1 + counts['audience']} | Atoms: {counts['atom']} | Vivids: {counts['vivid']}")

    # ── Append vào pipeline_report.md (nếu có) ──
    if report_path:
        with open(report_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## 1b. generate_baseline\n")
            f.write(f"- Audiences: {1 + counts['audience']} | Atoms: {counts['atom']} | Vivids: {counts['vivid']}\n")


if __name__ == '__main__':
    main()
