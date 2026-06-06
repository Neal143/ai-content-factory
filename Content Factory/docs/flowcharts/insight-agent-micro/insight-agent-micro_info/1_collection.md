## start
**Điều kiện Đầu vào**
Từ Bảng đen (Global Context), TUYỆT ĐỐI CHỈ truy xuất 2 khối:
1. **`Idea Brief`** (Phase 1 Idea Curator).
2. **`[3-5 Data-Points hoặc Quotes]`** (từ Gói nguyên liệu DIKW).

## collect_data
### Bước 2: Thu thập dẫn chứng
2. Thu thập tối thiểu: **2 studies/data points**, **1 expert authority**, **5 con số cụ thể**.
3. Áp dụng **SAS v18.2** (xem section trên) cho mọi dẫn chứng.
4. Áp dụng **KCS** (xem section trên) cho mỗi framework/concept.
5. Lấy **Atom path** từ cột 1 bảng Gói DIKW — dùng cho `view_file` ở Bước 3.

## find_experts
1. Đọc `[Persona_Path]/authorities.yaml` → tìm experts phù hợp topic.

## apply_filters
**SAS v18.2 — Hệ thống chống bịa chuyện**

**Chỉ 3 nguồn story hợp lệ:**
1. **Vault verified**: Story/data trong `vault/01-Atomic/` với `verified: true` → tag `source: vault`.
2. **Famous World**: Nhân vật/sự kiện nổi tiếng thế giới (Ray Dalio, Steve Jobs, Daniel Kahneman...) → tag `source: famous`.
3. **Published Book**: Câu chuyện từ sách đã xuất bản, ghi rõ tác giả + tên sách → tag `source: book`.

**AUTO-FAIL:**
- Bịa story: "Tôi có một người bạn tên A..."
- Số liệu không nguồn: "Theo nghiên cứu gần đây, 87% người..."
- Trích dẫn giả: Gán lời cho chuyên gia chưa từng nói.
- ⛔ Người Việt KHÔNG có trong vault → KHÔNG dùng.

Vault trống story → dùng famous world / published book / hoặc viết bằng data-research. TUYỆT ĐỐI KHÔNG BỊA.

**KCS — Knowledge Credibility System**

Mỗi khi nhắc Solution/Concept/Framework trong bài, BẮT BUỘC có ≥ 1 Credibility Intro:

| Loại | Fuzzy Definition | Ví dụ |
|------|-----------------|-------|
| **Origin** | Ai/tổ chức nào tạo ra? Bối cảnh uy tín nào đúc kết ra? | "Mô hình DIKW được Kenneth Boulding đề xuất từ 1955..." |
| **Achievement** | Giải quyết bài toán cụ thể nào? Tác động thực tế? | "OKR mà Google dùng quản trị suốt 20 năm qua..." |
| **Scale** | Phổ biến bao nhiêu người/tổ chức? Ảnh hưởng bao nhiêu %? | "Pomodoro được hơn 2 triệu người trên thế giới sử dụng..." |
