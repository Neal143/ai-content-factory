## ScoreInsight
### Bước 4: Anchor-First Selection (Chọn Combo Deterministic)

> Relevance = `topic_overlap_count` × `dikw_weight` (từ `injection-rules.md`).
> Loại atom có confidence < 0.5 hoặc status = "rejected"/"quarantine".

**Phase A — Chọn Anchor Insight:**
1. Score từng Insight trong Rổ. Sort DESC.
2. Tiebreaker ngang điểm: Insight có nhiều downstream atoms (Solutions/Concepts trỏ về) thắng. Vẫn ngang → alphabet filename.

## CheckViability
**Phase B — Kiểm tra Viability (top-down):**
3. FOR each Insight (score cao → thấp):
   a. Tìm Solutions/Concepts có `supports_insight` → Insight này. Không có → **skip**.
   b. Score Solutions/Concepts → chọn top 1.
   c. Tìm Stories có `supports_knowledge` → Solution/Concept đã chọn.
   d. Tìm Data-Points/Quotes có `supports_knowledge` → Solution/Concept đã chọn.
   e. Nếu (Data-Points + Quotes) < 1 → **skip**, thử Insight tiếp.
   f. **VIABLE** → chốt Anchor. BREAK.

## FillCombo
**Phase C — Lấp slot Combo:**
5. Stories: top 1-2 (score DESC, ưu tiên subtype theo `injection-rules.md`).
6. Data-Points/Quotes: top 3-5 (score DESC).
