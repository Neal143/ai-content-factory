# Prompt: Build Job Map (Step Sequence) cho Audience System

> Copy toàn bộ nội dung dưới đây vào conversation mới.

---

## Yêu cầu

Tôi cần build tính năng **Job Map** cho hệ thống Audience trong AI Content Factory. Tính năng này phát hiện và ghi nhận **mối quan hệ step sequence** giữa các audience đồng cấp (siblings) để phục vụ **content strategy theo journey**.

## Bối cảnh lý thuyết (JTBD - Jobs To Be Done)

Trong framework JTBD, một job có thể phân rã thành các **job steps** (job map). Ví dụ:

```
Little Job: "Thiết lập thói quen ngủ cho con"
  ├─ Step 1 (Micro): "Bổ sung đủ chất cho con ngủ tốt"
  ├─ Step 2 (Micro): "Xây dựng nhịp điệu ngủ cho con"
  ├─ Step 3 (Micro): "Xây dựng môi trường ngủ cho con"
  └─ Step 4 (Micro): "Lựa chọn công cụ hỗ trợ con vào giấc"
```

Các step này hiện đã tồn tại dưới dạng **audience files riêng biệt** trong vault, nhưng hệ thống chưa ghi nhận mối quan hệ **thứ tự** giữa chúng. Chúng chỉ đang là siblings (cùng `parent_audience`), chưa có thông tin nào thể hiện "step 1 → step 2 → step 3".

## Mục đích downstream

Thông tin step sequence sẽ phục vụ:
1. **Content strategy theo journey**: Tạo content series theo thứ tự step (bài 1 → bài 2 → bài 3) dẫn dắt audience qua từng giai đoạn.
2. **Content gap analysis**: Phát hiện step nào chưa có đủ Insights/Solutions.
3. **Editorial calendar**: Lên lịch content theo flow tự nhiên của job process.

## Hệ thống hiện tại

### Cấu trúc audience
- **File audience `.md`**: Nằm tại `vault/01-Atomic/Audiences/`. Mỗi file có YAML frontmatter gồm: `audience_level` (big/little/micro), `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `parent_audience` (wikilink), `aliases`, `vivid_circumstances`.
- **Index**: `vault/01-Atomic/Audiences/_audience_index.yaml` — Single Source of Truth cho toàn bộ audiences.
- **Cấu trúc cây**: Big → Little → Micro qua trường `parent_audience`.

### Files quan trọng cần đọc
- `vault/01-Atomic/Audiences/_audience_index.yaml` — Cấu trúc cây hiện tại
- `vault/01-Atomic/Audiences/*.md` — Ví dụ cấu trúc file audience
- `.agents/agents/vault-curator/AGENT.md` — Agent điều phối curation
- `.agents/scripts/prepare_curation_batches.py` — Batch management cho skills
- `.agents/scripts/cascade_merge.py` — Script cascade update (sẽ tồn tại sau khi chạy plan dedup trước đó)

### Constraint
- **Local-first**: Không dùng external API. Dùng LLM local (Gemini qua IDE).
- **Schema change phải backward-compatible**: Trường mới trong frontmatter không được break Dataview queries hiện tại.
- **Audience < 50**: Sau dedup, tổng audiences < 50 entries → batch nhỏ, có thể xử lý trong 1-2 passes.

## Scope yêu cầu

1. **Schema design**: Thiết kế trường mới (ví dụ: `step_of`, `step_order`, hoặc cách khác) trong audience frontmatter + index để thể hiện job step sequence. Đảm bảo backward-compatible.
2. **Taxonomy Management**: Ngoài step sequence, LLM cần có khả năng phát hiện quan hệ cha-con bị sai/thiếu (reparenting) giữa các audiences đang là đồng cấp, và đưa ra quyết định `reparent` (đổi `parent_audience` thay vì gộp).
3. **Detection**: Phương pháp phát hiện step sequence và quan hệ reparent — LLM evaluation trong batch pass (tương tự flow dedup hiện có).
4. **Cascade update**: Script/logic cập nhật trường mới và `parent_audience` vào file `.md` + `_audience_index.yaml` khi có quyết định.
5. **Tích hợp**: Tích hợp vào VaultCuratorAgent hoặc skill hiện có (hoặc tạo skill riêng nếu cần).

## Lưu ý
- Tạo implementation plan dưới dạng artifact.
- Plan đã có convention: Phase (Script → Skill → Integration) + Tasks chi tiết ở cuối.
- Đọc kỹ các file liên quan trước khi thiết kế — hệ thống có nhiều convention cần tuân thủ.
