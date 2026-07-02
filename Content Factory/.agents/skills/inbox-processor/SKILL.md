---
name: Inbox Processor
description: Skill xử lý và cấu trúc hóa nội dung thô thành 1 trong 5 loại Atoms (Insights, Solutions, Concepts, Quotes, Data-Points). Nhận dữ liệu đã routing từ process-inbox hoặc trực tiếp từ user. Stories do story-architect xử lý.
---

# Inbox Processor Skill

Bạn là công nhân phân loại. Hàng ngày user sẽ vứt rất nhiều ghi chú lộn xộn, cụt lủn vào thư mục `vault/00-Inbox/`. Nhiệm vụ của bạn là dọn dẹp nó.

## Hướng dẫn hoạt động

### Bước 0: Tiếp nhận Dữ liệu (Input Routing)
Tuyệt đối KHÔNG hỏi user nếu không cần thiết. Xử lý đầu vào theo các trường hợp:
1. **Được gọi ngầm từ `process-inbox`:** Nhận raw data + type đã routing (tên file giỏ = type). Chuyển thẳng đến Bước 1, **tuyệt đối không dừng lại hỏi user** làm gãy tự động hóa.
2. **User gọi trực tiếp:** Nhận text trực tiếp từ user → tự suy luận type ở Bước 1.

### Bước 1: Phân loại
Đọc file `.agents/skills/inbox-processor/references/atom-classification.md` để hiểu định nghĩa các loại. Nếu type đã được routing từ process-inbox → dùng trực tiếp. Nếu chưa → đọc nội dung, quyết định phân vào 1 (hoặc max 2) loại phù hợp nhất. Nếu mơ hồ → chọn type có DIKW cao hơn (W > K > I > D). Nếu 1 nội dung chứa nhiều loại → tách thành nhiều atoms riêng.

### Bước 1.5: Resolve Persona Path
Mỗi factory chỉ có **duy nhất 1 persona**. Quét thư mục `personas/` → lấy thư mục con duy nhất → đọc 3 file cấu hình:
- `personas/[tên-persona]/pillars.yaml` → danh sách Pillar + Insights
- `personas/[tên-persona]/audience.yaml` → `file_ref` của Big Audience (dùng cho `belongs_to_audience`)
- `personas/[tên-persona]/topic_map.yaml` → dùng khi dedup Topic ở Phase 3 Negotiation

Lưu path persona vào biến `persona_path` để dùng lại ở các Bước sau.

### Bước 2: Dedup — Kiểm tra trùng lặp
> ⚠️ **Quy tắc Vòng lặp:** Phải lặp lại toàn bộ Bước 2-3 này cho **từng mẩu nội dung** riêng biệt. Tuyệt đối không gom/trộn lẫn dữ liệu của nhiều mẩu nội dung vào chung một lần thực thi.

Quét vault kiểm tra trùng lặp theo tầng DIKW tương ứng với type đã phân loại:

- **Insight (Tầng 2):** Đọc `pillars.yaml` → lấy toàn bộ insight (`raw` + `llm_explain`) của mỗi Pillar → so sánh ngữ nghĩa nội dung mới vs danh sách insight.
- **Solution/Concept (Tầng 3):** Dùng lệnh: `powershell .agents/scripts/Search-SemanticAtom.ps1 -Keywords "[từ_khóa]" -TypeFilter "solution|concept"` → **BẮT BUỘC ĐỌC FILE TẠM** `.agents/temp/rag_results.json` để lấy Excerpt → Đánh giá ngữ nghĩa.
- **Quote/Data-Point (Tầng 4):** Dùng lệnh: `powershell .agents/scripts/Search-SemanticAtom.ps1 -Keywords "[từ_khóa]" -TypeFilter "quote|data-point"` → **BẮT BUỘC ĐỌC FILE TẠM** `.agents/temp/rag_results.json` để lấy Excerpt → Đánh giá ngữ nghĩa.

**Kết quả Dedup:**
- **Tìm thấy trùng:** Báo user: *"Nội dung này tương tự [atom X]. Bỏ qua?"* → User đồng ý → SKIP. User nói khác → tiếp Bước 3.
- **Không tìm thấy trùng:** Báo user: *"Không tìm thấy [type] tương tự."* → tiếp Bước 3.

### Bước 3: Đề xuất Combo & Negotiation (USER INTERACTION)
Agent tự phân tích nội dung → đề xuất combo đầy đủ cùng lúc cho user xác nhận.

**3.1. Chọn Combo (theo type):**

| Type | Agent tự chọn & đề xuất |
|---|---|
| **Insight** | {Pillar, Topic} — Đọc `pillars.yaml` chọn Pillar → kế thừa Topic từ insight gần nhất trong Pillar đó |
| **Solution/Concept** | Chạy lệnh `Search-SemanticAtom.ps1 -TypeFilter "insight"` → ĐỌC FILE `.agents/temp/rag_results.json` → Tự đánh giá Excerpt để đề xuất **1 HOẶC NHIỀU** Insight thực sự liên quan (Semantic Alignment) → Kế thừa Topic |
| **Quote/Data-Point** | Chạy lệnh `Search-SemanticAtom.ps1 -TypeFilter "solution|concept"` → ĐỌC FILE `.agents/temp/rag_results.json` → Tự đánh giá Excerpt để đề xuất **1 HOẶC NHIỀU** Node cha thực sự liên quan → Kế thừa Topic |

**3.2. Đề xuất cho user:**
```
Combo đề xuất:
- Pillar: [Tên Pillar]
- Insight: [file_ref]         (chỉ cho Tầng 3, 4)
- Solution/Concept: [file_ref] (chỉ cho Tầng 4)
- Topic: [topic_id]
Bạn muốn thay đổi gì không?
```

**3.3. Xử lý phản hồi user:**
- **User đồng ý:** Chốt combo → sang Bước 4.
- **User muốn thay đổi:** Áp dụng negotiation giống `combo-negotiation.md` (Bước 2 mục 4 trong `story-architect`):
  - Phase 1: Chốt Pillar (đề xuất combo cho các Pillar khác)
  - Phase 2: Chốt Insight (3 tầng escalation: insight hiện có → đề xuất mới → user tự đề xuất)
  - Phase 3: Chốt Topic (kế thừa từ insight, hoặc user tự đề xuất + dedup với `topic_map.yaml`)
  - Phase 4: Nếu có Insight/Topic MỚI → tạm dừng, sinh prompt `persona-interviewer`, user chạy conversation mới rồi quay lại
- **Tầng 4 không tìm thấy Solution/Concept phù hợp:** Escalation 3 tầng tương tự Phase 2 nhưng cho Solution/Concept. Nếu cần tạo mới → chạy Luồng 2 (tạo Solution/Concept) trước, rồi quay lại tạo Quote/Data-Point.

**3.4. Topic Resolution (sau khi Combo chốt):**
- **Primary:** Topic kế thừa từ node cha đã chốt.
- **Bổ sung:** Agent tự động thêm topic khác từ node cha nếu phù hợp (tối đa 3 topics tổng cộng).
- Lưu danh sách `topic_ids` đã chốt vào biến `resolved_topics`.

### Bước 4: Tạo Atom file theo template chuẩn
Mỗi atom tạo ra PHẢI theo format trong `.agents/skills/inbox-processor/references/atom-classification.md` → Section "Atom file (01-Atomic)".
Format 4 phần: YAML frontmatter + Nội dung + Giải thích + Liên kết.

**YAML Frontmatter cần cấy (theo tầng DIKW):**
- **Tầng 2 (Insights):** `keywords: []` + `belongs_to_audience: ["[[Big_Audience]]"]` (đọc `audience.yaml` → `file_ref`).
- **Tầng 3 (Solutions, Concepts):** `keywords: []` + `supports_insight: ["[[Tên_Insight_Đã_Chốt]]"]` + `knowledge_type` (tra bảng 8 Knowledge Type trong `atom-classification.md`).
- **Tầng 4 (Quotes, Data-Points):** `keywords: []` + `supports_knowledge: ["[[Tên_Solution_Hoặc_Concept_Đã_Chốt]]"]`.
- **Topics:** `topics: [resolved_topics]` — giá trị từ Bước 3.4.
- **Source Tagging:** `source_type: "User"`, `source_name: "Inbox Processor"` (mặc định).

**Lưu ý cho từng type:**
- **Solutions** → Phần Nội dung phải có ≥ 3 bước/thành phần.
- **Quotes** → Phải ghi rõ nguồn (speaker + context).
- **Data-Points** → Phải ghi năm và nguồn nghiên cứu.

### Bước 5: Di chuyển & Lưu
Di chuyển atom files sang `vault/01-Atomic/[Type]/`. Tất cả atoms đều dùng tiền tố `USER_`.

**Quy tắc đặt tên (Naming Convention):**

| Type | Pattern | Ví dụ |
|---|---|---|
| **Insight** | `USER_[insight-name].md` | `USER_attachment-goc-re-kho-dau.md` |
| **Solution** | `USER_[knowledge-name].md` | `USER_3-buoc-vuot-qua-bat-an.md` |
| **Concept** | `USER_[concept-name].md` | `USER_deliberate-practice.md` |
| **Quote** | `USER_[speaker]-[quote-keyword].md` | `USER_charlie-munger-invert.md` |
| **Data-Point** | `USER_[evidence-keyword].md` | `USER_harvard-stress-2019.md` |

- Slug: kebab-case, tiếng Việt không dấu, viết thường, 2-5 từ mô tả nội dung cốt lõi.

### Bước 5.5: Cập nhật Personal Atoms Queue
Sau khi atom files đã lưu, chạy script đăng ký vào hàng đợi (script tự bỏ qua nếu atom không có `source_type: "User"`):
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/scripts/Update-PersonalAtomsQueue.ps1" -Action "append" -AtomPathsRaw "[path_atom_1],[path_atom_2],..."
```
*(Truyền TẤT CẢ đường dẫn atoms vừa tạo, phân cách bằng dấu phẩy KHÔNG có khoảng trắng.)*

### Bước 6: Báo cáo
Report cho user:
- Số files đã xử lý
- Số atoms đã tạo (chia theo type)
- Danh sách files mới trong `01-Atomic/`

## Ví dụ

**Input** (nội dung nhận từ process-inbox, đã loại Story):
```
Ghi chú 1: Attachment là gốc rễ của khổ đau — khi ta bám víu, ta tạo ra kỳ vọng, kỳ vọng tạo ra thất vọng.
Ghi chú 2: Theo nghiên cứu Harvard 2019, 73% stress đến từ việc bám víu vào quá khứ.
```

**Output** (2 atoms tạo ra):
1. `01-Atomic/Insights/USER_attachment-root-of-suffering.md` (type: insight)
2. `01-Atomic/Data-Points/USER_harvard-stress-2019.md` (type: data-point)
