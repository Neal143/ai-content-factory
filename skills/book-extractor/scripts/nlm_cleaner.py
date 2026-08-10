"""
nlm_cleaner.py
==============
Ten file: nlm_cleaner.py
Last update: 09/08/2026 22:37 (GMT+7)
Vai tro: Shared utility - Clean NLM hallucination artifacts tu raw output.
Duoc su dung khi: gate_checker.py (Auto-Repair) va append_cache.py (safety net).
Output: Text da clean.
Logic:
  - clean_single_char_repeats: Strip ky tu don lap (loai 1).
    Case 1: Dong chi chua ky tu don lap → xoa ca dong.
    Case 2: Ky tu don lap o cuoi/giua cau → xoa cum, giu nguyen context.
"""

import re


def clean_single_char_repeats(text):
    """Strip ky tu don Latin vo nghia dung giua 2 whitespace.
    Buoc 1: Xoa moi ky tu don (tru I, a, A) dung giua 2 whitespace.
    Buoc 2: Collapse multiple spaces thanh 1 space.
    Vi du: 'abc h h h h xyz' → 'abc xyz'
           'abc s s s sưởi' → 'abc sưởi'
    """
    # Buoc 1: Xoa ky tu don giua whitespace (lookbehind/lookahead khong tieu thu)
    # Loai tru I (dai tu tieng Anh), a/A (mao tu tieng Anh)
    text = re.sub(r'(?<=\s)(?![IaA])[a-zA-Z](?=\s)', '', text)

    # Buoc 2: Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)

    # Don blank lines thua
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text
