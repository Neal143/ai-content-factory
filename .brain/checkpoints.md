# Lịch sử Checkpoints

### 📅 Ngày 04/06/2026
#### Fix QA Score, format logs & clean apply-profile
- **Mã khôi phục:** `8a39908`
- **Thẻ (Tag):** `v4.1.0-log-profile-fixes`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗi trích xuất điểm QA do khác biệt ký tự, cải tiến hệ thống nhật ký (Production Log, Hook History) dễ đọc hơn, đồng thời ngăn chặn rủi ro sập hệ thống (crash) khi tải Profile mới.
  - **🛠️ Kỹ thuật (Tech):** Sửa Regex lấy điểm QA và Normalize tiếng Việt ở `Get-Slug` trong `validate-format.ps1`. Áp dụng Markdown URL cho file ở `hook-history.md`. Xóa sạch logic cài đặt (patching) cho `format-agent/SKILL.md` khỏi `apply-profile.ps1` vì đã chuyển sang format bằng thuật toán thay vì prompt.

### 📅 Ngày 03/06/2026
#### Fix lỗi Format Agent và Metadata Script
- **Mã khôi phục:** `c463bfa`
- **Thẻ (Tag):** `cp-format-metadata-fix`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Khôi phục cấu hình định dạng xuất bản bài viết và sửa lỗi kịch bản trích xuất thông tin, đảm bảo an toàn quy trình xuất bản.
  - **🛠️ Kỹ thuật (Tech):** Khôi phục các biến số (Target_Audience, Marker) trong `format-agent/SKILL.md`, đồng bộ `AGENT.md` và sửa lỗi mã hóa dấu Em-dash gây syntax error trong `semantic-router/scripts/get_source_metadata.ps1`.

### 📅 Ngày 01/06/2026
#### Tái cấu trúc Macro-Session 1, 2, 4 (Anti-Bypass Poka-Yoke)
- **Mã khôi phục:** `c9778cc`
- **Thẻ (Tag):** `v4.0.2-poka-yoke`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Giải quyết dứt điểm tình trạng Agent lách luật tự viết mã Python để sinh file (Anti-Bypass). Áp dụng đòn tâm lý "Pre-filled Template" để ép Agent vào luồng điền dữ liệu. Hoàn tất việc nhốt file rác vào các thư mục `session_1/`, `session_2/`, `session_4/` (Macro-Session Isolation) giúp run folder sạch sẽ.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `prepare_topic_batches.py` và `extract_vivids.py` sinh template sẵn. Fix triệt để lỗi Trailing Slash. Cập nhật hàng loạt `SKILL.md` và code để I/O trỏ đúng thư mục con. Di dời thủ công dữ liệu legacy cũ về chuẩn mới.

### 📅 Ngày 01/06/2026
#### Tái cấu trúc Macro-Session 3 (Audience Matcher)
- **Mã khôi phục:** `f51ab0b`
- **Thẻ (Tag):** `v1.0.1-audience-session3-refactor`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đã dọn dẹp sạch sẽ quá trình phân tích đối tượng độc giả (Macro-Session 3). Từ nay hệ thống sẽ "nhốt" toàn bộ các bản nháp và dữ liệu trung gian vào một thư mục riêng biệt (`session_3/`), giúp hệ thống luôn gọn gàng và không bị rối rắm bởi dữ liệu rác.
  - **🛠️ Kỹ thuật (Tech):** Thay thế đường dẫn tương đối bằng Absolute Path (`os.path.abspath`) trong các script gatekeeper để vá lỗi Trailing Slash. Cập nhật `SKILL.md` đổi toàn bộ file path sang thư mục `session_3/`. Vá lỗi Crash của `parse_book_audiences.py` bằng `os.makedirs`.

### 📅 Ngày 29/05/2026
#### Tái cấu trúc pipeline Book Extractor thành 4-Session
- **Mã khôi phục:** `b303be6`
- **Thẻ (Tag):** `v4.0.0-book-extractor-batch`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp kiến trúc pipeline bóc tách sách (`book-extractor`) từ 3 session lên 4 session. Giúp giải quyết dứt điểm lỗi tràn bộ nhớ ngữ cảnh (Context Exhaustion) ở giai đoạn cuối, đảm bảo AI xử lý trơn tru mọi cuốn sách bằng cơ chế chia đợt (batching) tự động.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `book-extractor.md` để tách Breakpoint 3 và Handoff 3. Tạo mới script `prepare_topic_batches.py` làm gatekeeper chia mảng dữ liệu. Chỉnh sửa `book-parser/SKILL.md` áp dụng vòng lặp batching, chặn hành vi đọc file thô và tự động validate chứng cứ (evidence).

### 📅 Ngày 29/05/2026
#### Fix lỗi quy trình Curate Vivids
- **Mã khôi phục:** `065c64a`
- **Thẻ (Tag):** `v2.4.0-curate-vivids-fix`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá 3 lỗi kiểm toán của chuỗi Curate Vivids: Chống tình trạng "cheating" bỏ qua bước chấm điểm Rubric (buộc Agent phải chấm 5 tiêu chí), chống xả rác file `temp_batch.txt` (sử dụng cơ chế sao chép qua `current_batch.json` thay vì in ra terminal).
  - **🛠️ Kỹ thuật (Tech):** Cập nhật validation trong `extract_vivids.py` ép `scores` phải đủ C1-C5 và tổng điểm >= 7 đối với KEEP, LOW_SCORE với DISCARD vòng điểm. Đổi logic in content sang sao chép file tại hàm `handle_get_next` và `handle_submit`, đồng thời dọn dẹp sạch `current_batch.json` sau khi hoàn thành chuỗi. Cập nhật `SKILL.md` cấm redirect stdout.
### 📅 Ngày 28/05/2026
#### Tái cấu trúc 3-Session cho book-extractor & Chuẩn hóa curate-vivids
- **Mã khôi phục:** `ce48b39`
- **Thẻ (Tag):** `v1.1.0-book-extractor-3session`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp quy trình xử lý sách `/book-extractor` từ 2 session thành 3 session độc lập. Việc chia nhỏ quy trình giúp bảo vệ tuyệt đối Context Window của mô hình khỏi tình trạng quá tải token khi chạy bóc tách Atoms DIKW cho hàng chục chunk ở khâu cuối, đồng thời đem lại độ tin cậy và chính xác tối đa cho hệ thống.
  - **🛠️ Kỹ thuật (Tech):**
    - Tái cấu trúc `.agents/workflows/book-extractor.md` sang cấu trúc 3-Session chuẩn: Session 1 (Đào thô - Phase 1), Session 2 (Curation vivids & Niêm phong - Phase 2), Session 3 (Phân giải độc giả & Phân rã Atoms DIKW - Phase 3 & 4).
    - Cập nhật hai điểm bàn giao an toàn (`Handoff Prompt 1` và `Handoff Prompt 2`) với định dạng Markdown block rõ ràng để người dùng chuyển tiếp phiên một cách trực quan.
    - Đồng bộ 100% tài liệu workflow với các chỉ định trong `book-audience-matcher/SKILL.md` và `book-parser/SKILL.md`.
    - Ghi nhận mã nguồn commit chuẩn hóa `extract_vivids.py` và `apply_curation.py` đã hoàn thành trước đó.

### 📅 Ngày 27/05/2026
#### Chuẩn hóa SKILL metadata & dọn dẹp scratch
- **Mã khôi phục:** `ac15303`
- **Thẻ (Tag):** `v3.7.1-dikw-bridge-metadata-cleanup`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hoàn thiện và nâng cấp toàn diện Skill DIKW Bridge. Sắp xếp lại quy trình nghiệp vụ tuần tự mạch lạc (Bước 1, 2, 3), loại bỏ triệt để nợ kỹ thuật và dữ liệu trùng lặp. Dọn sạch hoàn toàn thư mục rác `scratch/` giúp codebase đạt tiêu chuẩn tinh gọn, sạch sẽ ở mức tối đa.
  - **🛠️ Kỹ thuật (Tech):**
    - Di chuyển file tĩnh `vault_index.json` vào thư mục chuyên biệt `assets/` và đồng bộ đường dẫn ở `build-vault-index.ps1` cùng `Get-DIKWCombo.ps1`.
    - Hợp nhất siêu dữ liệu theo Global Rule 7 trong `SKILL.md` và `injection-rules.md` từ dạng comment HTML trùng lặp vào YAML frontmatter thống nhất ở đầu file.
    - Cải tiến logic parsing chuỗi phân tách bằng dấu phẩy cho `-Topics` và `-Audience` trong `Get-DIKWCombo.ps1` và sửa cách truyền đối số trong `test-dikw-combo.ps1` vượt qua 100% unit tests.
    - Xóa sạch toàn bộ file deadcode trong `scratch/`.

### 📅 Ngày 26/05/2026
#### Hoàn thiện kiến trúc JIT Payload cho Phase 1
- **Mã khôi phục:** `2a101fb`
- **Thẻ (Tag):** `v3.7-payload-phase1`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đồng bộ cơ chế JIT Payload cho khâu đầu tiên (Idea Curator). Hệ thống hoạt động mượt mà không bị "béo phì dữ liệu" hay nhầm lẫn nguồn, đảm bảo chất lượng bài viết ổn định ngay từ khâu ý tưởng.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `content-post.md` (chèn lệnh compile-payload.ps1 cho Phase 1, bỏ constraint Phase 2+), khai báo lại `required_inputs` tường minh cho `idea-curator/SKILL.md` kèm theo quy tắc FATAL RULE trích xuất BUNDLE_KEY từ payload thay vì view_file trực tiếp.

### 📅 Ngày 26/05/2026
#### Bịt lỗ hổng DIKW Poka-yoke ở Phase 1 và Phase 3
- **Mã khôi phục:** `6c14de2`
- **Thẻ (Tag):** `v1.1.0-dikw-pokayoke-patch`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗ hổng quy trình Poka-Yoke: Yêu cầu AI ở bước 1 (Idea Curator) và bước 3 (Hook Engineer) phải đọc chính xác tài liệu DIKW Combo và chèn mã bảo mật `BUNDLE_KEY` để được cấp phép đi tiếp. Đảm bảo 100% các Agent không bịa đường dẫn hay bỏ qua dữ liệu thực tế đã cung cấp.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `detect-bypass.ps1` để mở rộng Check 4B (check BUNDLE_KEY) từ Phase 1 đến Phase 5. Thêm `FATAL RULE` yêu cầu trích xuất BUNDLE_KEY vào `idea-curator/SKILL.md` và `hook-engineer/SKILL.md`. Sửa lại định tuyến đường dẫn input một cách tuyệt đối minh bạch cho `hook-engineer`.

### 📅 Ngày 24/05/2026
#### Cập nhật DIKW Bridge source_id filter (Hoàn thành Plan v2)
- **Mã khôi phục:** `491fb92`
- **Thẻ (Tag):** `v2.1.0-dikw-source-id`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Giải quyết triệt để lỗi Context Leak: Nâng cấp DIKW Bridge để hệ thống có thể gom chính xác 100% dữ liệu từ một cuốn sách cụ thể khi được yêu cầu, dẹp bỏ tình trạng rò rỉ dữ liệu từ nguồn ngoài mà không bị lỗi "Không tìm thấy nguyên liệu".
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `dikw-bridge/SKILL.md` (Bước 2) thêm điều kiện bypass O(1) bằng thuộc tính `source_id` cho mảng `Target_Source_IDs`. Rollback code lỗi cũ ở `semantic-router`. Chạy `generate-phase-key.ps1` để rotate keys và reset `PIPELINE_STATUS` về SẴN SÀNG trong `content-post.md`.

### 📅 Ngày 24/05/2026
#### Tích hợp 8-keys standards, fix backup rollback, tự động hóa Sentinel
- **Mã khôi phục:** `00c10da`
- **Thẻ (Tag):** `v1.0.4-8keys-sentinel`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Thiết lập rào chắn tiêu chuẩn Việt Nam cực nghiêm ngặt: buộc AI đọc đủ 8 tệp quy tắc (viết hoa, dấu câu, chống trộn tiếng Anh) để xuất bản. Đồng thời, tự động hóa triệt để khâu dọn rác hệ thống (xóa file tạm), giúp anh yên tâm chạy bài mà không lo hệ thống "học nhầm" bản nháp cũ.
  - **🛠️ Kỹ thuật (Tech):** Khôi phục `SKILL.md` và vá `AGENT.md` dòng 41 (Sentinel Rule) để yêu cầu 8 keys. Xóa toàn bộ file `.bak` rác (nguyên nhân gây rollback). Tích hợp đoạn mã `AUTO RESTORE PROFILE` vào thẳng `detect-bypass.ps1` (cuối Phase 7) thay vì để AI tự gọi lệnh ở `content-post.md`.

### 📅 Ngày 23/05/2026
#### Redesign profile-selector questions & word count defaults
- **Mã khôi phục:** `7194544`
- **Thẻ (Tag):** `v2.1.0-profile-wordcount-redesign`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Redesign bộ câu hỏi Profile Selector (Basic + Advanced) để gộp heading spacing vào câu hỏi bật/tắt heading, tối ưu dependency và tăng trải nghiệm người dùng. Cập nhật word count mặc định chuẩn mới thành **1300-1800 từ** phân bổ tỉ lệ vàng 6/16/52/16/10% cho 5 sections.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật 6 files: `.agents/skills/profile-selector/SKILL.md` (redesign B1-B10, A1-A4), `.agents/scripts/apply-profile.ps1` (sync comments R1-R8), `profiles/default.json` & `profiles/active.json` (mặc định mới), `voice-writer/SKILL.md` & `references/writing-rules.md` (giới hạn total word count), `profiles/patch-patterns.json` (sync 9 find patterns), `structure-designer/SKILL.md` (sync outline section word counts). Chạy validation script PASS 100%.

### 📅 Ngày 23/05/2026
#### Merge format-pipeline-upgrade → master
- **Mã khôi phục:** `0c6d0ab`
- **Thẻ (Tag):** `v2.0.0-format-pipeline-merged`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Merge toàn bộ upgrade format pipeline (4-phase) vào master. Bao gồm: AGENT.md single source of truth, profile-selector questions fix, pipeline run bài "điều hòa cảm xúc". Tạo plan redesign questions + fix word count defaults (chưa thực thi).
  - **🛠️ Kỹ thuật (Tech):** Merge `feat/format-pipeline-upgrade` → `master` (no-ff). 28 files changed. Xóa .bak thừa. Tạo nhánh mới `feat/profile-wordcount-redesign` cho lần upgrade tiếp.

### 📅 Ngày 23/05/2026
#### Anti-Mechanic Compliance — word count 3-tier gate
- **Mã khôi phục:** `fab92b0`
- **Thẻ (Tag):** `v3.7.1-anti-mechanic-compliance`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Khắc phục hội chứng AI cắt xén/nhồi nhét câu từ máy móc để đạt quota số từ. Word count giờ là soft target thay vì hard gate — bài lệch nhẹ (±10%) vẫn được pipeline cho qua, chỉ lệch nặng mới bị chặn. QA-Checker thêm directive phát hiện dấu hiệu Mechanic Compliance.
  - **🛠️ Kỹ thuật (Tech):** 7 files thay đổi (+30 -20 lines). validate-draft.ps1 CHECK 1: binary PASS/FAIL → 3-tier PASS/WARN/FAIL với tolerance configurable. active.json + default.json: +`word_count_tolerance_percent: 10`. writing-rules.md Section 8: bỏ "KHÔNG quá 1800". voice-writer/SKILL.md Bước 3.2: soft target. qa-checker/AGENT.md: +directive #6 Anti-MC (MC-01). patch-patterns.json: 4 patterns sync. profile-selector/SKILL.md A4: +thông tin dung sai.

### 📅 Ngày 23/05/2026
#### Profile-selector fix + pipeline run điều hòa cảm xúc
- **Mã khôi phục:** `86fa12c`
- **Thẻ (Tag):** `v1.2.0-profile-fix-pipeline-run`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Sửa câu hỏi profile-selector cho user hiểu đúng (bỏ mặc định ⁂ sai, đổi "phần"→"section", cập nhật giá trị mặc định đúng default.json). Chạy pipeline tạo bài viết "điều hòa cảm xúc" thành công.
  - **🛠️ Kỹ thuật (Tech):** profile-selector/SKILL.md (redesign B1-B10 questions, bỏ hardcode section names, sync defaults). 9 SKILL.md files cập nhật EXECUTION_KEY/FILE_KEY sau pipeline run. Plan redesign A2/A3→B9/B10 đã tạo tại plans/230523-1132-profile-questions/.

### 📅 Ngày 23/05/2026
#### Upgrade format pipeline + AGENT.md single source of truth
- **Mã khôi phục:** `2da7d4a`
- **Thẻ (Tag):** `v1.1.0-format-pipeline-upgrade`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp hệ thống format bài viết — bổ sung khả năng tuỳ chỉnh khoảng cách giữa các chuỗi câu (chain separator), làm rõ cơ chế ngăn cách giữa các phần (section separator), mở rộng quy tắc bảo toàn nội dung. Dọn dẹp 9 file cấu hình agent để loại bỏ thông tin trùng lặp/xung đột, đảm bảo mỗi thông tin chỉ có 1 nguồn duy nhất.
  - **🛠️ Kỹ thuật (Tech):** 13 files thay đổi (+72 -401 lines). Phase 1: format-agent/SKILL.md (DATA INTEGRITY reword, section sep reword, +chain sep). Phase 2: patch-patterns.json (+4 chain sep patterns), apply-profile.ps1 (+12 lines chain sep logic). Phase 3: validate-draft.ps1 (-3 dead vars). Phase 4: 9 AGENT.md single source of truth (fix xung đột HookEngineer, xóa ghost ref ✏️). Bonus: sync canonical paragraph 3-5→8-10 khớp default.json.

### 📅 Ngày 22/05/2026
#### Plan v3: Upgrade Format Pipeline + AGENT.md Single Source of Truth
- **Mã khôi phục:** _(không có commit — chỉ plan, chưa thực thi code)_
- **Thẻ (Tag):** _(không có)_
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hoàn thành plan upgrade hệ thống format bài viết (bổ sung chain separator, làm rõ section separator, mở rộng DATA INTEGRITY) + dọn dẹp 26 mục duplicate/hardcode/xung đột trong 9 file AGENT.md để đảm bảo single source of truth.
  - **🛠️ Kỹ thuật (Tech):** Plan v3 final tại artifact `format-upgrade-plan.md` — 4 Phase, 12 Tasks, 13 files. Đã verify line-by-line, cross-reference, edge cases. Phát hiện 1 xung đột nghiêm trọng HookEngineer (AGENT nói "3 công thức" ↔ SKILL nói "1 formula"). Plan sẵn sàng thực thi.
- **Artifact**: `C:\Users\Admin\.gemini\antigravity-ide\brain\5f3f05a0-b963-4732-b52a-2bc47559f130\format-upgrade-plan.md`

### 📅 Ngày 22/05/2026
#### Cập nhật cấu hình không gian làm việc
- **Mã khôi phục:** `e20e6d4`
- **Thẻ (Tag):** `v1.0.0-cap-nhat-workspace`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hoàn tất việc định cấu hình không gian làm việc mới cho AWF.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật cấu trúc thư mục dự án vào `brain.json`, `preferences.json` và rules của `GEMINI.md`, lưu lại trạng thái mới nhất vào Git.
