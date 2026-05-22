"""
TÊN SCRIPT: normalizer.py
VAI TRÒ: Trình dọn rác chuyên sâu (Regex Cleaner). Quét sạch mọi mầm bệnh định dạng
         (AI text, lỗi tag META, ngoặc kép kép) trong Data tĩnh.
KHI NÀO SỬ DỤNG: (1) Hàm normalize_dikw_names được import độc lập bởi gate_checker.py (Shift-Left per-chunk).
                   (2) Hàm normalize_file được gọi TỰ ĐỘNG ở Phase 3 của post_mine.py (toàn cục).
OUTPUT: Sách sạch bong, sẵn sàng cho công đoạn xé nhỏ (Atomization) ở skill tiếp theo.

NORMALIZATION RULES (thứ tự thực thi):
  [N0-pre]      Strip AI Noise: Xóa <thinking>...</thinking>, strip chatbot preamble.
  [N0-sentinel] Dedup Sentinel: Xóa <!-- HEADER_END --> bị hallucinate trong <data_chunk>.
  [N0-toc]      TOC-Aware Chunk Name: Parse TOC_MASTER làm canonical, chuẩn hóa CHUNK=.
  [N0-N4]       Clean & Format: Strip ** ` \\`, sửa "Người", isolate <data_chunk>, xóa chatter.
  [N6]          XML Cover: Chèn <situation><problem><turning_point><outcome><lesson> cho Story thô.
  [N7]          Generate UI Obsidian: Dựng heading ## Chunk N: phía đỉnh mỗi Chunk.
  [N8]          Whitelist META Fields: Strip key=value ngoài ALLOWED_META_FIELDS.
"""

import re
import os
import sys

# Ép chuẩn utf-8 cho lệnh print() ra màn hình (Windows Console Poka-Yoke)
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ── Whitelist: Chỉ các key sau được phép tồn tại trong từng loại META ──
# Mọi key=value nằm ngoài danh sách này sẽ bị strip tự động bởi whitelist_meta_fields().
# Nguồn: prompt-mapper-v4.md + prompt-miner-v4.md
ALLOWED_META_FIELDS = {
    "META_BOOK":           {"book_name", "author", "year", "topics", "total_chunks", "total_blocks"},
    "META_BOOK_AUDIENCE":  {"book_audience"},
    "META_CHUNK":          {"CHUNK", "CHUNK_index"},
    "META_CHUNK_AUDIENCE": {"chunk_audience", "content_type"},
    "META_INSIGHT":        {"insight_type", "insight_name", "content_type", "supports_insight"},
    "META_KNOWLEDGE":      {"knowledge_type", "knowledge_name", "stance", "supports_insight", "content_type", "supports_knowledge"},
    "META_EVIDENCE":       {"content_type", "evidence_keyword", "supports_knowledge"},
    "META_STORY":          {"content_type", "supports_knowledge", "protagonist", "core_event", "timeline", "outcome_measurable"},
    "META_QUOTE":          {"content_type", "speaker", "quote_keyword", "context", "supports_knowledge"},
}

# Type keys có value dùng underscore theo thiết kế (pain_point, vivid_circumstance,...)
# Các key này KHÔNG được normalize underscore trong value.
# Tất cả keys còn lại: nếu value có underscore → replace thành space.
TYPE_KEYS = {'insight_type', 'knowledge_type', 'content_type'}


def normalize_sentinels(content):
    """[N0-sent] Chuẩn hóa biến thể sentinel về dạng canonical.

    Vai trò: NLM đôi khi viết [NOT FOUND], [Not Found], [not found]... thay vì [NOT_FOUND].
             Sentinel filter hạ nguồn (extract_metadata.py dòng 98) check exact match
             → biến thể bị lọt → gây ghost entry.
    Khi nào: Đầu pipeline normalize_file(), trước mọi pass khác phụ thuộc sentinel.
    Output: Content với sentinel đã chuẩn hóa.
    Idempotent.
    """
    content = re.sub(r'\[NOT[\s_]+FOUND\]', '[NOT_FOUND]', content, flags=re.IGNORECASE)
    content = re.sub(r'\[NO[\s_]+JTBD[\s_]+FOUND\]', '[NO_JTBD_FOUND]', content, flags=re.IGNORECASE)
    return content


def strip_ai_noise(content):
    '''[N0-pre] Strip AI thinking chunks và chatbot preamble trước mọi pass khác'''

    # Rule A: Xóa <thinking>...</thinking> chunks (NLM internal monologue lọt ra ngoài)
    content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)

    # Rule B: Strip chatbot preamble — xóa text đứng trước heading đầu tiên của nội dung thật
    # CHỈ cắt nếu phần trước heading KHÔNG chứa header hợp lệ (META_BOOK, HEADER_END, TOC_MASTER).
    # Nếu chứa → đây là header cấu trúc của sách, KHÔNG ĐƯỢC cắt.
    first_heading = re.search(r'^#{1,4}\s', content, re.MULTILINE)
    if first_heading and first_heading.start() > 0:
        preamble = content[:first_heading.start()]
        has_legit_header = any(marker in preamble for marker in [
            '<!-- HEADER_END -->', 'META_BOOK:', 'TOC_MASTER'
        ])
        if not has_legit_header:
            content = content[first_heading.start():]

    return content


def dedup_sentinel(content):
    '''[N0-sentinel] Xóa <!-- HEADER_END --> bị NLM hallucinate bên trong <data_chunk>'''
    return re.sub(
        r'(<data_chunk>)(.*?)(</data_chunk>)',
        lambda m: m.group(1) + m.group(2).replace('<!-- HEADER_END -->', '') + m.group(3),
        content, flags=re.DOTALL
    )


def normalize_header(content):
    '''[N0] NORMALIZE HEADER'''
    # Split header and content
    parts = content.split('<!-- HEADER_END -->')
    if len(parts) == 2:
        header, rest = parts
    else:
        # Try to find TOC_MASTER to insert sentinel
        if 'TOC_MASTER' in content:
            header, rest = content.split('TOC_MASTER', 1)
            # Find the end of the TOC chunk
            lines = rest.split('\n')
            toc_end_idx = 0
            for i, line in enumerate(lines):
                if re.match(r'^\s*<data_chunk>', line):
                    toc_end_idx = i
                    break
            header = header + 'TOC_MASTER' + '\n'.join(lines[:toc_end_idx]) + '\n\n<!-- HEADER_END -->\n'
            rest = '\n'.join(lines[toc_end_idx:])
        else:
            return content # Unable to parse reliably
            
    # Strip formatting from META_BOOK
    def clean_meta(match):
        text = match.group(0)
        return text.replace('**', '').replace('`', '')
        
    header = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?META_BOOK(?:\*\*)?:.*$', clean_meta, header, flags=re.MULTILINE)
    header = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?META_BOOK_AUDIENCE(?:\*\*)?:.*$', clean_meta, header, flags=re.MULTILINE)
    header = header.replace('"Người"', 'Người')
    
    return header + '<!-- HEADER_END -->' + rest

def isolate_and_normalize_chunks(content):
    '''[N1-N7] ISOLATE DATA CHUNK AND NORMALIZE'''
    parts = content.split('<!-- HEADER_END -->')
    if len(parts) != 2:
        return content
    header, chunks_content = parts
    
    # Isolate data chunks
    chunks = re.findall(r'<data_chunk>(.*?)</data_chunk>', chunks_content, re.DOTALL)
    if not chunks:
        return content
        
    normalized_chunks = []
    
    for chunk in chunks:
        # N1: STRIP PROMPT LEAKAGE
        meta_chunk_pos = chunk.find('META_CHUNK:')
        if meta_chunk_pos != -1:
            pre_text = chunk[:meta_chunk_pos]
            if any(leak in pre_text for leak in ['PROMPT MINER', 'VAI TRÒ', 'KHUNG']):
                # Giải cứu cơ chế Warning Isolation: Trích xuất các cờ Warning bị gộp chung trong khối rò rỉ prompt
                saved_warnings = re.findall(r'>\s*\[!warning\][^\n]*', pre_text, re.IGNORECASE)
                
                # Cắt bỏ phần rò rỉ prompt
                chunk = chunk[meta_chunk_pos:]
                
                # Định tuyến lại các cờ Warning về vị trí gốc trên đầu data chunk
                if saved_warnings:
                    chunk = '\n'.join(saved_warnings) + '\n' + chunk
                
        # N2: NORMALIZE META LINES & N3: FIX JTBD FORMAT
        lines = chunk.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'META_(?:CHUNK|CHUNK_AUDIENCE|INSIGHT|KNOWLEDGE|EVIDENCE|STORY|QUOTE):', line):
                line = line.replace('\\`', '').replace('**', '').replace('`', '')
                line = re.sub(r'^\s*[-*]\s+(?=META_)', '', line)
                if 'META_CHUNK_AUDIENCE' in line:
                    line = line.replace('"Người"', 'Người')
                lines[i] = line
        
        # N6: Auto-wrap XML for Story/Case Study
        # If we see content_type=story but no <S> tags, wrap the next paragraphs.
        # This is a naive but effective rescue mechanism.
        chunk_str = '\n'.join(lines)
        if 'content_type=story' in chunk_str or 'content_type=case_study' in chunk_str:
            if '<S>' not in chunk_str:
                # Find the story text chunk and wrap it using the static header
                chunk_str = re.sub(r'(- \*\*Nguyên văn.*?:.*?\n)(.*?)(?=\n(?:- |## |META_|\**[①-⑤]|\Z))', r'\1<S><P><T><O><L>\n\2\n</L></O></T></P></S>', chunk_str, flags=re.DOTALL)
        
        # We process the modified content to get chunk info
        chunk_view = chunk_str
        
        # Parse chunk heading info for N7
        chunk_name = "Unknown Chunk"
        chunk_audience = "Unknown Audience"
        insight_name = "Unknown Insight"
        
        meta_chunk_match = re.search(r'META_CHUNK:.*?CHUNK=([^|\n`\r]+)', chunk_view)
        if meta_chunk_match:
            chunk_name = meta_chunk_match.group(1).strip()
            
        chunk_index_match = re.search(r'CHUNK_index=(\d+)', chunk_view)
        chunk_index = chunk_index_match.group(1) if chunk_index_match else "N"
            
        audience_match = re.search(r'META_CHUNK_AUDIENCE:.*?chunk_audience=([^|\n`\r]+)', chunk_view)
        if audience_match:
            chunk_audience = audience_match.group(1).strip()
            
        insight_match = re.search(r'insight_name=([^|\n`\r]+)', chunk_view)
        if insight_match:
            insight_name = insight_match.group(1).strip()
            
        # [N7] Generate Headings
        heading = f"## Chunk {chunk_index}: {chunk_name}\n\n> 🎯 {chunk_audience} | 🔥 {insight_name}\n\n"
        
        normalized_chunks.append(f"{heading}<data_chunk>\n{chunk_str.strip()}\n</data_chunk>")
        
    return header + "<!-- HEADER_END -->\n\n" + "\n\n".join(normalized_chunks)


def whitelist_meta_fields(content):
    """[N8] Strip foreign key=value fields + normalize underscore trong name values.

    Vai trò: (1) Dọn biến lạ mà NLM tự bịa (VD: belongs_to_audience).
             (2) Normalize underscore → space trong value của non-type keys
                 để đảm bảo slug deterministic (VD: Kiet_Suc → Kiet Suc).
    Khi nào: Được gọi trong normalize_file(), SAU isolate_and_normalize_chunks().
    Output: (cleaned_content, stats_dict) — stats_dict VD: {"belongs_to_audience": 103}
    Logic:
      1. Regex tìm mọi dòng bắt đầu bằng META_XXX:
      2. Xác định loại META → lấy whitelist tương ứng từ ALLOWED_META_FIELDS
      3. Tách phần sau ':' bằng '|', kiểm tra từng segment
      4. Giữ segment có key hợp lệ + segment không có key= (text/[NOT_FOUND])
      5. Bỏ segment có key ngoài whitelist → đếm vào stats
      6. Nếu key hợp lệ và KHÔNG thuộc TYPE_KEYS → replace _ bằng space trong value
    """
    stats = {}

    def process_meta_line(match):
        full_line = match.group(0)
        meta_type_match = re.match(r'(META_\w+):\s*(.*)', full_line)
        if not meta_type_match:
            return full_line

        meta_type = meta_type_match.group(1)
        rest = meta_type_match.group(2)

        allowed = ALLOWED_META_FIELDS.get(meta_type)
        if allowed is None:
            return full_line  # META type không xác định → giữ nguyên

        segments = rest.split('|')
        kept = []

        for seg in segments:
            seg_stripped = seg.strip()
            key_match = re.match(r'(\w+)\s*=', seg_stripped)
            if key_match:
                if key_match.group(1) in allowed:
                    # Normalize underscore → space trong value của non-type keys
                    # Bỏ qua sentinel values dạng [NOT_FOUND], [NO_JTBD_FOUND]
                    if key_match.group(1) not in TYPE_KEYS:
                        k, v = seg_stripped.split('=', 1)
                        v_clean = v.strip()
                        if not (v_clean.startswith('[') and v_clean.endswith(']')):
                            v = v.replace('_', ' ')
                        seg_stripped = f"{k}={v}"
                    kept.append(seg_stripped)
                else:
                    stats[key_match.group(1)] = stats.get(key_match.group(1), 0) + 1
            else:
                # Segment không có key= (text, [NOT_FOUND], etc.) → giữ
                if seg_stripped:
                    kept.append(seg_stripped)

        return f"{meta_type}: {' | '.join(kept)}"

    content = re.sub(r'^META_\w+:.*$', process_meta_line, content, flags=re.MULTILINE)
    return content, stats


def build_toc_map(content):
    '''Parse TOC_MASTER và trả về dict {chunk_index: canonical_name}'''
    toc_map = {}
    toc_match = re.search(r'TOC_MASTER[:\*\s]*\n(.*?)(?:\n\n\n|\Z|<!--)', content, re.DOTALL)
    if not toc_match:
        return toc_map
    toc_body = toc_match.group(1)
    for m in re.finditer(r'(?:[-*]\s*)Chunk\s+(\d+):\s*(.+?)(?:\r?\n|$)', toc_body):
        idx = int(m.group(1))
        toc_map[idx] = m.group(2).strip()
    return toc_map


def normalize_toc_chunk_names(content):
    '''[N0-toc] Chuẩn hóa CHUNK= trong data_chunk dùng TOC_MASTER làm canonical source'''
    toc_map = build_toc_map(content)
    if not toc_map:
        return content

    def fix_chunk(match):
        chunk = match.group(1)
        idx_match = re.search(r'CHUNK_index=(\d+)', chunk)
        if not idx_match:
            return match.group(0)
        idx = int(idx_match.group(1))
        canonical = toc_map.get(idx)
        if not canonical:
            return match.group(0)
        # Đảm bảo prefix "Chunk N:"
        if not re.match(rf'Chunk\s+{idx}\s*:', canonical):
            canonical = f'Chunk {idx}: {canonical}'
        # Thay thế CHUNK= value (xử lý cả ** và backtick variations)
        chunk = re.sub(
            r'(?:\*\*)?META_CHUNK(?:\*\*)?:\s*`?CHUNK=[^|\n`]*',
            f'META_CHUNK: CHUNK={canonical}',
            chunk
        )
        return f'<data_chunk>{chunk}</data_chunk>'

    content = re.sub(r'<data_chunk>(.*?)</data_chunk>', fix_chunk, content, flags=re.DOTALL)
    return content

import re

def poka_yoke_word_prefix(S, valid_names):
    """
    Thuật toán Longest Common Word Prefix
    Trả về: (Matched_Name, Extra_Text) hoặc (None, "")
    """
    if not S or not valid_names:
        return None, ""
        
    S_words = S.split()
    best_N = None
    best_match_words = 0
    
    for N in valid_names:
        N_words = N.split()
        match_count = 0
        for wS, wN in zip(S_words, N_words):
            # So sánh không phân biệt hoa thường
            if wS.lower() == wN.lower():
                match_count += 1
            else:
                break
                
        # N trùng tiền tố với S theo số lượng từ tối thiểu (min 3 hoặc tổng số từ của N)
        required = min(3, len(N_words))
        if match_count >= required and match_count > best_match_words:
            best_match_words = match_count
            best_N = N
            
    if best_N:
        # Tái tạo lại extra text từ các từ bị dôi ra
        extra_text = " ".join(S_words[best_match_words:])
        return best_N, extra_text
        
    return None, ""


# ── Mapping cố định: vivid type → META prefix ──
VIVID_META_MAP = {
    'vivid_circumstance': 'META_CHUNK_AUDIENCE',
    'vivid_insight':      'META_INSIGHT',
    'vivid_knowledge':    'META_KNOWLEDGE',
}


def repair_vivid_tags(chunk, valid_insights, valid_knowledges):
    """[N-VIVID] Repair 4 dạng lỗi format vivid trong 1 data_chunk.

    Vai trò: Sửa format vivid tag bị NLM viết sai, đảm bảo extract_metadata.py
             hạ nguồn parse đúng (content_type exact match + body_text tách riêng dòng).
    Khi nào: Được gọi BÊN TRONG normalize_dikw_names(), sau Bước 2 (thu thập
             valid_insights/valid_knowledges), trước Bước 3 (poka-yoke supports_*).
    Input: chunk string, valid_insights set, valid_knowledges set.
    Output: chunk string đã repair.
    Idempotent.

    4 sub-repairs theo thứ tự:
      (A) Prepend META prefix nếu NLM viết content_type=vivid_* mà thiếu META_*:
      (B) Xuống dòng nếu vivid body bị dính cùng dòng với META tag
      (C) Inject thẻ vivid + [NOT_FOUND] nếu NLM bỏ qua hoàn toàn
      (D) Sanitize brackets & normalize separators trong vivid body text
    """
    # ── Sub-repair A: Prepend META prefix nếu thiếu ──
    # Target: dòng bắt đầu bằng content_type=vivid_* KHÔNG CÓ META_*: đằng trước
    def _prepend_meta(match):
        vivid_type = match.group(1)
        rest = match.group(2)
        prefix = VIVID_META_MAP.get(vivid_type)
        if not prefix:
            return match.group(0)
        return f'{prefix}: content_type={vivid_type}{rest}'

    chunk = re.sub(
        r'^content_type=(vivid_\w+)(.*?)$',
        _prepend_meta,
        chunk,
        flags=re.MULTILINE
    )

    # ── Sub-repair B: Xuống dòng nếu body dính cùng dòng ──
    # Target: META_*: content_type=vivid_TYPE... TEXT_DÔI_RA
    # Ví dụ Chunk 10: META_CHUNK_AUDIENCE: content_type=vivid_circumstance [Khi trẻ...]
    # → Tách thành 2 dòng
    def _split_vivid_body(match):
        meta_tag = match.group(1)
        after_colon = match.group(2)

        segments = after_colon.split('|')
        clean_segments = []
        extra_body = None

        for seg in segments:
            seg_stripped = seg.strip()
            if not seg_stripped:
                continue

            kv_match = re.match(r'(\w+)=(.+)', seg_stripped)
            if kv_match:
                key = kv_match.group(1)
                value = kv_match.group(2).strip()

                if key == 'content_type' and value.startswith('vivid_'):
                    # Tách: vivid_TYPE vs text dôi
                    ct_match = re.match(r'(vivid_\w+)\s+(.*)', value, re.DOTALL)
                    if ct_match:
                        clean_segments.append(f'content_type={ct_match.group(1)}')
                        extra_body = ct_match.group(2).strip()
                    else:
                        clean_segments.append(f'content_type={value}')

                elif key in ('supports_insight', 'supports_knowledge'):
                    # Dùng poka_yoke_word_prefix để phát hiện body dính trong value
                    lookup = valid_insights if key == 'supports_insight' else valid_knowledges
                    if lookup:
                        matched_name, extra_text = poka_yoke_word_prefix(value, list(lookup))
                        if matched_name and extra_text:
                            clean_segments.append(f'{key}={matched_name}')
                            extra_body = extra_text.strip()
                        else:
                            clean_segments.append(seg_stripped)
                    else:
                        clean_segments.append(seg_stripped)
                else:
                    clean_segments.append(seg_stripped)
            else:
                # Segment không có key= → body dính lọt qua pipe split
                if extra_body:
                    extra_body += ' | ' + seg_stripped
                else:
                    extra_body = seg_stripped

        rebuilt = f'{meta_tag}: {" | ".join(clean_segments)}'
        if extra_body:
            return f'{rebuilt}\n{extra_body}'
        return rebuilt

    chunk = re.sub(
        r'^(META_\w+):\s*(content_type=vivid_\w+.+)$',
        _split_vivid_body,
        chunk,
        flags=re.MULTILINE
    )

    # ── Sub-repair C: Inject thẻ vivid + [NOT_FOUND] nếu thiếu hoàn toàn ──
    # Chỉ inject nếu master tag tồn tại mà vivid tag tương ứng vắng mặt.
    has_vivid_circ = bool(re.search(r'content_type=vivid_circumstance', chunk))
    has_vivid_insight = bool(re.search(r'content_type=vivid_insight', chunk))

    # Track knowledge nào đã có vivid
    knowledges_with_vivid = set()
    for m in re.finditer(r'content_type=vivid_knowledge\s*\|\s*supports_knowledge=([^\n\r]+)', chunk):
        knowledges_with_vivid.add(m.group(1).strip())

    lines = chunk.split('\n')
    new_lines = []

    for line in lines:
        new_lines.append(line)
        stripped = line.strip()

        # (C1) Inject vivid_circumstance sau META_CHUNK_AUDIENCE: chunk_audience=...
        if not has_vivid_circ and stripped.startswith('META_CHUNK_AUDIENCE:') and 'chunk_audience=' in stripped:
            new_lines.append('META_CHUNK_AUDIENCE: content_type=vivid_circumstance')
            new_lines.append('[NOT_FOUND]')
            has_vivid_circ = True

    # (C2) Inject vivid_insight — tìm boundary ② hoặc META_KNOWLEDGE đầu tiên
    if not has_vivid_insight and valid_insights:
        insight_name = list(valid_insights)[0]
        inject_tag = f'META_INSIGHT: content_type=vivid_insight | supports_insight={insight_name}'
        final_lines = []
        injected = False
        for line in new_lines:
            s = line.strip()
            if not injected and (s.startswith('**\u2461') or s.startswith('\u2461') or
                                 (s.startswith('META_KNOWLEDGE:') and 'knowledge_name=' in s)):
                final_lines.append(inject_tag)
                final_lines.append('[NOT_FOUND]')
                final_lines.append('')
                injected = True
            final_lines.append(line)
        new_lines = final_lines

    # (C3) Inject vivid_knowledge cho từng knowledge thiếu vivid
    missing_knowledges = set(valid_knowledges) - knowledges_with_vivid
    if missing_knowledges:
        boundary_pattern = re.compile(
            r'^\s*(?:\*?\*?(?:\u2461|\u2462|\u2463|\u2464)|META_(?:KNOWLEDGE|EVIDENCE|STORY|QUOTE):)'
        )
        final_lines = []
        current_knowledge = None
        pending_inject = None  # knowledge đang chờ inject

        for j, line in enumerate(new_lines):
            s = line.strip()

            # Detect knowledge master tag
            if s.startswith('META_KNOWLEDGE:') and 'knowledge_name=' in s and 'content_type=' not in s:
                # Nếu có pending inject chưa xử lý, inject trước knowledge mới
                if pending_inject and pending_inject in missing_knowledges:
                    final_lines.append(f'META_KNOWLEDGE: content_type=vivid_knowledge | supports_knowledge={pending_inject}')
                    final_lines.append('[NOT_FOUND]')
                    final_lines.append('')
                    missing_knowledges.discard(pending_inject)

                kn_match = re.search(r'knowledge_name=([^|\n\r]+)', s)
                if kn_match:
                    current_knowledge = kn_match.group(1).strip()
                    pending_inject = current_knowledge if current_knowledge in missing_knowledges else None
                else:
                    current_knowledge = None
                    pending_inject = None

            # Detect boundary khác (③④⑤, META_EVIDENCE/STORY/QUOTE) → inject nếu đang pending
            elif pending_inject and pending_inject in missing_knowledges:
                is_other_boundary = boundary_pattern.match(s) and not (
                    s.startswith('META_KNOWLEDGE:') and 'content_type=vivid_knowledge' in s
                )
                if is_other_boundary:
                    final_lines.append(f'META_KNOWLEDGE: content_type=vivid_knowledge | supports_knowledge={pending_inject}')
                    final_lines.append('[NOT_FOUND]')
                    final_lines.append('')
                    missing_knowledges.discard(pending_inject)
                    pending_inject = None

            final_lines.append(line)

        # Edge case: pending inject ở cuối chunk
        if pending_inject and pending_inject in missing_knowledges:
            final_lines.append(f'META_KNOWLEDGE: content_type=vivid_knowledge | supports_knowledge={pending_inject}')
            final_lines.append('[NOT_FOUND]')
            missing_knowledges.discard(pending_inject)

        new_lines = final_lines

    # ── Sub-repair D: Sanitize brackets & normalize separators trong vivid body ──
    # Vai trò: Dọn rác ngoặc vuông [] và chuẩn hóa dấu phân cách mà NLM
    #          hallucinate do Context Window Degradation ở các chunk cuối.
    # Khi nào: Chạy SAU Sub-repair A/B/C — lúc này vivid body đã nằm ở dòng riêng.
    # Quy tắc:
    #   - BẢO VỆ sentinel [NOT_FOUND] — KHÔNG strip ngoặc trên sentinel.
    #   - vivid_circumstance: Strip [] và chuẩn hóa ' | ' (giữ pipe vì là vector 3 chiều).
    #   - vivid_insight/vivid_knowledge: Strip [] và replace '|' → ',' (ép thành 1 câu).
    # Idempotent.
    final_lines = new_lines  # Kế thừa kết quả từ Sub-repair C
    sanitized_lines = []
    i = 0
    while i < len(final_lines):
        line = final_lines[i]
        stripped = line.strip()

        # Detect vivid META tag line
        vivid_match = re.match(r'^META_\w+:\s*.*content_type=(vivid_\w+)', stripped)
        if vivid_match:
            vivid_type = vivid_match.group(1)
            sanitized_lines.append(line)
            i += 1

            # Xử lý dòng body ngay sau META tag
            if i < len(final_lines):
                body_line = final_lines[i]
                body_stripped = body_line.strip()

                # BẢO VỆ sentinel — không chạm vào [NOT_FOUND]
                if body_stripped not in ('[NOT_FOUND]', '[NO_JTBD_FOUND]'):
                    # (D1) Strip ngoặc vuông
                    body_stripped = body_stripped.replace('[', '').replace(']', '')

                    if vivid_type == 'vivid_circumstance':
                        # (D2) Chuẩn hóa pipe separator: ' | '
                        body_stripped = re.sub(r'\s*\|\s*', ' | ', body_stripped)
                    elif vivid_type in ('vivid_insight', 'vivid_knowledge'):
                        # (D3) Loại bỏ pipe — ép thành 1 câu liền mạch
                        body_stripped = body_stripped.replace(' | ', ', ')
                        body_stripped = body_stripped.replace('|', ',')

                    # Trim khoảng trắng thừa sau khi dọn
                    body_stripped = re.sub(r'\s{2,}', ' ', body_stripped).strip()
                    sanitized_lines.append(body_stripped)
                else:
                    sanitized_lines.append(body_line)
                i += 1
        else:
            sanitized_lines.append(line)
            i += 1

    return '\n'.join(sanitized_lines)


def normalize_dikw_names(content):
    """[N-DIKW] Chuẩn hóa DIKW names + Repair vivid tags trong toàn bộ file cache.

    Vai trò: (1) Làm sạch giá trị insight_name/knowledge_name đã có trong META tags.
             (2) Repair vivid tags: prepend META prefix, xuống dòng body dính, inject thiếu.
             (3) Đồng bộ tham chiếu chéo (supports_insight, supports_knowledge) trong cùng chunk.
    Khi nào: (1) Import độc lập bởi gate_checker.py — Shift-Left per-chunk.
              (2) Trong normalize_file() — SAU isolate_and_normalize_chunks, TRƯỚC whitelist_meta_fields.
              Idempotent — chạy nhiều lần cho kết quả giống nhau.
    Output: Content đã chuẩn hóa tên + vivid format chuẩn + tham chiếu chéo nhất quán.

    Tóm tắt logic:
    1. Tách content thành các <data_chunk> riêng biệt
    2. Trong mỗi chunk: tìm insight_name=, knowledge_name= → làm sạch (underscore, **, `)
    2.5 Repair vivid tags: prepend META prefix thiếu, xuống dòng body dính, inject [NOT_FOUND] nếu thiếu hoàn toàn
    3. Đồng bộ: sửa supports_insight= trong cùng chunk (bao gồm thẻ vivid mới inject)
    4. Đồng bộ: sửa supports_knowledge= trong cùng chunk (bao gồm thẻ vivid mới inject)
    """
    # Tách từng <data_chunk>...</data_chunk> để xử lý độc lập
    chunks = re.findall(r'(<data_chunk>.*?</data_chunk>)', content, re.DOTALL)
    if not chunks:
        return content

    for chunk_raw in chunks:
        chunk_new = chunk_raw

        # --- Bước 0: Strip ngoặc vuông [] khỏi ② headers ---
        # NotebookLM đôi khi wrap knowledge type: ②-1. [Khung giải pháp]: Tên...
        # Sửa thành: ②-1. Khung giải pháp: Tên...
        chunk_new = re.sub(
            r'([②③][\-—]?\s*\d+[\.\s]+)\[([^\]]+)\](\s*:)',
            r'\1\2\3',
            chunk_new
        )

        # --- Bước 1: Thu thập và làm sạch insight_name ---
        valid_insights = set()
        insight_matches = re.findall(r'insight_name=([^|\n\r]+)', chunk_new)
        for old_name in insight_matches:
            old_name_stripped = old_name.strip()
            if not old_name_stripped:
                continue
            # Làm sạch: underscore → space, strip **, *, `, whitespace
            new_name = old_name_stripped.replace('_', ' ')
            new_name = new_name.rstrip('*').strip('`').strip()
            valid_insights.add(new_name)
            
            if new_name != old_name_stripped:
                # Sửa insight_name= tại META_INSIGHT
                chunk_new = chunk_new.replace(
                    f'insight_name={old_name_stripped}',
                    f'insight_name={new_name}'
                )

        # --- Bước 2: Thu thập và làm sạch knowledge_name ---
        valid_knowledges = set()
        knowledge_matches = re.findall(r'knowledge_name=([^|\n\r]+)', chunk_new)
        for old_name in knowledge_matches:
            old_name_stripped = old_name.strip()
            if not old_name_stripped:
                continue
            new_name = old_name_stripped.replace('_', ' ')
            new_name = new_name.rstrip('*').strip('`').strip()
            valid_knowledges.add(new_name)
            
            if new_name != old_name_stripped:
                chunk_new = chunk_new.replace(
                    f'knowledge_name={old_name_stripped}',
                    f'knowledge_name={new_name}'
                )

        # --- Bước 2.5: Repair vivid tags (prepend prefix, xuống dòng, inject thiếu) ---
        chunk_new = repair_vivid_tags(chunk_new, valid_insights, valid_knowledges)

        # --- Bước 3: POKA-YOKE Phục hồi supports_insight ---
        # Sắp xếp chuỗi dài thay trước để tránh ghi đè đụng hàng
        si_matches = list(set(re.findall(r'supports_insight=([^|\n\r]+)', chunk_new)))
        si_matches.sort(key=len, reverse=True)
        for old_name in si_matches:
            old_name_stripped = old_name.strip()
            if not old_name_stripped:
                continue
            new_name = old_name_stripped.replace('_', ' ')
            new_name = new_name.rstrip('*').strip('`').strip()
            # Poka-Yoke logic: Longest Common Word Prefix
            matched_full_name, extra_text = poka_yoke_word_prefix(new_name, list(valid_insights) if valid_insights else [])
            
            if matched_full_name:
                if extra_text:
                    replacement_str = f'supports_insight={matched_full_name}\n{extra_text}'
                else:
                    replacement_str = f'supports_insight={matched_full_name}'
                    
                if replacement_str != f'supports_insight={old_name_stripped}':
                    chunk_new = chunk_new.replace(
                        f'supports_insight={old_name_stripped}',
                        replacement_str
                    )

        # --- Bước 4: POKA-YOKE Phục hồi supports_knowledge ---
        sk_matches = list(set(re.findall(r'supports_knowledge=([^|\n\r]+)', chunk_new)))
        sk_matches.sort(key=len, reverse=True)
        for old_name in sk_matches:
            old_name_stripped = old_name.strip()
            if not old_name_stripped:
                continue
            new_name = old_name_stripped.replace('_', ' ')
            new_name = new_name.rstrip('*').strip('`').strip()
            # Poka-Yoke logic: Longest Common Word Prefix
            matched_full_name, extra_text = poka_yoke_word_prefix(new_name, valid_knowledges if valid_knowledges else [])
            
            if matched_full_name:
                if extra_text:
                    replacement_str = f'supports_knowledge={matched_full_name}\n{extra_text}'
                else:
                    replacement_str = f'supports_knowledge={matched_full_name}'
                    
                if replacement_str != f'supports_knowledge={old_name_stripped}':
                    chunk_new = chunk_new.replace(
                        f'supports_knowledge={old_name_stripped}',
                        replacement_str
                    )

        # Thay thế chunk cũ bằng chunk đã sửa
        if chunk_new != chunk_raw:
            content = content.replace(chunk_raw, chunk_new)

    return content


def normalize_file(filepath):
    """Main entry point. Chạy toàn bộ pipeline normalization.

    Returns: dict {"success": bool, "whitelist_stats": dict}
        - whitelist_stats: số lượng foreign fields đã strip, VD: {"belongs_to_audience": 103}
    """
    # ── Rào chắn 1: Chỉ chấp nhận file Markdown ──
    if not filepath.endswith('.md'):
        print(f"Normalizer REJECTED: {filepath} — only .md files accepted")
        return {"success": False, "whitelist_stats": {}}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # ── Rào chắn 2: Kiểm tra đặc trưng nội dung ──
        if '<data_chunk>' not in content:
            print(f"Normalizer REJECTED: {filepath} — no <data_chunk> found (wrong file?)")
            return {"success": False, "whitelist_stats": {}}

        content = strip_ai_noise(content)                # [N0-pre] Strip thinking tags + chatbot preamble
        content = normalize_sentinels(content)            # [N0-sent] Chuẩn hóa biến thể sentinel [NOT FOUND] → [NOT_FOUND]
        content = dedup_sentinel(content)                 # [N0-sentinel] Xóa sentinel hallucinated trong data_chunk
        content = normalize_toc_chunk_names(content)     # [N0-toc] TOC-aware chunk name normalization
        content = normalize_header(content)
        content = isolate_and_normalize_chunks(content)
        content = normalize_dikw_names(content)           # [N-DIKW] Chuẩn hóa insight_name/knowledge_name + đồng bộ tham chiếu
        content, whitelist_stats = whitelist_meta_fields(content)  # [N8] Strip foreign META fields

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        total = sum(whitelist_stats.values())
        if total > 0:
            print(f"Normalizer Success: {filepath} (stripped {total} foreign fields)")
        else:
            print(f"Normalizer Success: {filepath}")
        return {"success": True, "whitelist_stats": whitelist_stats}
    except Exception as e:
        print(f"Normalizer Error {filepath}: {e}")
        return {"success": False, "whitelist_stats": {}}

if __name__ == '__main__':
    if len(sys.argv) > 1:
        normalize_file(sys.argv[1])
    else:
        print("Usage: python normalizer.py <path_to_markdown_file>")
