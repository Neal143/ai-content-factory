---
name: post-jtbd-calibrator
description: "Bước 1/4 của PostClassifierAgent: Phân loại hình thái bài viết (post_format), lọc bài tạp (no_jtbd_found), khóa luận điểm trung tâm (core_thesis), chọn Pillar và trích xuất JTBD đạt chuẩn Problem Space."
last_update: 10/11/2026 19:50 (GMT+7)
---

# Post JTBD Calibrator Skill (Bước 1/4)

> **Tên file**: .agents/skills/post-jtbd-calibrator/SKILL.md
> **Last update**: 10/11/2026 19:50 (GMT+7)
> **Vai trò**: Đọc nội dung bài viết trong `vault/03-Content/Viral Posts/` để phân loại hình thái bài viết, lọc rác/bài tạp (`no_jtbd_found`), khóa luận điểm trung tâm (`core_thesis`), chọn Pillar mục tiêu (`target_pillar`), và nhận diện hiệu đính JTBD (`audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `aliases`) đạt chuẩn Problem Space.
> **Sử dụng khi**: Được gọi ở Bước 1 bởi `PostClassifierAgent` / `classify_vault_posts.py`.
> **Output**: JSON chứa `no_jtbd_found`, `post_format`, `core_thesis`, `target_pillar` và mảng `calibrated_jtbds`.
> **Tóm tắt logic hoạt động**: Nhận nội dung bài viết sạch -> Phân loại `post_format` (`deep_dive`, `listicle`, `summary`, `news`, `noise`) -> Nếu là `noise` (không có giá trị tri thức/JTBD) thì xuất `no_jtbd_found: true` để dừng sớm -> Nếu hợp lệ, khóa `core_thesis` (chiếm >= 70% dung lượng) và ánh xạ vào `target_pillar` thích hợp nhất -> Hiệu đính JTBD qua 12 quy tắc Problem Space -> Xuất JSON chuẩn hóa.

## 1. NGUYÊN TẮC CỐT LÕI & CỔNG LỌC BÀI TẠP (`[NO_JTBD_FOUND]`)
1. **Tiếng Việt có dấu chuẩn 100%** cho toàn bộ các trường.
2. **Phân loại Hình thái Bài viết (`post_format`) & Cổng chặn bài tạp (`no_jtbd_found`)**:
   - `deep_dive`: Bài phân tích chuyên sâu 1 luận điểm/vấn đề trọng tâm.
   - `listicle`: Bài tổng hợp liệt kê nhiều mục/lời khuyên (`1, 2, 3...`).
   - `summary`: Bài tóm tắt/điểm sách, dịch bài phát biểu/nghiên cứu của tác giả/diễn giả khác.
   - `news`: Bài bình luận tin tức thời sự, sự kiện xã hội, lễ hội mùa hoặc thông báo sự kiện chuyên môn (Open Day/Hội thảo).
   - `noise`: Bài đăng ảnh khoảnh khắc đời thường/kể chuyện vụn vặt không có luận điểm hướng dẫn hay phân tích, bài chúc lễ Tết xã giao, thông báo hành chính/nghỉ lễ/tuyển dụng nội bộ.
   - ⛔ **CỔNG `[NO_JTBD_FOUND]`**: Nếu bài viết thuộc dạng `noise` (không giải quyết bất kỳ Big/Little Job nào của độc giả), BẮT BUỘC trả về `"no_jtbd_found": true`, `"post_format": "noise"`, `"core_thesis": ""`, `"target_pillar": ""`, `"calibrated_jtbds": []`.
3. **Khóa Luận điểm Trung tâm (`core_thesis`) & Trụ cột (`target_pillar`)**:
   - `core_thesis`: Tóm tắt trong 1–2 câu luận điểm chính chiếm $\ge 70\%$ dung lượng bài viết (bỏ qua các ví dụ mở bài hoặc câu chuyện dẫn nhập).
   - `target_pillar`: Chọn chính xác tên 1 trong 4 Pillar chuyên môn từ danh sách Pillars được cung cấp phù hợp nhất với `core_thesis`.
4. **Mỗi bài viết hợp lệ ưu tiên xác định 1 JTBD trung tâm duy nhất** đại diện cho toàn bài (tối đa 2 nếu bài thực sự phục vụ 2 hoàn cảnh tách biệt).
5. **Phân tầng độ lớn của Main Job (Chỉ chọn Big Job hoặc Little Job):**
   - ❌ **Aspiration (Quá rộng — CẤM):** Động từ tiếp diễn không có điểm kết thúc (*"Nuôi dạy con"*, *"Quản lý tài chính"*, *"Phát triển bản thân"*). Phải hạ xuống nhiệm vụ có điểm hoàn tất rõ ràng.
   - ✅ **Big Job / Little Job (Hợp lệ):** Nhiệm vụ chức năng có chủ đích và có điểm hoàn thành (*"Thiết lập nếp sinh hoạt cho trẻ"*, *"Chọn trường tiểu học cho con"*, *"Xử lý cơn ăn vạ của con"*).
   - ❌ **Micro Job (Quá vụn — CẤM):** Thao tác cơ học (*"Mặc quần áo cho con"*, *"Mở sách ra đọc"*). Phải hỏi *"Why?"* 1 bậc để nâng lên Little/Big Job.

## 2. BẢNG 12 QUY TẮC HIỆU ĐÍNH JTBD (CALIBRATION CHECKLIST)

### A. 7 Quy tắc cho `audience_main_job` (`Động từ + Tân ngữ + [Clarifier phẳng]`)
| # | Quy tắc | Hướng dẫn xử lý | Ví dụ SAI ❌ → ĐÚNG ✅ |
| :--- | :--- | :--- | :--- |
| **#1** | **Bắt đầu bằng động từ** | Bỏ từ đệm/xưng hô đầu câu (*"Giúp tôi..."*, *"Cách để..."*) | ❌ *"Giúp tôi lên kế hoạch kỳ nghỉ"* → ✅ **"Lên kế hoạch kỳ nghỉ gia đình"** |
| **#2** | **Đơn trị (Atomic)** | CẤM chứa *"và"*, *"hoặc"*, *"kiêm"*, *"đồng thời"*. Hỏi *"Why?"* 1 lần để gộp thành 1 Job | ❌ *"Rửa rau và cắt thịt"* → ✅ **"Chuẩn bị bữa ăn gia đình"** |
| **#3** | **Có chủ đích (Purposeful)** | Thay hành vi cơ học bằng mục tiêu chức năng thực sự | ❌ *"Nhìn vào bảng điểm của con"* → ✅ **"Đánh giá năng lực học tập của con"** |
| **#4** | **Hướng đích (Telic)** | Litmus Test: *"[Tân ngữ] đã được [Verb] xong → có thể dừng lại vì mục tiêu đợt này đã đạt?"* Nếu KHÔNG → đổi sang động từ telic có điểm hoàn tất (nhưng không rơi vào cơ học #3) | ❌ *"Nuôi dưỡng trẻ"* (Ongoing) / ❌ *"Cho con ăn"* (Cơ học) → ✅ **"Thiết lập chế độ dinh dưỡng cho con"** |
| **#5** | **Góc nhìn Performer** | Bỏ lớp quan sát/sở thích bên ngoài | ❌ *"Cha mẹ muốn tìm trường cho con"* → ✅ **"Chọn trường học cho con"** |
| **#6** | **Phi giải pháp** | Xóa tên công nghệ, phương pháp, thương hiệu khỏi Job | ❌ *"Dùng kỷ luật tích cực để rèn con"* → ✅ **"Uốn nắn hành vi lệch chuẩn của con"** |
| **#7** | **Kiểm tra ngược cuối** | Đảm bảo sau khi sửa vẫn thỏa mãn đồng thời #1 đến #6 | ❌ *"Quản lý cảm xúc của con"* → ✅ **"Đồng hành cùng con vượt qua khủng hoảng tâm lý"** |

### B. 2 Quy tắc cho `audience_circumstance`
- **#8 — Mở đầu bằng `"Khi..."`**: Bắt buộc bắt đầu bằng chữ **`"Khi..."`** (mô tả Thời gian / Địa điểm / Tình huống khách quan).
- **#9 — Chủ ngữ tường minh**: CẤM ẩn chủ ngữ khi nói về hành vi/trạng thái (❌ *"Khi đối mặt với áp lực thi cử"* → ✅ **"Khi con bước vào giai đoạn ôn thi chuyển cấp"**).

### C. 3 Quy tắc Problem Space (Áp dụng cho cả `audience_main_job` & `audience_circumstance`)
| # | Thành phần bị cấm trong Job & Circumstance | Cách hiệu chỉnh để giữ thuần Problem Space |
| :--- | :--- | :--- |
| **#10** | **Tính từ/trạng từ chỉ chất lượng hiệu suất:** *nhanh, dễ dàng, rẻ, an toàn, toàn diện, hiệu quả, chính xác, bền vững, tối ưu, đúng đắn...* | Xóa tính từ/trạng từ chỉ chất lượng khỏi `audience_main_job` & `audience_circumstance`, chỉ giữ lại hành động và đối tượng cốt lõi (VD: ❌ *"Chọn trường tiểu học tốt nhất cho con"* → ✅ **"Chọn trường tiểu học cho con"**). |
| **#11** | **Kỳ vọng cảm xúc / Nỗi đau / Tránh tổn thương:** *tận hưởng, bớt lo lắng, hoang mang, bế tắc, "mà không làm tổn thương con"...* | Xóa yếu tố cảm xúc khỏi `audience_main_job` & `audience_circumstance`, chỉ giữ lại sự kiện/trạng thái khách quan (VD: ❌ *"Khi cha mẹ hoang mang vì con nghiện điện thoại"* → ✅ **"Khi thời gian con sử dụng thiết bị điện tử vượt quá giới hạn kiểm soát"**). |
| **#12** | **Mệnh đề mục đích / Hướng cải tiến:** *"nhằm...", "sao cho...", "để mà...", "để tiết kiệm...", "để giúp con tự lập..."* | Xóa mệnh đề mục đích khỏi `audience_main_job` & `audience_circumstance`, chỉ giữ lại bối cảnh phẳng nếu có (VD: ❌ *"Thiết lập kỷ luật cho con để con tự giác học tập"* → ✅ **"Thiết lập kỷ luật sinh hoạt cho con"**). |

### D. `audience_Job_performer` & `aliases`
- `audience_Job_performer`: Danh từ chỉ vai trò cụ thể gắn với Main Job (VD: `"Cha mẹ"`, `"Người quản lý đội nhóm"`, `"Giáo viên"`).
- `aliases`: `["<audience_Job_performer> muốn <audience_main_job> (<audience_circumstance>)"]`.

## 3. ĐỊNH DẠNG JSON ĐẦU RA
Chỉ trả về JSON theo cấu trúc:
```json
{
  "no_jtbd_found": false,
  "post_format": "deep_dive",
  "core_thesis": "Trẻ dưới 7 tuổi học qua bắt chước vô thức từ hành vi thực tế của người lớn chứ không học qua lời giảng giải lý lẽ.",
  "target_pillar": "Xác định triết lý giáo dục cho con",
  "calibrated_jtbds": [
    {
      "audience_Job_performer": "Cha mẹ",
      "audience_main_job": "Thiết lập kỷ luật sinh hoạt cho con",
      "audience_circumstance": "Khi nuôi dạy con trong độ tuổi từ 0 đến 7 tuổi tại gia đình",
      "aliases": ["Cha mẹ muốn Thiết lập kỷ luật sinh hoạt cho con (Khi nuôi dạy con trong độ tuổi từ 0 đến 7 tuổi tại gia đình)"],
      "calibration_reason": "Đã kiểm tra đủ 12 điều kiện Problem Space"
    }
  ]
}
```
