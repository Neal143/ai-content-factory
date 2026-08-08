"""
nlm_query.py
============
Ten file: nlm_query.py
Last update: 08/08/2026 (GMT+7)
Vai tro: Wrapper goi NLM query an toan cho Windows PowerShell.
         Doc query tu file text (tranh truyen tieng Viet qua CLI args).
Duoc su dung khi: Agent can goi NLM voi query chua tieng Viet.
Output: Ghi NLM answer vao output_file. Exit code 0 = OK, 1 = error.
Logic:
  1. Doc query tu query_file (UTF-8)
  2. Goi subprocess: nlm notebook query <notebook_id> <query> --json
  3. Parse JSON output -> extract truong 'answer'
  4. Ghi answer vao output_file (UTF-8)
"""

import sys
import json
import subprocess
import os

# Fix Windows console encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def run_nlm_query(notebook_id, query_file, output_file):
    """Doc query tu file, goi NLM, ghi answer ra output_file."""
    # Doc query
    with open(query_file, 'r', encoding='utf-8') as f:
        query_text = f.read().strip()

    if not query_text:
        print('ERROR: query_file is empty', file=sys.stderr)
        return False

    # Goi NLM subprocess
    cmd = ['nlm', 'notebook', 'query', notebook_id, query_text, '--json']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    if result.returncode != 0:
        print(f'NLM ERROR (exit {result.returncode}): {result.stderr}', file=sys.stderr)
        return False

    # Parse JSON -> extract answer
    try:
        data = json.loads(result.stdout)
        answer = data.get('answer', '')
    except json.JSONDecodeError:
        # Fallback: stdout la plain text
        answer = result.stdout

    if not answer:
        print('ERROR: NLM returned empty answer', file=sys.stderr)
        return False

    # Ghi answer ra output file
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(answer)

    print(f'OK: Wrote {len(answer)} chars to {os.path.basename(output_file)}')
    return True


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: python nlm_query.py <notebook_id> <query_file> <output_file>')
        sys.exit(1)
    nb_id = sys.argv[1]
    qf = sys.argv[2]
    of = sys.argv[3]
    ok = run_nlm_query(nb_id, qf, of)
    sys.exit(0 if ok else 1)
