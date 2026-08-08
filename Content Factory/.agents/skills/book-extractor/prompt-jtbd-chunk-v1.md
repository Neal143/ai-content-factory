---
name: JTBD Chunk Audience Identifier v2
description: >
  Prompt chuyên biệt để NLM xác định JTBD audience cho từng chunk sách.
  Được sử dụng trong Phase 1 của 2-phase extraction flow.
  Last update: 09/08/2026 (GMT+7)
---

# JTBD Audience Identifier — Chunk Level

## Nhiệm vụ
Xác định chính xác JTBD (Jobs-To-Be-Done) audience cho chunk sách được chỉ định.

## Context
- **Tên chunk:** `[CHUNK_NAME]`
- **Chunk index:** `[CHUNK_INDEX]`
- **JTBD Audience cấp sách:** `[BOOK_AUDIENCE]`

## Output Format BẮT BUỘC
TUYỆT ĐỐI KHÔNG chào hỏi, KHÔNG giải thích lân la. Bạn CHỈ được phép xuất đúng định dạng sau:

```
_Căn cứ phân tầng:_ [Phân tích ngắn gọn phạm vi của chunk để quyết định tầng Job phù hợp]
_Phân tầng Job:_ [Điền chính xác "Big Job" hoặc "Little Job"]
_Tự kiểm thử:_ [Trả lời NHANH 3 câu hỏi: 1. Main Job có Đơn trị không (có chứa "và/hoặc" không)? 2. Main Job đã sạch giải pháp cụ thể và tính từ chất lượng chưa? 3. Circumstance đã bắt đầu bằng "khi" và có chủ ngữ chưa?]
META_CHUNK_AUDIENCE: chunk_audience=[Điền CHÍNH XÁC 1 câu JTBD theo quy trình bên dưới]
_Căn cứ:_ [Trích dẫn nguyên văn tối đa 5 câu từ chunk — TUYỆT ĐỐI KHÔNG tự sáng tác]
```

**Công thức:** `"Người" muốn [Main Job] khi [Circumstances]`
- Chữ **"Người"** là hằng số cố định, KHÔNG thay thế bằng chức danh.

---

## Quy trình xác định Main Job

Main Job là **việc/nhiệm vụ chức năng cụ thể DUY NHẤT** mà tác giả viết nội dung của chunk này để giúp người đọc hoàn thành.

**Công thức phát biểu:** `Động từ + Tân ngữ + [Clarifier tùy chọn]`

Ví dụ mẫu chuẩn:
- "Thiết lập nếp sinh hoạt cho con" *(Verb + Object + Clarifier)*
- "Lập ngân sách gia đình" *(Verb + Object)*
- "Nhận diện dấu hiệu kiệt sức" *(Verb + Object)*

### Phân tầng Job — Nhắm đúng mức trừu tượng

Main Job có 4 tầng. Bạn **BẮT BUỘC** nhắm vào **Big Job** hoặc **Little Job**.

| Tầng | Đặc điểm nhận dạng | Ví dụ | Phán định |
|---|---|---|---|
| Aspiration | Verb ongoing, không có điểm kết thúc, chứa Need/Why | "Nuôi dạy con", "Phát triển kỹ năng tự học", "Quản lý tài chính gia đình" | ❌ QUÁ CAO — tìm job cụ thể hơn |
| **Big Job** | Nhiệm vụ bao trùm, telic, không chứa giải pháp cụ thể | "Thiết lập môi trường chơi cho trẻ tại nhà", "Thiết lập nếp sinh hoạt cho trẻ" | ✅ ĐẠT CHUẨN |
| **Little Job** | Nhiệm vụ cụ thể hơn, vẫn telic, vẫn không chứa giải pháp | "Chọn lọc đồ chơi phù hợp cho trẻ", "Lập thời gian biểu hoạt động cho trẻ" | ✅ ĐẠT CHUẨN |
| Micro Job | Task cơ học, hành vi trực tiếp có thể quan sát bằng mắt | "Mặc quần áo cho con", "Xếp khối gỗ vào kệ", "Đỗ xe" | ❌ QUÁ THẤP — tìm job tổng quát hơn |

### Bước 1: Tìm tín hiệu Job trong chunk

Tác giả sách tri thức thường nhắc đến việc/nhiệm vụ muốn giải quyết cho người đọc rất ít (1-2 lần). Tìm tín hiệu:
- Đầu hoặc cuối chapter: "Chương này giúp bạn...", "Mục tiêu là..."
- Suy từ nội dung: chunk dạy/hướng dẫn người đọc hoàn thành việc gì cụ thể?

> **Lưu ý:** Không nhầm "vấn đề" (bao gồm cả nhu cầu/kỳ vọng) với "việc/nhiệm vụ".
> - Vấn đề: "Cha mẹ muốn con 2 tuổi nghe lời nhưng con chống đối" (chứa cả Need/Why)
> - Việc: "Đạt được sự hợp tác của trẻ trong các hoạt động hàng ngày" (chỉ Main Job)

### Bước 2: Kiểm tra tính ĐƠN TRỊ

Main Job phải là DUY NHẤT 1 hành động. Nếu phát hiện nhiều hành động (tín hiệu: chứa "và", "hoặc", dấu phẩy "," hoặc chấm phẩy ";"):
→ Hỏi "Why?" 1 lần để gộp thành 1 Bigger Job bao trùm.

| Sai (compound) | Why? | Đúng (1 Bigger Job) |
|---|---|---|
| "Rửa rau và cắt thịt" | Để chuẩn bị bữa ăn | "Chuẩn bị bữa ăn" |
| "Điều chỉnh quần áo, mũ đội đầu cho trẻ" | Để bảo vệ thân nhiệt | "Bảo vệ thân nhiệt cho trẻ" |
| "Sắp xếp thời gian ăn, ngủ và chơi" | Để thiết lập nếp sinh hoạt | "Thiết lập nếp sinh hoạt cho trẻ" |

### Bước 3: Kiểm tra trạng thái kết thúc (Telic Test)

Áp dụng Litmus Test: "[Tân ngữ] đã được [Verb] → người đọc có thể dừng lại vì mục tiêu đã đạt?"

| Sai (ongoing) | Test | Đúng (telic) |
|---|---|---|
| "Quản lý tài chính" | "Tài chính đã được quản lý → dừng?" → Không | "Lập ngân sách gia đình" |
| "Nuôi dạy con" | "Con đã được nuôi dạy → dừng?" → Không | "Thiết lập kỷ luật cho con" |
| "Chăm sóc sức khỏe" | "Sức khỏe đã được chăm sóc → dừng?" → Không | "Nhận diện dấu hiệu kiệt sức" |

### Bước 4: Trừu tượng hóa — Loại bỏ giải pháp/công cụ cụ thể

Main Job phải ổn định qua thời gian, không gắn với công cụ hay phương pháp cụ thể. Nếu Main Job chứa tên công cụ, vật liệu, hoặc giải pháp cụ thể → trừu tượng hóa lên mục tiêu gốc.

| Sai (chứa giải pháp) | Đúng (mục tiêu gốc) |
|---|---|
| "Chuẩn bị khối gỗ, vỏ sò và khăn vải" | "Trang bị không gian chơi cho trẻ" |
| "Dùng ChatGPT viết email" | "Soạn email chuyên nghiệp" |
| "Loại bỏ đồ chơi nhựa khỏi phòng" | "Chọn lọc đồ chơi phù hợp cho trẻ" |

### Bước 5: Loại bỏ Need/Why

Tách triệt để mục tiêu (Job) ra khỏi nhu cầu/thước đo thành công (Need/Why). Ba nhóm cần loại bỏ:

1. **Tính từ chỉ chất lượng:** nhanh, dễ dàng, hiệu quả, an toàn, toàn diện...
2. **Kỳ vọng cảm xúc:** tận hưởng, mà không, bớt lo lắng...
3. **Mệnh đề mục đích:** nhằm..., sao cho..., để mà...

| Sai | Loại lỗi | Đúng |
|---|---|---|
| "Quản lý tài chính **hiệu quả**" | Qualifying adj | "Lập ngân sách gia đình" |
| "Kế hoạch kỳ nghỉ **mà gia đình tận hưởng**" | Emotional | "Lên kế hoạch kỳ nghỉ gia đình" |
| "Nấu ăn **nhằm đảm bảo dinh dưỡng**" | Purpose clause | "Chuẩn bị bữa ăn cho gia đình" |

---

## Quy trình xác định Circumstances

Circumstances là **bối cảnh/tình huống của Main Job của người đọc đã được xác định trước đó**, KHÔNG phải bối cảnh viết sách, bối cảnh tác giả, hay bối cảnh nội dung chapter.

**Cấu trúc bắt buộc:** Bắt đầu bằng _"khi..."_

**3 chiều kích bối cảnh hợp lệ:**
1. **Thời gian:** Khi nào? (khi trẻ bước vào tuổi lên 3, khi mùa đông đến)
2. **Địa điểm:** Ở đâu? (tại nhà, tại trường)
3. **Trạng thái tình huống:** Ai đang làm gì? (khi cha mẹ thiết lập nếp sinh hoạt chung)

**Quy tắc chủ ngữ:** Khi circumstance liên quan đến hành vi/trạng thái của ai đó, BẮT BUỘC nêu rõ chủ thể.
- ❌ "Khi đối mặt với áp lực" → ✅ "Khi cha mẹ đối mặt với áp lực từ con"

**Được phép:** Dùng "và", "hoặc", dấu phẩy "," hoặc chấm phẩy ";" để mô tả nhiều điều kiện đồng thời trong cùng 1 tình huống.

**CẤM TUYỆT ĐỐI:**
- Cấm nhét Insight (nỗi đau, bế tắc, nỗi sợ) vào Circumstances.
- Cấm tính từ chỉ chất lượng, kỳ vọng cảm xúc, mệnh đề mục đích (áp dụng Bước 5).

---

## Chống ảo giác

Đọc kỹ TOÀN BỘ nội dung chunk. Nếu chunk thuần túy tả cảnh, dẫn nhập, chuyện phiếm và KHÔNG hướng đến giải quyết "việc/nhiệm vụ" nào của người đọc → TUYỆT ĐỐI KHÔNG cố nặn ra JTBD. Trả:
```
META_CHUNK_AUDIENCE: chunk_audience=[NO_JTBD_FOUND]
```
