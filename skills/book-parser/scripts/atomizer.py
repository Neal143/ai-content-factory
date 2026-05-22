"""
TÊN SCRIPT: atomizer.py
VAI TRÒ: Script deterministic thay thế Agent tạo file Atom thủ công.
         Parse JSON metadata → Phân loại DIKW → Sinh Atom in-memory →
         Vivid-Append → Gate Validation POKA-YOKE → Commit Write.
KHI NÀO SỬ DỤNG: Được gọi bởi Agent trong book-parser Phase 2, Bước 2.3.
OUTPUT: Atom files vật lý trong vault + stdout báo cáo + DLQ files nếu lỗi.

TÓM TẮT LOGIC:
  1. Đọc parsed_metadata.json và atomizer_context.json (Agent tạo)
  2. Duyệt TOÀN BỘ items[] trong mỗi chunk — KHÔNG bỏ sót
  3. Phân loại DIKW theo bảng ánh xạ (dikw-mapping.md)
  4. Vivid items → buffer, Core items → atom in-memory
  5. Vivid-Append: nhét vivid vào Host Mẹ (Hard Cap 3, Orphan Drop)
  6. Gate Validation: kiểm tra graph links trước khi ghi
  7. Commit Write: ghi file hoặc dry-run
"""

import sys
import os
import re
import json
import unicodedata
import argparse

# ── Hằng số phân loại DIKW ──

# Vivid types: CẤM tạo file vật lý
VIVID_TYPES = {"vivid_circumstance", "vivid_insight", "vivid_knowledge"}

# Knowledge types → Solution (Tầng 3, nhóm Thực thi Động)
SOLUTION_KNOWLEDGE_TYPES = {"principle", "framework", "mental_model", "actionable_rule", "typology", "trend"}

# Knowledge types → Concept (Tầng 3, nhóm Lý thuyết tĩnh)
CONCEPT_KNOWLEDGE_TYPES = {"concept", "philosophy"}

# Atom type → thư mục lưu trữ (tương đối so với vault_root)
ATOM_FOLDERS = {
    "insight":    "01-Atomic/Insights",
    "solution":   "01-Atomic/Solutions",
    "concept":    "01-Atomic/Concepts",
    "story":      "01-Atomic/Stories",
    "data-point": "01-Atomic/Data-Points",
    "quote":      "01-Atomic/Quotes",
}


# ══════════════════════════════════════════════════════════════
# HÀM SLUGIFY TIẾNG VIỆT
# ══════════════════════════════════════════════════════════════

def slugify_vi(text):
    """Chuyển text tiếng Việt thành slug ASCII-hyphenated.

    Thứ tự xử lý:
    1. Lowercase toàn bộ
    2. Thay đ→d, Đ→D (ký tự stroke KHÔNG decompose bằng NFD)
    3. NFD decomposition → strip dấu (Mn category)
    4. Xóa ký tự đặc biệt, giữ a-z 0-9 space hyphen
    5. Space → hyphen, gộp hyphen liên tiếp
    """
    text = text.lower()
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    text = text.replace('_', ' ')  # Underscore → space để giữ ranh giới từ
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    slug = text.strip('-')
    return slug if slug else "untitled"


# ══════════════════════════════════════════════════════════════
# KIỂM TRA ĐIỀU KIỆN SKIP
# ══════════════════════════════════════════════════════════════

def should_skip_item(item):
    """Kiểm tra 3 điều kiện skip.

    Returns: (bool, str) — (True nếu cần skip, lý do skip)
    Điều kiện:
    1. meta dict rỗng (intro text)
    2. body_text chứa [NOT_FOUND] hoặc rỗng/whitespace
    3. Bất kỳ value trong meta chứa [NOT_FOUND]
    """
    meta = item.get("meta", {})
    body = item.get("body_text", "").strip()

    # Điều kiện 1: meta rỗng
    if not meta:
        return True, "meta rỗng (intro text)"

    # Điều kiện 2: body chứa [NOT_FOUND] hoặc rỗng
    if not body or "[NOT_FOUND]" in body:
        return True, f"body rỗng hoặc [NOT_FOUND]"

    # Điều kiện 3: giá trị meta chứa [NOT_FOUND]
    for key, val in meta.items():
        if "[NOT_FOUND]" in str(val):
            return True, f"meta[{key}] chứa [NOT_FOUND]"

    return False, ""


# ══════════════════════════════════════════════════════════════
# PHÂN LOẠI DIKW
# ══════════════════════════════════════════════════════════════

def classify_dikw(meta):
    """Phân loại item theo bảng ánh xạ DIKW.

    Returns: dict với keys: atom_type, sub_field_name, sub_field_value, folder
             hoặc None nếu không phân loại được.
    """
    ct = meta.get("content_type", "")
    kt = meta.get("knowledge_type", "")
    it = meta.get("insight_type", "")

    # Vivid → buffer
    if ct in VIVID_TYPES:
        return {"atom_type": "vivid", "vivid_type": ct}

    # Tầng 2: Insight
    if it:
        return {
            "atom_type": "insight",
            "sub_field_name": "insight_type",
            "sub_field_value": it,
            "folder": ATOM_FOLDERS["insight"],
        }

    # Tầng 3: Solution
    if kt in SOLUTION_KNOWLEDGE_TYPES:
        return {
            "atom_type": "solution",
            "sub_field_name": "knowledge_type",
            "sub_field_value": kt,
            "folder": ATOM_FOLDERS["solution"],
        }

    # Tầng 3: Concept
    if kt in CONCEPT_KNOWLEDGE_TYPES:
        return {
            "atom_type": "concept",
            "sub_field_name": "knowledge_type",
            "sub_field_value": kt,
            "folder": ATOM_FOLDERS["concept"],
        }

    # Tầng 4: Quote
    if ct == "quote":
        return {
            "atom_type": "quote",
            "sub_field_name": None,
            "sub_field_value": None,
            "folder": ATOM_FOLDERS["quote"],
        }

    # Tầng 4: Data-Point
    if ct in ("shocking_fact", "evidence"):
        return {
            "atom_type": "data-point",
            "sub_field_name": "data_type",
            "sub_field_value": ct,
            "folder": ATOM_FOLDERS["data-point"],
        }

    # Tầng 4: Story
    if ct in ("story", "case_study"):
        return {
            "atom_type": "story",
            "sub_field_name": "subtype",
            "sub_field_value": ct,
            "folder": ATOM_FOLDERS["story"],
        }

    return None


# ══════════════════════════════════════════════════════════════
# SINH FILENAME
# ══════════════════════════════════════════════════════════════

def generate_filename(atom_type, meta, acr, chunk_idx):
    """Sinh filename theo quy tắc: {SOURCE_ACRONYM}_{KEYWORD_SLUG}.md

    Insight/Solution/Concept: slug từ insight_name/knowledge_name (unique trong sách)
    Quote/Data-Point/Story: slug + chunk_index (vì slug ngắn, dễ trùng)
    """
    if atom_type == "insight":
        name = meta.get("insight_name", "unknown")
        slug = slugify_vi(name)
        return f"{acr}_{slug}.md"

    elif atom_type in ("solution", "concept"):
        name = meta.get("knowledge_name", "")
        if not name:
            # Fallback: dùng supports_insight nếu knowledge_name thiếu
            name = meta.get("supports_insight", "unknown")
        slug = slugify_vi(name)
        return f"{acr}_{slug}.md"

    elif atom_type == "quote":
        speaker = meta.get("speaker", "unknown")
        keyword = meta.get("quote_keyword", "")
        if keyword:
            slug = slugify_vi(f"{speaker}-{keyword}")
        else:
            slug = slugify_vi(speaker)
        return f"{acr}_quote-{slug}-{chunk_idx}.md"

    elif atom_type == "data-point":
        keyword = meta.get("evidence_keyword", "")
        if keyword:
            slug = slugify_vi(keyword)
        else:
            slug = meta.get("content_type", "data")
        return f"{acr}_data-{slug}-{chunk_idx}.md"

    elif atom_type == "story":
        protagonist = meta.get("protagonist", "unknown")
        core_event = meta.get("core_event", "")
        if core_event:
            slug = slugify_vi(f"{protagonist}-{core_event}")
        else:
            slug = slugify_vi(protagonist)
        return f"{acr}_story-{slug}-{chunk_idx}.md"

    return f"{acr}_unknown-{chunk_idx}.md"


# ══════════════════════════════════════════════════════════════
# SINH YAML FRONTMATTER (STRING TEMPLATE)
# ══════════════════════════════════════════════════════════════

def build_frontmatter(atom):
    """Sinh YAML frontmatter hoàn toàn an toàn bằng JSON serialization.

    Dùng json.dumps() cho mọi value dạng chuỗi tự do (protagonist, source_name) 
    và mảng (topics, vivid_*) để đảm bảo 100% ký tự đặc biệt (dấu ngoặc kép, newline) 
    được escape đúng chuẩn flow-style YAML.
    """
    lines = ['---']

    # Root type
    lines.append(f'type: {atom["type"]}')

    # Sub-type field (chỉ 1 trong 4, tùy atom type)
    if atom.get("sub_field_name") and atom.get("sub_field_value"):
        lines.append(f'{atom["sub_field_name"]}: {atom["sub_field_value"]}')

    # Topics (mảng inline)
    if atom.get("topics"):
        lines.append(f'topics: {json.dumps(atom["topics"], ensure_ascii=False)}')
    else:
        lines.append('topics: []')

    # Status
    lines.append('status: processed')

    # Protagonist (chỉ cho Story)
    if atom.get("protagonist"):
        lines.append(f'protagonist: {json.dumps(atom["protagonist"], ensure_ascii=False)}')

    # Source
    lines.append('source_type: book')
    lines.append(f'source_name: {json.dumps(atom["source_name"], ensure_ascii=False)}')
    lines.append('confidence: 0.9')

    # Graph links (chỉ field áp dụng cho type tương ứng)
    if atom["type"] == "insight":
        lines.append(f'belongs_to_audience: "{atom["belongs_to_audience"]}"')
    elif atom["type"] in ("solution", "concept"):
        lines.append(f'supports_insight: "{atom["supports_insight"]}"')
    elif atom["type"] in ("story", "quote", "data-point"):
        lines.append(f'supports_knowledge: "{atom["supports_knowledge"]}"')

    # Vivid arrays: canonical + reserve (xếp theo cặp để dễ đọc trong Obsidian)
    if atom.get("vivid_insights"):
        lines.append(f'vivid_insights: {json.dumps(atom["vivid_insights"], ensure_ascii=False)}')
    if atom.get("vivid_insights_reserve"):
        lines.append(f'vivid_insights_reserve: {json.dumps(atom["vivid_insights_reserve"], ensure_ascii=False)}')
    if atom.get("vivid_knowledges"):
        lines.append(f'vivid_knowledges: {json.dumps(atom["vivid_knowledges"], ensure_ascii=False)}')
    if atom.get("vivid_knowledges_reserve"):
        lines.append(f'vivid_knowledges_reserve: {json.dumps(atom["vivid_knowledges_reserve"], ensure_ascii=False)}')

    lines.append('---')
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════
# GRAPH LINK RESOLUTION
# ══════════════════════════════════════════════════════════════

def resolve_graph_link(atom_type, meta, acr, chunk_idx, context):
    """Resolve graph link cho từng atom type.

    Returns: dict với key = tên field graph, value = wikilink string
    """
    result = {}

    if atom_type == "insight":
        # belongs_to_audience: lấy từ _adm_lookup (pre-built từ Decision Map array)
        adm = context.get("_adm_lookup", {})
        audience_entry = adm.get(chunk_idx, adm.get("book", {}))
        audience_filename = audience_entry.get("audience_filename", "")
        result["belongs_to_audience"] = f"[[{audience_filename}]]" if audience_filename else ""

    elif atom_type in ("solution", "concept"):
        # supports_insight: slugify tên insight từ meta['supports_insight']
        insight_name = meta.get("supports_insight", "")
        if insight_name:
            slug = slugify_vi(insight_name)
            result["supports_insight"] = f"[[{acr}_{slug}]]"
        else:
            result["supports_insight"] = ""

    elif atom_type in ("story", "quote", "data-point"):
        # supports_knowledge: slugify tên knowledge từ meta['supports_knowledge']
        knowledge_name = meta.get("supports_knowledge", "")
        if knowledge_name:
            slug = slugify_vi(knowledge_name)
            result["supports_knowledge"] = f"[[{acr}_{slug}]]"
        else:
            result["supports_knowledge"] = ""

    return result


# ══════════════════════════════════════════════════════════════
# TOPIC STAMPING
# ══════════════════════════════════════════════════════════════

def get_topics(chunk_idx, context):
    """Lấy topics cho chunk: book_topics + chunk_topics, loại trùng."""
    book_topics = context.get("book_topics", [])
    chunk_key = str(chunk_idx)
    chunk_topics = context.get("chunk_topics_map", {}).get(chunk_key, [])
    # Deduplicate: book trước, chunk sau
    combined = list(book_topics)
    for t in chunk_topics:
        if t not in combined:
            combined.append(t)
    return combined


# ══════════════════════════════════════════════════════════════
# SOURCE NAME
# ══════════════════════════════════════════════════════════════

def build_source_name(context):
    """Sinh chuỗi source_name theo chuẩn: 'Tên Sách (bởi Tác Giả, Năm)'"""
    bm = context.get("book_meta", {})
    name = bm.get("book_name", "Unknown")
    author = bm.get("author", "Unknown")
    year = bm.get("year", "Không đề cập")
    return f"{name} (bởi {author}, {year})"


# ══════════════════════════════════════════════════════════════
# ADM LOOKUP BUILDER
# ══════════════════════════════════════════════════════════════

def build_adm_lookup(context):
    """Chuyển audience_decision_map từ array sang dict lookup.

    Input: context["audience_decision_map"] là list (array format Decision Map)
    Output: dict {chunk_idx(int): entry, "book": entry}
    Lưu vào context["_adm_lookup"] để dùng trong resolve_graph_link và process_vivid_buffer.
    """
    adm_raw = context.get("audience_decision_map", [])
    # Lá chắn phòng vệ: chỉ chấp nhận array format (chuẩn duy nhất từ book-audience-matcher)
    if not isinstance(adm_raw, list):
        print(f"❌ FATAL: audience_decision_map phải là array, nhận được {type(adm_raw).__name__}.")
        print(f"   Kiểm tra file audience_decision_map.json hoặc giá trị --decision-map đã truyền.")
        sys.exit(1)
    lookup = {}
    for entry in adm_raw:
        if entry.get("scope") == "book":
            lookup["book"] = entry
        else:
            ci = entry.get("chunk_index")
            if ci is not None:
                lookup[ci] = entry
    context["_adm_lookup"] = lookup


# ══════════════════════════════════════════════════════════════
# VIVID-APPEND
# ══════════════════════════════════════════════════════════════

def process_vivid_buffer(vivid_buffer, atoms_by_slug, acr, context, vault_root):
    """Xử lý vivid buffer: append vào Host Mẹ (canonical) hoặc reserve.

    Returns: dict stats {appended: int, orphan_dropped: int, cap_reserved: int}
    """
    stats = {"appended": 0, "orphan_dropped": 0, "cap_reserved": 0, "appended_keys": set(), "reserved_keys": set()}
    HARD_CAP = 3

    for vivid in vivid_buffer:
        vtype = vivid["vivid_type"]
        body = vivid["body_text"]

        if vtype == "vivid_insight":
            # Tìm insight atom in-memory qua supports_insight
            si = vivid["meta"].get("supports_insight", "")
            if not si:
                stats["orphan_dropped"] += 1
                continue
            target_slug = f"{acr}_{slugify_vi(si)}"
            target_atom = atoms_by_slug.get(target_slug)
            if not target_atom:
                stats["orphan_dropped"] += 1
                continue
            arr = target_atom.setdefault("vivid_insights", [])
            if len(arr) < HARD_CAP:
                arr.append(body)
                stats["appended"] += 1
                # Key = (chunk_idx_str, vivid_type, id) — khớp 1-1 với baseline CSV
                stats["appended_keys"].add((str(vivid["chunk_idx"]), "vivid_insight", si.strip()))
            else:
                arr_reserve = target_atom.setdefault("vivid_insights_reserve", [])
                arr_reserve.append(body)
                stats["cap_reserved"] += 1
                stats["reserved_keys"].add((str(vivid["chunk_idx"]), "vivid_insight", si.strip()))

        elif vtype == "vivid_knowledge":
            # Tìm solution/concept atom in-memory qua supports_knowledge
            sk = vivid["meta"].get("supports_knowledge", "")
            if not sk:
                stats["orphan_dropped"] += 1
                continue
            target_slug = f"{acr}_{slugify_vi(sk)}"
            target_atom = atoms_by_slug.get(target_slug)
            if not target_atom:
                stats["orphan_dropped"] += 1
                continue
            arr = target_atom.setdefault("vivid_knowledges", [])
            if len(arr) < HARD_CAP:
                arr.append(body)
                stats["appended"] += 1
                stats["appended_keys"].add((str(vivid["chunk_idx"]), "vivid_knowledge", sk.strip()))
            else:
                arr_reserve = target_atom.setdefault("vivid_knowledges_reserve", [])
                arr_reserve.append(body)
                stats["cap_reserved"] += 1
                stats["reserved_keys"].add((str(vivid["chunk_idx"]), "vivid_knowledge", sk.strip()))

        elif vtype == "vivid_circumstance":
            # Patch Audience file trên disk
            chunk_idx = vivid["chunk_idx"]
            adm = context.get("_adm_lookup", {})
            audience_entry = adm.get(chunk_idx, {})
            audience_filename = audience_entry.get("audience_filename", "")
            if not audience_filename:
                stats["orphan_dropped"] += 1
                continue

            audience_path = os.path.join(vault_root, "01-Atomic", "Audiences", f"{audience_filename}.md")
            if not os.path.exists(audience_path):
                stats["orphan_dropped"] += 1
                continue

            # Đọc file audience và normalize CRLF→LF (vault Windows dùng \r\n)
            with open(audience_path, 'r', encoding='utf-8') as f:
                aud_content = f.read()
            aud_content = aud_content.replace('\r\n', '\n')

            # Tách frontmatter và body
            fm_match = re.match(r'^---\n(.*?)\n---', aud_content, re.DOTALL)
            if not fm_match:
                stats["orphan_dropped"] += 1
                continue

            fm_text = fm_match.group(1)

            # Khai thác an toàn 2 arrays hiện tại qua PyYAML
            import yaml
            try:
                fm_data = yaml.safe_load(fm_text) or {}
                existing = fm_data.get("vivid_circumstances", [])
                if not isinstance(existing, list):
                    existing = []
                existing_reserve = fm_data.get("vivid_circumstances_reserve", [])
                if not isinstance(existing_reserve, list):
                    existing_reserve = []
            except Exception as e:
                print(f"⚠️ Lỗi parse YAML Audience {audience_filename}: {e}")
                stats["orphan_dropped"] += 1
                continue

            # Route: canonical (dưới cap) hoặc reserve (đạt/vượt cap)
            if len(existing) < HARD_CAP:
                existing.append(body)
                target_field = "vivid_circumstances"
                target_arr = existing
                stats["appended"] += 1
                stats["appended_keys"].add((str(chunk_idx), "vivid_circumstance", vivid["chunk_audience"]))
            else:
                existing_reserve.append(body)
                target_field = "vivid_circumstances_reserve"
                target_arr = existing_reserve
                stats["cap_reserved"] += 1
                stats["reserved_keys"].add((str(chunk_idx), "vivid_circumstance", vivid["chunk_audience"]))

            # Serialize mảng đã sửa thành inline JSON (tương thích YAML)
            import json
            new_arr_str = json.dumps(target_arr, ensure_ascii=False)

            # Regex patch field đích vào frontmatter
            escaped_field = re.escape(target_field)
            pattern = r'\n' + escaped_field + r':\s*.*?(?=\n\S|$)'
            padded_fm_text = '\n' + fm_text

            if not re.search(r'\n' + escaped_field + ':', padded_fm_text):
                # Field chưa tồn tại (file cũ) → chèn cuối frontmatter
                if not padded_fm_text.endswith('\n'):
                    padded_fm_text += '\n'
                padded_fm_text += target_field + ': ' + new_arr_str
                new_fm = padded_fm_text[1:]
            else:
                new_fm_padded = re.sub(
                    pattern,
                    '\n' + target_field + ': ' + new_arr_str,
                    padded_fm_text,
                    flags=re.DOTALL
                )
                new_fm = new_fm_padded[1:]

            # Ráp lại file
            new_content = f'---\n{new_fm}\n---' + aud_content[fm_match.end():]

            # Ghi an toàn (Atomic Write) để chống rủi ro hỏng file nếu process crash
            tmp_path = audience_path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            os.replace(tmp_path, audience_path)

    return stats


# ══════════════════════════════════════════════════════════════
# GATE VALIDATION (POKA-YOKE FINAL LAYER)
# ══════════════════════════════════════════════════════════════

def validate_atoms(atoms, atoms_by_slug, vault_root):
    """Kiểm tra graph links trước commit write. Lọc triệt để Broken Links.
    
    Returns: (valid_atoms, quarantine_atoms)
    """
    valid = []
    quarantine = []

    for atom in atoms:
        t = atom["type"]
        is_valid = True
        reason = ""

        if t == "insight":
            if not atom.get("belongs_to_audience"):
                is_valid = False
                reason = "belongs_to_audience rỗng"
        elif t in ("solution", "concept"):
            target_link = atom.get("supports_insight", "")
            if not target_link:
                is_valid = False
                reason = "supports_insight rỗng"
            else:
                # Trích xuất slug từ wikilink [[slug]]
                target_slug = target_link.strip("[]")
                if target_slug not in atoms_by_slug:
                    is_valid = False
                    reason = f"Lỗi Khóa Ngoại: Insight mục tiêu không tồn tại lọt vào tới Atomizer ({target_slug})"
                    
        elif t in ("story", "quote", "data-point"):
            target_link = atom.get("supports_knowledge", "")
            if not target_link:
                is_valid = False
                reason = "supports_knowledge rỗng"
            else:
                # Trích xuất slug từ wikilink [[slug]]
                target_slug = target_link.strip("[]")
                if target_slug not in atoms_by_slug:
                    is_valid = False
                    reason = f"Lỗi Khóa Ngoại: Knowledge mục tiêu không tồn tại lọt vào tới Atomizer ({target_slug})"

        if is_valid:
            valid.append(atom)
        else:
            atom["status"] = "quarantine"
            atom["quarantine_reason"] = reason
            quarantine.append(atom)

    return valid, quarantine


# ══════════════════════════════════════════════════════════════
# COMMIT WRITE
# ══════════════════════════════════════════════════════════════

def write_atom_file(atom, vault_root, overwrite=False):
    """Ghi 1 atom file xuống disk (Atomic Write)."""
    folder_path = os.path.join(vault_root, atom["folder"])
    os.makedirs(folder_path, exist_ok=True)

    filepath = os.path.join(folder_path, atom["filename"])

    if os.path.exists(filepath) and not overwrite:
        print(f"  ⏭️ SKIP (đã tồn tại): {filepath}")
        return False

    frontmatter = build_frontmatter(atom)
    body = atom.get("body_text", "")

    content = f"{frontmatter}\n\n{body}\n"

    # Atomic write: ghi tmp rồi replace, chống truncate khi crash
    tmp_path = filepath + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(content)
    os.replace(tmp_path, filepath)
    return True


def write_dlq_file(atom, vault_root):
    """Ghi atom quarantine vào DLQ."""
    dlq_path = os.path.join(vault_root, "01-Atomic", "_DLQ")
    os.makedirs(dlq_path, exist_ok=True)

    filepath = os.path.join(dlq_path, atom["filename"])
    frontmatter = build_frontmatter(atom)
    body = atom.get("body_text", "")
    reason = atom.get("quarantine_reason", "unknown")

    content = f"{frontmatter}\n\n<!-- QUARANTINE: {reason} -->\n\n{body}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


# ══════════════════════════════════════════════════════════════
# BASELINE VERIFICATION (POKA-YOKE LEDGER)
# ══════════════════════════════════════════════════════════════

def verify_baseline(baseline_path, valid_atoms, quarantine_atoms, appended_keys, reserved_keys, report_path=None):
    """Đối chiếu kết quả atomize với extraction_baseline.csv.

    - Atom: match qua (chunk_idx, category, _baseline_id)
    - Vivid: match qua appended_keys (canonical) và reserved_keys (reserve)
             KHÔNG mượn trạng thái Atom cha — điểm danh độc lập.

    Returns: (missing_count, dlq_count, reserved_count)
    """
    import csv as _csv

    FIELDNAMES = ['section', 'chunk', 'category', 'id', 'status']

    # Map atom_type trong atomizer → category trong baseline CSV
    ATOM_TO_CAT = {
        "insight":    "insight",
        "solution":   "knowledge",
        "concept":    "knowledge",
        "data-point": "evidence",
        "story":      "story",
        "quote":      "quote",
    }

    # Set định danh Atom đã ghi thành công
    written_set = {
        (str(a["chunk_idx"]), ATOM_TO_CAT.get(a["type"], a["type"]), a.get("_baseline_id", "").strip())
        for a in valid_atoms
    }
    # Set định danh Atom đã vào DLQ (broken link)
    dlq_set = {
        (str(a["chunk_idx"]), ATOM_TO_CAT.get(a["type"], a["type"]), a.get("_baseline_id", "").strip())
        for a in quarantine_atoms
    }

    with open(baseline_path, 'r', encoding='utf-8') as f:
        all_rows = list(_csv.DictReader(f))

    for row in all_rows:
        if row['section'] == 'audience':
            # Audience đã được verify_audiences.py xử lý — không đụng vào
            continue

        key = (row['chunk'], row['category'], row['id'].strip())

        if row['section'] == 'atom':
            if key in written_set:
                row['status'] = 'DONE'
            elif key in dlq_set:
                row['status'] = 'DLQ'
            else:
                row['status'] = 'MISSING'

        elif row['section'] == 'vivid':
            # Vivid điểm danh ĐỘC LẬP — KHÔNG mượn trạng thái Atom cha
            if key in appended_keys:
                row['status'] = 'DONE'
            elif key in reserved_keys:
                row['status'] = 'CAP_RESERVED'
            else:
                row['status'] = 'MISSING'

    # Ghi đè baseline.csv
    with open(baseline_path, 'w', encoding='utf-8', newline='') as f:
        writer = _csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    # Thống kê
    atom_rows      = [r for r in all_rows if r['section'] in ('atom', 'vivid')]
    missing        = sum(1 for r in atom_rows if r['status'] == 'MISSING')
    dlq_count      = sum(1 for r in atom_rows if r['status'] == 'DLQ')
    done_count     = sum(1 for r in atom_rows if r['status'] == 'DONE')
    reserved_count = sum(1 for r in atom_rows if r['status'] == 'CAP_RESERVED')

    if report_path:
        with open(report_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## 3. book-parser (Atomizer)\n")
            f.write(f"- DONE: {done_count} | DLQ: {dlq_count} | CAP_RESERVED: {reserved_count} | MISSING: {missing}\n")
            for r in atom_rows:
                if r['status'] == 'MISSING':
                    f.write(f"  ❌ Chunk {r['chunk']} — [{r['category']}] {r['id'][:50]}\n")

    return missing, dlq_count, reserved_count


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════

def run_atomizer(metadata, context, vault_root, dry_run=False, overwrite=False,
                 baseline_path=None, report_path=None):
    """Pipeline chính: parse → classify → build → vivid → validate → write."""

    acr = context["source_acronym"]
    source_name = build_source_name(context)
    build_adm_lookup(context)

    # Bộ đệm
    atoms = []               # Atom core (sẽ ghi file)
    atoms_by_slug = {}        # Lookup nhanh bằng slug (cho vivid-append)
    vivid_buffer = []         # Vivid items (sẽ append vào host)

    # Counters
    counts = {t: 0 for t in ["insight", "solution", "concept", "story", "data-point", "quote"]}
    skip_count = 0

    # ── Bước 1: Duyệt TOÀN BỘ items[] ──
    for chunk_data in metadata["chunks"]:
        chunk_meta = chunk_data.get("chunk", {})
        chunk_idx = int(chunk_meta.get("CHUNK_index", 0))
        topics = get_topics(chunk_idx, context)

        for item in chunk_data["items"]:
            meta = item.get("meta", {})
            body = item.get("body_text", "").strip()

            # Skip check
            skip, reason = should_skip_item(item)
            if skip:
                skip_count += 1
                continue

            # Phân loại DIKW
            classification = classify_dikw(meta)
            if classification is None:
                skip_count += 1
                continue

            atom_type = classification["atom_type"]

            # Vivid → buffer
            if atom_type == "vivid":
                vivid_buffer.append({
                    "vivid_type": classification["vivid_type"],
                    "meta": meta,
                    "body_text": body,
                    "chunk_idx": chunk_idx,
                    # Inject chunk_audience từ parsed_metadata.json (cùng nguồn với generate_baseline.py)
                    # Dùng cho appended_keys của vivid_circumstance — KHÔNG phụ thuộc Decision Map
                    "chunk_audience": chunk_data.get("audience", {}).get("chunk_audience", "").strip(),
                })
                continue

            # Sinh filename
            filename = generate_filename(atom_type, meta, acr, chunk_idx)

            # Resolve graph links
            graph = resolve_graph_link(atom_type, meta, acr, chunk_idx, context)

            # Build atom dict
            atom = {
                "type": atom_type,
                "sub_field_name": classification.get("sub_field_name"),
                "sub_field_value": classification.get("sub_field_value"),
                "topics": topics,
                "source_name": source_name,
                "folder": classification["folder"],
                "filename": filename,
                "body_text": body,
                "chunk_idx": chunk_idx,
            }

            # Merge graph links
            atom.update(graph)

            # Gán _baseline_id: khớp 1-1 với id trong extraction_baseline.csv
            # Quy tắc: dùng đúng field mà generate_baseline.py đã dùng để tạo row
            if atom_type == "insight":
                atom["_baseline_id"] = meta.get("insight_name", "").strip()
            elif atom_type in ("solution", "concept"):
                atom["_baseline_id"] = meta.get("knowledge_name", "").strip()
            elif atom_type == "data-point":
                atom["_baseline_id"] = meta.get("evidence_keyword", "").strip()
            elif atom_type == "story":
                protagonist = meta.get("protagonist", "").strip()
                core_event  = meta.get("core_event", "").strip()
                atom["_baseline_id"] = f"{protagonist}-{core_event}" if core_event else protagonist
            elif atom_type == "quote":
                atom["_baseline_id"] = meta.get("quote_keyword", "").strip()
            else:
                atom["_baseline_id"] = ""

            # Story: thêm protagonist
            if atom_type == "story":
                atom["protagonist"] = meta.get("protagonist", "")

            # Lưu atom
            atoms.append(atom)

            # Lookup slug cho vivid-append (phát hiện collision)
            slug_key = filename.replace('.md', '')
            if slug_key in atoms_by_slug:
                print(f"  ⚠️ COLLISION: filename '{filename}' trùng! Atom trước sẽ bị mất trong vivid-lookup.")
            atoms_by_slug[slug_key] = atom

            counts[atom_type] += 1

    # ── Bước 2: Vivid-Append ──
    vivid_stats = process_vivid_buffer(vivid_buffer, atoms_by_slug, acr, context, vault_root)

    # ── Bước 3: Gate Validation ──
    valid_atoms, quarantine_atoms = validate_atoms(atoms, atoms_by_slug, vault_root)

    # ── Bước 4: Commit Write hoặc Dry-Run ──
    if dry_run:
        print("\n🔍 DRY-RUN MODE — Không ghi file\n")
    else:
        written = 0
        skipped_exist = 0
        for atom in valid_atoms:
            ok = write_atom_file(atom, vault_root, overwrite)
            if ok:
                written += 1
            else:
                skipped_exist += 1
        for atom in quarantine_atoms:
            write_dlq_file(atom, vault_root)

    # ── Bước 5: Báo cáo ──
    print("=" * 50)
    if dry_run:
        print("🔍 DRY-RUN REPORT")
    else:
        print("✅ Atomization hoàn tất!")
    print("=" * 50)
    print(f"  Insights:    {counts['insight']}")
    print(f"  Solutions:   {counts['solution']}")
    print(f"  Concepts:    {counts['concept']}")
    print(f"  Stories:     {counts['story']}")
    print(f"  Data-Points: {counts['data-point']}")
    print(f"  Quotes:      {counts['quote']}")
    print(f"  ──────────────────────")
    print(f"  Total Atoms: {sum(counts.values())}")
    print(f"  Skipped:     {skip_count}")
    print(f"  ──────────────────────")
    print(f"  Vivid Appended:  {vivid_stats['appended']}")
    print(f"  Vivid Orphan Drop: {vivid_stats['orphan_dropped']}")
    print(f"  Vivid Cap Reserved: {vivid_stats['cap_reserved']}")
    print(f"  ──────────────────────")
    print(f"  Quarantine:  {len(quarantine_atoms)}")
    if quarantine_atoms:
        for a in quarantine_atoms:
            print(f"    ⚠️ {a['filename']}: {a.get('quarantine_reason','')}")

    if not dry_run:
        print(f"  ──────────────────────")
        print(f"  Written:     {written}")
        if skipped_exist:
            print(f"  Skipped (exists): {skipped_exist}")

    # In danh sách wikilinks
    print(f"\n📋 Wikilinks ({len(valid_atoms)}):")
    for atom in valid_atoms:
        wl = atom['filename'].replace('.md', '')
        print(f"  [[{wl}]]")

    # ── Verify Baseline (chỉ chạy nếu có --baseline) ──
    if baseline_path and os.path.isfile(baseline_path):
        m, d, r = verify_baseline(
            baseline_path,
            valid_atoms,
            quarantine_atoms,
            vivid_stats["appended_keys"],
            vivid_stats["reserved_keys"],
            report_path,
        )
        if m > 0:
            print(f"\n❌ BASELINE ALERT: {m} Atom/Vivid MISSING so với manifest!")
            print("   → Kiểm tra pipeline_report.md để xem danh sách cụ thể.")
            sys.exit(2)   # exit code 2 = data loss
        if d > 0:
            print(f"\n⚠️ WARN: {d} Atom vào DLQ (broken link — kiểm tra quarantine_reason).")

    return {
        "counts": counts,
        "quarantine": len(quarantine_atoms),
        "vivid_stats": vivid_stats,
    }


# ══════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Atomizer: Script deterministic tạo Atom files từ parsed metadata"
    )
    parser.add_argument("metadata_json", help="Đường dẫn tới parsed_metadata.json")
    parser.add_argument("context_json", help="Đường dẫn tới atomizer_context.json")
    parser.add_argument("vault_root",  help="Đường dẫn tới vault root (VD: vault/)")
    parser.add_argument("--decision-map", required=True,
                        help="Đường dẫn tới audience_decision_map.json")
    parser.add_argument("--dry-run",   action="store_true", help="In báo cáo mà không ghi file")
    parser.add_argument("--overwrite", action="store_true", help="Ghi đè file atom đã tồn tại")
    parser.add_argument("--baseline",  default=None, help="Đường dẫn extraction_baseline.csv")
    parser.add_argument("--report",    default=None, help="Đường dẫn pipeline_report.md")

    args = parser.parse_args()

    # Validate input files
    for fpath, label in [
        (args.metadata_json, "metadata"),
        (args.context_json, "context"),
        (args.decision_map, "decision-map"),
    ]:
        if not os.path.exists(fpath):
            print(f"❌ Error: File {label} không tồn tại: {fpath}")
            sys.exit(1)

    # Load JSON
    with open(args.metadata_json, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    with open(args.context_json, 'r', encoding='utf-8') as f:
        context = json.load(f)

    # Đọc Decision Map trực tiếp từ file trên disk — không phụ thuộc vào context
    with open(args.decision_map, 'r', encoding='utf-8') as f:
        context["audience_decision_map"] = json.load(f)

    # Run
    result = run_atomizer(
        metadata, context, args.vault_root,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        baseline_path=args.baseline,
        report_path=args.report,
    )

    # Exit code
    if result["quarantine"] > 0:
        sys.exit(1)
    sys.exit(0)
