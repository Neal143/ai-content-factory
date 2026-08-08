---
name: JTBD Chunk Audience Identifier v1
description: >
  Prompt chuyên biệt để NLM xác định JTBD audience cho từng chunk sách.
  Được sử dụng trong Phase 1 của 2-phase extraction flow.
  Last update: 04/08/2026 (GMT+7)
---

# JTBD Audience Identifier — Chunk Level

## Nhiệm vụ
Xác định chính xác JTBD (Jobs-To-Be-Done) audience cho chunk sách được chỉ định.

## Context
- **Tên chunk:** `[CHUNK_NAME]`
- **Chunk index:** `[CHUNK_INDEX]`
- **JTBD Audience cấp sách:** `[BOOK_AUDIENCE]`

## Output Format BẮT BUỘC
```
META_CHUNK_AUDIENCE: chunk_audience=[Điền CHÍNH XÁC 1 câu JTBD theo công thức bên dưới]
_Căn cứ:_ [Trích dẫn nguyên văn tối đa 5 câu từ chunk — TUYỆT ĐỐI KHÔNG tự sáng tác]
```

**Công thức:** `"Người" muốn [Main Job] khi [Circumstances]`
- Chữ **"Người"** là hằng số cố định, KHÔNG thay thế bằng chức danh.

---

## Hướng dẫn chi tiết

### 1. Định nghĩa Main Job

Main Job là **việc/nhiệm vụ chức năng cụ thể** mà người đọc muốn hoàn thành:
- Phải có trạng thái "hoàn thành" rõ ràng
- **Test:** "[Tân ngữ] đã được [Verb] → người đọc có thể dừng lại vì mục tiêu đã đạt?" Nếu KHÔNG (vẫn phải tiếp tục ngày mai) → verb ongoing.
  - ✅ "Kế hoạch kỳ nghỉ đã được lên → dừng lại?" → Có → PASS
  - ❌ "Tài chính đã được quản lý → dừng lại?" → Không, ngày mai vẫn phải quản lý → FAIL
- Diễn đạt: _Động từ + Đối tượng_ cụ thể

### 2. Cách tìm Main Job trong sách

Tác giả sách tri thức thường nhắc đến việc/nhiệm vụ muốn giải quyết cho người đọc rất ít (1-2 lần), không phải nội dung chính (so với giải pháp/cảm xúc). Tìm tín hiệu:
- Đầu hoặc cuối chapter: "Chương này giúp bạn...", "Mục tiêu là...", "Sau khi đọc, bạn sẽ..."
- Suy từ nội dung: chunk dạy/hướng dẫn người đọc hoàn thành việc gì cụ thể?

> **Lưu ý:** Không nhầm "vấn đề" (bao gồm cả nhu cầu/kỳ vọng) với "việc/nhiệm vụ".
> - Vấn đề: "Cha mẹ muốn con 2 tuổi nghe lời nhưng con chống đối" (chứa cả Need/Why)
> - Việc: "Đạt được sự hợp tác của trẻ trong các hoạt động hàng ngày" (chỉ Main Job)

### 3. Ổn định qua thời gian

Viết sao cho câu lệnh vẫn đúng ngay cả khi công nghệ thay đổi.

### 4. Tiêu chuẩn bắt buộc

❌ **6 LỖI BỊ CẤM:**

| # | Lỗi | Ví dụ sai → đúng |
|---|---|---|
| [1] | CẤM prefix/xưng hô | ❌ "Giúp tôi lên kế hoạch" → ✅ "Lên kế hoạch kỳ nghỉ" |
| [2] | CẤM "VÀ"/"HOẶC" gộp nhiều ý | ❌ "Nấu ăn và dọn dẹp" → ✅ "Nấu bữa ăn gia đình" |
| [3] | CẤM hành vi cơ học không mục tiêu | ❌ "Nhìn vào bức tranh" → ✅ "Thấu hiểu tác phẩm nghệ thuật" |
| [4] | CẤM công nghệ/giải pháp | ❌ "Dùng ChatGPT viết email" → ✅ "Soạn email chuyên nghiệp" |
| [5] | CẤM góc nhìn quan sát | ❌ "Mọi người thích tham dự..." → ✅ "Tham dự..." |
| [6] | CẤM mệnh đề mục đích (ví dụ: "nhằm...", "sao cho...", "để mà..."...), tính từ/trạng từ chỉ chất lượng (ví dụ: "nhanh", "dễ dàng", "hiệu quả", "an toàn", "toàn diện"...), kỳ vọng cảm xúc (ví dụ: "tận hưởng", "mà không"...) | ❌ "Quản lý tài chính hiệu quả nhằm tự do" → ✅ "Lập ngân sách gia đình" |

Lỗi [6] áp dụng cho cả Main Job và Circumstances.

### 5. Circumstances

- Circumstances là **bối cảnh/tình huống mà NGƯỜI ĐỌC thực hiện Main Job**, KHÔNG phải bối cảnh viết sách, bối cảnh tác giả, hay bối cảnh nội dung chapter.
- BẮT BUỘC bắt đầu bằng _"Khi..."_
- Mô tả tình huống khách quan (Thời gian / Địa điểm / Trạng thái thực hiện Main Job)
- ⚠️ **QUY TẮC CHỦ NGỮ BẮT BUỘC:** Khi Circumstance liên quan đến hành vi/trạng thái của ai đó, BẮT BUỘC nêu rõ chủ thể.
  - ❌ "Khi đối mặt với áp lực" → ✅ "Khi cha mẹ đối mặt với áp lực từ con"
- ⚠️ **CẢNH BÁO:** Cấm tuyệt đối nhét Insight (nỗi đau, bế tắc, nỗi sợ) vào Circumstances.

### 6. Ví dụ tổng hợp

| ❌ Sai | Lý do | ✅ Đúng |
|---|---|---|
| "Quản lý tài chính" | "tài chính đã được quản lý → dừng lại?" → Không → ongoing | "Lập ngân sách gia đình" |
| "Giúp tôi nuôi dạy con" | prefix + "con đã được nuôi dạy → dừng lại?" → Không → ongoing | "Thiết lập kỷ luật cho con" |
| "Nấu ăn hiệu quả và an toàn" | compound + qualifying adj | "Chuẩn bị bữa ăn cho gia đình" |
| "Chăm sóc sức khỏe tâm thần nhằm sống hạnh phúc" | "sức khỏe đã được chăm sóc → dừng lại?" → Không → ongoing + mệnh đề mục đích | "Nhận diện dấu hiệu kiệt sức" |

### 7. Chống ảo giác

Đọc kỹ TOÀN BỘ nội dung chunk. Nếu chunk thuần túy tả cảnh, dẫn nhập, chuyện phiếm và KHÔNG chứa "việc/nhiệm vụ" nào → TUYỆT ĐỐI KHÔNG cố nặn ra JTBD. Trả:
```
META_CHUNK_AUDIENCE: chunk_audience=[NO_JTBD_FOUND]
```
