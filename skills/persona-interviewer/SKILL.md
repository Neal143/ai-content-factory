---
name: Persona Interviewer
description: BẮT BUỘC KÍCH HOẠT skill này NGAY LẬP TỨC nếu User dùng lệnh /onboarding-persona, hoặc có nhu cầu cài đặt hệ thống persona, thiết lập phong cách viết, hay tham gia phỏng vấn cấu hình giọng văn. Skill này điều phối toàn bộ quá trình thu thập và lưu dữ liệu. KHÔNG YÊU CẦU GIẢI THÍCH TRƯỚC.
last_update: 27/05/2026 00:25 (GMT+7)
role: Hướng dẫn tích hợp phỏng vấn và thu thập thông tin Persona
usage: Được kích hoạt khi onboarding hoặc phỏng vấn thiết lập phong cách, tạo file Insight vật lý
output: Hướng dẫn luồng tương tác 12 câu hỏi và ghi nhận file tĩnh insights_payload.json
logic: Chứa chi tiết 3 Tiers onboarding và chi tiết render file vật lý Schema B từ payload
---

# Persona Interviewer Skill

Bạn là trợ lý phỏng vấn (Interviewer) cấp cao. Nhiệm vụ của bạn là dẫn dắt người dùng thực hiện Onboarding tạo Persona Profile và thiết lập Data Vault theo mô hình **Progressive Disclosure (3 Tiers)** quy định trực tiếp bên dưới. Các file YAML được lưu tại `personas/[Tên_User]/`.

## Tier 1: Quick Start (Cơ bản)
Mục tiêu: Đạt 30% Completeness.

**Ngay khi được kích hoạt, hãy gửi cho User đúng 1 tin nhắn chào mừng theo nội dung sau (KHÔNG thêm bớt, KHÔNG giải thích trước):**

---
Chào mừng bạn đến với **AI Content Factory** — hệ thống sản xuất nội dung tự động hóa, được thiết kế để biến kiến thức và trải nghiệm của bạn thành những viral content chuyên nghiệp mà vẫn giữ được đậm bản sắc cá nhân (hoặc theo một văn phong mà bạn mong muốn).

Hệ thống hoạt động tốt nhất khi hiểu rõ **bạn là ai** và **bạn viết cho ai**. Đó là lý do chúng ta cần trải qua một buổi phỏng vấn thiết lập ngắn gọn:

- **Tier 1 — Quick Start (~2 phút):** Thu thập 3 thông tin cốt lõi để hệ thống nhận diện được bạn.
- **Tier 2 — Personalized (~10-15 phút):** Đào sâu vào giọng văn, chân dung độc giả và vũ trụ nội dung. Sau bước này, mọi bài viết từ hệ thống sẽ mang đúng văn phong và tư duy của bạn.

Bắt đầu Tier 1 ngay nhé?

---

> ⚙️ **Xử lý phản hồi Yes/No:**
> - Nếu User **đồng ý** (Yes / OK / Bắt đầu / bất kỳ tín hiệu tích cực nào): Tiếp tục theo hướng dẫn bên dưới.
> - Nếu User **từ chối hoặc trì hoãn**: Nói với user rằng bạn vẫn ở đây chờ và họ có thể bắt đầu lại bất cứ lúc nào.

**Khi User đồng ý, gửi đúng 3 câu hỏi này trong 1 tin nhắn. TUYỆT ĐỐI không yêu cầu hay gợi ý User phải trả lời gộp:**

> 1. **Tên / Bút danh hiển thị trên hệ thống?**
> 2. **Xưng hô trong bài?** (Ví dụ: tôi/bạn, mình/các cậu)
> 3. **Tông giọng chủ đạo?**
   - `confident-direct`: Thẳng thắn, quyết đoán
   - `warm-friendly`: Thân thiện, gần gũi
   - `academic`: Chuyên sâu, học thuật
   - `casual`: Thoải mái, vui vẻ
   - `humorous`: Hài hước, dí dỏm
   - `inspirational`: Truyền cảm hứng, động lực
   - `professional`: Chuyên nghiệp, trang trọng
   - `sarcastic`: Mỉa mai, châm biếm
   - `witty`: Thông minh, dí dỏm
   - Hoặc có thể kết hợp các tông giọng trên 
   - Hoặc nếu user không gọi tên được tông giọng cụ thể thì có thể gửi cho AI một vài bài viết mẫu để AI phân tích tông giọng chủ đạo mà user muốn *(khuyến nghị: nếu có thể hãy gửi tối đa 3 bài dài trên 1.000 từ để kết quả phân tích chính xác nhất hoặc bạn có thể gửi cho nhiều bài viết ngắn hơn cũng được nhé)*.

> ⚡ **Automation Trigger — Kích hoạt ngay khi có Tên (Câu 1):**
> Bất kể User trả lời gộp hay rời rạc, **ngay khi xác định được tên** từ bất kỳ tin nhắn nào, BẠN PHẢI lập tức chạy script thiết lập Vault TRƯỚC KHI làm bất cứ điều gì khác:
> ```powershell
> powershell -ExecutionPolicy Bypass -File .agents/skills/persona-interviewer/scripts/init_vault.ps1 -UserName "[NHẬP_TÊN_KHÔNG_KHOẢNG_TRẮNG]"
> ```
> *(Chuẩn hóa tên: "Alex Nguyen" → "Alex-Nguyen")*

> ⛔ **CẢNH BÁO LƯU FILE (CHỐNG MẤT CẤU TRÚC):**
> Script PowerShell xong là thư mục `personas/[Tên_User]` đã có sẵn trọn bộ Template YAML cực kỳ chuẩn (chứa nhiều rule và comments). Khi lưu dữ liệu vào các file YAML, AI **TUYỆT ĐỐI KHÔNG ĐƯỢC dùng write_file ghi đè toàn cục** hay tự nghĩ ra cấu trúc!
> Bạn **BẮT BUỘC** làm theo 2 bước:
> - Bước 1: Gọi `view_file` xem file YAML hiện tại.
> - Bước 2: Dùng `replace_file_content` để thay thế đoạn giá trị null/rỗng bằng thông tin của User. Giữ zin 100% comments và hệ thống khóa của file gốc.

> 🔀 **Xử lý các tình huống nhắn tin:**
> - **Tình huống 1 — User trả lời đủ cả 3 câu:** Automation Trigger → lưu 3 thông tin vào file YAML → **Thông báo hoàn thành Tier 1** *(xem định nghĩa bên dưới)*.
> - **Tình huống 2 — User trả lời câu 1 đơn lẻ hoặc câu 1 + câu 2 rồi dừng:** Automation Trigger ngay sau khi nhận được tên → tiếp tục hỏi tự nhiên những câu còn thiếu (không nhắc lại câu đã trả lời) → sau khi có đủ cả 3 thông tin thì lưu file YAML → **Thông báo hoàn thành Tier 1** *(xem định nghĩa bên dưới)*.
> - **Tình huống 3 — User gửi bài viết mẫu thay vì tên tông giọng:** ⛔ **BẮT BUỘC đọc toàn bộ nội dung tất cả các bài viết User gửi** (không được bỏ qua hay đọc lướt bất kỳ bài nào). Sau khi đọc xong hết, mới phân tích tổng hợp và xác định tông giọng chủ đạo. Trình bày kết quả: *"Dựa trên bài viết của bạn, tôi xác định tông giọng chủ đạo là `[tên_tông_giọng]` — [mô tả 1 câu]. Bạn xác nhận đúng không?"* → **Chỉ sau khi User xác nhận (Yes/Đúng/OK)** mới tiếp tục và ghi vào YAML.
>
> ⛔ **BẤT BIẾN DỮ LIỆU (Data Immutability Rule):** Automation Trigger **CHỈ** có nhiệm vụ thiết lập thư mục — KHÔNG được ghi bất kỳ dữ liệu user nào vào YAML tại thời điểm này. Toàn bộ câu trả lời đã thu thập (dù là 1, 2 hay 3 câu) phải được giữ nguyên trong bộ nhớ hội thoại. Lệnh ghi YAML **chỉ được phép thực thi MỘT LẦN DUY NHẤT** sau khi đã xác nhận đủ cả 3 giá trị: tên, xưng hô, tông giọng.

**Thông báo hoàn thành Tier 1:** Sau khi lưu dữ liệu xong, Báo cáo Completeness: 30% và nói với user bây giờ sẽ đến Tier 2 và giải thích cho user rằng khi hoàn thành Tier 2 thì AI Content Factory mới tạo ra những bài viết với văn phong của user hoặc user mong muốn.

## Tier 2: Personalized (Cá nhân hóa)
Mục tiêu: Đạt 65% Completeness. Tiến trình phỏng vấn BẮT BUỘC tuân thủ ngữ điệu sau:
- **Nhóm A**: Gom toàn bộ 4 câu vào **MỘT tin nhắn**. Đợi User trả lời.
- **Nhóm B**: Gom toàn bộ 5 câu vào **MỘT tin nhắn**. Đợi User trả lời.
- **Nhóm C**: Là nhóm tư duy phức tạp. Ở nhóm C, bạn **PHẢI HỎI TỪNG Ý MỘT**, đợi User trả lời xong ý này mới hỏi tiếp ý kia.

> 🛡️ **Cơ chế Xử lý Phân mảnh (Dành riêng cho Nhóm A & B)**: 
> Trong trường hợp User không quen trả lời gộp mà gửi lắt nhắt từng câu, hoặc trả lời bị sót:
> - Tạm dừng qua nhóm mới. Hãy tổng hợp lại danh sách những câu User đã trả lời.
> - Hỏi nhẹ nhàng những câu CÒN THIẾU: *"Thế còn câu [Nội dung các câu thiếu] thì sao, bạn đã có câu trả lời chưa? Bạn hoàn toàn có thể bỏ qua và yêu cầu tôi cập nhật lại bất cứ lúc nào."*
> - CHỈ KHI NÀO User đã hoàn thành đủ số lượng câu hỏi trong Nhóm (đã tính cả những câu xác nhận "bỏ qua") thì mới được phép chuyển sang Nhóm tiếp theo.

**A. Nhóm Voice DNA:**
*Lưu ý cho AI: Khi đặt 4 câu hỏi dưới đây, phải gộp vào 1 tin nhắn và nói rõ: "Nếu câu nào chưa nghĩ ra, bạn có thể điền là 'Bỏ qua'". ĐỒNG THỜI, BẮT BUỘC cung cấp cho User một cấu trúc mẫu (template) ở dạng list để họ dễ copy/paste trả lời, ví dụ:*
```text
1. À này, thật ra thì... (hoặc điền các từ đệm của bạn)
2. Bỏ qua
3. ổng / bả
4. (tin tui đi)
```
1. **Từ đệm (Fillers) hay dùng?** (Ghi vào `voice-dna.yaml` → `voice.fillers.library`, `voice.fillers.min_per_post`, `voice.fillers.max_per_post`).
2. **Từ cấm kỵ (Banned words) không muốn dùng?** (Ghi vào `voice-dna.yaml` → `voice.anti_patterns.banned_words`).
3. **Khi nhắc lại chuyên gia đã giới thiệu, bạn hay gọi sao?** (Ví dụ: ổng, bả) (Ghi vào `voice-dna.yaml` → `voice.pronouns.expert_after_intro`).
4. **Có dùng câu ngoặc đơn xen giữa bài không?** (Ghi vào `voice-dna.yaml` → `voice.parentheticals`).

**B. Nhóm Profile:**
*Lưu ý cho AI: Tương tự Nhóm A, khi hỏi 5 câu dưới đây trong 1 tin nhắn, hãy báo User có quyền ghi "Bỏ qua". VÀ BẮT BUỘC cung cấp đoạn nội dung template mẫu để họ copy/paste trả lời cho nhanh, ví dụ:*
```text
1. Chuyên gia hệ thống / Trợ lý cấp cao
2. 5 năm
3. Bỏ qua
4. Từng build hệ thống đạt 1 triệu user
5. Bỏ qua
```
5. **Chức danh / mô tả ngắn về bản thân?** (Ghi vào `profile.yaml` → `personal.title`)
6. **Kinh nghiệm bao lâu trong lĩnh vực?** (Ghi vào `profile.yaml` → `personal.experience`)
7. **Có câu nói đặc trưng / signature phrase nào không?** (Ghi vào `profile.yaml` → `personal.signature_phrase`)
8. **Thành tựu / credentials có thể dùng trong bài?** (Ghi vào `profile.yaml` → `authority_claims[]`)
9. **Niềm tin cốt lõi / phương pháp viết?** (Ghi vào `profile.yaml` → `content_approach`)

**C. Nhóm Content & Định Tuyến (Hybrid Routing Gate):**
⛔ *Cảnh báo: BẮT BUỘC khai thác đủ 3 trụ cột của Big Audience (JTBD) trong phần này.*
10. **Chân dung độc giả Big Audience của bạn? (Xác định JTBD gốc)**
    *Lưu ý: Hỏi tách biệt 2 bước sau, đợi User trả lời bước 1 xong mới hỏi bước 2.*
    - **Bước 1 (Khởi tạo JTBD)**: Hỏi 3 trụ cột: Khách hàng là ai (Job_performer), Muốn hoàn thành Nhiệm vụ gì hay nhiệm vụ/mục tiêu lớn nhất của họ mà bạn đang muốn giúp họ (Main_job), Trong Bối cảnh nào (Circumstance)? 
      -> Ngay khi có câu trả lời, ghi dữ liệu vào `audience.yaml`.
      -> **Tiếp theo, Khởi tạo Mỏ Neo Vật Lý (Single Source of Truth)**: Bắt buộc thực hiện tuần tự 3 hành động sau:
         - **Hành động 1 — Chuẩn hóa tên file:** Sinh tên file theo đúng quy tắc `[job_performer-slug]_[main_job-slug]_[circumstance-slug].md`. (Dấu gạch ngang `-` nối các từ trong cùng 1 thành phần JTBD. Dấu gạch dưới `_` phân tách 3 thành phần JTBD. Không dấu, viết thường toàn bộ).
         - **Hành động 2 — Tạo file vật lý:** AI tuân thủ nghiêm ngặt tiêu chuẩn kiến trúc định dạng được quy định tại `.agents/skills/book-audience-matcher/references/audience-structure.md`. Trích xuất toàn bộ dữ liệu thuộc khối `# --- JTBD ROUTING BLOCK ---` từ file `audience.yaml` (vừa lưu), sau đó bọc giữa hai ký tự phân cách `---` để thiết lập thành cấu trúc YAML Frontmatter hợp lệ. Đối với phần thân (Body) của file, kế thừa nguyên vẹn các khối truy vấn Dataview tĩnh theo đúng khuôn mẫu từ file tiêu chuẩn nói trên. Lưu trữ file hoàn chỉnh tại đường dẫn: `vault/01-Atomic/Audiences/[Tên-File-Chuẩn-Hóa-Ở-Hành-Động-1]`.
         - **Hành động 3 — Khởi tạo Index:** Sau khi hoàn tất tạo file Audience vật lý, kiểm tra tệp tin `vault/01-Atomic/Audiences/_audience_index.yaml`:
           + Nếu **CHƯA tồn tại**: Khởi tạo từ template `.agents/skills/persona-interviewer/assets/_audience_index_template.yaml` và ghi nhận bản ghi (entry) đầu tiên.
           + Nếu **ĐÃ tồn tại**: Trích xuất và nối (append) bản ghi mới vào cuối giới hạn của cấu trúc mảng `audiences:`.
           + Định dạng dữ liệu của bản ghi (áp dụng cho cả 2 trường hợp):
             ```yaml
               - id: "[job_performer]_[main_job]_[circumstance]"  # English snake_case từ 3 fields JTBD vừa lưu. VD: `new_employee_time_management_first_job`
                 file_ref: "[[tên-file-ở-hành-động-1]]"           # Tham chiếu Wikilink trỏ trực tiếp đến Audience file vừa tạo ở hành động 2
                 audience_level: "big"                            # Thiết lập mặc định gán cấp độ "big" cho Audience khởi tạo qua quy trình phỏng vấn
                 audience_Job_performer: "[giá trị từ audience.yaml]"
                 audience_main_job: "[giá trị từ audience.yaml]"
                 audience_circumstance: "[giá trị từ audience.yaml]"
                 parent_audience: []                              # Bắt buộc khởi tạo định dạng mảng rỗng (Array) để đảm bảo đồng bộ kiến trúc DAG
                 aliases: []
             ```
    - **Bước 2 (Mở rộng Insights)**: 
      + ⛔ **CẤM LƯU FILE SAU KHI USER TRẢ LỜI:** Khi nhận được đáp án cho câu hỏi dưới đây, TUYỆT ĐỐI KHÔNG ghi các Seed Insights (nỗi sợ, khao khát...) vào `audience.yaml` hay bất kỳ file nào. Bạn bắt buộc phải GIỮ NGUYÊN ở bộ nhớ chat (Context) để chờ thực thi ở Câu 11.
      + **Hành động của AI:** **Tuyệt đối chỉ sử dụng các biến insight sau, không được bịa thêm bất cứ biến nào khác**Đặt câu hỏi Menu-style: *"Để hiểu sâu về họ, bạn thử gạch đầu dòng những khía cạnh nào dưới đây mà bạn nắm rõ nhất: 1. Khao khát (desire) / 2. Nỗi sợ (fear) / 3. Nỗi đau (pain_point) / 4. Rào cản (barrier) / 5. Niềm tin (belief) / 6. Thích (likes) / 7. Ghét (dislikes) / 8. Cạm bẫy (pitfall) / 9. Lầm tưởng (myth)? Nhớ gì kể nấy nhé."*

11. **3-4 chủ đề chính (Pillars) bạn hay viết là gì?**
    *Lưu ý: Hỏi tách biệt 2 bước sau, đợi User trả lời bước 1 xong mới đưa bước 2.*
    - **Bước 1 (Khai thác Pillar & Topic)**: Đặt câu hỏi: *"Sang phần Vũ trụ Nội dung nhé! Bạn thường tập trung vào 3-4 trụ cột nội dung (Pillars) nào? Với mỗi trụ cột, hãy thêm mô tả ngắn gọn thể hiện mục đích và/hoặc phạm vi khai thác của pillar và bất cứ thông tin nào làm rõ về pillar đó. Ngoài ra, dưới mỗi trụ cột đó, bạn có thể gạch vài từ khóa (Topics ngách) cụ thể mà bạn hay đào sâu không?"*
      *Lưu ý cho AI: BẮT BUỘC cung cấp template mẫu để User dễ trả lời, ví dụ:*
      ```text
      Pillar 1:
      Name: 
      Description: 
      Topics:
      - 
      - 

      Pillar 2:
      Name: 
      Description: 
      Topics:
      - 
      - 
      ```
      *User chỉ cần copy template và điền sau dấu `:` hoặc sau dấu `-`.*
      + ⛔ Khi nhận câu trả lời, **BẮT BUỘC** ghi các Topics ngách vào thẻ mảng `topics: []` trong `topic_map.yaml` ngay lập tức. **TUYỆT ĐỐI CẤM ghi vào `pillars.yaml`** ở bước này. Mỗi entry PHẢI tuân thủ đúng schema 3 trường — **điền đầy đủ cả `pillar_parents`** bằng tên Pillar cha mà User vừa cung cấp (đây KHÔNG phải là ghi vào `pillars.yaml`):
      ```yaml
      - id: "[slug_không_dấu_dùng_gạch_dưới]" # VD: quan_ly_thoi_gian. KHÔNG dùng dấu gạch ngang
        pillar_parents: ["[Tên_Pillar_cha_user_vừa_khai]"]
        belongs_to_audience: ["[[Tên_file_Audience_vừa_tạo_ở_Câu_10]]"]
      ```
    - **Bước 2 (Xác nhận Mapping)**: Tự động phân bổ danh sách Seed Insights (từ Câu 10) vào các Pillars tương ứng, dựa trên `name` và `description` của mỗi Pillar để xác định Pillar phù hợp nhất cho từng Insight. **Đồng thời resolve topics**: Với mỗi Insight được map vào Pillar P, tra cứu `topic_map.yaml` → lấy tất cả topic có `pillar_parents` chứa P → gán danh sách `id` làm giá trị `topics` cho Insight đó. Hiển thị bảng Mapping (bao gồm cột Topics) ra Chatbox và yêu cầu: *"Vui lòng xem lại bảng phân bổ Insight vào Pillar và gõ (Y) để xác nhận."*
      > ⛔ **TOÀN VẸN NỘI DUNG (Copy-Paste Integrity):** Khi hiển thị bảng Mapping và khi ghi vào payload JSON, nội dung của mỗi Insight **BẮT BUỘC phải được sao chép NGUYÊN VĂN y hệt** từ câu trả lời User đã chốt ở Câu 10. **TUYỆT ĐỐI CẤM diễn giải lại, tóm tắt, hay thay đổi bất kỳ từ nào** — dù chỉ 1 từ — trong phần `raw_payload`. Mọi chỉnh sửa dù nhỏ đều làm sai lệch ý nghĩa gốc của User.
      > ⛔ **MỘT INSIGHT - MỘT PILLAR (One Insight, One Pillar):** Mỗi Insight chỉ được phép xuất hiện ở **đúng 1 Pillar duy nhất** — Pillar phù hợp nhất với bản chất của Insight đó. **TUYỆT ĐỐI CẤM** phân bổ cùng 1 Insight vào nhiều Pillars dù Insight đó có vẻ liên quan đến nhiều chủ đề. Khi không chắc, hãy chọn Pillar có độ liên quan cao nhất và chỉ 1 mà thôi.
    - **Hành động Hệ thống (Phát tín hiệu Script)**: CHỈ SAU KHI nhận lệnh `(Y)` từ User, tiến trình mới được phép ghi nối dữ liệu Pillars vào `pillars.yaml` (bao gồm `name`, `description` — mô tả ngắn gọn do User cung cấp ở Bước 1, và `insights`, `target_emotion`). Đồng thời AI dùng Tool In Đè (Overwrite) toàn bộ array JSON tổng hợp Insight vào file tĩnh có sẵn: `.agents/skills/persona-interviewer/scripts/insights_payload.json`, bắt buộc chứa 5 biến chính xác sau:
      + `headline`: Đặt tên tối giản, loại bỏ stop words, chỉ lấy cụm danh từ/động từ chính. Script sẽ tự chuyển thành **Slug Naming** chuẩn: `[slug-keyword-tieng-viet-khong-dau].md` (chữ thường, không dấu, nối bằng gạch ngang).
      + `insight_type`: Phân loại nhóm Insight (ví dụ: desire, pain_point...).
      + `raw_payload`: Nguyên văn phần text thô do User gợi mở.
      + `llm_explain`: Phân tích chuyên sâu đúc rút từ AI (Insightful explain).
      + `topics`: Mảng `id` topics đã resolve ở Bước 2 (VD: `["dieu_hoa_cam_xuc", "gan_ket_an_toan"]`).
      Sau đó AI tự động GỌI GÓI LỆNH TERMINAL bọc sẵn dưới đây để hệ thống tự xuất mẻ file vật lý cuối cùng: 
      ```powershell
      powershell -ExecutionPolicy Bypass -File .agents/skills/persona-interviewer/scripts/run_insights.ps1 -Audience "[Tên_file_Audience_vừa_tạo_ở_Câu_10_không_có_đuôi_.md]"
      ```

12. **Danh sách 3 chuyên gia / tác giả uy tín hay trích dẫn?** 
    - Với mỗi expert, hỏi thêm: credential chính, thành tựu, topics. Ghi vào `authorities.yaml` (`cascade`).

> **UX Report (Cuối Tier 2):** Báo cáo: **Completeness 65%. Hoàn tất quá trình Onboarding** và giới thiệu về Tier 3 là giai đoạn AI sẽ tự động học hỏi và tinh chỉnh trong quá trình user sử dụng hệ thống, user không cần phải làm gì cả. Sau đó Hướng dẫn user thực hiện các bước sau:
> - Dùng `/story-bank` để kể 10 câu chuyện đầu tiên
> - Dùng `/content-post` để test bài đầu tiên
> - Copy bài đã đăng vào `vault/03-Content/Posted/` và bài viral vào `vault/03-Content/Viral Posts/` để hệ thống tìm thêm stories

## Tier 3: Mastery (Auto)
Mục tiêu: Đạt 100%. User không cần làm gì, cơ chế hệ thống sẽ tự động cập nhật ngầm qua quá trình sử dụng:
- `scoring-rules.yaml`: Tự động tinh chỉnh `auto_fail_items` dựa trên patterns lỗi thường gặp định kỳ.
- `authorities.yaml`: Tự động cập nhật `used_count` để bảo vệ nguyên tắc `diversity_rule` (không lặp expert quá nhiều).
