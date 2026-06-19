import os
import json
import re
import unicodedata

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)[:40]

run_folder = r"d:\AI\AI content factory - v3.7B\.extraction_runs\good-inside_2026-05-21"
parsed_file = os.path.join(run_folder, "audiences_parsed.json")

with open(parsed_file, 'r', encoding='utf-8') as f:
    parsed = json.load(f)

calibrated = []
decision_map = []

# Process book
book_raw = parsed.get("book", "")
main_job = "nuoi-day-con-kien-cuong"
circumstance = "khi-doi-mat-voi-hanh-vi-kho-khan"
calibrated.append({
    "scope": "book",
    "chunk_index": None,
    "chunk_name": None,
    "audience_Job_performer": "Cha mẹ",
    "audience_main_job": "nuôi dạy con kiên cường",
    "audience_circumstance": "khi đối mặt với hành vi khó khăn",
    "aliases": ["nuôi con", "đối mặt khó khăn"]
})
decision_map.append({
    "scope": "book",
    "chunk_index": None,
    "action": "create",
    "audience_filename": f"cha-me_{main_job}_{circumstance}",
    "audience_level": "big",
    "parent_audience": [],
    "jtbd_raw": book_raw
})

# Process chunks
for chunk in parsed.get("chunks", []):
    idx = chunk["chunk_index"]
    raw = chunk["jtbd_raw"]
    
    parts = raw.split("khi", 1)
    if len(parts) > 1:
        job = parts[0].strip()
        circ = "khi " + parts[1].strip()
    else:
        job = raw
        circ = "khi đối mặt thử thách"
    
    slug_job = slugify(job)
    slug_circ = slugify(circ)
    
    calibrated.append({
        "scope": "chunk",
        "chunk_index": idx,
        "chunk_name": chunk["chunk_name"],
        "audience_Job_performer": "Cha mẹ",
        "audience_main_job": job,
        "audience_circumstance": circ,
        "aliases": [job]
    })
    
    decision_map.append({
        "scope": "chunk",
        "chunk_index": idx,
        "action": "create",
        "audience_filename": f"cha-me_{slug_job}_{slug_circ}",
        "audience_level": "little",
        "parent_audience": [],
        "jtbd_raw": raw
    })

with open(os.path.join(run_folder, 'jtbd_calibrated.json'), 'w', encoding='utf-8') as f:
    json.dump(calibrated, f, indent=4, ensure_ascii=False)

with open(os.path.join(run_folder, 'audience_decision_map.json'), 'w', encoding='utf-8') as f:
    json.dump(decision_map, f, indent=4, ensure_ascii=False)

print("Decision map built.")
