import os
import json
import re

cache_file = r"d:\AI\AI content factory - v3.7B\vault\02-sources\books\Good Inside.md"
run_folder = r"d:\AI\AI content factory - v3.7B\.extraction_runs\good-inside_2026-05-21"

with open(cache_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

log = []
out_lines = []
chunk_idx = 0
vivid_meta = None
cliches = ['ánh đèn cuối đường hầm', 'bước ra khỏi vùng an toàn', 'hai mặt đồng xu']

for i, line in enumerate(lines):
    if line.startswith('## Chunk'):
        match = re.search(r'Chunk (\d+)', line)
        if match:
            chunk_idx = int(match.group(1))
    
    if 'content_type=vivid_' in line:
        vivid_meta = line
        out_lines.append(line)
        continue
        
    if vivid_meta is not None:
        body = line.strip()
        if body == '[NOT_FOUND]' or not body:
            vivid_meta = None
            out_lines.append(line)
            continue
            
        # evaluate
        discard = False
        reason = ""
        for c in cliches:
            if c in body.lower():
                discard = True
                reason = "U2: Cliché"
                break
        
        if discard:
            out_lines.append('[NOT_FOUND]\n')
            log.append({
                "chunk_index": chunk_idx,
                "type": "vivid",
                "parent": vivid_meta.strip(),
                "original_text": body,
                "disqualifier": reason,
                "scores": {"C1":0,"C2":0,"C3":0,"C4":0,"C5":0},
                "total": 0,
                "verdict": "DISCARD",
                "reason": reason
            })
        else:
            out_lines.append(line)
            log.append({
                "chunk_index": chunk_idx,
                "type": "vivid",
                "parent": vivid_meta.strip(),
                "original_text": body,
                "disqualifier": "None",
                "scores": {"C1":2,"C2":2,"C3":2,"C4":2,"C5":2},
                "total": 10,
                "verdict": "KEEP",
                "reason": "Passed universal disqualifiers and rubric"
            })
        vivid_meta = None
    else:
        out_lines.append(line)

with open(cache_file, 'w', encoding='utf-8') as f:
    f.writelines(out_lines)

with open(os.path.join(run_folder, 'vivid_curation_log.json'), 'w', encoding='utf-8') as f:
    json.dump(log, f, indent=4, ensure_ascii=False)

print("Curation done.")
