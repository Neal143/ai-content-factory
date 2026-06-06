## Start
**Quy tắc Cốt lõi:** Skill này trả về DUY NHẤT 1 TOPIC — hoặc `mapped_topic` hoặc `novel_angle`, không bao giờ cả hai.

## CheckPillarInput
### Bước 1: Xác định Pillar
Đọc `[Persona_Path]/pillars.yaml` (Persona_Path đã xác định ở Bước 3 của workflow). Xác định `Target_Pillar`:

- **A — User KHÔNG nhập Pillar:**
  - In danh sách Pillar đánh số. Thêm option cuối: `N. Hãy chọn cho tôi`.
  - Tư vấn 1 Pillar phù hợp nhất.
  - ⛔ STOP — CHỜ USER PHẢN HỒI. KHÔNG tự chọn.
  - User chọn 1→N-1: chốt `Target_Pillar` → **Bước 2**.
  - User chọn N (ủy quyền): → **Bước 3** (bỏ qua Bước 2).

- **B — User CÓ nhập Pillar:**
  - Semantic Match với `pillars.yaml`.
  - Không khớp: Cảnh báo, in menu chọn lại. Gợi ý có thể chạy `/onboarding-persona` để thêm Pillar mới.
  - Khớp: chốt `Target_Pillar` → **Bước 2**.

## ReadLog1
### Bước 2: Kiểm tra trùng Pillar (Sớm)
Chỉ áp dụng khi User tự chọn Pillar (không ủy quyền).
→ Thực hiện **Pillar Duplicate Check**. Bước kế: **Bước 3**.

### Thủ tục: Pillar Duplicate Check
Đọc `output/logs/production-log.md`. Trích xuất `Pillar` của 2 bài gần nhất.
- Nếu cả 2 trùng với `Target_Pillar` → Dừng, hỏi: *"Pillar **[Target_Pillar]** đã dùng 2 bài liên tiếp. Tiếp tục hay đổi Pillar?"*
  - User tiếp tục → đi tiếp bước kế.
  - User đổi → quay Bước 1.
- Nếu không trùng → đi tiếp.
