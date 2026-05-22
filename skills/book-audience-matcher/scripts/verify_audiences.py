"""
TÊN SCRIPT: verify_audiences.py
VAI TRÒ: Cập nhật status audience rows trong extraction_baseline.csv.
          So khớp Audience Decision Map với file vật lý trên disk.
          (Optional) Enrich Audience Decision Map với jtbd_raw từ audiences_parsed.json.
KHI NÀO SỬ DỤNG: Sau khi book-audience-matcher hoàn tất Giai đoạn 3.
INPUT:  --baseline, --decision-map, --vault-root, --audiences-parsed (optional), --report (optional)
OUTPUT: Ghi đè baseline.csv, ghi đè decision_map.json (nếu enrich), append vào report.

TÓM TẮT LOGIC:
  1. Đọc baseline CSV, Audience Decision Map, và audiences_parsed.json (nếu có)
  2. Build normalized lookup từ Audience Decision Map (array format, dùng scope/chunk_index)
  3. (Optional) Enrichment: ghép jtbd_raw vào Audience Decision Map bằng scope/chunk_index
  4. Verification: đối chiếu audience rows với file vật lý → DONE/MISSING
  5. Ghi đè baseline CSV và (nếu enrich) Audience Decision Map
  6. Append tóm tắt vào pipeline_report.md
"""

import sys
import os
import csv
import json
import re
import argparse

# Fieldnames cố định — phải khớp với generate_baseline.py và verify_baseline() trong atomizer.py
FIELDNAMES = ['section', 'chunk', 'category', 'id', 'status']



def main():
    parser = argparse.ArgumentParser(
        description="Verify audience rows trong baseline CSV + enrich Audience Decision Map"
    )
    parser.add_argument('--baseline',          required=True,
                        help="Path tới extraction_baseline.csv")
    parser.add_argument('--decision-map',      required=True,
                        help="Path tới audience_decision_map.json")
    parser.add_argument('--vault-root',        required=True,
                        help="Path tới vault root (VD: vault/)")
    parser.add_argument('--audiences-parsed',  default=None,
                        help="Path tới audiences_parsed.json (enrich Audience Decision Map với jtbd_raw)")
    parser.add_argument('--report',            default=None,
                        help="Path tới pipeline_report.md")
    args = parser.parse_args()

    # ── Đọc inputs ──
    with open(args.baseline, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    with open(args.decision_map, 'r', encoding='utf-8') as f:
        decision_map = json.load(f)

    # ── Build normalized lookup từ Decision Map (array format) ──
    # scope="book" → "book", scope="chunk" → chunk_index (int)
    norm_map = {}
    for entry in decision_map:
        if entry.get("scope") == "book":
            norm_key = "book"
        else:
            norm_key = entry["chunk_index"]  # KeyError nếu thiếu → fail loud
        norm_map[norm_key] = entry

    # ── Enrichment: ghép jtbd_raw vào Audience Decision Map (nếu có --audiences-parsed) ──
    if args.audiences_parsed and os.path.isfile(args.audiences_parsed):
        with open(args.audiences_parsed, 'r', encoding='utf-8') as f:
            parsed = json.load(f)

        # Book-level: audiences_parsed.json["book"] là string (raw JTBD)
        if 'book' in parsed and 'book' in norm_map:
            entry = norm_map['book']
            if isinstance(parsed['book'], str):
                entry['jtbd_raw'] = parsed['book']
            elif isinstance(parsed['book'], dict):
                entry['jtbd_raw'] = parsed['book'].get('jtbd_raw', '')

        # Chunk-level: audiences_parsed.json["chunks"] là array với chunk_index (int)
        for chunk_entry in parsed.get('chunks', []):
            cidx = chunk_entry.get('chunk_index')
            if cidx is not None and cidx in norm_map:
                dm_entry = norm_map[cidx]
                dm_entry['jtbd_raw'] = chunk_entry.get('jtbd_raw', '')

        # Ghi đè Audience Decision Map đã enriched
        with open(args.decision_map, 'w', encoding='utf-8') as f:
            json.dump(decision_map, f, ensure_ascii=False, indent=2)
        print("✅ Audience Decision Map enriched với jtbd_raw (traceability)")

    # ── Verification: update baseline CSV ──
    missing_ids = []

    for row in rows:
        if row['section'] != 'audience':
            continue

        chunk_val = row['chunk']

        # Normalize CSV chunk value → lookup key (int hoặc 'book')
        if chunk_val == 'book':
            lookup_key = 'book'
        else:
            lookup_key = int(chunk_val)

        # Tìm entry trong normalized Audience Decision Map
        if lookup_key not in norm_map:
            row['status'] = 'MISSING'
            missing_ids.append(row['id'])
            continue

        entry = norm_map[lookup_key]
        audience_filename = entry.get('audience_filename', '')

        if not audience_filename:
            row['status'] = 'MISSING'
            missing_ids.append(row['id'])
            continue

        # Kiểm tra file vật lý trên disk
        aud_path = os.path.join(args.vault_root, '01-Atomic', 'Audiences', f"{audience_filename}.md")
        if os.path.exists(aud_path):
            row['status'] = 'DONE'
        else:
            row['status'] = 'MISSING'
            missing_ids.append(row['id'])

    # ── Ghi đè baseline.csv ──
    with open(args.baseline, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    # ── Báo cáo ──
    done  = sum(1 for r in rows if r['section'] == 'audience' and r['status'] == 'DONE')
    total = sum(1 for r in rows if r['section'] == 'audience')
    print(f"✅ Audiences verified: {done}/{total} DONE")
    if missing_ids:
        print(f"❌ MISSING: {missing_ids}")

    # ── Append vào pipeline_report.md (nếu có) ──
    if args.report:
        with open(args.report, 'a', encoding='utf-8') as f:
            f.write(f"\n## 2. book-audience-matcher\n")
            f.write(f"- DONE: {done} / {total}\n")
            if missing_ids:
                for mid in missing_ids:
                    f.write(f"  ❌ MISSING audience: {mid}\n")


if __name__ == '__main__':
    main()
