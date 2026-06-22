---
name: Voice Writer
description: Skill Phase 5 â€” Viáº¿t bÃ i hoÃ n chá»‰nh dá»±a trÃªn Voice DNA, tiÃªm atoms theo DIKW, Ã¡p dá»¥ng Anti-AI scan.
last_update: 24/05/2026 14:30 (GMT+7)
required_inputs:
  - OUTLINE_SECTIONS         # from 04-outline.md (Phase 4)
  - CLOSING_COMBO            # from 04-outline.md (Phase 4)
  - PERSONA_DNA              # from 04.5-persona-pack.md (Phase 4.5)
  - EVIDENCE_LIST            # from 02-research-brief.md (Phase 2)
  - STORY_LIST               # from 02-research-brief.md (Phase 2)
  - dikw_combo               # 00.5-dikw-combo.md
provided_outputs:
  - DRAFT_SECTIONS
---

# Voice Writer (Phase 5)

> EXECUTION_KEY:

## Äiá»u kiá»‡n Äáº§u vÃ o
> **PAYLOAD:** Dá»¯ kiá»‡n tá»« cÃ¡c phase trÆ°á»›c Ä‘Ã£ Ä‘Æ°á»£c biÃªn dá»‹ch sáºµn trong `.temp/payload.md` (run folder). Äá»c file nÃ y Ä‘á»ƒ láº¥y input tá»« phase trÆ°á»›c. CÃ¡c file khÃ¡c (persona, references, logs) váº«n Ä‘á»c trá»±c tiáº¿p theo hÆ°á»›ng dáº«n bÃªn dÆ°á»›i.

1. **`Outline 5 pháº§n`** (Phase 4)
2. **`Persona Pack`** (Phase 4.5 â€” Ä‘Ã£ cÃ³ trong context)
3. **`Atomic Combo`** (Stories, Insight, Solutions, Concepts... tá»« BÆ°á»›c 5 cá»§a workflow)
4. **`Minified JSON Vivid Payload`** (tá»« BÆ°á»›c 5 cá»§a workflow)

## HÆ°á»›ng dáº«n hoáº¡t Ä‘á»™ng

### BÆ°á»›c 1: Äá»c tham chiáº¿u Báº®T BUá»˜C
DÃ¹ng tool `view_file` Ä‘á»c láº§n lÆ°á»£t 5 file:
- `.agents/skills/voice-writer/references/writing-rules.md`
- `.agents/skills/voice-writer/references/anti-ai-rules.md`
- `.agents/skills/voice-writer/references/english-rules.md`
- `.agents/skills/voice-writer/references/typography-and-format.md`
- `.agents/skills/voice-writer/references/metaphor.md`

> â›” **FATAL RULE:** PHáº¢I dÃ¹ng tool Ä‘á»c thÃ nh cÃ´ng toÃ n bá»™ 5 file. File Not Found â†’ Dá»ªNG, BÃO USER. Cáº¥m hallucinate ná»™i dung.

Sau khi Ä‘á»c má»—i file, ghi nháº­n giÃ¡ trá»‹ `FILE_KEY` á»Ÿ dÃ²ng cuá»‘i file Ä‘Ã³.

Sau khi hoÃ n thÃ nh toÃ n bá»™ ná»™i dung `05-draft.md`, append vÃ o **cuá»‘i file** dÃ²ng:
```
<!-- ref_keys: writing-rules=[key1], anti-ai-rules=[key2], english-rules=[key3], typography-and-format=[key4], metaphor=[key5] -->
```
Thay [key1]...[key5] báº±ng Ä‘Ãºng giÃ¡ trá»‹ FILE_KEY Ä‘Ã£ Ä‘á»c tá»« má»—i file.

### BÆ°á»›c 2: Nháº­n input
TrÃ­ch xuáº¥t dá»¯ liá»‡u tá»« Global Context theo Äiá»u kiá»‡n Äáº§u vÃ o.
- Náº¿u Payload cÃ³ khá»‘i `connection` (`IDEA_CONNECTION`) mang thÃ´ng tin liÃªn káº¿t, hÃ£y Äá»ŒC HIá»‚U Báº£n cháº¥t Má»‘i ná»‘i Logic vÃ  sá»­ dá»¥ng thÃ´ng tin nÃ y linh hoáº¡t á»Ÿ pháº§n Má»Ÿ bÃ i hoáº·c Chuyá»ƒn Ã½ Ä‘á»ƒ nháº¯c nhá»› Ä‘á»™c giáº£ vá» bÃ i trÆ°á»›c Ä‘Ã³, táº¡o máº¡ch liá»n máº¡ch cho kÃªnh. Náº¿u cÃ³ nhiá»u bÃ¡o cÃ¡o liÃªn káº¿t, hÃ£y tá»± do lá»±a chá»n 1 má»‘i ná»‘i phÃ¹ há»£p nháº¥t.
**Báº®T BUá»˜C**: DÃ¹ng tool `view_file` Ä‘á»c file `00.5-dikw-combo.md` trong run folder Ä‘á»ƒ láº¥y dá»¯ liá»‡u thÃ´ cá»§a cÃ¡c Atoms vÃ  trÃ­ch xuáº¥t mÃ£ `BUNDLE_KEY` á»Ÿ cuá»‘i file.

### BÆ°á»›c 3: Viáº¿t bÃ i section-by-section

> â›” **TUYá»†T Äá»I KHÃ”NG viáº¿t toÃ n bá»™ 1300-1800 tá»« trong 1 lÆ°á»£t.**

**3.0 â€” Word Budget:**
Äá»c word count tá»« Outline (Phase 4). Náº¿u khÃ´ng cÃ³, dÃ¹ng máº·c Ä‘á»‹nh:

| Section | Tá»« |
|---------|-----|
| Hook | 100 |
| Story | 250 |
| Deep Dive | 800 |
| Pivot | 250 |
| Closing | 150 |

**3.0.1 â€” Hook Adaptation:**
Core Hook trong outline lÃ  nguyÃªn liá»‡u thÃ´ tá»« Hook Engineer â€” KHÃ”NG pháº£i text cuá»‘i cÃ¹ng. Khi viáº¿t section Hook, PHáº¢I:
1. Äá»c `Hook Intent` vÃ  `Core Hook` tá»« outline
2. Viáº¿t láº¡i cÃ¢u hook báº±ng Voice DNA (pronoun, filler, tone, sentence rhythm), giá»¯ nguyÃªn Hook Intent vÃ  Formula
3. Cáº¤M copy nguyÃªn vÄƒn Core Hook vÃ o draft

**3.1 â€” Viáº¿t tá»«ng section:**
Viáº¿t láº§n lÆ°á»£t 5 sections. TOÃ€N Bá»˜ ná»™i dung bÃ i viáº¿t (tá»« dÃ²ng `<!-- TITLE: ... -->` Ä‘áº¿n háº¿t Closing) Báº®T BUá»˜C bá»c trong `<!-- [BLOCK: DRAFT_SECTIONS] -->...<!-- [/BLOCK: DRAFT_SECTIONS] -->`. Má»—i section:
- BÃ¡m sÃ¡t outline, náº±m trong word budget
- Ghi vÃ o `05-draft.md` trong run folder (section 1: overwrite, section 2-5: append). LUÃ”N viáº¿t Ä‘áº§y Ä‘á»§ structural markers (dáº¡ng HTML comment). Táº¥t cáº£ marker KHÃ”NG Ä‘Æ°á»£c Ä‘áº¿m vÃ o word count.

**Markers báº¯t buá»™c:**
- DÃ²ng Ä‘áº§u tiÃªn: `<!-- TITLE: [TiÃªu Ä‘á» bÃ i viáº¿t] -->`
- DÃ²ng cuá»‘i cÃ¹ng cá»§a file 05-draft.md (sau khi káº¿t thÃºc Closing vÃ  ghi cÃ¡c ref_keys): `<!-- bundle_key: [MÃ£ trÃ­ch xuáº¥t tá»« 00.5-dikw-combo.md] -->`
- TrÆ°á»›c má»—i section: `<!-- SECTION: [TÃªn section] -->` (Hook/Story/Deep Dive/Pivot/Closing)
- Sau SECTION marker: `<!-- SECTION_HEADING: [Heading section â€” AI tá»± Ä‘áº·t] -->`
- TrÆ°á»›c má»—i Ä‘oáº¡n: `<!-- PARAGRAPH: [Sá»‘ thá»© tá»± Ä‘oáº¡n â€” Ä‘Ã¡nh sá»‘ liÃªn tá»¥c 1â†’N trÃªn toÃ n bÃ i] -->`
- Sau PARAGRAPH marker: `<!-- PARAGRAPH_HEADING: [Heading Ä‘oáº¡n â€” AI tá»± Ä‘áº·t] -->`
- Káº¿t thÃºc má»—i section (trá»« section cuá»‘i): marker `â‚` trÃªn 1 dÃ²ng riÃªng, cÃ¡ch dÃ²ng trÃªn 1 dÃ²ng trá»‘ng, cÃ¡ch dÃ²ng dÆ°á»›i 1 dÃ²ng trá»‘ng
- TrÆ°á»›c khi viáº¿t section tiáº¿p, Ä‘á»c láº¡i section vá»«a viáº¿t Ä‘á»ƒ Ä‘áº£m báº£o transition tá»± nhiÃªn

**3.2 â€” Kiá»ƒm tra toÃ n bÃ i:**
Äá»c láº¡i `05-draft.md` â†’ kiá»ƒm tra transitions + tá»•ng word count (má»¥c tiÃªu: 1300-1800 tá»«, Æ°u tiÃªn ngá»¯ nghÄ©a hÆ¡n con sá»‘ tuyá»‡t Ä‘á»‘i).

**Constraints Ã¡p dá»¥ng cho Má»–I section:**

| Constraint | Quy táº¯c |
|------------|---------|
| **Voice DNA** (AUTO-FAIL) | ÄÃºng pronoun tá»« `voice-dna.yaml`. Ráº£i fillers 3-5 láº§n/bÃ i. KhÃ´ng dÃ¹ng `banned_words`. Ãp dá»¥ng `sentence_rhythm`, `analogy_style`, `closing_style`, `humor_style` |
| **JTBD PhÃ¢n RÃ£** (AUTO-FAIL) | KhÃ´ng ghÃ©p chuá»—i tÄ©nh 3 tham sá»‘ JTBD â€” xem báº£ng biáº¿n thiÃªn bÃªn dÆ°á»›i. Vi pháº¡m â†’ REVISE toÃ n Ä‘oáº¡n |
| **Atom Injection** | Story â†’ viáº¿t láº¡i theo subtype (xem writing-rules.md Section 3). Solution/Concept â†’ KCS credibility intro. KhÃ´ng cÃ³ atom â†’ bá» qua, KHÃ”NG Bá»ŠA |
| **VTS v19.0** | Má»—i Ä‘oáº¡n PHáº¢I cÃ³ value signal. PhÃ¢n bá»• theo section â€” xem writing-rules.md Section 4. Gap > 5 cÃ¢u = bá»‹ QA pháº¡t |
| **SAS v18.2** (AUTO-FAIL) | CHá»ˆ dÃ¹ng stories tá»« Vault (verified) HOáº¶C ngÆ°á»i/tá»• chá»©c ná»•i tiáº¿ng tháº¿ giá»›i. Vault trá»‘ng â†’ famous world stories + ghi nguá»“n. KhÃ´ng story phÃ¹ há»£p â†’ viáº¿t báº±ng data/research. KHÃ”NG Bá»ŠA |
| **KCS** | Má»i Solution/Concept PHáº¢I cÃ³ â‰¥1: Ai táº¡o + credential / Ai dÃ¹ng thÃ nh cÃ´ng + káº¿t quáº£ / Bao nhiÃªu ngÆ°á»i Ã¡p dá»¥ng |
| **Authority Citation** | Ãp dá»¥ng Credential Cascade theo writing-rules.md Section 7. Äa dáº¡ng cÃ¡ch giá»›i thiá»‡u expert |
| **Vivid Extrapolation** | TuÃ¢n thá»§ 2 ká»‹ch báº£n táº¡i writing-rules.md Section 6. Báº®T BUá»˜C Ã¡p dá»¥ng 1 trong 3 cáº¥u trÃºc áº©n dá»¥ (Extended, Compounding, Loop) tá»« metaphor.md náº¿u cÃ³ yáº¿u tá»‘ áº©n dá»¥. Cáº¥m áº©n dá»¥ sÃ¡o rá»—ng |
| **Anti-AI** | QuÃ©t 10 patterns + blacklist + AI detection. Äáº·c biá»‡t: Cáº¥m AI Labels (Key, Note, Summary). Cáº¥m láº¡m dá»¥ng tá»« ná»‘i (>3 láº§n/bÃ i). Cáº¥m trá»™n tiáº¿ng Anh. |
| **Killer Statements** | â‰¥ 2 cÃ¢u kháº³ng Ä‘á»‹nh máº¡nh, Ä‘Ã¡ng nhá»› má»—i bÃ i |
| **Paragraph** | 8-10 cÃ¢u/paragraph. KhÃ´ng viáº¿t paragraph 1 cÃ¢u (trá»« Hook cÃ¢u Ä‘áº§u tiÃªn). KhÃ´ng viáº¿t paragraph > 10 cÃ¢u. LÆ¯U Ã: Äoáº¡n má»›i CHá»ˆ báº¯t Ä‘áº§u khi cÃ³ marker `<!-- PARAGRAPH: N -->`. |
| **Chain** | Báº®T BUá»˜C báº¥m ENTER (xuá»‘ng dÃ²ng) Ä‘á»ƒ ngáº¯t cÃ¢u thÃ nh cÃ¡c chuá»—i 1-2 cÃ¢u/dÃ²ng. CÃ³ 3-5 chuá»—i dÃ i (3-5 cÃ¢u/dÃ²ng) toÃ n bÃ i. Xem writing-rules.md Section 9 |
| **Prose & Punc** (AUTO-FAIL) | KhÃ´ng dÃ¹ng Title Case (H2+ viáº¿t hoa chá»¯ Ä‘áº§u). KhÃ´ng dáº¥u hai cháº¥m trong tiÃªu Ä‘á». Dáº¥u cÃ¢u sÃ¡t tá»« trÆ°á»›c, cÃ¡ch tá»« sau. Cáº¥m em-dash `â€”` (Ä‘á»•i sang tá»« ná»‘i hoáº·c ` - `). Cáº¥m Oxford comma `, vÃ `. Cáº¥m Bullet trong thÃ¢n vÄƒn xuÃ´i. Äá»™ dÃ i Ä‘oáº¡n vÄƒn pháº£i biáº¿n thiÃªn, trÃ¡nh cÃ¡c Ä‘oáº¡n liÃªn tiáº¿p cÃ³ sá»‘ cÃ¢u báº±ng nhau. |

**Báº£ng biáº¿n thiÃªn JTBD (Deconstructed):**

| Biáº¿n | Cáº¥m | Pháº£i |
|------|-----|------|
| `audience_Job_performer` | GhÃ©p nguyÃªn chuá»—i | Biáº¿n thiÃªn: "bá»‘ máº¹", "phá»¥ huynh", "chÃºng ta"... |
| `audience_main_job` | GhÃ©p nguyÃªn chuá»—i | Biáº¿n thiÃªn Ä‘á»™ng tá»«: "thiáº¿t láº­p náº¿p", "táº­p tá»± ngá»§"... |
| `audience_circumstance` | GhÃ©p nguyÃªn chuá»—i | Biáº¿n thiÃªn tráº¡ng tá»«: "giai Ä‘oáº¡n nÃ y", "Ä‘á»‘i vá»›i Ä‘á»™ tuá»•i sÆ¡ sinh"... |

### BÆ°á»›c 4: Scripted Validation
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/voice-writer/scripts/validate-draft.ps1" -DraftPath "[ÄÆ°á»ng dáº«n file Draft]"
```
Script kiá»ƒm tra 10 chá»‰ sá»‘ objective. Náº¿u FAIL â†’ **sá»­a ngay** trÆ°á»›c khi tiáº¿p tá»¥c.

### BÆ°á»›c 5: Self-Check Gate

> â›” **KHÃ”NG ÄÆ¯á»¢C Bá»Ž QUA.** Kiá»ƒm soÃ¡t cháº¥t lÆ°á»£ng cuá»‘i cÃ¹ng trÆ°á»›c Phase 6.

**Äiá»u kiá»‡n tiÃªn quyáº¿t:** Script validation BÆ°á»›c 4 PHáº¢I Ä‘áº¡t `ALL OBJECTIVE CHECKS PASSED`.

**TiÃªu chÃ­ kiá»ƒm tra:**

| Check | TiÃªu chÃ­ | Rollback |
|-------|----------|----------|
| Voice DNA | 100% pronoun/filler/tone compliance | â†’ REVISE, quay BÆ°á»›c 3 |
| Anti-AI | Zero AI signatures (10 patterns) | â†’ REVISE, quay BÆ°á»›c 3 |
| Vivid | Neo cháº·t JSON Vivid gá»‘c hoáº·c phÃ³ng tÃ¡c 5 giÃ¡c quan. TuÃ¢n thá»§ 3 cáº¥u trÃºc áº©n dá»¥ tá»« metaphor.md (Extended, Compounding, Loop). Cáº¥m áº©n dá»¥ sÃ¡o rá»—ng | â†’ REVISE, quay BÆ°á»›c 3 |
| Engagement | KhÃ´ng gap > 5 cÃ¢u liÃªn tiáº¿p khÃ´ng value signal | â†’ REVISE, quay BÆ°á»›c 3 |
| Killer Statements | â‰¥ 2 cÃ¢u máº¡nh, Ä‘Ã¡ng nhá»› | â†’ REVISE, quay BÆ°á»›c 3 |
| Atom Integrity | No fabricated atoms, all verified | â†’ REVISE, quay BÆ°á»›c 3 |
| SAS v18.2 | Má»i story trace back: â‘  vault, â‘¡ famous person/org + nguá»“n, â‘¢ published book + tÃ¡c giáº£. Bá»‹a = AUTO-FAIL | â†’ FAIL, escalate User |
| KCS v18.2 | Má»i Solution/Concept cÃ³ credibility intro (origin/achievement/scale) | â†’ REVISE, quay BÆ°á»›c 3 thÃªm credibility intro |
| JTBD | KhÃ´ng chá»©a chuá»—i tÄ©nh JTBD | â†’ REVISE, quay BÆ°á»›c 3 |
| VN Standards | ÄÃºng chuáº©n viáº¿t hoa (H2+), khÃ´ng trá»™n tiáº¿ng Anh, Prose format (khÃ´ng bullet), Punctuation chuáº©n | â†’ REVISE, quay BÆ°á»›c 3 |

**Verdict:**
- **PASS** â†’ Chuyá»ƒn Phase 6.
- **REVISE** â†’ Ghi issues vÃ o `output/runs/[run-folder]/gate5-issues.md` â†’ Revision Mode. Max 3 retry.
- **FAIL** (SAS violation) â†’ Dá»«ng pipeline, escalate User.

**Ghi log:** `[Phase 5 Self-Check] Verdict: PASS/REVISE/FAIL | Attempt: N/3`

### BÆ°á»›c 6: Issue Tracking (khi REVISE)
Ghi vÃ o `output/runs/[run-folder]/gate5-issues.md`:
```yaml
## Round N
- id: ISSUE_NAME
  location: "paragraph X, cÃ¢u Y-Z"
  criteria: "TiÃªu chÃ­ vi pháº¡m"
  severity: HIGH/MEDIUM
  status: OPEN
```

### BÆ°á»›c 7: Revision Mode (khi cÃ³ issues OPEN)
1. Äá»c `gate5-issues.md` â†’ lá»c `status: OPEN`.
2. Vá»›i má»—i issue: Ä‘á»c location â†’ tÃ¬m vá»‹ trÃ­ trong `05-draft.md` â†’ sá»­a theo criteria.
3. Ghi Ä‘Ã¨ `05-draft.md`. **KHÃ”NG viáº¿t láº¡i toÃ n bá»™ draft** â€” chá»‰ sá»­a Ä‘Ãºng vá»‹ trÃ­ issue.
4. Cháº¡y láº¡i `validate-draft.ps1`.
5. Quay BÆ°á»›c 5 verify: Fix â†’ `VERIFIED` âœ… / ChÆ°a fix â†’ `OPEN` âŒ
6. Táº¥t cáº£ VERIFIED â†’ PASS. CÃ²n OPEN â†’ thÃªm round (max 3).
