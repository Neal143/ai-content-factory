# Lịch sử Checkpoints

### 📅 Ngày 30/06/2026
#### Cập nhật tiếng Việt có dấu, xóa story-bank và refactor init_vault
- **Mã khôi phục:** `cb526ec`
- **Thẻ (Tag):** `v4.0.0-tieng-viet-init-vault`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Chuẩn hóa tiếng Việt có dấu cho các file hướng dẫn sử dụng và bảng phân loại để người dùng dễ đọc hơn. Dọn dẹp workflow Story Bank đã lỗi thời để nhường chỗ cho Omni-channel Inbox mới.
  - **🛠️ Kỹ thuật (Tech):** Chuyển đổi mã hóa UTF-8 BOM cho các file `.md`. Xóa `.agents/workflows/story-bank.md`. User refactor `.agents/skills/persona-interviewer/scripts/init_vault.ps1` để gọi `sync-factory-scaffold.ps1`. User tự update phiên bản lên `v4.0.0` trong `README.md`.
### 📅 Ngày 30/06/2026
#### Refactor cấu trúc Assets sang Factory Scaffold
- **Mã khôi phục:** `c1fe981`
- **Thẻ (Tag):** `v4.2-assets-refactor`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Chuyển đổi toàn bộ hệ thống quản lý thư mục, file mẫu (template) sang một thư mục trung tâm (factory-scaffold). Đảm bảo không bao giờ bị mất/ghi đè dữ liệu của user khi cập nhật hệ thống, đồng thời đồng bộ tự động tài nguyên mới.
  - **🛠️ Kỹ thuật (Tech):** Thay thế `structure-manifest.txt` bằng `factory-scaffold/` system. Xóa các tài nguyên cũ, viết mới script `sync-factory-scaffold.ps1`, và cấu trúc lại `init_vault.ps1`, `run-migrations.ps1` (thêm bước đồng bộ và kiểm tra an toàn) cùng `detect-structure-changes.ps1`.

### 📅 Ngày 29/06/2026
#### Nâng cấp Inbox Processor thành Omni-channel Router
- **Mã khôi phục:** `b499a6c`
- **Thẻ (Tag):** `v3.9.0`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Tái cấu trúc Inbox Processor thành Omni-channel Router, tự động định tuyến dữ liệu thô từ 3 nguồn (Chat, Extract, Tĩnh) và áp dụng cơ chế Reverse-Chronological Logging. Bổ sung bảng 8 Knowledge Type cho Solutions/Concepts.
  - **🛠️ Kỹ thuật (Tech):** Ghi đè toàn diện `process-inbox.md`, `inbox-processor/SKILL.md` và `atom-classification.md`. Tạo mới `_Huong-dan.md`, update `structure-manifest.txt` và `init_vault.ps1`.
### 📅 Ngày 29/06/2026
#### Cập nhật lại thư mục lưu File A và quy tắc tên File B
- **Mã khôi phục:** `338f2e5`
- **Thẻ (Tag):** `v3.8.2-patch-1`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Làm rõ và chốt cứng thư mục lưu của nguyên liệu nội dung theo loại (Knowledge hay Concept).
  - **🛠️ Kỹ thuật (Tech):** Xóa bảng category cũ rác trong `SKILL.md`. Bổ sung rule Poka-Yoke rẽ nhánh if/else cho script tự động nhận diện folder `Solutions/` hoặc `Concepts/` trong `output-schema.md`.

### 📅 Ngày 28/06/2026
#### Cập nhật Story Architect SKILL và Output Schema
- **Mã khôi phục:** `7d7862a`
- **Thẻ (Tag):** `v3.8.2-story-architect-upgrade`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp quy trình Story Architect để tự động hóa trơn tru việc bóc tách câu chuyện (Story Atom). Ép cấu trúc Output thống nhất, có kịch bản xử lý tự động khi user muốn đổi Topic/Insight mà không bị đứt gãy luồng.
  - **🛠️ Kỹ thuật (Tech):** Overwrite toàn diện `SKILL.md` (giảm dư thừa, thêm Poka-Yoke trực tiếp), chia nhỏ `combo-negotiation.md` cho luồng đàm phán Combo, gom 1 schema vào `output-schema.md` chuẩn hóa field `source_type` và xóa file `story-schema.md` cũ. Thêm script tự động ép UTF-8 BOM để tránh vỡ font chữ tiếng Việt.

### 📅 Ngày 27/06/2026
#### Fix IDE unapproved verb warnings
- **Mã khôi phục:** `e7ef2a0`
- **Thẻ (Tag):** `v3.8.1-clean-warnings`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Dọn dẹp cảnh báo mã nguồn, giữ file script sạch sẽ 100% không còn warning từ trình soạn thảo.
  - **🛠️ Kỹ thuật (Tech):** Đổi tên 2 hàm `Parse-AtomFrontmatter` thành `Get-AtomFrontmatter` và `Build-TopicLookup` thành `New-TopicLookup` trong file `Update-PersonalAtomsQueue.ps1` để tuân thủ danh sách Approved Verbs của PowerShell (PSScriptAnalyzer).

### 📅 Ngày 27/06/2026
#### Fix array unrolling Update-PersonalAtomsQueue
- **Mã khôi phục:** `b3c68ff`
- **Thẻ (Tag):** `v3.8.0-fix-array-unroll`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗi bỏ sót việc tự động gán Topic/Pillar cho những atom cá nhân chỉ có duy nhất 1 topic trong mảng.
  - **🛠️ Kỹ thuật (Tech):** Áp dụng phòng thủ nhiều lớp trong `Update-PersonalAtomsQueue.ps1`: ép kiểu về mảng `@(...)` khi parse inline array tại `Parse-AtomFrontmatter` và thêm fallback ép kiểu `[String]` -> `[Array]` trước khi duyệt tại `Format-AtomRow`.

### 📅 Ngày 27/06/2026
#### Tắt tính năng tạo YAML aliases trong topic_map.yaml
- **Mã khôi phục:** `d9781b8`
- **Thẻ (Tag):** `v1.3.1-disable-yaml-aliases`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Xóa các ký tự neo/bí danh lạ (`&id001`, `*id001`) trong file `topic_map.yaml` giúp người dùng đọc file dễ chịu hơn.
  - **🛠️ Kỹ thuật (Tech):** Thêm cấu hình `yaml.Dumper.ignore_aliases = lambda *args: True` vào file `topic_manager.py` để ra lệnh cho PyYAML ngừng rút gọn file bằng Anchors & Aliases. Cập nhật vật lý lại file `topic_map.yaml` của Neal.


### 📅 Ngày 27/06/2026
#### Thêm file_ref/file_link cho audience.yaml (Reverse Lookup)
- **Mã khôi phục:** `1ed09c5`
- **Thẻ (Tag):** `v1.3-audience-reverse-lookup`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** File `audience.yaml` giờ tự động có link clickable trỏ thẳng đến file Audience vật lý trong vault. User click trực tiếp từ VS Code để nhảy đến file, không cần tìm thủ công. Validator kiểm tra link có trỏ đúng file thật trên ổ cứng.
  - **🛠️ Kỹ thuật (Tech):** Thêm hàm `backfill_audience()` vào `generate_insights.py` sử dụng cơ chế Reverse Lookup (quét Frontmatter 3 trường JTBD trong `vault/01-Atomic/Audiences/` để match file). Cập nhật `validate_outputs.ps1` thêm check `file_ref`, `file_link` + verify file tồn tại bằng `Test-Path` sau decode `%20`. Cập nhật template `audience.yaml` thêm 2 placeholder rỗng.


### 📅 Ngày 26/06/2026
#### feat: auto file_ref/file_link via script (PENDING mechanism)
- **Mã khôi phục:** `2d2e931`
- **Thẻ (Tag):** `v1.2-pending-mechanism`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Tự động hóa hoàn toàn việc gắn link Insight vào file Pillars. Người dùng giờ đây có thể click trực tiếp vào link Insight từ VS Code hoặc Obsidian mà không bị lỗi link mồ côi (không mở được).
  - **🛠️ Kỹ thuật (Tech):** Chuyển việc gán `file_ref` và `file_link` từ LLM (hay đoán sai) sang Python script (`generate_insights.py`) thông qua cơ chế `PENDING_N` placeholder. Cập nhật validator `validate_outputs.ps1` để check `file_link` và reject PENDING thừa. Thêm tính năng backfill bằng cờ `--backfill-only`.

### 📅 Ngày 26/06/2026
#### Tạo validator V6 + tích hợp workflow audit
- **Mã khôi phục:** `d66cdd9`
- **Thẻ (Tag):** `v3.7.1-validator-v6`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Tạo công cụ kiểm định tự động (Output Validator V6) chạy ngay sau mỗi phiên onboarding, đảm bảo mọi dữ liệu Persona (giọng văn, chân dung độc giả, trụ cột nội dung, insights) đều được sinh ra đầy đủ và chính xác. Chốt chặn này ngăn chặn việc Agent tiếp theo (Story Architect) nhận dữ liệu lỗi.
  - **🛠️ Kỹ thuật (Tech):** Tạo mới `validate_outputs.ps1` (V6) với Unified Regex xử lý đúng YAML inline comments, Block Scalar, array items. Chỉ kiểm tra output BẮT BUỘC theo SKILL.md (loại trừ template placeholders và trường skippable). Tích hợp Post-Execution Audit vào `onboarding-persona.md` workflow với cảnh báo ⛔ ép AI chạy script sau Tier 2.


### 📅 Ngày 25/06/2026
#### Cập nhật Schema YAML cho Insights
- **Mã khôi phục:** `2498d3a`
- **Thẻ (Tag):** `v1.0.x-fix-yaml-schema`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo hệ thống lưu trữ Insight của Persona (File `pillars.yaml`) luôn ổn định, không bị gãy vỡ do lỗi ký tự. Đồng thời lưu vết nguồn gốc rõ ràng (User -> Script -> LLM) giúp bảo vệ luồng tư duy xuyên suốt của hệ thống bài viết.
  - **🛠️ Kỹ thuật (Tech):** Áp dụng cấu trúc Block Scalar (`>`) thay thế ngoặc kép (`""`) trong định dạng Schema YAML của `persona-interviewer/SKILL.md` để triệt tiêu lỗi YAML parse error (Poka-Yoke). Bổ sung biến `file_ref` và `llm_explain` vào Schema để đồng bộ (Single Source of Truth) giữa payload tĩnh và cấu hình YAML.

### 📅 Ngày 24/06/2026
#### Hoàn thiện logic phân tích Git Diff cho Migration Detection
- **Mã khôi phục:** `d175ff5`
- **Thẻ (Tag):** `v3.7.3-fix-git-diff-logic`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗ hổng nghiêm trọng trong khâu Checkpoint. Hệ thống hiện tại có thể phát hiện chính xác khi hệ thống mã nguồn tạo ra một folder mới, từ đó cảnh báo user ngay lập tức để đồng bộ cho toàn bộ dự án thay vì bỏ sót như phiên bản trước.
  - **🛠️ Kỹ thuật (Tech):** Thay đổi thuật toán của `detect-structure-changes.ps1`: Chuyển từ kiểm tra động (so sánh disk vs manifest) sang phân tích tĩnh (Static Analysis) trên `git diff HEAD~1`. Bắt chính xác sự kiện tạo mới folder qua lệnh PowerShell (như `New-Item -ItemType Directory`) và các thay đổi text trực tiếp trên file `structure-manifest.txt`. Cập nhật nội dung luồng checkpoint.md để phản ánh đúng thông báo mới.
### 📅 Ngày 24/06/2026
#### Xây dựng Migration Detection System & manifest
- **Mã khôi phục:** `1d6102b`
- **Thẻ (Tag):** `v3.7.2-migration-detection`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Tự động hóa hoàn toàn việc phát hiện thay đổi cấu trúc thư mục. Bất cứ khi nào có folder hệ thống mới được thêm vào, `/checkpoint` sẽ tự động quét và báo động nếu user cũ cần cập nhật, ngăn chặn rủi ro lỗi phần mềm do thiếu file/folder.
  - **🛠️ Kỹ thuật (Tech):** Thay thế LLM analysis trong Giai đoạn 2.5 của `checkpoint.md` bằng một deterministic PowerShell script (`detect-structure-changes.ps1`). Tạo `structure-manifest.txt` làm single source of truth cho toàn bộ cấu trúc folder hệ thống ngoài `.agents/`. Refactor `init_vault.ps1` đọc từ manifest thay vì hardcode mảng, giúp đồng bộ giữa user mới và hệ thống migration. Thêm chuẩn encoding UTF-8 with BOM cho tất cả scripts liên quan.

### 📅 Ngày 24/06/2026
#### Personal Atoms Queue system
- **Mã khôi phục:** `bc60b8c`
- **Thẻ (Tag):** `v3.7.1-personal-atoms-queue`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Thêm bảng theo dõi atoms cá nhân chưa sử dụng tại `vault/03-Content/Content Plan/personal-atoms-queue.md`. User mở file bất kỳ lúc nào để biết còn insight/story cá nhân nào chưa được dùng trong bài đăng, kèm gợi ý topic để chạy `/content-post`. Bảng tự động cập nhật khi thêm atoms mới (qua story-bank/process-inbox) và tự xóa atoms đã dùng (sau khi publish).
  - **🛠️ Kỹ thuật (Tech):** Tạo script `Update-PersonalAtomsQueue.ps1` (3 actions: init/append/remove). Thêm field `source_type` vào templates của `story-architect` (story-schema.md + SKILL.md Bước 6-7) và `inbox-processor` (atom-classification.md + SKILL.md Bước 7.5). Hook remove vào `validate-format.ps1` sau production-log write với try/catch bảo vệ pipeline. Xóa files cũ `Get-UnusedPersonalAtoms.ps1` và `my-atoms.md`.


### 📅 Ngày 23/06/2026
#### Tối ưu hóa hiệu suất /update-agents (Fast Version Check)
- **Mã khôi phục:** `13322b9`
- **Thẻ (Tag):** `v3.8.1-fast-update-workflow`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Giúp người dùng nâng cấp hệ thống chớp nhoáng! Lệnh `/update-agents` giờ đây chỉ mất chưa tới 0.5 giây để kiểm tra xem có phiên bản mới hay không mà không cần phải tải ngầm nguyên cục dữ liệu về máy để kiểm tra như trước. Tiết kiệm băng thông, ổ cứng và thời gian chờ đợi.
  - **🛠️ Kỹ thuật (Tech):** Thay thế logic `git clone` để so sánh version bằng lệnh PowerShell `Invoke-RestMethod` chọc thẳng vào API Raw của GitHub để đọc dòng đầu tiên của `README.md`. Đồng thời gộp (merge) thành công logic Consolidated Backup (tạo thư mục timestamp) để không bị conflict với tính năng Version Check.

### 📅 Ngày 23/06/2026
#### Thêm version tracking vào README
- **Mã khôi phục:** `3f35eb5`
- **Thẻ (Tag):** `v3.8.1-version-tracking`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hệ thống giờ hiển thị rõ phiên bản đang chạy (`v3.8.0`) ngay trên tiêu đề README. Khi user chạy `/update-agents`, hệ thống tự so sánh version local vs remote trước khi quyết định có cần cập nhật không — tránh tải và thay thế vô ích nếu đã là bản mới nhất.
  - **🛠️ Kỹ thuật (Tech):** Sửa `README.md` tiêu đề thêm `v3.8.0`. Sửa `workflows/update-agents.md` Giai đoạn 3 thêm bước 3 so sánh dòng đầu tiên của README local vs remote, nếu version giống thì dọn tạm và kết thúc.

### 📅 Ngày 23/06/2026
#### Tích hợp cơ chế Consolidated Backup cho cập nhật/migration
- **Mã khôi phục:** `aa518d1`
- **Thẻ (Tag):** `v3.7.2-consolidated-backup`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Bảo vệ an toàn tuyệt đối dữ liệu người dùng (`vault/`, `personas/`) mỗi khi nâng cấp Agent. Tất cả backup (cả code cũ và dữ liệu) được quy hoạch gọn gàng vào thư mục `.update_backups/backup_NgàyTháng` theo thời gian thực (GMT+7) thay vì ghi đè. Tích hợp trực tiếp vào quy trình `/update-agents`.
  - **🛠️ Kỹ thuật (Tech):** Sửa `update-agents.md` sinh folder timestamp qua PowerShell (TimeZone SE Asia) và truyền `$BackupDir` sang `run-migrations.ps1`. Trong `run-migrations.ps1` dùng `robocopy /E` mirror data và check `LASTEXITCODE -ge 8` để handle lỗi I/O. Cập nhật `migrations/README.md` cấm sửa `.update_backups/`.

### 📅 Ngày 23/06/2026
#### Fix double-encoding SKILL.md + thêm pre-commit hook
- **Mã khôi phục:** `3d617e6`
- **Thẻ (Tag):** `v3.7.1-fix-encoding`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Khắc phục lỗi mã hóa ký tự (double-encoding) trên 2 file chỉ thị viết bài (voice-writer, structure-designer) đang chặn toàn bộ pipeline viết bài. Thêm cơ chế bảo vệ tự động ngăn lỗi tương tự lọt vào hệ thống trong tương lai.
  - **🛠️ Kỹ thuật (Tech):** Decode ngược CP1252 trên 2 file SKILL.md bị double-encoding (nguyên nhân: commit auto-save `8a47f73` ghi sai encoding). Tạo git pre-commit hook (`.git/hooks/pre-commit` + `check-encoding.ps1`) scan byte pattern `C3 83 C2` / `C3 A2 E2` trên tất cả staged text files — reject commit nếu phát hiện. Hook chỉ cần tồn tại ở repo gốc (không cần clone theo) vì chỉ repo gốc commit `.agents/`.

### 📅 Ngày 23/06/2026
#### Thêm migration system + update workflow
- **Mã khôi phục:** `2c8cc80`
- **Thẻ (Tag):** `v3.8.0-migration-system`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hệ thống giờ có khả năng phân phối bản cập nhật cho người dùng cuối. User chỉ cần gõ `/update-agents` để tải phiên bản `.agents` mới nhất từ GitHub. Khi cấu trúc thư mục `vault/personas` thay đổi, hệ thống tự động chạy migration script để cập nhật cấu trúc mà không ảnh hưởng dữ liệu hiện có. Repo GitHub đã chuyển sang Public, kèm README hướng dẫn onboarding.
  - **🛠️ Kỹ thuật (Tech):** Tạo mới `migrations/README.md` (hướng dẫn viết migration), `scripts/run-migrations.ps1` (engine chạy migration tuần tự với version tracking qua `FACTORY_VERSION`). Cập nhật `workflows/update-agents.md` (thêm bước gọi migration sau replace). Cập nhật `checkpoint.md` (AWF) thêm Giai đoạn 2.5 tự hỏi và tạo migration khi checkpoint. Tối ưu subtree push bằng `--rejoin` + xóa nhánh cũ trước khi tạo lại.

### 📅 Ngày 22/06/2026
#### Ngăn Voice Writer copy nguyên văn câu Hook
- **Mã khôi phục:** `4fbc835`
- **Thẻ (Tag):** `fix-voice-writer-hook`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo hệ thống giữ đúng DNA giọng văn thương hiệu ngay từ câu mở đầu (Hook). Voice Writer giờ đây sẽ viết lại nguyên liệu thô của câu Hook bằng giọng điệu riêng, loại bỏ hoàn toàn tình trạng sao chép nguyên văn lạnh lùng làm phá vỡ tính nhất quán của bài viết.
  - **🛠️ Kỹ thuật (Tech):** Thay đổi định dạng giao tiếp giữa Phase 4 (Structure Designer) và Phase 5 (Voice Writer). Cập nhật `structure-designer/SKILL.md` tách câu Hook thành 2 trường: `Hook Intent` và `Core Hook` (có nhãn nguyên liệu thô). Cập nhật `voice-writer/SKILL.md` bổ sung quy tắc `3.0.1 — Hook Adaptation` buộc rewrite. Đã xác thực an toàn Validation/Payload Script và ép UTF-8 BOM.

### 📅 Ngày 22/06/2026
#### Fix topic_map.yaml path resolution
- **Mã khôi phục:** `989f124`
- **Thẻ (Tag):** `fix-topic-map-path`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗi hệ thống phân tích chủ đề (Topic Manager) tự động tạo nhầm file `topic_map.yaml` rác. Hệ thống giờ đây có khả năng nhận biết chính xác thư mục Persona đang hoạt động để đọc/ghi dữ liệu vào đúng cấu hình thay vì tạo mới vô tội vạ.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `topic_manager/SKILL.md` thay thế toàn bộ placeholder `[topic_map_yaml_path]` bằng đường dẫn có tính kế thừa `[Persona_Path]/topic_map.yaml`. Cập nhật `book-parser/SKILL.md` hướng dẫn LLM cách lấy tên `Persona_Path` bằng cách truy xuất thư mục con duy nhất trong `personas/` và truyền rõ ràng tham số này khi ủy thác sang cho plugin.
### 📅 Ngày 21/06/2026
#### Nâng cấp Prefix-based Cross-Pillar
- **Mã khôi phục:** `83cd140`
- **Thẻ (Tag):** `v1.0.0-cross-pillar`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp kiến trúc quản lý chủ đề đa trụ cột (Cross-Pillar Topic). Áp dụng cơ chế tiền tố `pN_` an toàn để phân biệt rõ ràng các khái niệm cùng tên nhưng thuộc các nhóm nội dung (Pillar) khác nhau, đảm bảo dữ liệu không bao giờ bị trộn lẫn sai ngữ cảnh.
  - **🛠️ Kỹ thuật (Tech):** Thay đổi quy tắc sinh ID trên 5 file SKILL.md (`persona-interviewer`, `inbox-processor`, `story-architect`, `book-parser`, `topic_manager`). Cấy chốt chặn Poka-Yoke bằng regex (`^p\d+_`) vào sâu trong `dedup_engine.py` để block mọi nỗ lực cross-pillar merge O(1). Cập nhật `direct_match.ps1` hỗ trợ bóc tách tiền tố khi định tuyến.


### 📅 Ngày 22/06/2026
#### Fix init_vault structure + move formats/ into .agents/
- **Mã khôi phục:** `0ee462f`
- **Thẻ (Tag):** `v3.7.1-vault-formats-refactor`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Sửa lỗi script onboarding tạo sai cấu trúc thư mục vault (thiếu `03-Content/`, `_DLQ`, `02-sources/books/`, thừa `output/`). Di chuyển thư mục cấu hình format bài viết từ root vào `.agents/` để thống nhất convention lưu trữ hệ thống.
  - **🛠️ Kỹ thuật (Tech):** Sửa mảng `$vaultFolders` trong `init_vault.ps1` (fix 3 path sai, xóa 2 folder rác, thêm 2 folder thiếu). Di chuyển `formats/` → `.agents/formats/` và cập nhật 13 files reference path (4 scripts PS1, 3 SKILL/AGENT/workflow docs, 2 docs, 4 comment/description).

### 📅 Ngày 21/06/2026
#### Fix path .agent → .agents trong SKILL.md persona-interviewer
- **Mã khôi phục:** `8a5f592`
- **Thẻ (Tag):** `v4.1.5-fix-skill-paths`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hoàn tất đồng bộ đường dẫn `.agent` → `.agents` trong tài liệu hướng dẫn SKILL.md của persona-interviewer. Đảm bảo các lệnh PowerShell mẫu trong tài liệu trỏ đúng thư mục thực tế, tránh lỗi đường dẫn khi agent AI thực thi theo hướng dẫn.
  - **🛠️ Kỹ thuật (Tech):** Sửa 5 vị trí hardcode `.agent` → `.agents` trong `persona-interviewer/SKILL.md`: line 56 (init_vault.ps1 command), line 123 (audience-structure.md ref), line 125 (_audience_index_template.yaml ref), line 171 (insights_payload.json path), line 179 (run_insights.ps1 command).

### 📅 Ngày 21/06/2026
#### Fix path .agent → .agents trong persona-interviewer scripts
- **Mã khôi phục:** `76367c0`
- **Thẻ (Tag):** `v4.1.4-fix-persona-paths`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đồng bộ đường dẫn thư mục trong 3 script của skill persona-interviewer từ `.agent` (thiếu 's') sang `.agents` (có 's') cho khớp với cấu trúc thư mục thực tế. Bổ sung khả năng xử lý 2 định dạng JSON payload (bare array `[...]` và wrapped object `{"insights": [...]}`) để tránh crash khi format đầu vào khác nhau.
  - **🛠️ Kỹ thuật (Tech):** `init_vault.ps1`: sửa comment line 8. `run_insights.ps1`: sửa 3 đường dẫn hardcode tại lines 8, 9, 14 (TemplatePath, PayloadPath, lệnh gọi python). `generate_insights.py`: thêm `isinstance(payload, list)` check tại lines 61-66 để hỗ trợ cả 2 format payload, backward-compatible.

### 📅 Ngày 19/06/2026
#### Dual-mode transfer workflow + import script
- **Mã khôi phục:** `f7dbd26`
- **Thẻ (Tag):** `v3.7.1-transfer-extraction`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp workflow export sách thành hệ thống 2 chiều (Export/Import). Đổi tên `/export-extraction` → `/transfer-extraction`. Tạo script import tự động đưa dữ liệu sách từ folder tạm về đúng vị trí trong factory mới, có cơ chế phát hiện conflict và báo cáo cụ thể. Migrate cấu trúc `vault/.extraction_runs/` flat → subfolder `books/`.
  - **🛠️ Kỹ thuật (Tech):** Tạo `import_extraction_runs.ps1` (move cache file → `02-sources/books/`, move run folder → `.extraction_runs/books/`, conflict detection 2 loại, auto-cleanup). Xóa `export-extraction.md`, tạo `transfer-extraction.md` (dual-mode detection Export/Import). Fix `export_extraction_runs.ps1`: thêm `vault/` prefix cho `run_folder` (L112, L174, L199), sửa `pipeline_report.md` chỉ giữ phần Session 1. Commit cả `vault/.extraction_runs/books/` (trước đó chưa bao giờ tracked) và `vault/.extraction_runs_export/`.

### 📅 Ngày 18/06/2026
#### Bổ sung hướng dẫn đọc mapper_raw trước khi chọn Pillar
- **Mã khôi phục:** `3dd896a`
- **Thẻ (Tag):** `v4.1.3-book-parser-mapper`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo hệ thống bóc tách sách (`book-parser`) chọn đúng Pillar nhất cho toàn bộ cuốn sách. Agent giờ đây bắt buộc phải đọc file báo cáo tổng quan sách (`mapper_raw.md`) để có bối cảnh toàn diện trước khi quyết định, thay vì chọn mù.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `book-parser/SKILL.md`. Tái cấu trúc Bước 1.1 và 1.2, di chuyển luồng đọc `mapper_raw.md` lên đầu Bước 1.1 để làm input đối chiếu với `pillars.yaml`, giúp Agent có đủ context khi gán Pillar bất biến cho sách.

### 📅 Ngày 18/06/2026
#### Đổi theme thành description và cập nhật 5 skills
- **Mã khôi phục:** `c16e5de`
- **Thẻ (Tag):** `v4.1.2-pillars-description`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đổi tên trường thông tin của Pillars từ `theme` thành `description` để tường minh hơn. Sửa lại các câu hỏi phỏng vấn Pillars để hiển thị cấu trúc rõ ràng, dễ trả lời hơn cho người dùng.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật schema yaml trong `pillars.yaml` của Persona Template và Persona Neal. Sửa luồng prompt trong `persona-interviewer` (đổi câu hỏi, update mapping insight) và vá instruction bắt buộc LLM quét dựa trên `name` và `description` tại 4 SKILL.md (`semantic-router`, `book-parser`, `inbox-processor`, `story-architect`). Xóa 4 file rác bị dư.

### 📅 Ngày 11/06/2026
#### Dọn dẹp deadcode gây cảnh báo IDE
- **Mã khôi phục:** `16fb2fe`
- **Thẻ (Tag):** `v1.2.1-clean-warnings`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Làm sạch mã nguồn, loại bỏ các dòng lệnh thừa không còn giá trị sử dụng để ngăn chặn rác hệ thống và giữ cho trình soạn thảo code (IDE) hoàn toàn sạch sẽ (0 Warning).
  - **🛠️ Kỹ thuật (Tech):** Xóa bỏ dòng gán biến `$ideaHeaderCheck` không sử dụng ở dòng 411 trong file `validate-format.ps1`. Việc này triệt tiêu cảnh báo của PSScriptAnalyzer mà không làm ảnh hưởng đến khối điều kiện `if (-notmatch)` dùng để check trùng lặp log ở dòng 414.

### 📅 Ngày 11/06/2026
#### Đồng bộ timestamp file và log
- **Mã khôi phục:** `b37a8e6`
- **Thẻ (Tag):** `v1.2.0-timestamp-sync`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo toàn bộ hệ thống file bài viết đầu ra (`Posted`) và nhật ký quản lý luôn đồng bộ chặt chẽ về mặt thời gian gốc của dự án. Khắc phục vấn đề các bài viết cũ có tên lệch chuẩn.
  - **🛠️ Kỹ thuật (Tech):** Thay đổi logic trích xuất Regex trong `validate-format.ps1` lấy dữ liệu từ `RunFolder`. Khởi tạo kịch bản `scratch/fix-old-posts.ps1` chạy độc lập để quét toàn bộ thư mục, rename 9 file, cập nhật YAML date, và replace tên file, timestamp trong `production-log.md`, `hook-history.md`, `idea-history.md`. Script tự biến mất sau khi chạy xong.

### 📅 Ngày 11/06/2026
#### Tối ưu hóa lệnh Payload
- **Mã khôi phục:** `9ec4094`
- **Thẻ (Tag):** `v1.1.0-payload-opt`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Rút gọn tối đa các lệnh chạy payload trong workflow (content-post.md và content-post-IDE.md). Giảm thiểu rủi ro sai sót (hallucination) cho các Agent nhờ lệnh rút gọn và cơ chế tự định tuyến (Configuration Router).
  - **🛠️ Kỹ thuật (Tech):** Tạo mới script `prepare-payload.ps1` chứa cấu trúc Hashtable splatting tự động lấy cấu hình `PrevOutput` và `InputMap` cho 7 phases, tự động fallback RunFolder. Ép mã hóa chuẩn UTF-8 with BOM. Cập nhật thay thế chuỗi lệnh cũ trên 2 file workflow.

### 📅 Ngày 11/06/2026
#### Cập nhật Gate Check và cơ chế Reset Key
- **Mã khôi phục:** `8c43870`
- **Thẻ (Tag):** `v1.0.0-reset-key`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗi cơ chế Gate Check UX. Hoàn thiện luồng "/content-post hủy và viết mới" giúp dọn dẹp hệ thống ngay lập tức với 1 chạm. Bịt lỗi tràn IDE khi gộp code, đưa tệp workflow về đúng nguyên trạng ban đầu.
  - **🛠️ Kỹ thuật (Tech):** Xóa bỏ script thừa thãi `clear-phase-key.ps1`. Gom chức năng thành `-Action Clear` trong `generate-phase-key.ps1` với sửa đổi regex bảo toàn CRLF. Tích hợp lệnh tự động chạy ở Phase 7 trong `detect-bypass.ps1`. Sửa lỗi thiếu dòng trên file `content-post.md` do ghi đè text.
### 📅 Ngày 11/06/2026
#### Nâng cấp content-post sang kiến trúc Sub-agents
- **Mã khôi phục:** `c293b34`
- **Thẻ (Tag):** `v4.0.0-content-post-subagents`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Giải quyết lỗi tràn ngữ cảnh (Context Truncation) bằng kiến trúc Multi-Agent Orchestration. Môi trường Antigravity 2.0 sẽ chạy các sub-agents biệt lập, môi trường IDE giữ cơ chế tương thích ngược an toàn (Graceful Degradation). Bao gồm các bản vá lỗi về khoảng trắng (Paragraph/Chain Separator) và gia cố cơ chế chống sập (Sentinel Error Logging).
  - **🛠️ Kỹ thuật (Tech):** Sửa đổi toàn diện `content-post.md` (tích hợp chuỗi `define_subagent` và `invoke_subagent` kết hợp định danh `TypeName` và `enable_write_tools`). Lưu commit cho script `apply-format.ps1` (đổi điều kiện quy tắc R2 thành `>=`) và `detect-bypass.ps1` (Try-Catch I/O JSON, nâng -Depth 5, log errors tự động vào `sentinel-checklist.md`).

### 📅 Ngày 10/06/2026
#### Tích hợp metaphor vào voice-writer
- **Mã khôi phục:** `e73dac9`
- **Thẻ (Tag):** `v1.0.0-metaphor`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Bổ sung cấu trúc định hướng ẩn dụ (Extended, Compounding, Loop) giúp hệ thống tự động sinh ra các bài viết có chiều sâu lập luận, tránh văn mẫu và miêu tả rời rạc.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `voice-writer/SKILL.md` (buộc áp dụng cấu trúc từ `metaphor.md`), khởi tạo `references/metaphor.md` chuẩn metadata. Cập nhật đồng bộ `generate-phase-key.ps1` và `validate-draft.ps1` để sinh và kiểm tra khóa bảo mật `FILE_KEY` cho file tham chiếu mới.
### 📅 Ngày 10/06/2026
#### Nâng cấp văn phong tiếng Việt tự nhiên và quy tắc chống dịch thô
- **Mã khôi phục:** `d5d847c`
- **Thẻ (Tag):** `v3.7.1-vietnamese-naturalness`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp năng lực viết tiếng Việt tự nhiên cho hệ thống bằng cách gỡ bỏ các danh sách cấm cứng nhắc, chuyển sang định hướng minh họa tư duy (Paradigm Shift). Bản địa hóa các ví dụ công thức mở bài.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `writing-rules.md` (Thêm 2 ví dụ đối chiếu Anh-Việt), `anti-ai-rules.md` (chuyển rào cản AI thành ngữ cảnh), `hook-formulas.md` (Việt hóa F1, F4, F13), `qa-checker/SKILL.md` (Thêm Verification Protocol cho AI-05). Đã commit an toàn.

### 📅 Ngày 09/06/2026
#### Hoàn thiện hệ thống kiểm soát Punchline & Cleanup Final Output
- **Mã khôi phục:** `3d25cbb`
- **Thẻ (Tag):** `v19.1-punchline-format-fix`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo hệ thống AI chấm điểm chính xác số lượng câu nhấn (Punchline/Killer Statements) theo cấu hình động và tự động dọn dẹp sạch sẽ các thẻ kỹ thuật (`<!-- PUNCHLINE -->`) khỏi bài đăng cuối cùng.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `punchlines_per_article` vào `formats/default.json`. Thêm regex patch vào `formats/patch-patterns.json` cho `writing-rules.md` và `qa-checker/SKILL.md`. Cập nhật `validate-draft.ps1` để đọc cấu hình số lượng Punchline động. Sửa `writing-rules.md` về base 2-3 và hợp nhất quy định gắn thẻ dùng chung. Cập nhật `validate-format.ps1` để xóa thẻ `<!-- PUNCHLINE -->` ở output. Cắt đứt rò rỉ `SKILL.md` khỏi `content-post.md` (Encapsulation).
### 📅 Ngày 09/06/2026
#### Refactor Voice Writer references và validation scripts
- **Mã khôi phục:** `26c3eb2`
- **Thẻ (Tag):** `v3.7-voice-writer-refactor`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Giảm tải bối cảnh (context) cho AI khi viết nội dung, dọn dẹp các quy tắc lỗi thời, đảm bảo Agent vận hành ổn định và giữ nguyên bộ khung kiểm soát chất lượng nội dung viết tay.
  - **🛠️ Kỹ thuật (Tech):** Tích hợp 8 file quy tắc tiếng Anh, Anti-AI và Typography thành 4 file chuẩn. Cập nhật `SKILL.md`, `generate-phase-key.ps1` (để tính tổng key chính xác: 18/13), và `validate-draft.ps1` (sửa lỗi linting false-positive, thay đổi regex bắt bảng để parse chính xác rules blacklist).

### 📅 Ngày 09/06/2026
#### Nâng cấp cấu trúc Agents và Skills
- **Mã khôi phục:** `0378637`
- **Thẻ (Tag):** `v1.3.0-upgrade-agents`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Nâng cấp đồng loạt các Agents và Skills trong dây chuyền (Idea Curator, Format Agent, Hook Engineer, Persona Loader, v.v.), chuẩn hóa quy định về cấu trúc chuỗi câu nhằm nâng cao chất lượng nội dung bài viết đầu ra.
  - **🛠️ Kỹ thuật (Tech):** Đã cập nhật các file sau:
    - **Hệ thống SKILL.md:** `format-agent`, `hook-engineer`, `idea-curator`, `insight-agent`, `persona-loader`, `qa-checker`, `semantic-router`, `structure-designer`, `voice-writer`.
    - **Tài liệu tham chiếu (Voice Writer):** `ai-detection.md`, `anti-ai-patterns.md`, `capitalization.md`, `english-blacklist.md`, `english-mixing.md`, `prose-format.md`, `punctuation.md`.
    - **Scripts & Workflows:** `.agents/scripts/compile-payload.ps1`, `.agents/scripts/detect-bypass.ps1`, `validate-format.ps1`, `content-post.md`.
    - **Cấu hình & Persona:** `formats/active.json`, `personas/Neal/` (audience.yaml, authorities.yaml, profile.yaml, scoring-rules.yaml, voice-dna.yaml).
    - **Logs & Data:** `hook-history.md`, `production-log.md`, `vault_index.json`, và dọn dẹp các thư mục bản nháp cũ trong `vault/.content-pipeline/runs/`.
### 📅 Ngày 09/06/2026
#### Fix lỗi dính văn bản, dọn cảnh báo IDE
- **Mã khôi phục:** `b8846ca`
- **Thẻ (Tag):** `v1.0.0-validate-format-cleanup`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Vá lỗi các chuỗi văn bản bị dính liền vào nhau sau khi xuất bản, đồng thời dọn dẹp sạch sẽ các cảnh báo hệ thống, giúp bản thảo trình bày chuẩn xác và đẹp mắt hơn.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật `validate-format.ps1` thêm logic theo dõi biến cờ `$lastLineWasText` để nạp đúng cấu hình `chain_separator` giữa 2 khối text liền kề. Khắc phục 14 cảnh báo PSScriptAnalyzer bằng cách đảo `$null` sang vế trái và xóa biến thừa `$atomsStr`.
### 📅 Ngày 06/06/2026
#### Đổi tên profile thành format, xóa Reflective Writing, sửa lỗi BOM
- **Mã khôi phục:** `a16b8ab`
- **Thẻ (Tag):** `v1.0.1-fix-bom-format`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:**
    - **Chuẩn hóa khái niệm (Conceptual Alignment):** Chấm dứt sự nhập nhằng thuật ngữ bằng việc chuyển đổi toàn bộ khái niệm "Profile" thành "Format". Sự phân định này giúp người vận hành (và cả AI) tách bạch rõ ràng giữa "Persona" (Giọng văn/Đại diện) và "Format" (Quy cách/Định dạng đầu ra của bài viết).
    - **Tinh gọn luồng tri thức (Knowledge Streamlining):** Khai tử hoàn toàn nguồn dữ liệu thừa "Reflective Writing". Việc này giúp kho tàng (Vault) gọn nhẹ hơn, đồng thời loại bỏ rủi ro AI bị phân tâm hoặc cào nhầm dữ liệu rác trong quá trình tổng hợp bài.
    - **Bảo vệ tính liên tục của hệ thống (Pipeline Stability):** Xử lý dứt điểm tình trạng sập/đứt gãy đột ngột của dây chuyền tự động hóa `content-post` do lỗi hệ thống ngầm. Bảng theo dõi an ninh (Sentinel Checklist) hiện đã hiển thị chính xác tên từng file nháp, mang lại sự minh bạch tuyệt đối cho người giám sát.
  - **🛠️ Kỹ thuật (Tech):** 
    - **Refactor Profile -> Format:** Đổi tên toàn cục thư mục `profile-selector` thành `format-selector`. Cập nhật đồng loạt mã nguồn trong 9 files `AGENT.md`, hàng loạt files `SKILL.md` (của semantic-router, idea-curator, format-agent, v.v.), đổi tên script `apply-profile.ps1` thành `apply-format.ps1` và sửa các biến liên quan.
    - **Clean-up Reflective Writing:** Xóa đoạn mã khởi tạo file rác trong `init_vault.ps1`, gỡ bỏ logic quét Regex `*Reflective*` khỏi `Get-DIKWCombo.ps1` và xóa file tĩnh `Reflective-Writing.md` khỏi Vault. Làm sạch tài liệu hệ thống tại `docs/BRIEF-DIKW-Index.md` và `docs/flowcharts/dikw-bridge-micro/dikw-bridge-micro_info/1_context_filter.md`.
    - **Fix Encoding BOM & PowerShell Parser:** Cấp cứu sự cố ParserError bằng cách tự động chèn chữ ký UTF-8 BOM vào 7 scripts quan trọng (`validate-draft.ps1`, `validate-outline.ps1`, `validate-format.ps1`, `detect-bypass.ps1`, `apply-format.ps1`, `init_vault.ps1`, `Get-DIKWCombo.ps1`) để khắc phục lỗi vỡ font ký tự ANSI sinh ra từ môi trường.
    - **Fix String Interpolation:** Cập nhật script `detect-bypass.ps1` (Dòng 448 & 450) bổ sung chuỗi thoát dấu backtick (` `` `) để bảng checklist hiển thị chính xác tên file Output của các Agent.

### 📅 Ngày 04/06/2026
#### Di dời Run Folder link sang YAML Frontmatter
- **Mã khôi phục:** `a94bff0`
- **Thẻ (Tag):** `v3.7-frontmatter-link`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo link trỏ tới Thư mục Nguồn (Run Folder) được nhúng chính quy vào Properties của phần mềm Obsidian, mang lại giao diện quản lý siêu dữ liệu gọn gàng hơn.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật kịch bản Format Agent (alidate-format.ps1), chuyển chuỗi Markdown URL từ footer lên khai báo Metadata YAML. Dọn dẹp footer rác.

### 📅 Ngày 04/06/2026
#### Nâng cấp Continuous Tracking & Time-stamped Format
- **Mã khôi phục:** `0b8685d`
- **Thẻ (Tag):** `v3.7-tracking-timestamp`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Hệ thống giờ đây lưu tiến trình liên tục, tự động chống trùng lặp tên bài viết và gắn link thư mục nguồn tiện lợi ở cuối bài.
  - **🛠️ Kỹ thuật (Tech):** Thay thế checkpoint tĩnh bằng sentinel-data.json, nâng cấp workflow và script alidate-format.ps1 tạo timestamp HHmmss cho Folder & Log để tránh đè.

### 📅 Ngày 04/06/2026
#### Fix lỗi khoảng trắng khi lấy QA Score
- **Mã khôi phục:** `5467565`
- **Thẻ (Tag):** `v4.1.1-qa-score-spacing-fix`
- **Nội dung chính:**
  - **📱 Sản phẩm / Business:** Đảm bảo hệ thống cập nhật đúng và đủ điểm số QA vào báo cáo (Production Log, Hook History), ngay cả khi AI chấm điểm chèn thừa dấu cách vào kết quả.
  - **🛠️ Kỹ thuật (Tech):** Cập nhật Regex trong `validate-format.ps1` thành `\d+\s*/\s*\d+` và thêm logic `-replace '\s+', ''` để tự động loại bỏ các khoảng trắng rác. Dọn dẹp file `.bak` thừa.

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
