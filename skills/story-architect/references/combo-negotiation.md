---
Mô tả file:
- Tên file: combo-negotiation.md
- Last update: 29/06/2026 05:57 (GMT+7)
- Vai trò: Hướng dẫn xử lý khi user muốn thay đổi Combo {Pillar, Insight, Topic} đã đề xuất ở Bước 2.
- Được sử dụng khi nào?: Khi user không đồng ý với Combo và SKILL.md chuyển hướng đến file này.
- Output: Combo mới đã chốt + prompt persona-interviewer nếu có insight/topic mới.
- Tóm tắt: 3 Phase tuần tự (Pillar → Insight → Topic) + Phase 4 kết thúc. Sau khi chốt, quay lại SKILL.md tiếp tục mục 5 (Topic Resolution) của Bước 2.
---

# Xử lý thay đổi Combo

File này được gọi từ `SKILL.md` Bước 2 khi user muốn thay đổi Combo đề xuất.
Flow xử lý **tuần tự**: chốt Pillar trước → Insight sau → Topic cuối.

## Phase 1 — Chốt Pillar

User không đồng ý với Pillar đề xuất.

1. Đưa danh sách combo cho **mỗi Pillar còn lại** (chưa được đề xuất trước đó):
   - Mỗi combo gồm: 1 Pillar (name + description) + 1 Insight phù hợp nhất + 1 Topic phù hợp nhất.
   - Cách chọn Insight/Topic: giống mục 2 Bước 2 trong SKILL.md (đọc `pillars.yaml` → `insights[]` → file insight vật lý → `topics`).
2. User chọn 1 Pillar → **Pillar chốt.**
3. Tiếp theo:
   - User đồng ý luôn cả combo (Insight + Topic) → sang **Phase 4**.
   - User chỉ đồng ý Pillar, muốn đổi Insight → sang **Phase 2**.

## Phase 2 — Chốt Insight (trong Pillar đã chốt)

**Tầng 1:** Đưa **toàn bộ** insights từ `pillars.yaml` thuộc Pillar đã chốt. Mỗi insight kèm 01 topic phù hợp nhất (mở file insight vật lý → trường `topics`). User chọn 1.

**Tầng 2:** User không đồng ý bất kỳ insight nào trong danh sách → Agent đề xuất 3 insights **MỚI** dựa trên Lesson đã suy luận, mỗi insight kèm 01 topic. User chọn 1 → **Insight MỚI** (cần persona-interviewer).

**Tầng 3:** User vẫn không đồng ý → User tự đề xuất insight (hoặc lúc này user đã tự nêu rồi). Agent tiếp nhận insight do user đề xuất, kèm topic nếu user đã có. → **Insight MỚI** (cần persona-interviewer).

> **Cross-pillar:** Nếu user chọn 1 insight nhưng nói Pillar khác phù hợp hơn cho insight đó → Dùng insight đó cho story hiện tại (không chờ). **Đồng thời** đưa luôn prompt persona-interviewer để chuyển insight sang Pillar kia, kèm hướng dẫn: *"Nếu muốn chuyển insight này sang Pillar [X], dùng prompt bên dưới trong conversation mới. Nếu không cần, bỏ qua."* KHÔNG chờ xác nhận — tiếp tục ngay.

**Sau Phase 2:** Insight đã chốt.
- Nếu topic đã có (từ Tầng 1/2/3) → sang **Phase 4**.
- Nếu chưa có topic → sang **Phase 3**.

## Phase 3 — Chốt Topic (chỉ khi chưa có topic từ Phase 2)

**Tầng 1:** Đọc `topic_map.yaml` → lọc topics có `belongs_to_audience` **chứa** Big Audience wikilink (đọc `audience.yaml` → `file_ref`). Đề xuất 3 topics phù hợp nhất với story cho user chọn.

**Tầng 2:** User không chọn được topic nào → User tự đề xuất topic.
Agent chạy dedup **1 lần** (dữ liệu `topic_map.yaml` đã có trong working memory từ Tầng 1):
- Chuẩn bị: `id` = `[pN_id_moi]`, `label` = `"[label mới]"`.
- **Phạm vi:** Chỉ so khớp với topics có cùng tiền tố Pillar (`pN_`).
- **Quy luật:** MATCH nếu Synonym (từ đồng nghĩa), Paraphrase (diễn đạt khác cùng nghĩa), hoặc Reorder (đảo vị trí từ). Cross-Pillar (khác tiền tố `pN_`) = NO MATCH.
- **Nếu MATCH:** Thông báo: *"Topic này trùng ngữ nghĩa với `[topic_gốc]`. Dùng topic đó?"*
  - User OK → chốt topic gốc. Sang **Phase 4**.
  - User không OK → user sửa đề xuất → dedup lại 1 lần.
- **Nếu NO MATCH:** → **Topic MỚI** (cần persona-interviewer). Sang **Phase 4**.

## Phase 4 — Kết thúc

**Trường hợp A — Không có Insight/Topic mới:**
Quay lại SKILL.md Bước 2 mục 5 (Topic Resolution).

**Trường hợp B — Có Insight và/hoặc Topic MỚI:**
1. Agent **TẠM DỪNG** xử lý story.
2. Agent sinh prompt cho user, gồm đầy đủ:
   - Insight mới (nếu có): type, raw (nguyên văn user đã chốt), pillar key cụ thể (vd: `pillar_1`).
   - Topic mới (nếu có): id, label, pillar_parents (vd: `[pillar_1]`), belongs_to_audience (= Big Audience `file_ref` từ `audience.yaml`).
3. Hướng dẫn: *"Mở conversation mới, paste prompt bên dưới và gọi persona-interviewer thực thi. Sau khi xong, quay lại conversation này để tiếp tục."*
4. Khi user quay lại: Agent đọc file insight mới tạo trong `vault/01-Atomic/Insights/` → lấy `file_ref` chính xác → quay lại SKILL.md Bước 2 mục 5.
