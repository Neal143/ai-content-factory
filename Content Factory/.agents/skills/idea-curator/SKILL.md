---
name: Idea Curator
description: Skill Phase 1 — Phân tích topic, tìm góc nhìn contrarian và đánh giá tiềm năng viral.
required_inputs:
  - blackboard              # 00-blackboard.yaml (topic, Target_Pillar, Target_Audience, Is_Novel_Angle)
  - dikw_combo              # 00.5-dikw-combo.md (optional, chỉ Kịch bản 1)
provided_outputs:
  - CONTRARIAN_ANGLE
  - CORE_TENSION
  - HIDDEN_BELIEF
  - TRANSFORMATION_PROMISE
  - IDEA_CONNECTION
  - VIRAL_SCORE
---

# Idea Curator (Phase 1)

> EXECUTION_KEY: 40e1378a

## Điều kiện Đầu vào
> **PAYLOAD:** Dữ kiện đầu vào (từ các phase trước hoặc hệ thống) đã được biên dịch sẵn trong `.temp/payload.md` (run folder). BẮT BUỘC đọc file này để lấy dữ kiện thay vì tự mở file gốc.

1. **`topic`**: ID chủ đề bài viết (String) (Đọc từ payload).
2. **`Target_Pillar`**: Pillar thương hiệu đã phân loại bởi Semantic Router (Đọc từ payload).
3. **`Target_Audience`**: Đối tượng độc giả (chỉ có khi `Is_Novel_Angle == False`) (Đọc từ payload).
4. **`Gói nguyên liệu DIKW (Atomic Combo)`**: Các file `Insight`, `Solution/Concept` từ Vault (chỉ có khi Kịch bản 1) (Đọc từ payload).

## Luồng Xử lý (2-Mode)

### Kịch bản 1: Thuần Vault (Standard)
- **Điều kiện:** `Is_Novel_Angle == False` + `Gói nguyên liệu DIKW (Atomic Combo)` hợp lệ.
- **Hành động:** BẮT BUỘC tham chiếu 100% Insight + Solution/Concept từ Vault. Không sáng tạo vượt xa nguồn.

### Kịch bản 2: Suy luận Sáng tạo (Fallback)
- **Điều kiện:** `Is_Novel_Angle == True` HOẶC DIKW trả về rỗng.
- **Hành động:** Dùng kiến thức LLM sáng tạo dựa trên `topic` + `Target_Pillar`. TUYỆT ĐỐI CẤM kết hợp chéo Data Vault.

---

## [Nguyên tắc Định hướng Lịch sử]
Bạn sẽ nhận được khối dữ liệu lịch sử (`history`) trong Payload. Trước khi viết bài mới, hãy nghiên cứu kỹ để:
- **Chống trùng lặp:** TUYỆT ĐỐI KHÔNG sao chép lại bộ khung ý tưởng đã dùng (bao gồm `Contrarian Angle`, `Core Tension` và `Hidden Belief`). Nếu nguyên liệu hiện tại dễ dẫn đến trùng lặp, hãy áp dụng **Công thức Đổi mới An toàn**: 
  - *Phát triển Sâu hơn:* Khai thác một `Hidden Belief` tinh vi hơn, hoặc thu hẹp vào một bối cảnh ngách.
  - *Xoay Góc Nhìn (Angle):* Giữ nguyên Tension nhưng thay đổi cách tiếp cận `Contrarian Angle` (vd: từ "lên án" sang "đồng cảm").
  - *(Luật Tối thượng Kịch bản 1): Không tự bịa kiến thức ngoài Vault, không tạo quan điểm phủ nhận bài cũ.*
- **Độc lập là Ưu tiên, Liên kết là Tùy chọn:** Lịch sử chủ yếu đóng vai trò làm CHỐT CHẶN CHỐNG TRÙNG LẶP. Ưu tiên cao nhất của bạn là sáng tạo ý tưởng MỚI HOÀN TOÀN dựa trên nguyên liệu. CHỈ KHI ý tưởng mới tình cờ chia sẻ chung bối cảnh tự nhiên với bài cũ, bạn mới thực hiện việc thiết lập "Liên kết". Tuyệt đối không khiên cưỡng ép buộc một ý tưởng độc lập phải liên quan đến lịch sử.

## Khởi tạo Idea Brief
1. Tìm góc nhìn contrarian (dựa theo Vault hoặc Improvise): Điều gì đa số người ta tin là đúng nhưng thực ra sai (hoặc ngược lại)? Đảm bảo góc nhìn này không trùng lặp với lịch sử.
2. Xác định **Core Tension**: Mâu thuẫn cốt lõi mà reader đang chịu đựng (vd: muốn dành thời gian cho con nhưng bận kiếm tiền).
3. Xác định **Hidden Belief**: Niềm tin ẩn mà bài viết sẽ phá vỡ (vd: "cho con xem iPad là bình thường vì ai cũng làm vậy").
4. Xác định **Transformation Promise**: Reader thay đổi gì sau khi đọc? (before → after rõ ràng).
5. Chấm **Viral Score** (tổng /10, cần ≥ 7):

| Tiêu chí | Trọng số | Mô tả |
|----------|---------|-------|
| Gây tranh cãi | 4đ | Topic có đi ngược lại niềm tin phổ biến không? |
| Cá nhân hóa | 3đ | Người đọc có thấy mình trong đó không? |
| Ứng dụng tức thời | 3đ | Đọc xong có thể làm ngay không? |

6. Xuất **Idea Brief** — mỗi khối nội dung BẮT BUỘC bọc trong thẻ `[BLOCK: TÊN]...[/BLOCK: TÊN]`:
   - ⛔ BẮT BUỘC giữ nguyên văn từ Blackboard: `topic`, `Target_Pillar`, `Target_Audience` (nếu có), `Is_Novel_Angle`.
   - Các block bắt buộc:
     - `[BLOCK: CONTRARIAN_ANGLE]` — Góc nhìn phản trực giác
     - `[BLOCK: CORE_TENSION]` — Căng thẳng cốt lõi
     - `[BLOCK: HIDDEN_BELIEF]` — Niềm tin ẩn cần phá vỡ
     - `[BLOCK: TRANSFORMATION_PROMISE]` — Hứa hẹn thay đổi
     - `[BLOCK: IDEA_CONNECTION]` — Sau khi hoàn thành các bước trên, hãy đánh giá Idea Brief bạn vừa tạo có liên quan tới bài cũ nào trong lịch sử không. NẾU ĐỘC LẬP: Ghi "Không có liên kết". NẾU CÓ LIÊN KẾT: Phải lập Báo Cáo Liên Kết RIÊNG BIỆT cho từng bài cũ bị ảnh hưởng. Mỗi báo cáo bao gồm: (1) Link Markdown bài post & link Idea-brief cũ; (2) Tóm tắt bài cũ trong tối đa 3 câu; (3) Phân tích Bản chất Mối quan hệ: Viết thành một đoạn văn ngắn gọn, cung cấp TRỌN VẸN thông tin thực tế về điểm chạm giữa 2 bài để Voice-writer dùng trực tiếp làm tư liệu chuyển ý. KHÔNG bắt Voice-writer phải đi đọc file cũ (Ví dụ: Bài cũ đã giải quyết nỗi sợ A bằng cách X, nay bài mới sẽ tiếp nối bằng cách chỉ ra rủi ro Y phát sinh sau khi đã làm X).
     - `[BLOCK: VIRAL_SCORE]` — Điểm viral + bảng phân tích
   - Bổ sung: Kịch bản đã dùng.
   - ⛔ **FATAL RULE (nếu chạy Kịch bản 1):** BẮT BUỘC tìm mã bundle key trong khối DIKW của file payload và chèn dòng `<!-- bundle_key: [Mã trích xuất] -->` vào dòng cuối cùng của Idea Brief.
7. **[SCRIPTED VALIDATION]** Chạy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/skills/idea-curator/scripts/validate-idea.ps1" -IdeaPath "[Đường dẫn file Idea Brief]"
   ```
   - **PASS** (exit code = 0, tức 0 FAIL) → Chuyển Phase 2.
   - **REVISE** (exit code > 0) → Sửa Idea Brief theo lỗi báo cáo. Tối đa 3 lần retry.
   - **FAIL 3 lần** → Dừng pipeline, escalate cho User.
   - **Ghi log:** `[Phase 1 Self-Check] Verdict: PASS/REVISE | Attempt: N/3`
