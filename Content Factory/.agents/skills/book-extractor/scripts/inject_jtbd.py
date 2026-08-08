"""
inject_jtbd.py
==============
Ten file: inject_jtbd.py
Last update: 04/08/2026 (GMT+7)
Vai tro: Inject confirmed JTBD audience + evidence vao raw content file tu Phase 2.
Duoc su dung khi: Phase 2 content extraction hoan tat, can merge voi JTBD tu Phase 1.
Output: Raw file da merge (ghi de), san sang cho gate_checker.py.
Logic:
  1. Doc jtbd_raw_file → parse chunk_audience= va _Can cu:_
  2. Doc raw_file (Phase 2 output)
  3. XOA cac dong META_CHUNK_AUDIENCE va _Can cu:_ ma NLM Phase 2 co the da tu xuat (tranh duplicate)
  4. Chen 2 dong confirmed (META_CHUNK_AUDIENCE + Can cu) ngay sau META_CHUNK:
  5. Ghi de raw_file

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
    Buoc 1: Xoa cac dong JTBD sai lech ma NLM Phase 2 co the da tu xuat.
    Buoc 2: Chen confirmed JTBD ngay sau META_CHUNK:."""
    audience, evidence = parse_jtbd_response(jtbd_file)

    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buoc 1: Xoa cac dong JTBD cu (NLM Phase 2 co the da xuat sai)
    # CHI xoa dong chua chunk_audience=, KHONG xoa dong content_type=vivid_circumstance
    content = re.sub(r'\nMETA_CHUNK_AUDIENCE:[^\n]*chunk_audience=[^\n]*', '', content)
    content = re.sub(r'\n_Căn cứ:_[^\n]*', '', content)

    # Buoc 2: Chen confirmed JTBD ngay sau META_CHUNK:
    pattern = r'(META_CHUNK:\s*CHUNK=[^\n]+)'
    jtbd_lines = f'META_CHUNK_AUDIENCE: chunk_audience={audience}'
    if evidence:
        jtbd_lines += f'\n_Căn cứ:_ {evidence}'
    replacement = r'\1' + '\n' + jtbd_lines
    new_content = re.sub(pattern, replacement, content, count=1)

    with open(raw_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

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
