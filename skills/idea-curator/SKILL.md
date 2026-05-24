---
name: Idea Curator
description: Skill Phase 1 — Phân tích topic, tìm góc nhìn contrarian và đánh giá tiềm năng viral.
---

# Idea Curator (Phase 1)

> EXECUTION_KEY: c3a154e0

## Điều kiện Đầu vào
1. **`topic`**: ID chủ đề bài viết (String).
2. **`Target_Pillar`**: Pillar thương hiệu đã phân loại bởi Semantic Router.
3. **`Target_Audience`**: Đối tượng độc giả (chỉ có khi `Is_Novel_Angle == False`).
4. **`Gói nguyên liệu DIKW (Atomic Combo)`**: Các file `Insight`, `Solution/Concept` từ Vault (chỉ có khi Kịch bản 1).

## Luồng Xử lý (2-Mode)

### Kịch bản 1: Thuần Vault (Standard)
- **Điều kiện:** `Is_Novel_Angle == False` + `Gói nguyên liệu DIKW (Atomic Combo)` hợp lệ.
- **Hành động:** BẮT BUỘC tham chiếu 100% Insight + Solution/Concept từ Vault. Không sáng tạo vượt xa nguồn.

### Kịch bản 2: Suy luận Sáng tạo (Fallback)
- **Điều kiện:** `Is_Novel_Angle == True` HOẶC DIKW trả về rỗng.
- **Hành động:** Dùng kiến thức LLM sáng tạo dựa trên `topic` + `Target_Pillar`. TUYỆT ĐỐI CẤM kết hợp chéo Data Vault.

---

## Khởi tạo Idea Brief
1. Tìm góc nhìn contrarian (dựa theo Vault hoặc Improvise): Điều gì đa số người ta tin là đúng nhưng thực ra sai (hoặc ngược lại)?
2. Xác định **Core Tension**: Mâu thuẫn cốt lõi mà reader đang chịu đựng (vd: muốn dành thời gian cho con nhưng bận kiếm tiền).
3. Xác định **Hidden Belief**: Niềm tin ẩn mà bài viết sẽ phá vỡ (vd: "cho con xem iPad là bình thường vì ai cũng làm vậy").
4. Xác định **Transformation Promise**: Reader thay đổi gì sau khi đọc? (before → after rõ ràng).
5. Chấm **Viral Score** (tổng /10, cần ≥ 7):

| Tiêu chí | Trọng số | Mô tả |
|----------|---------|-------|
| Gây tranh cãi | 4đ | Topic có đi ngược lại niềm tin phổ biến không? |
| Cá nhân hóa | 3đ | Người đọc có thấy mình trong đó không? |
| Ứng dụng tức thời | 3đ | Đọc xong có thể làm ngay không? |

6. Xuất **Idea Brief** gồm:
   - ⛔ BẮT BUỘC giữ nguyên văn từ Blackboard: `topic` (NGUYÊN VĂN GỐC), `Target_Pillar` (NGUYÊN VĂN GỐC), `Target_Audience` (nếu có), `Is_Novel_Angle`.
   - Bổ sung: Contrarian Angle, Core Tension, Hidden Belief, Transformation Promise, Viral Score, Kịch bản đã dùng.
7. **[SCRIPTED VALIDATION]** Chạy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/skills/idea-curator/scripts/validate-idea.ps1" -IdeaPath "[Đường dẫn file Idea Brief]"
   ```
   - **PASS** (exit code = 0, tức 0 FAIL) → Chuyển Phase 2.
   - **REVISE** (exit code > 0) → Sửa Idea Brief theo lỗi báo cáo. Tối đa 3 lần retry.
   - **FAIL 3 lần** → Dừng pipeline, escalate cho User.
   - **Ghi log:** `[Phase 1 Self-Check] Verdict: PASS/REVISE | Attempt: N/3`
