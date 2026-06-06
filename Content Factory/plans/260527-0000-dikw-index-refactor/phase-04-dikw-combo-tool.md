---
name: phase-04-dikw-combo-tool.md
last_update: 27/05/2026 00:00 (GMT+7)
role: Implementation Phase
usage: Hướng dẫn thực thi Phase 4 — Tạo Get-DIKWCombo tool
output: Script Get-DIKWCombo.ps1 thay thế logic Bước 1-4 của dikw-bridge
logic: Đọc index, áp dụng Pre-Filter + Bước 2-4 filter/scoring, output combo + vivid + jtbd
---

# Phase 04: Get-DIKWCombo Tool

**Trạng thái:** ⬜ Pending
**Nhóm BRIEF:** A (A3)
**Dependencies:** Phase 3 (cần `build-vault-index.ps1` và `vault_index.json` schema)

---

## Task 4.1: Tạo script `Get-DIKWCombo.ps1`

**File mới:** `.agents/skills/dikw-bridge/scripts/Get-DIKWCombo.ps1`

**Mô tả:**
- Tên file: Get-DIKWCombo.ps1
- Vai trò: Tool chuẩn thay thế logic duyệt graph ad-hoc của Agent
- Sử dụng khi: Được gọi bởi dikw-bridge SKILL.md (Bước mới thay thế Bước 1-4)
- Output: Bảng Combo + Vivid Payload JSON + resolved_jtbd (stdout)
- Logic: Rebuild index → Pre-Filter → Bước 2-4 filter/score → Output

**Tham số:**

| Param | Type | Required | Mô tả |
|---|---|---|---|
| `-Topics` | string/array | Có | Topic IDs từ Blackboard (chấp nhận cả single string lẫn array) |
| `-Audience` | string/array | Có | Target Audience ID(s) |
| `-TargetSourceIds` | string[] | Không | Mảng source_id để Pre-Filter (VD: `@("good-inside")`) |
| `-PersonaUser` | string | Có | Tên user (VD: "Neal") — dùng cho path Nguồn 2-4 |
| `-VaultPath` | string | Không | Mặc định `vault/01-Atomic/` |
| `-ProductionLog` | string | Không | Mặc định `output/logs/production-log.md` |

**Logic chi tiết (phải khớp 1:1 với `dikw-bridge/SKILL.md`):**

```
PHASE 0: REBUILD INDEX
1. Gọi build-vault-index.ps1 -VaultPath $VaultPath -OutputPath ".agents/skills/dikw-bridge/vault_index.json"
2. Đọc vault_index.json vào biến $index

PHASE 1: POKA-YOKE FILTERS (áp dụng trước mọi logic)
3. Loại nodes có confidence < 0.5
4. Loại nodes có status = "rejected" hoặc "quarantine"

PHASE 2: SMART GLOBAL PRE-FILTER
5. IF $TargetSourceIds có phần tử:
   - Loại tất cả nodes trong 01-Atomic/ có source_id KHÔNG nằm trong $TargetSourceIds
   - KHÔNG áp dụng filter này cho Nguồn 2-4 (Zero-breakage Rule)
   ELSE: Bỏ qua pre-filter

PHASE 3: LỌC NHÁNH CHÍNH (Bước 2)
6. Normalize $Topics: nếu string → chuyển thành array 1 phần tử
7. Lọc Insights: topics có overlap với $Topics AND audience match
   - audience match: strip [[]] rồi so sánh
   - $Audience là string → so sánh trực tiếp
   - $Audience là array → khớp bất kỳ phần tử nào
8. Insights thỏa mãn → Anchors (đưa vào Rổ)

PHASE 4: LỌC NHÁNH RỄ (Bước 3)
9. Tầng 3: Solutions/Concepts có edges.supports_insight trỏ vào 1 trong các Anchors
10. Tầng 4: Stories/Quotes/Data-Points có edges.supports_knowledge trỏ vào 1 trong Tầng 3
11. Orphan Purge: Drop atoms thiếu link hoặc link trỏ ra ngoài Rổ

PHASE 5: ANTI-REPETITION (Bước 3)
12. Đọc $ProductionLog → trích atom paths từ 3 bài post gần nhất
13. Loại atoms đã dùng khỏi Rổ

PHASE 6: ANCHOR-FIRST SELECTION (Bước 4)
14. Relevance = topic_overlap_count × dikw_weight
    - dikw_weight: Stories=10, Insights/Solutions=7, Concepts=3, Quotes/Data-Points=1
15. Phase A: Score Insights, sort DESC. Tiebreaker: nhiều downstream atoms → alphabet filename
16. Phase B: FOR each Insight (score cao → thấp):
    a. Tìm Solutions/Concepts trỏ về → Score → top 1
    b. Tìm Stories trỏ về Solution/Concept → Score
    c. Tìm Data-Points/Quotes trỏ về Solution/Concept → Score
    d. (Data-Points + Quotes) < 1 → skip, thử Insight tiếp
    e. VIABLE → BREAK
17. Phase C: Stories top 1-2 (score DESC, ưu tiên subtype: personal=15, observed=12, secondhand=8, famous_world=7, historical=5)
18. Data-Points/Quotes top 3-5 (score DESC)

PHASE 7: NGUỒN 2-4 (dự phòng — files markdown thô, KHÔNG có DIKW frontmatter)
19. Quét vault/[PersonaUser]/Viral Posts/*.md:
    - Nếu có file .md → đọc toàn bộ content làm Story body
    - Gán mặc định: type="story", confidence=0.9, topics=[], source_id=null
    - Thêm vào Rổ Stories (không cần topic match — đây là nội dung user viết)
20. Quét vault/[PersonaUser]/Posted/*.md → tương tự, confidence=0.8
21. Quét vault/Content/Reflective Writing.md → tương tự, confidence=0.6
22. KHÔNG áp dụng TargetSourceIds filter cho Nguồn 2-4 (Zero-breakage Rule)
23. Nguồn 2-4 hiện ĐANG RỖNG (chưa có file). Script phải xử lý gracefully (không crash nếu thư mục không tồn tại hoặc rỗng)

PHASE 8: OUTPUT
23. Bảng Combo: Atom path | DIKW Layer | Weight | Relevance Score | Node Trỏ
    ⚠ Path format: tương đối từ CWD, VD: vault/01-Atomic/Stories/GI_story.md
24. Vivid Payload: Quét frontmatter atoms trong Combo → gộp vivid_circumstances + vivid_insights + vivid_knowledges → Minified JSON
25. Audience Resolution (nếu $Audience là array):
    - Lấy audience ID từ belongs_to_audience của Anchor Insight
    - Đọc vault/01-Atomic/Audiences/[audience-ID].md
    - Trích: audience_Job_performer, audience_main_job, audience_circumstance
    → Output resolved_jtbd block
```

**⚠️ CWD Constraint:** Phải chạy từ `Content Factory/`

---

## Task 4.2: Tạo file test data cho unit testing

**File mới:** `.agents/skills/dikw-bridge/scripts/test-dikw-combo.ps1`

**Mục tiêu:** Script chạy Get-DIKWCombo với params thực tế để kiểm tra output.

**Test cases:**

1. **Có TargetSourceIds:**
```powershell
.\Get-DIKWCombo.ps1 -Topics "dieu_hoa_cam_xuc" -Audience "cha-me_ap-dung-chien-luoc-khoa-hoc-than-kinh-dieu-chinh-cam-xuc_khi-doi-mat-khung-hoang-nuoi-day-con" -TargetSourceIds @("good-inside") -PersonaUser "Neal"
```
→ Chỉ trả về GI_ atoms.

2. **Không có TargetSourceIds (viết tự do):**
```powershell
.\Get-DIKWCombo.ps1 -Topics "dieu_hoa_cam_xuc" -Audience "cha-me_ap-dung-chien-luoc-khoa-hoc-than-kinh-dieu-chinh-cam-xuc_khi-doi-mat-khung-hoang-nuoi-day-con" -PersonaUser "Neal"
```
→ Trả về atoms từ MỌI nguồn có topic match.

3. **Audience là array:**
```powershell
.\Get-DIKWCombo.ps1 -Topics "dieu_hoa_cam_xuc" -Audience @("aud1", "aud2") -PersonaUser "Neal"
```
→ resolved_jtbd được output.

**Kiểm tra:**
- Output có đúng 3 phần (Bảng Combo, Vivid JSON, resolved_jtbd).
- Path format tương đối `vault/01-Atomic/...`.
- Combo có đủ: 1 Insight + 1 Solution/Concept + 1-2 Stories + 3-5 Data/Quotes.
- Atoms đã dùng trong production-log.md không xuất hiện trong kết quả.

---

## Task 4.3: Đăng ký tool trong `injection-rules.md`

**File:** `.agents/skills/dikw-bridge/references/injection-rules.md`

**Thay đổi:** Thêm section cuối file:

```markdown
## 4. Tool Interface

Toàn bộ logic Bước 1-4 được đóng gói trong script:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/dikw-bridge/scripts/Get-DIKWCombo.ps1" -Topics "[topic]" -Audience "[audience]" -PersonaUser "[user]" [-TargetSourceIds @("source1")]
```
```

**Kiểm tra:** injection-rules.md không bị conflict với nội dung hiện có.

---

**Hoàn thành Phase 4 → Chuyển sang Phase 5.**
