---
name: post-audience-matcher
description: "Bước 2/4 của PostClassifierAgent: Đối chiếu ngữ nghĩa JTBD đã hiệu đính với _audience_index.yaml để quyết định tái sử dụng (reuse - ưu tiên tuyệt đối) hoặc khởi tạo mới (create) kèm khóa phả hệ DAG."
last_update: 10/11/2026 19:50 (GMT+7)
---

# Post Audience Matcher Skill (Bước 2/4)

> **Tên file**: .agents/skills/post-audience-matcher/SKILL.md
> **Last update**: 10/11/2026 19:50 (GMT+7)
> **Vai trò**: Nhận JTBD đã hiệu đính từ Bước 1 và danh sách Audience hiện có trong `vault/01-Atomic/Audiences/_audience_index.yaml`, thực hiện Semantic Match để chốt `reuse` hoặc `create`.
> **Sử dụng khi**: Được gọi ở Bước 2 bởi `PostClassifierAgent` / `classify_vault_posts.py`.
> **Output**: JSON chứa mảng `audiences` đã chốt.
> **Tóm tắt logic hoạt động**: Đối chiếu ngữ nghĩa từng JTBD đã hiệu đính với toàn bộ mục trong `_audience_index.yaml`. Ưu tiên tối đa `reuse` khi cùng bản chất công việc/hoàn cảnh. Nếu bắt buộc `create`, đặt tên slug 3 phần, bắt buộc khóa `parent_audience` về Big Audience gốc hoặc Little Audience gần nhất (không để mồ côi) và xác định `audience_level` ("little" hoặc "micro").

## 1. QUY TẮC SO KHỚP NGỮ NGHĨA (SEMANTIC MATCH)

Với mỗi JTBD đã hiệu đính từ Bước 1 (`audience_Job_performer`, `audience_main_job`, `audience_circumstance`), đối chiếu với toàn bộ các mục trong `_audience_index.yaml`:

### Trường hợp 1: `action = "reuse"` (Verdict: `IDENTICAL` — ƯU TIÊN TUYỆT ĐỐI)
- **Điều kiện**: Trong `_audience_index.yaml` đã tồn tại một Audience có **cùng bản chất công việc (`main_job`) và cùng hoàn cảnh cốt lõi (`circumstance`)**, kể cả khi dùng từ đồng nghĩa hoặc diễn đạt lại (VD: *"tại nhà"* vs *"tại gia đình"*, *"độ tuổi mầm non"* vs *"từ 0 đến 7 tuổi"*, *"định hướng giáo dục"* vs *"chọn phương pháp giáo dục"*). BẮT BUỘC ưu tiên chọn `"action": "reuse"` để chống phân mảnh phả hệ Audience.
- **Hành động**:
  - Đặt `"action": "reuse"`.
  - Điền nguyên văn `file_ref` của mục trùng khớp trong Index vào `"matched_file_ref"` (VD: `"[[cha-me_chon-truong-tieu-hoc-cho-con_khi-con-chuan-bi-vao-lop-1]]"`).
  - Giữ nguyên `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `audience_level`, `parent_audience` theo mục đã có trong Index.

### Trường hợp 2: `action = "create"` (Verdict: `DISTINCT`)
- **Điều kiện**: Chưa có bất kỳ Audience nào trong `_audience_index.yaml` có cùng mục tiêu chức năng hoặc cùng hoàn cảnh kích hoạt đó.
- **Hành động bắt buộc**:
  1. **Đặt tên `audience_filename` theo chuẩn Naming Convention 3 phần**:
     - Cấu trúc: `[job-performer-slug]_[main-job-slug]_[circumstance-slug]`
     - Tiếng Việt không dấu, chữ thường, các từ trong cùng 1 phần nối bằng dấu gạch ngang (`-`), 3 phần ngăn cách bằng dấu gạch dưới (`_`), mỗi phần cô đọng 3–6 từ khóa cốt lõi.
     - Ví dụ: `"cha-me_thiet-lap-ky-luat-sinh-hoat_khi-con-buoc-vao-tuoi-day-thi"`
  2. **Truy tìm `parent_audience` trong `_audience_index.yaml` (BẮT BUỘC CÓ PARENT)**:
     - Rà soát `_audience_index.yaml` để chọn Audience cấp `big` hoặc `little` bao trùm trực tiếp Job này.
     - Nếu không có Little Audience nào bao trùm trực tiếp: **BẮT BUỘC** gán `parent_audience` về Big Audience gốc (`audience_level: "big"`) của Persona trong `_audience_index.yaml` và đặt `"audience_level": "little"`. Tuyệt đối KHÔNG để `parent_audience: []` và KHÔNG tự tạo mới `audience_level: "big"`.
  3. **Suy diễn `audience_level` theo DAG Level Rule**:
     - Nếu `parent_audience` chỉ chứa parent cấp `"big"` → `"audience_level": "little"`.
     - Nếu `parent_audience` có chứa parent cấp `"little"` hoặc `"micro"` → `"audience_level": "micro"`.

## 2. ĐỊNH DẠNG JSON ĐẦU RA
Chỉ trả về JSON theo cấu trúc:
```json
{
  "audiences": [
    {
      "action": "reuse",
      "matched_file_ref": "[[cha-me_chon-truong-tieu-hoc-cho-con_khi-con-chuan-bi-vao-lop-1]]",
      "audience_filename": "",
      "audience_level": "little",
      "audience_Job_performer": "Cha mẹ",
      "audience_main_job": "Chọn trường tiểu học cho con",
      "audience_circumstance": "Khi con chuẩn bị bước vào lớp 1",
      "parent_audience": ["[[cha-me_dinh-huong-lo-trinh-giao-duc-cho-con_khi-con-o-do-tuoi-pho-thong]]"],
      "aliases": ["Cha mẹ muốn Chọn trường tiểu học cho con (Khi con chuẩn bị bước vào lớp 1)"],
      "reasoning": "Trùng khớp ngữ nghĩa hoàn toàn với Audience hiện có trong Index"
    }
  ]
}
```
