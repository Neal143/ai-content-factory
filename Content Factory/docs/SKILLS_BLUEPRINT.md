# AI Content Factory: Skills Blueprint

> **Status:** Hoàn thành (Phase 03)  
> **Phiên bản kiến trúc:** v4.0.2 (Local AWF)  
> **Cập nhật lần cuối:** 17/05/2026

Tài liệu này là bản thiết kế kiến trúc tổng thể (Master Blueprint) của toàn bộ hệ thống AWF AI Content Factory. Nó hệ thống hóa luồng sản xuất vĩ mô, cơ chế bảo mật ngầm (Poka-Yoke), các tiêu chuẩn Hardcode, và cung cấp bản đồ định hướng cho toàn bộ các sơ đồ vi mô (Micro Flowcharts).

---

## 1. TỔNG QUAN KIẾN TRÚC AWF (AWF Architecture)

Hệ thống AWF (Antigravity Workflow Framework) sản xuất nội dung bài viết theo cơ chế **Chuyền Sản Xuất (Assembly Line)**.
Thay vì dùng 1 prompt dài duy nhất, hệ thống chia nhỏ thành 10 kỹ năng (Skills) độc lập. Mỗi Skill đóng vai trò như một chuyên gia, nhận Output của người trước làm Input của mình, xử lý, tự kiểm tra lỗi (Self-Check), và chuyển tiếp.

### Nguyên tắc Cốt lõi:
1. **Phân cực Trách nhiệm:** Ý tưởng không lo dàn ý. Viết nháp không lo Format. Chấm điểm (QA) là một tổ chức độc lập.
2. **Poka-Yoke (Chống sai lỗi):** Lỗi của AI phải được phát hiện và tự sửa *trước khi* người dùng nhìn thấy.
3. **Cơ chế 2 Phiên (Multi-session):** Chặn đứng sự kiệt quệ Context Window của LLM bằng cách ngắt phiên ở điểm giữa (sau khi lập dàn bài) và khởi động lại với bộ nhớ sạch để tập trung vào việc viết.

---

## 2. BẢN ĐỒ LUỒNG VĨ MÔ (Macro Workflow)

Luồng sản xuất nội dung chính thức được định nghĩa tại `.agents/workflows/content-post.md` và tuân theo sơ đồ [content-pipeline-macro.mmd](flowcharts/content-pipeline-macro/content-pipeline-macro.mmd).

**Cấu trúc 2 Phiên:**
*   **Phiên 1 (Nghiên cứu & Dàn bài):** `semantic-router` ➔ `dikw-bridge` ➔ `idea-curator` ➔ `insight-agent` ➔ `hook-engineer` ➔ `structure-designer`.
*   **Điểm dừng:** Tự động tạo `checkpoint.yaml`. Pipeline trả cờ `[HALT]` yêu cầu User mở Session mới.
*   **Phiên 2 (Viết & Hoàn thiện):** Khôi phục Context (Chạy `resolve-checkpoint.ps1`) ➔ `persona-loader` ➔ `voice-writer` ➔ `qa-checker` ➔ `format-agent`.

---

## 3. CƠ CHẾ BẢO MẬT & KIỂM SOÁT LỖI (Sentinel & Gates)

Hệ thống sử dụng hệ thống giám sát kép: **Đồng bộ** (Self-Check Gate) và **Bất đồng bộ ngầm** (Sentinel).

### 3.1. Sentinel (Giám sát toàn cục)
*   **Script:** `detect-bypass.ps1`
*   **Nhiệm vụ:** Rà quét sau mỗi Phase để kiểm tra tính toàn vẹn của mã hóa `EXECUTION_KEY` (cho SKILL.md) và `FILE_KEY` (cho References/Persona).
*   **Hành động:** Nếu phát hiện LLM bypass, nhảy cóc, tự chế output, tự vẽ ra Key ảo ➔ **Dừng ngay lập tức & Escalate User**. Không có ngoại lệ.

### 3.2. Self-Check Gates (Giám sát cục bộ)
*   **Vị trí:** Chèn trong kịch bản PowerShell (`validate-*.ps1`) của từng Skill cụ thể.
*   **Nhiệm vụ:** Bắt LLM đọc lại chính sản phẩm mình vừa viết và đối chiếu với bộ luật Poka-Yoke.
*   **Hành động:** Nếu FAIL ➔ Sinh ra file báo cáo lỗi (vd: `gate5-issues.md`) ➔ Ép AI đọc file lỗi và tự động sửa (Rewrite). **Tối đa 3 lần Retry**. Trượt quá 3 lần ➔ Escalate User.

---

## 4. DANH SÁCH CÁC ĐIỂM HARDCODE (Validation Rules)

Toàn bộ thông số chất lượng của hệ thống được Hardcode khắt khe trong các script nội bộ. Bất kỳ sự thay đổi nào đối với các thông số này đều yêu cầu cập nhật lại tài liệu kỹ thuật.

### 4.1. Phase 1: Idea Curator (`validate-idea.ps1`)
*   **Viral Score Threshold:** Điểm Viral Score bắt buộc **≥ 7/10**.
*   **Structural Completeness:** Ý tưởng bắt buộc phải đủ 4 Core Sections: `Contrarian`, `Core Tension`, `Hidden Belief`, `Transformation Promise`.

### 4.2. Phase 2: Insight Agent (`validate-research.ps1`)
*   **Specific Numbers Count:** Bắt buộc phải có từ **5 cụm số liệu cụ thể** trở lên (%, tỷ, năm, tháng...).
*   **Story Source Tags:** Nếu bài nhắc đến câu chuyện, BẮT BUỘC phải có thẻ `source:` đi kèm (vault, famous, book, none).
*   **KCS Status:** Bắt buộc có dòng xác nhận tự đánh giá `KCS status: PASS`.

### 4.3. Phase 3: Hook Engineer (`validate-hook.ps1`)
*   **Word Count Limit:** Độ dài của câu mở bài BẮT BUỘC nằm trong khoảng **30 - 65 từ**. Vi phạm → Rewrite.

### 4.4. Phase 4: Structure Designer (`validate-outline.ps1`)
*   **Total Word Limit:** Bắt buộc phân bổ cụ thể độ dài tổng các phần trong giới hạn **1500 - 1800 từ** (phải là số tuyệt đối, không dùng range).
*   **Rotation Logic:** Combination giữa "Emotional Tone" và "Structural Technique" ở phần Closing **không được trùng lặp** với 2 bài gần nhất.
*   **Nomenclature Lock:** Tuyệt đối KHÔNG sử dụng từ khóa "Framework" (bắt buộc dùng "Solution" hoặc "Concept").
*   **Atom Tracing:** Section "Story" và "Deep Dive" bắt buộc phải khai báo nguồn nguyên liệu qua trường `Atoms: ...`.

### 4.5. Phase 4.5: Persona Loader (`validate-persona-pack.ps1`)
*   **Section Integrity:** Bắt buộc phải có đủ 4 headers: `[Voice DNA]`, `[JTBD Anchor]`, `[Profile]`, `[Authorities]`.
*   **Key Rotation:** Mỗi lần load, hệ thống tự động sinh ra chuỗi **8 ký tự Hex** mới và ghi đè `FILE_KEY` vào `voice-dna.yaml` để ép Phase 6 đọc lại cấu hình thực tế.

### 4.6. Phase 5: Voice Writer (`validate-draft.ps1`)
*   **Anti-AI Pattern Detection:** Chặn đứng 14 dấu hiệu văn phong máy móc:
    - Bắt đầu bằng: `"Hãy tưởng tượng"`, `"Trong thế giới"`, `"Bức tranh"`, `"Bạn đã bao giờ"`.
    - Lạm dụng từ khóa nối: `"Không chỉ... mà còn"`, `"Tuy nhiên"`, `"Nhìn chung"`.
*   **Core Keyword Constraint:** Chống đạo văn/chống chệch hướng bằng kiểm tra sự hiện diện của **ít nhất 2 Unique Keywords** từ `04-outline.md`.

### 4.7. Phase 6: QA Checker (`validate-qa.ps1`)
*   **Quality Score Threshold:** Điểm số đánh giá tổng thể (Rubric-based) bắt buộc **≥ 130/150 điểm**.
*   **Atom Attribution (Chống Ảo Giác):** Tổng số lượng Fact được QA chấm điểm ("Vault Fact") phải nhỏ hơn hoặc bằng tổng số lượng thẻ `[Atom: ...]` đánh dấu trong bản nháp gốc.

### 4.8. Phase 7: Format Agent (`validate-format.ps1`)
*   **YAML Header Integrity:** Không cho phép thêm bớt bất kỳ metadata nào ngoài: `title`, `slug`, `date`, `pillar`, `viral_score`.
*   **Paragraph Pacing:** Độ dài đoạn văn tối đa cho phép là **4 câu/đoạn**. Vi phạm → Báo lỗi định dạng để tách dòng.

---

## 5. CHỈ MỤC SƠ ĐỒ KỸ THUẬT (Diagram Index)

Danh sách đường dẫn đến các bản thiết kế vi mô chi tiết (LOD 2) của từng trạm trong hệ thống. Tất cả sơ đồ được lưu tại `docs/flowcharts/` và mở bằng *Mermaid Diagram Viewer*.

| Phân loại | Tên Tiến Trình | Đường dẫn thư mục |
| :--- | :--- | :--- |
| **Vĩ Mô** | Content Pipeline Macro | `content-pipeline-macro` |
| **Khởi Tạo** | Generate Phase Key | `generate-phase-key-micro` |
| | Validate Persona | `validate-persona-micro` |
| **Global** | Sentinel & Checkpoint | `sentinel-checkpoint-micro` |
| | Resolve Checkpoint | `resolve-checkpoint-micro` |
| **Skill (Ph.0.5)**| Semantic Router | `semantic-router-micro` |
| **Skill (Ph.1)** | DIKW Bridge | `dikw-bridge-micro` |
| **Skill (Ph.1)** | Idea Curator | `idea-curator-micro` |
| **Skill (Ph.2)** | Insight Agent | `insight-agent-micro` |
| **Skill (Ph.3)** | Hook Engineer | `hook-engineer-micro` |
| **Skill (Ph.4)** | Structure Designer | `structure-designer-micro` |
| **Skill (Ph.4.5)**| Persona Loader | `persona-loader-micro` |
| **Skill (Ph.5)** | Voice Writer | `voice-writer-micro` |
| **Skill (Ph.6)** | QA Checker | `qa-checker-micro` |
| **Skill (Ph.7)** | Format Agent | `format-agent-micro` |

---
*Tài liệu này được tạo tự động từ quá trình Audit của Phase 03. Nó đóng vai trò là nguồn chân lý (Single Source of Truth) để phục vụ cho các hoạt động gỡ lỗi và nâng cấp kiến trúc trong tương lai.*
