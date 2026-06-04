

# Writing Rules — Quy tắc viết bài
# Version: v19.0

## 1. Voice DNA Application
- Dùng đúng pronoun từ `voice-dna.yaml`:
  - `voice.pronouns.self` → đại từ xưng hô bản thân (vd: tôi, mình, tui)
  - `voice.pronouns.audience` → đại từ gọi đối phương (vd: bạn, anh em, mọi người)
  - `voice.pronouns.expert_after_intro` → đại từ khi nhắc lại expert đã giới thiệu (vd: ổng, họ)
  - Sai pronoun = AUTO-FAIL.
- Rải fillers tự nhiên theo `voice.fillers.min_per_post` → `voice.fillers.max_per_post` (mặc định 3-5 lần/bài). Chọn từ `voice.fillers.library`.
- Tuyệt đối không dùng từ trong `voice.anti_patterns.banned_words`.
- Nếu `voice.parentheticals.enabled: true` → rải parentheticals theo min/max từ library.

## 2. Engagement Rules
- Tần suất engage reader theo `voice.engagement.frequency` (mặc định mỗi 2-3 câu).
- Dùng patterns từ `voice.engagement.patterns` (vd: "bạn thấy không", "thử nghĩ xem").
- `voice.engagement.max_gap`: Nếu vượt quá N câu liên tiếp không engage → QA sẽ phạt.

## 3. Story Rewriting — 5 Subtypes
Khi gặp Story atom từ vault, viết lại theo đúng subtype:

| Subtype | Ngôi kể | Cách viết | Ví dụ |
|---------|---------|----------|-------|
| **personal** | Ngôi 1 | Cảm xúc sâu, timeline cụ thể | "Năm 2019, tôi mất sạch tiền tiết kiệm..." |
| **observed** | Ngôi 3, thân mật | Giữ tên + relationship | "Thằng bạn tôi tên Minh, hồi đó nó..." |
| **secondhand** | Attribution rõ | Ghi nguồn cụ thể | "Trong cuốn Atomic Habits, James Clear kể rằng..." |
| **historical** | Ngắn gọn | Chỉ giữ chi tiết nổi bật | "Steve Jobs từng bị đuổi khỏi chính công ty mình tạo ra." |
| **famous_world** | Kể lại + nguồn | Người/tổ chức nổi tiếng thế giới + trích nguồn | "Ray Dalio kể trong cuốn Principles rằng năm 2008..." |

## 4. VTS v19.0 — Value Threading (BẮT BUỘC)
Mỗi đoạn PHẢI có ít nhất 1 value signal. Phân bổ theo section:

| Section | Value Signal Type | Ví dụ |
|---------|-------------------|-------|
| **Hook** | Value Promise | "Đọc xong bài này bạn sẽ hiểu tại sao..." |
| **Story** | Result Preview | "Và kết quả là...", "Bài học rút ra..." |
| **Deep Dive** | Pain Avoidance + Value Promise | "Nếu không biết điều này → X. Nhưng nếu biết → Y." |
| **Pivot** | Social Proof + Value Promise | "Framework này đã giúp 10,000 người..." |
| **Closing** | Result Preview / Personal Commitment | "Tôi đang đi con đường này..." |

Nếu 5 câu liên tiếp mà không có giá trị gì → Engagement Gap → sẽ bị QA phạt.

## 5. Killer Statements
Mỗi bài cần ≥ 2 "Killer Statements" — câu nói mạnh, đáng nhớ, có thể trích dẫn riêng lẻ.
Ví dụ: "Người thành công không phải người biết nhiều, mà là người biết bỏ đúng thứ."

## 6. Constraint-based Improvise (Áp chế Văn mẫu & Vivid Động)
Mọi hình ảnh ẩn dụ BẮT BUỘC tuân thủ 2 Kịch bản Bắt buộc:
- **Kịch bản 1 - Có Vivid (Nhưng bị thiếu hụt dung lượng):** AI ĐƯỢC PHÉP phóng tác (Improvise) các chi tiết vệ tinh để nới dài tình tiết từ Cành Rễ của các Neo Vivid Chính Tắc trong JSON, nhưng TUYỆT ĐỐI CẤM phát minh ra quy chiếu ẩn dụ gốc xa lạ. (Phát hiện = REVISE).
- **Kịch bản 2 - Khuyết Vivid (Payload không đủ 3 tham số):** Quyền **Phóng tác Cảm giác từ Logic (Sensory Extrapolation)** được kích hoạt: Tự phóng tác kết hợp giữa **[Bề chìm Logic]** (Ví dụ: 'cha mẹ kiệt sức') và **[Lớp vỏ Cảm giác lột tả trực diện Logic đó]** (Ví dụ: 'tiếng khóc xé tai lúc 2h sáng, đôi mắt thâm quầng'). TUYỆT ĐỐI CẤM DÙNG tu từ, so sánh hay ẩn dụ sáo rỗng (VD: cấm "như con thuyền giữa bão", "ánh sáng cuối đường hầm"). Dính văn mẫu = LỖI AUTO-REVISE.

## 7. Authority Citation — Credential Cascade
Khi nhắc expert từ `authorities.yaml`:
- Dùng `cascade` để giới thiệu thuyết phục (tên + credentials + thành tựu nổi bật).
- Đa dạng hóa cách giới thiệu theo `citation_patterns` (full_intro, soft_name_drop, achievement_first, story_based).
- Tuân thủ `diversity_rule` (không lặp expert quá 2 lần trong 5 bài).

## 8. Word Count
Mục tiêu: 1300-1800 từ. Ưu tiên chất lượng ngữ nghĩa — nếu lệch nhẹ (±10%) mà mạch văn mạch lạc, KHÔNG cắt xén hay nhồi câu vô hồn để ép số.

## 9. Chain Structure — Nhịp câu trong đoạn
Mỗi paragraph gồm 3-5 câu tổng cộng. Chia đoạn thành các "chuỗi câu" (chain) bằng cách xuống dòng (newline) trong cùng 1 đoạn. TUYỆT ĐỐI KHÔNG viết liền một mạch. BẮT BUỘC bấm ENTER (xuống dòng) để tạo chuỗi. Mỗi chuỗi bình thường có 1-2 câu. Có 3-5 chuỗi dài (3-5 câu trên cùng dòng) trong toàn bài. Chuỗi dài chỉ dùng khi cần chiều sâu cảm xúc hoặc lập luận phức tạp (thường ở Story hoặc Deep Dive).

**Ví dụ đoạn có 4 câu, chia thành 2 chuỗi (2 câu + 2 câu):**
```
<!-- PARAGRAPH: 4 -->
<!-- PARAGRAPH_HEADING: Bước ngoặt của nhận thức -->
Phần lớn phụ huynh đều mắc phải sai lầm này. Họ kỳ vọng con hành xử như một người trưởng thành thu nhỏ.
Nhưng thực tế não bộ trẻ chưa hoàn thiện. Đây là lý do mọi lập luận đều bị dội ngược.
```

**Ví dụ đoạn có 5 câu, chia thành 3 chuỗi (2 + 2 + 1):**
```
<!-- PARAGRAPH: 5 -->
<!-- PARAGRAPH_HEADING: Hai bán cầu não -->
Bán cầu não trái xử lý logic. Bán cầu não phải tiếp nhận cảm xúc.
Khi trẻ gặp cú sốc, phần não phải lấn át hoàn toàn. Mọi thông điệp răn đe đều bị đóng băng.
Đây chính là lúc kết nối quan trọng hơn kỷ luật.
```

**Ví dụ chuỗi dài — dùng tiết kiệm, có 3-5 chuỗi dài trong toàn bài:**
```
<!-- PARAGRAPH: 7 -->
<!-- PARAGRAPH_HEADING: Dàn đồng ca của tâm trí -->
Hãy hình dung tâm trí như một dàn đồng ca gồm nhiều giọng hát khác biệt — nếu mỗi người tự do cất giọng theo ý mình, thứ âm thanh tạo ra sẽ chỉ là một mớ hỗn độn. Tuy nhiên khi có người nhạc trưởng tài ba xuất hiện, những giọng hát rời rạc ấy hòa quyện thành bản giao hưởng tuyệt mỹ. Sự hội nhập chính là quá trình giúp các khu vực riêng biệt học cách làm việc cùng nhau. Khi liên kết trở nên bền chặt, trẻ nuôi dưỡng được khả năng thấu cảm tinh tế.
```

**LƯU Ý:** Xuống dòng giữa các chuỗi KHÔNG tạo đoạn mới — vẫn thuộc cùng 1 paragraph (cùng 1 ý lớn). Đoạn mới chỉ bắt đầu khi có marker `<!-- PARAGRAPH: N -->`.

> FILE_KEY: ef20d713
