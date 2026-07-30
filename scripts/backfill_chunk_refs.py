import os, re, json

BOOKS = [
    {
        "name": "Good Inside",
        "wikilink_match": "[[Good Inside",
        "decision_map": "vault/.extraction_runs/books/good-inside_2026-05-21/audience_decision_map.json"
    },
    {
        "name": "Beyond the rainbow bridge",
        "wikilink_match": "[[Beyond the rainbow bridge",
        "decision_map": "vault/.extraction_runs/books/beyond-the-rainbow-bridge_2026-05-27/audience_decision_map.json"
    },
    {
        "name": "The Whole-Brain Child",
        "wikilink_match": "[[The Whole-Brain Child",
        "decision_map": "vault/.extraction_runs/books/the-whole-brain-child_2026-04-17/session_3/audience_decision_map.json"
    }
]
VAULT_ATOMIC = "vault/01-Atomic"

def read_file(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return f.read()

def extract_wikilink_name(text, field):
    """Extract filename từ wikilink, xử lý [[path|alias]] và [[simple]]."""
    m = re.search(rf'{field}:.*?\[\[(.+?)\]\]', text, re.DOTALL)
    if not m:
        return None
    raw = m.group(1)
    if '|' in raw:
        raw = raw.split('|')[-1]
    if '/' in raw:
        raw = raw.rsplit('/', 1)[-1]
    return raw.strip()

def update_source_fields(content, book_name, fragment):
    """Regex replace source_link và source_path trong frontmatter."""
    new_link = f'[[{book_name}#^{fragment}]]'
    new_path = f'02-sources/books/{book_name}.md#^{fragment}'
    content = re.sub(
        r'(source_link:\s*)"?\[\[' + re.escape(book_name) + r'(?:#\^[a-z0-9-]+)?\]\]"?',
        rf'\1"{new_link}"',
        content
    )
    content = re.sub(
        r'(source_path:\s*)"?' + re.escape(f'02-sources/books/{book_name}.md') + r'(?:#\^[a-z0-9-]+)?"?',
        rf'\1"{new_path}"',
        content
    )
    return content

def atomic_write(path, content):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp, path)

for book in BOOKS:
    name = book["name"]
    match = book["wikilink_match"]
    
    # Build audience map
    with open(book["decision_map"], 'r', encoding='utf-8') as f:
        aud_map = {d["audience_filename"]: d for d in json.load(f)}
    
    # BƯỚC A: Audiences (0-hop)
    aud_dir = os.path.join(VAULT_ATOMIC, "Audiences")
    for fname in os.listdir(aud_dir):
        if not fname.endswith('.md'): continue
        fpath = os.path.join(aud_dir, fname)
        content = read_file(fpath)
        if match not in content or '#^' in content: continue  # skip nếu không phải book này hoặc đã có fragment
        
        stem = fname[:-3]  # bỏ .md
        entry = aud_map.get(stem)
        if not entry:
            print(f"WARNING: audience {stem} not in decision_map, skip")
            continue
        
        scope = entry.get("scope", "book")
        ci = entry.get("chunk_index")
        fragment = "book-overview" if scope == "book" else f"chunk-{int(ci):02d}"
        
        new_content = update_source_fields(content, name, fragment)
        if new_content != content:
            atomic_write(fpath, new_content)
            print(f"  Updated audience: {fname} → ^{fragment}")
    
    # BƯỚC B: Insights (1-hop)
    ins_dir = os.path.join(VAULT_ATOMIC, "Insights")
    for fname in os.listdir(ins_dir):
        if not fname.endswith('.md'): continue
        fpath = os.path.join(ins_dir, fname)
        content = read_file(fpath)
        if match not in content or '#^' in content: continue
        
        aud_name = extract_wikilink_name(content, "belongs_to_audience")
        if not aud_name or aud_name not in aud_map:
            print(f"WARNING: insight {fname} → audience '{aud_name}' not in map, skip")
            continue
        
        ci = aud_map[aud_name].get("chunk_index")
        scope = aud_map[aud_name].get("scope", "book")
        fragment = "book-overview" if scope == "book" else f"chunk-{int(ci):02d}"
        
        new_content = update_source_fields(content, name, fragment)
        if new_content != content:
            atomic_write(fpath, new_content)
            print(f"  Updated insight: {fname} → ^{fragment}")
    
    # BƯỚC C: Solutions/Concepts (2-hop)
    for folder in ["Solutions", "Concepts"]:
        sc_dir = os.path.join(VAULT_ATOMIC, folder)
        if not os.path.exists(sc_dir): continue
        for fname in os.listdir(sc_dir):
            if not fname.endswith('.md'): continue
            fpath = os.path.join(sc_dir, fname)
            content = read_file(fpath)
            if match not in content or '#^' in content: continue
            
            # 2-hop: supports_insight → insight → belongs_to_audience
            insight_name = extract_wikilink_name(content, "supports_insight")
            if not insight_name:
                print(f"WARNING: {folder}/{fname} has no supports_insight, skip")
                continue
            
            insight_path = os.path.join(ins_dir, f"{insight_name}.md")
            if not os.path.exists(insight_path):
                print(f"WARNING: {folder}/{fname} → insight '{insight_name}' not found, skip")
                continue
            
            ins_content = read_file(insight_path)
            aud_name = extract_wikilink_name(ins_content, "belongs_to_audience")
            if not aud_name or aud_name not in aud_map:
                print(f"WARNING: {folder}/{fname} → insight → audience '{aud_name}' not in map, skip")
                continue
            
            ci = aud_map[aud_name].get("chunk_index")
            scope = aud_map[aud_name].get("scope", "book")
            fragment = "book-overview" if scope == "book" else f"chunk-{int(ci):02d}"
            
            new_content = update_source_fields(content, name, fragment)
            if new_content != content:
                atomic_write(fpath, new_content)
                print(f"  Updated {folder}: {fname} → ^{fragment}")
    
    # BƯỚC D: Quotes/Stories/Data-Points (3-hop primary, filename fallback)
    for folder in ["Quotes", "Stories", "Data-Points"]:
        qsd_dir = os.path.join(VAULT_ATOMIC, folder)
        if not os.path.exists(qsd_dir): continue
        for fname in os.listdir(qsd_dir):
            if not fname.endswith('.md'): continue
            fpath = os.path.join(qsd_dir, fname)
            content = read_file(fpath)
            if match not in content or '#^' in content: continue
            
            fragment = None
            
            # PRIMARY: 3-hop chain
            kn_name = extract_wikilink_name(content, "supports_knowledge")
            if kn_name:
                kn_path = None
                for sf in ["Solutions", "Concepts"]:
                    candidate = os.path.join(VAULT_ATOMIC, sf, f"{kn_name}.md")
                    if os.path.exists(candidate):
                        kn_path = candidate
                        break
                
                if kn_path:
                    kn_content = read_file(kn_path)
                    si_name = extract_wikilink_name(kn_content, "supports_insight")
                    if si_name:
                        si_path = os.path.join(ins_dir, f"{si_name}.md")
                        if os.path.exists(si_path):
                            si_content = read_file(si_path)
                            aud_name = extract_wikilink_name(si_content, "belongs_to_audience")
                            if aud_name and aud_name in aud_map:
                                ci = aud_map[aud_name].get("chunk_index")
                                scope = aud_map[aud_name].get("scope", "book")
                                fragment = "book-overview" if scope == "book" else f"chunk-{int(ci):02d}"
            
            # FALLBACK: parse filename suffix
            if not fragment:
                m = re.search(r'-(\d+)\.md$', fname)
                if m:
                    ci = int(m.group(1))
                    fragment = f"chunk-{ci:02d}"
                    print(f"  FALLBACK: {fname} → ^{fragment}")
            
            if not fragment:
                print(f"WARNING: {folder}/{fname} → both chain and fallback failed, skip")
                continue
            
            new_content = update_source_fields(content, name, fragment)
            if new_content != content:
                atomic_write(fpath, new_content)
                print(f"  Updated {folder}: {fname} → ^{fragment}")

print("\nDone.")
