"""
inject_jtbd.py
==============
Ten file: inject_jtbd.py
Last update: 09/08/2026 22:45 (GMT+7)
Vai tro: Inject confirmed JTBD audience + evidence vao raw content file tu Phase 2.
Duoc su dung khi: Phase 2 content extraction hoan tat, can merge voi JTBD tu Phase 1.
Output: Raw file da merge (ghi de), san sang cho gate_checker.py.
Logic (3 strategies uu tien):
  1. Neu raw_file DA CO dong chunk_audience= (NLM Phase 2 tu xuat) → REPLACE truc tiep.
  2. Neu KHONG CO chunk_audience= nhung CO dong vivid_circumstance → chen TRUOC no.
  3. Fallback: chen sau META_CHUNK:
  Ket qua: chunk_audience= luon nam ngay TREN dong vivid_circumstance (dung vi tri).

Input:
    python inject_jtbd.py <raw_file> --jtbd-response <jtbd_raw_file>

Output:
    Ghi de raw_file voi JTBD injected.
"""

import sys
import re
import os


def parse_jtbd_response(jtbd_file):
    """Doc JTBD response file, tra ve (audience_str, evidence_str)."""
    with open(jtbd_file, 'r', encoding='utf-8') as f:
        content = f.read()
    audience_match = re.search(r'chunk_audience\s*=\s*(.+)', content)
    evidence_match = re.search(r'_Căn cứ:_\s*(.+)', content)
    audience = audience_match.group(1).strip() if audience_match else '[NO_JTBD_FOUND]'
    evidence = evidence_match.group(1).strip() if evidence_match else ''
    return audience, evidence


def inject_jtbd(raw_file, jtbd_file):
    """Inject confirmed JTBD tu Phase 1 vao raw_file (Phase 2 output).
    Logic:
      1. Neu raw_file da co chunk_audience= → REPLACE truc tiep.
      2. Neu khong co → chen TRUOC dong content_type=vivid_circumstance.
      3. Fallback: chen sau META_CHUNK:."""
    audience, evidence = parse_jtbd_response(jtbd_file)

    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Xay dung 2 dong confirmed JTBD
    jtbd_line = f'META_CHUNK_AUDIENCE: chunk_audience={audience}'
    evidence_line = f'_Căn cứ:_ {evidence}' if evidence else ''

    # --- Strategy 1: REPLACE dong chunk_audience= cu (neu co) ---
    existing_audience = re.search(r'^(META_CHUNK_AUDIENCE:[^\n]*chunk_audience=[^\n]*)', content, re.MULTILINE)
    if existing_audience:
        content = content.replace(existing_audience.group(0), jtbd_line)
        # Replace hoac chen dong _Can cu:_
        existing_evidence = re.search(r'^[\*_]*Căn cứ:[\*_]*[^\n]*', content, re.MULTILINE)
        if existing_evidence and evidence_line:
            content = content.replace(existing_evidence.group(0), evidence_line)
        elif evidence_line:
            # Chen _Can cu:_ ngay sau dong chunk_audience= vua replace
            content = content.replace(jtbd_line, jtbd_line + '\n' + evidence_line)
    else:
        # --- Strategy 2: Chen TRUOC dong vivid_circumstance ---
        vivid_match = re.search(r'^(META_CHUNK_AUDIENCE:\s*content_type=vivid_circumstance)', content, re.MULTILINE)
        if vivid_match:
            insert_block = jtbd_line
            if evidence_line:
                insert_block += '\n' + evidence_line
            content = content[:vivid_match.start()] + insert_block + '\n' + content[vivid_match.start():]
        else:
            # --- Strategy 3 (fallback): Chen sau META_CHUNK: ---
            meta_match = re.search(r'(META_CHUNK:\s*CHUNK=[^\n]+)', content)
            if meta_match:
                insert_block = jtbd_line
                if evidence_line:
                    insert_block += '\n' + evidence_line
                end_pos = meta_match.end()
                content = content[:end_pos] + '\n' + insert_block + content[end_pos:]

    # Xoa dong _Can cu:_ thua (neu co nhieu hon 1)
    evidence_matches = list(re.finditer(r'^[\*_]*Căn cứ:[\*_]*[^\n]*', content, re.MULTILINE))
    if len(evidence_matches) > 1:
        # Giu dong dau tien, xoa cac dong sau
        for m in reversed(evidence_matches[1:]):
            content = content[:m.start()] + content[m.end():]
            # Xoa newline thua
            if content[m.start():m.start()+1] == '\n':
                content = content[:m.start()] + content[m.start()+1:]

    with open(raw_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Injected JTBD into {os.path.basename(raw_file)} successfully.')
    return audience, evidence


if __name__ == '__main__':
    if len(sys.argv) < 2 or '--jtbd-response' not in sys.argv:
        print('Usage: python inject_jtbd.py <raw_file> --jtbd-response <jtbd_raw_file>')
        sys.exit(1)
    raw_f = sys.argv[1]
    jr_idx = sys.argv.index('--jtbd-response')
    jtbd_f = sys.argv[jr_idx + 1]
    inject_jtbd(raw_f, jtbd_f)
