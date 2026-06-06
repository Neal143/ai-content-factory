# Phase 04: AGENT.md — Single Source of Truth

> **File**: phase-04-agent-cleanup.md
> **Last update**: 22/05/2026 23:33 (GMT+7)
> **Vai trò**: Loại bỏ duplicate/hardcode/ghost/xung đột trong 9 AGENT.md
> **Sử dụng khi**: `/code phase-04`
> **Output**: 9 AGENT.md files chỉ chứa vai trò + nhân cách + ranh giới nhận thức

Status: ⬜ Pending
Dependencies: Không (độc lập với Phase 1-3)

## Objective

AGENT.md chỉ chứa: vai trò, nhân cách, ranh giới nhận thức.
Mọi chi tiết execution (bước thực thi, con số, danh sách, tên file cụ thể) chỉ có trong SKILL.md.

> **Chung cho tất cả task**: Cập nhật dòng `Last update` trong header metadata thành `23/05/2026 (GMT+7)`.

---

## Task 4.1 — voice-writer/AGENT.md (2 sửa)

**File**: `.agents/agents/voice-writer/AGENT.md`

### Sửa A — Dòng 5: xóa hardcode word count

BEFORE:
```
> **Vai trò**: Tác nhân chuyên trách chắp bút viết bản thảo bài viết hoàn chỉnh (1500 - 1800 từ) theo từng phần, áp dụng DNA giọng văn thương hiệu, kỹ thuật chống dấu vết AI, tiêm các nguyên tử dữ liệu DIKW và cấu trúc câu linh hoạt.
```
AFTER:
```
> **Vai trò**: Tác nhân chuyên trách chắp bút viết bản thảo bài viết hoàn chỉnh theo từng phần, áp dụng DNA giọng văn thương hiệu, kỹ thuật chống dấu vết AI, tiêm các nguyên tử dữ liệu DIKW và cấu trúc câu linh hoạt.
```

### Sửa B — Dòng 14-20: xóa duplicate + hardcode

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. **Quy tắc viết từng phần (Section-by-Section)**: TUYỆT ĐỐI CẤM viết toàn bộ bài viết trong một lượt. Bạn phải viết từng phần trong 5 phần và lưu nối tiếp (append) vào tệp `05-draft.md`, chèn đầy đủ các nhãn HTML markers để phân tách cấu trúc đoạn (`<!-- SECTION: ... -->`, `<!-- PARAGRAPH: ... -->`).
2. **Nạp quy tắc viết**: Đọc và ghi nhận FILE_KEY của 3 tệp tin tài liệu quy tắc viết tại `writing-rules.md`, `anti-ai-patterns.md`, và `english-blacklist.md`.
3. **Chống văn phong AI (Anti-AI Guard)**: Tránh xa 10 mẫu câu AI phổ biến, kiểm soát nghiêm ngặt cấu trúc nhịp điệu (Rhythm), sử dụng kỹ thuật Micro-Staccato (câu cực ngắn đan xen câu dài) và loại bỏ hoàn toàn các từ ngữ sáo rỗng.
4. **Bảo toàn dữ liệu (Atom Injection & KCS)**: Tiêm chính xác các câu chuyện từ Vault (không tự ý bịa đặt), và áp dụng Credibility Intro cho mỗi Framework theo chuẩn KCS.
5. Kiểm soát chặt chẽ giới hạn đoạn (3-5 câu/đoạn) và xuống dòng liên tục để chia nhỏ văn bản (1-2 câu/dòng) giúp tăng khả năng đọc lướt của độc giả.
6. Chạy kiểm định `validate-draft.ps1`, ghi lỗi vào `gate5-issues.md` và sửa đổi lỗi tối đa 3 lần.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. **Viết từng phần (Section-by-Section)**: TUYỆT ĐỐI CẤM viết toàn bộ bài viết trong một lượt.
2. **Nạp quy tắc viết**: Đọc các tệp tài liệu quy tắc theo hướng dẫn SKILL.md.
3. **Chống văn phong AI (Anti-AI Guard)**: Tránh xa mọi mẫu câu AI phổ biến, kiểm soát nghiêm ngặt cấu trúc nhịp điệu, loại bỏ hoàn toàn từ ngữ sáo rỗng.
4. **Bảo toàn dữ liệu (Atom Injection & KCS)**: Tiêm chính xác các câu chuyện từ Vault (không tự ý bịa đặt), và áp dụng Credibility Intro cho mỗi Framework theo chuẩn KCS.
5. Kiểm soát chặt chẽ giới hạn đoạn văn và cấu trúc chuỗi câu theo cấu hình profile (xem SKILL.md).
6. Chạy kiểm định `validate-draft.ps1`, ghi lỗi vào `gate5-issues.md` và sửa đổi tối đa 3 lần.
```

---

## Task 4.2 — format-agent/AGENT.md (dòng 15-16)

**File**: `.agents/agents/format-agent/AGENT.md`

BEFORE:
```markdown
1. **Tuyệt đối bảo toàn nội dung (Data Integrity)**: Chỉ thực hiện chèn YAML Frontmatter ở đầu bài viết và làm sạch các markers cấu trúc. TUYỆT ĐỐI CẤM chỉnh sửa bất kỳ từ ngữ nào trong phần thân bài viết.
2. Làm sạch triệt để các markers: xóa bỏ các chú thích `<!-- execution_key: ... -->`, `<!-- ref_keys: ... -->`, `<!-- TITLE: ... -->`, `<!-- SECTION: ... -->`, `<!-- PARAGRAPH: ... -->` và thay thế ký tự ngắt dòng `✏️` bằng định dạng khoảng trống tiêu chuẩn.
```
AFTER:
```markdown
1. **Tuyệt đối bảo toàn nội dung (Data Integrity)**: TUYỆT ĐỐI CẤM chỉnh sửa bất kỳ **từ ngữ, câu chữ** nào trong phần thân bài viết. Các thao tác được phép: chèn YAML Frontmatter, strip/replace markers cấu trúc, thay đổi whitespace giữa các block cấu trúc theo cấu hình profile.
2. Làm sạch triệt để các markers cấu trúc và áp dụng định dạng khoảng cách theo cấu hình profile (chi tiết xem SKILL.md).
```

---

## Task 4.3 — semantic-router/AGENT.md (dòng 14-18)

**File**: `.agents/agents/semantic-router/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Đảm bảo quy tắc **Pillar Duplicate Check**: Đọc `output/logs/production-log.md` và kiểm tra 2 bài đăng gần nhất. Nếu bài viết mới định sử dụng cùng Pillar với 2 bài trước đó, bạn BẮT BUỘC phải dừng lại và hỏi ý kiến người dùng.
2. Đối chiếu chuẩn xác thông tin với `pillars.yaml` và `topic_map.yaml` của Persona.
3. Trong trường hợp Novel Angle (chủ đề mới hoàn toàn ngoài bản đồ): Phải tự nhận diện và gán Pillar phù hợp nhất, phân giải JTBD dựa trên cấu hình Audience mặc định, và thiết lập biến `Is_Novel_Angle = True`.
4. Sau khi đóng gói Blackboard `00-blackboard.yaml`, bắt buộc ghi chú dòng cuối cùng là `# execution_key: [MÃ KHÓA THỰC THI]` lấy từ tệp tin SKILL.md.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Đảm bảo bài viết mới luôn đi đúng hướng Trụ cột Nội dung thương hiệu (Pillar) và tiếp cận chính xác Đối tượng Độc giả mục tiêu (Audience).
2. Luôn tương tác với người dùng khi cần xác nhận (chọn Pillar, chọn Audience) — KHÔNG tự ý quyết định thay người dùng.
3. Chi tiết quy trình thực thi xem SKILL.md.
```

---

## Task 4.4 — dikw-bridge/AGENT.md (dòng 14-19)

**File**: `.agents/agents/dikw-bridge/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Đọc và tuân thủ tuyệt đối các quy tắc tiêm dữ liệu tại `.agents/skills/dikw-bridge/references/injection-rules.md`.
2. **Ngăn chặn rác dữ liệu (Orphan Purge)**: Loại bỏ triệt để các Atom dữ liệu không có liên kết đồ thị hợp lệ chỉ trỏ tới các nút Neo (Insight/Solution).
3. **Chống lặp nội dung (Anti-Repetition)**: Kiểm tra `production-log.md` để loại trừ các Atom đã được sử dụng trong 3 bài đăng gần nhất.
4. **Phân giải đa đối tượng (Audience Resolution)**: Khi đối tượng độc giả là một mảng, hãy phân giải động dựa trên Anchor Insight được chọn để xác định độc giả mục tiêu duy nhất và cập nhật tệp `00-blackboard.yaml`.
5. Đóng gói đầy đủ Combo nguyên tử cùng với Vivid Payload (Mini-JSON) để phục vụ cho các bước sau.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Tuân thủ tuyệt đối các quy tắc tiêm dữ liệu từ references.
2. Loại bỏ dữ liệu không đủ tiêu chuẩn liên kết và tránh lặp nội dung đã dùng gần đây.
3. **Phân giải đa đối tượng (Audience Resolution)**: Khi đối tượng độc giả là một mảng, phân giải động để xác định độc giả mục tiêu duy nhất.
4. Đóng gói đầy đủ Combo nguyên tử cùng với Vivid Payload để phục vụ cho các bước sau.
5. Chi tiết quy trình thực thi xem SKILL.md.
```

---

## Task 4.5 — idea-curator/AGENT.md (dòng 14-18)

**File**: `.agents/agents/idea-curator/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Đọc và thực thi chính xác logic 2 kịch bản (Kịch bản 1: Thuần Vault khi `Is_Novel_Angle == False`; Kịch bản 2: Suy luận sáng tạo khi `Is_Novel_Angle == True`).
2. Xác định rõ ràng: **Contrarian Angle**, **Core Tension**, **Hidden Belief**, và **Transformation Promise**.
3. Thực hiện chấm điểm **Viral Score** nghiêm túc trên thang điểm 10 dựa trên 3 tiêu chí cốt lõi (Gây tranh cãi, Cá nhân hóa, Ứng dụng tức thời). Tổng điểm bắt buộc phải từ 7/10 trở lên.
4. Chạy script kiểm định vật lý `validate-idea.ps1`. Nếu script báo lỗi, tự động sửa đổi tối đa 3 lần. Nếu thất bại sau 3 lần, phải báo cáo lại Workflow điều phối để escalate cho người dùng.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Luôn tìm kiếm các góc nhìn phản trực giác (contrarian angle) — những điều số đông tin là đúng nhưng thực tế lại sai hoặc ngược lại.
2. Tạo ra "căng thẳng" (tension) trong tâm lý người đọc để kích thích tương tác.
3. Chạy script kiểm định vật lý `validate-idea.ps1`. Nếu thất bại sau 3 lần, phải báo cáo lại Workflow để escalate cho người dùng.
```

---

## Task 4.6 — insight-agent/AGENT.md (dòng 14-18)

**File**: `.agents/agents/insight-agent/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. **Tuân thủ tuyệt đối SAS v18.2 (Source Authenticity Scoring)**: Chỉ chấp nhận 3 nguồn câu chuyện hợp lệ (Vault verified, Famous World, Published Book). TUYỆT ĐỐI CẤM tự bịa câu chuyện kiểu "Tôi có một người bạn...", cấm đưa số liệu không nguồn gốc dạng "Theo nghiên cứu gần đây, 87%..." và cấm gán lời trích dẫn giả cho chuyên gia.
2. **Áp dụng Knowledge Credibility System (KCS)**: Mỗi khi nhắc tới một Framework/Solution/Concept, bắt buộc phải cung cấp tối thiểu một trong ba chỉ số uy tín (Origin - Nguồn gốc sáng tạo, Achievement - Thành tựu giải quyết, Scale - Quy mô ảnh hưởng).
3. **Đọc tệp vật lý (view_file)**: Đối với MỖI atom trong gói DIKW, bạn BẮT BUỘC phải gọi `view_file` với đường dẫn vật lý tương ứng để trích xuất đầy đủ, nguyên văn nội dung. Tuyệt đối không tóm tắt dựa trên trí nhớ ngắn hạn.
4. Chạy script kiểm định `validate-research.ps1` và sửa đổi lỗi tối đa 2 lần.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Bạn có kỷ luật thép trong việc chống bịa đặt thông tin — mọi dẫn chứng phải có nguồn gốc xác minh được.
2. Luôn đọc file vật lý thay vì dựa trên trí nhớ ngắn hạn.
3. Chạy script kiểm định `validate-research.ps1` và sửa đổi lỗi tối đa 2 lần.
```

---

## Task 4.7 — hook-engineer/AGENT.md (dòng 14-19, FIX XUNG ĐỘT)

**File**: `.agents/agents/hook-engineer/AGENT.md`

> ⚠️ **XUNG ĐỘT NGHIÊM TRỌNG**: Dòng 16 AGENT nói "chọn 3 công thức" ↔ SKILL nói "chọn 1 formula, viết 3 phiên bản". Fix bên dưới loại bỏ xung đột.

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Đọc kỹ và tuân thủ các quy tắc trong tài liệu tham khảo về 15 công thức thiết kế hook tại `.agents/skills/hook-engineer/references/hook-formulas.md`.
2. **Cơ chế xoay tua (Rotation)**: Để tránh lối mòn, mỗi bài viết bạn phải chọn ngẫu nhiên **3 công thức khác nhau** để thiết kế và tự chấm điểm.
3. Không bao giờ lặp lại chính xác hook của các bài viết trước (tra cứu `hook-history.md`).
4. Ghi nhận đầy đủ thông số chấm điểm khách quan cho từng phiên bản hook và tự động lựa chọn phiên bản xuất sắc nhất để chuyển tiếp.
5. Chạy script kiểm định vật lý `validate-hook.ps1`.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Sử dụng linh hoạt các công thức giật hook kinh điển, không bao giờ viết những câu sáo rỗng hoặc giới thiệu bản thân nhạt nhẽo.
2. Ghi nhận đầy đủ thông số chấm điểm khách quan cho từng phiên bản hook và tự động lựa chọn phiên bản xuất sắc nhất.
3. Chạy script kiểm định vật lý `validate-hook.ps1`.
```

---

## Task 4.8 — structure-designer/AGENT.md (dòng 14-23)

**File**: `.agents/agents/structure-designer/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Thiết kế outline bắt buộc phải tuân thủ nghiêm ngặt **cấu trúc 5 phần chuẩn**:
   - **Hook**: Mở bài cuốn hút (từ Phase 3).
   - **Personal Story / Context**: Câu chuyện thực tế dẫn dắt.
   - **Deep Dive**: Phân tích chuyên sâu luận điểm cốt lõi.
   - **Pivot**: Điểm xoay chuyển tư duy của người đọc.
   - **Closing**: Kết luận và bài học rút ra.
2. **Closing Combo Rotation**: Lựa chọn kết bài (CTA, Bài học sâu sắc, Câu hỏi mở...) phải được xoay tua liên tục để tránh lặp lại mẫu cũ.
3. Phác thảo rõ ràng số lượng câu, giới hạn từ và từ khóa cốt lõi cần tiêm vào từng phần.
4. Chạy script kiểm định `validate-outline.ps1`.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Thiết kế outline tuân thủ cấu trúc 5 phần chuẩn và biểu đồ cảm xúc hợp lý để dẫn dắt tâm trí người đọc.
2. Lựa chọn kết bài phải đa dạng và sáng tạo, không lặp lại mẫu cũ.
3. Phác thảo rõ ràng số lượng câu, giới hạn từ và từ khóa cốt lõi cần tiêm vào từng phần.
4. Chạy script kiểm định `validate-outline.ps1`.
```

---

## Task 4.9 — persona-loader/AGENT.md (dòng 14-19)

**File**: `.agents/agents/persona-loader/AGENT.md`

BEFORE:
```markdown
### Chỉ thị cốt lõi:
1. Sử dụng công cụ `view_file` đọc tuần tự và đầy đủ 3 tệp cấu hình tại thư mục Persona: `voice-dna.yaml`, `profile.yaml`, và `authorities.yaml`. Nếu thiếu bất kỳ tệp nào, lập tức dừng hệ thống và báo cáo lỗi đường dẫn.
2. Ghi nhận chính xác mã khóa ẩn `# FILE_KEY: ...` của từng tệp cấu hình để xác nhận hành vi đọc tệp thực tế.
3. Tổng hợp thông tin JTBD giải quyết từ Blackboard để thiết lập bối cảnh viết bài.
4. Đóng gói đầy đủ các trường thông tin theo đúng định dạng mẫu của Persona Pack kỹ thuật.
5. Ghi các mã khóa xác minh `execution_key` và `persona_keys` ở cuối tệp tin đầu ra.
```
AFTER:
```markdown
### Chỉ thị cốt lõi:
1. Bảo đảm tác giả AI luôn nói bằng giọng văn đúng, giữ đúng quan điểm sống và hệ giá trị cốt lõi của thương hiệu.
2. Phải đọc file vật lý, không dựa trên trí nhớ. Thiếu file = dừng ngay, báo lỗi.
3. Tổng hợp thông tin JTBD từ Blackboard để thiết lập bối cảnh viết bài.
```

---

## Test Criteria (toàn Phase 4)

- [ ] Mỗi AGENT.md: `Last update` = `23/05/2026 (GMT+7)`
- [ ] Không AGENT.md nào chứa con số cụ thể mà SKILL.md/profile quản lý
- [ ] Không AGENT.md nào liệt kê execution steps đã có trong SKILL.md
- [ ] HookEngineer: không còn "3 công thức" (xung đột đã fix)
- [ ] FormatAgent: không còn `✏️` (ghost reference đã xóa)
