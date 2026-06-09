

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

## 5. Killer Statements & Punchline
Mỗi bài BẮT BUỘC có từ **2 đến 3** "Killer Statements" hoặc "Punchline" — câu nói mạnh, đáng nhớ, chứa đựng sự thật nghịch lý (paradox) hoặc insight sắc bén, có sức sát thương cao và có thể trích dẫn riêng lẻ.
- **Marker Bắt Buộc:** Dù bạn viết Killer Statement hay Punchline, ngay sau câu đó ĐỀU PHẢI dán nhãn `<!-- PUNCHLINE -->` (dùng chung 1 thẻ) để hệ thống QA đếm số lượng.
- *Lưu ý:* Luôn kết hợp với Quy tắc Lấy đà (Setup Context) bằng Normal/Long Chain ở phía trước để câu đó phát huy tối đa uy lực (xem Section 9).
Ví dụ: "Người thành công không phải người biết nhiều, mà là người biết bỏ đúng thứ." <!-- PUNCHLINE -->

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

## 9. Chain Structure & Emotional Pacing — Nhịp câu trong đoạn
Đoạn văn (Paragraph) là một khối ý lớn được tạo bởi nhiều câu. Để bài viết không trở thành những "bức tường chữ" đơn điệu, bạn phải tạo biến thiên nhịp điệu (Rhythm) và kiểm soát nhịp cảm xúc (Emotional Pacing) bằng cách phân mảnh đoạn văn thành các "chuỗi câu" (chain) qua dấu ENTER.

### A. Phân loại Chuỗi (Chain) và Mục đích
- **Câu đơn (1 câu 1 dòng):** Là dạng chuỗi ngắn mang tính sát thương cao nhất. Dùng cho: Insights then chốt, khoảnh khắc dramatic, killer statement, Punchline x Paradox (Câu đấm chứa nghịch lý), hoặc dùng 1 nhóm câu đơn liên tiếp để tạo khoảng lặng thị giác.
  > *Quy tắc Lấy đà:* Nếu dùng làm Punchline/Paradox, BẮT BUỘC phải có Long/Normal Chain phía trước làm bệ phóng (Setup Context). Cú đấm chỉ phát huy uy lực khi có khoảng lấy đà đủ tốt.
- **Normal Chain (Chuỗi bình thường 1-2 câu):** Dùng để chuyển ý, giải thích ngắn, hoặc tạo nhịp thở (Breath) sau một chuỗi dài.
- **Long Chain (Chuỗi dài):** Đóng vai trò như đoạn trung/dài, dùng để giải thích chính, xây dựng lập luận.
- **Super Long Chain (Chuỗi siêu dài):** Chỉ dùng khi bắt buộc, giới hạn tối đa 1-2 lần/bài. 
  > *Quy tắc Nhịp thở:* Trước và sau một Super Long Chain BẮT BUỘC phải có Câu đơn hoặc Normal Chain để tạo trạm dừng lấy hơi cho người đọc.
  
  Super Long Chain chỉ hợp lệ trong 3 trường hợp sau:

| Lý do | Ví dụ | Tại sao không ngắt |
|-------|-------|---------------------|
| Chuỗi bằng chứng liền mạch | Debunk: tóm tắt báo cáo gốc 17 trang, mỗi ý dẫn đến ý tiếp | Ngắt giữa chừng → người đọc mất mạch source-vs-claim |
| Chuỗi logic A→B→C→D dài | Personal essay: tình huống → vấn đề → insight → chứng minh | Ngắt đoạn = phá vỡ flow lập luận, insight không đủ sức |
| Show-don't-tell cần nhiều chi tiết | Kể cụ thể "không biết đọc báo cáo tài chính theo thứ tự nào, chỉ số nào cần cảnh báo..." | Ngắt = mất tính cụ thể, thành tell thay vì show |

> **CẤM:** Viết chuỗi dài chỉ vì lười ngắt. Nếu trong một chuỗi dài mà mỗi câu có thể tự đứng độc lập trọn vẹn ý → BẮT BUỘC phải ngắt xuống dòng. Tránh tuyệt đối việc các chuỗi liên tiếp có độ dài bằng nhau (gây đơn điệu).

### B. Quy tắc ngắt chuỗi
TUYỆT ĐỐI KHÔNG viết liền một mạch. BẮT BUỘC bấm ENTER (xuống dòng) để tạo chuỗi. Mỗi chuỗi bình thường có 1-2 câu. Có 3-5 chuỗi dài (3-5 câu trên cùng dòng) trong toàn bài.

### C. Emotional Pacing (Nhịp Cảm Xúc)
**Vary rhythm liên tục — Không bao giờ để nhịp điệu bị đoán trước.**
Sự kết hợp giữa các Chain tạo ra đường cong cảm xúc:
- **Tăng tension:** Setup (Long Chain) → Complication (Long/Normal Chain) → Crisis (Normal Chain ngắn) → Câu dramatic (Câu đơn).
- **Giải phóng tension:** Impact (Câu đơn) → Breath (Normal Chain) → Explanation (Long Chain) → Exploration (Super Long Chain).

### D. Ví dụ Minh Họa

**Ví dụ đoạn có 10 câu, chia thành 5 chuỗi (4 + 2 + 2 + 1 + 1) — Biến thiên nhịp độ từ cao trào đến tĩnh lặng:**
```
<!-- PARAGRAPH: 10 -->
<!-- PARAGRAPH_HEADING: Huyền thoại về sự bận rộn -->
Trong văn hóa làm việc hiện đại, sự bận rộn thường bị nhầm lẫn với năng suất. Chúng ta tự hào khoe khoang về những đêm thức trắng, những ly cà phê thứ tư trong ngày và những danh sách công việc dài dằng dặc chưa bao giờ được gạch hết. Xã hội tung hô những người kiệt sức như những chiến binh, tạo ra một tiêu chuẩn độc hại rằng nếu bạn không stress, nghĩa là bạn đang lười biếng. Cảm giác lúc nào cũng phải làm một việc gì đó trở thành một cơn nghiện khó bỏ.
Nhưng sự thật là, chuyển động không đồng nghĩa với tiến lên. Phần lớn thời gian, chúng ta chỉ đang chạy tại chỗ với tốc độ tối đa.
Khi năng lượng bị cạn kiệt, não bộ chuyển sang chế độ sinh tồn và từ chối mọi tư duy sáng tạo. Những quyết định mang tính chiến lược dần bị thay thế bởi phản xạ đối phó ngắn hạn.
Sự bận rộn giả tạo chính là liều thuốc độc giết chết những đột phá thực sự.
Hãy dừng lại trước khi bạn tự thiêu rụi chính mình.
```

**Ví dụ đoạn có 8 câu, chia thành 4 chuỗi (3 + 2 + 2 + 1) — Thể hiện rõ Nhịp Cảm Xúc (Tăng Tension):**
```
<!-- PARAGRAPH: 8 -->
<!-- PARAGRAPH_HEADING: Cái bẫy của sự hoàn hảo -->
Khi một đứa trẻ luôn đạt điểm mười, người lớn thường vội vàng gắn cho chúng cái mác "thiên tài" hoặc "đứa trẻ hoàn hảo". Họ liên tục dùng những lời khen ngợi có cánh để củng cố hình tượng đó, mặc định rằng đây là cách tốt nhất để nuôi dưỡng sự tự tin. Thậm chí, những tấm giấy khen được đóng khung treo trang trọng giữa nhà như một minh chứng cho sự thành công của cả gia đình.
Nhưng ẩn đằng sau lớp vỏ bọc hào nhoáng ấy là một nỗi sợ hãi đang âm thầm lớn lên. Đứa trẻ bắt đầu tin rằng giá trị của mình chỉ tồn tại khi và chỉ khi không bao giờ mắc lỗi.
Mỗi bài kiểm tra giờ đây không còn là cơ hội để học hỏi. Chúng biến thành những phiên tòa phán xét sự tồn tại của chính mình.
Sự hoàn hảo không tạo ra thiên tài, nó tạo ra những tù nhân.
```

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

> FILE_KEY: 47dbac56
