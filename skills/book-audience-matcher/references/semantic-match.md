---
name: 3-Verdict LLM Semantic Match & Hierarchy Collapsing
description: 3-Verdict LLM Semantic Match và cơ chế so khớp 3 Tầng để Phẳng hóa 100% rác lưu trữ Audience
---

# 3-Verdict LLM Semantic Match (Audience Resolution)

Bản chất tối thượng của tiến trình này là nhằm **Nhận diện và Sắp xếp các tập khách hàng vớt được từ Sách (Book Audience & Chunk Audience)** vào đúng vị trí trên Cây Phả hệ phân cấp của Vault. 
Hệ thống quản lý cấu trúc phả hệ theo nguyên lý Vô Cấp (Level-free). Level của một Audience BẮT BUỘC phải là TÍNH CHẤT PHÁI SINH từ mảng Parent của nó bằng các quy tắc toán học biểu đồ DAG:

| Mảng Parent chứa | → Quy tắc phái sinh tự động (Level Kế cận) |
|---|---|
| Rỗng `[]` (Không có cha) | Gán định mức là **big** (Root Audience). |
| Có các parent chứa Level | Lấy min parent (parent có cấp bậc nhỏ, hẹp nhất). Nếu min parent = `big` → gán `little`. Nếu min parent = `little` hoặc `micro` → gán `micro`. |

Để giảm tải Review mệt mỏi cho Human và giữ nguyên vẹn Mạng lưới Phả hệ, hệ thống ngăn chặn Duplicate qua cơ chế: Quét Nội Bộ (Internal Dedup), Quét Ngoại Biên (External Index 3-Verdict Semantic Match) và Nhánh Gộp Chéo (Parent Append).

## Phần 1: Chuẩn bị Query Variables
Từ JTBD object đã được calibrate ở Giai đoạn 1, LLM tự sinh **3 giá trị** CHO TOÀN BỘ nhóm sách (Book + toàn bộ Chunks). Các giá trị này sẽ được ghi vào `internal_map.json` (Phần 2A) chứ KHÔNG giữ In-Memory:
1. `id`: English snake_case, giữ nguyên chuẩn cấu trúc 3 phần JTBD: `[job_performer]_[main_job]_[circumstance]`. VD: `new_employee_time_management_first_job`
2. `semantic_query`: Câu tiếng Việt ghép từ 3 field JTBD. VD: *"Người mới đi làm muốn quản lý thời gian khi bắt đầu công việc"*
3. `file_ref`: Wikilink chứa tên file vật lý sẽ tạo (nếu action = create). BẮT BUỘC tuân thủ **Quy Tắc Đặt Tên File (Naming Convention)** sau:
   - Dấu gạch ngang (`-`) nối các từ trong cùng 1 thành phần JTBD.
   - Dấu gạch dưới (`_`) phân tách 3 thành phần JTBD với nhau.
   - Tiếng Việt không dấu, không ký tự đặc biệt, toàn bộ viết thường.
   - **Cú pháp:** `[[[job_performer-slug]_[main_job-slug]_[circumstance-slug]]]`
   - **Ví dụ:** `[[nguoi-moi-di-lam_quan-ly-thoi-gian_bat-dau-cong-viec]]`

## Phần 2A: Quét Nội Bộ (Rolling Dedup & Parent-Child)
Quét Nội Bộ sử dụng cơ chế xử lý tịnh tiến (Rolling Batch) qua cổng xác thực (password gate). Ở mỗi lô dữ liệu (batch), LLM nhận một tập `anchors` (Các Audience đã được xác nhận từ lô trước) và tập `items_to_process` (5 chunks mới).

BẮT BUỘC áp dụng lưới lọc kép khắt khe để đối chiếu:
1. Đối chiếu item mới với tập `anchors`.
2. Đối chiếu các items mới với nhau.

**Output Phase 2A → Submit qua cổng xác thực:**
Kết quả mỗi lô dữ liệu được nộp qua script `prepare_dedup_batches.py` (xem SKILL.md Bước 2.1b). LLM KHÔNG trực tiếp ghi `internal_map.json` — file này do script tự động khởi tạo sau khi quá trình phân lô tịnh tiến hoàn tất.

Schema submission (đối với mỗi lô dữ liệu):
```json
{
  "password": "MẬT KHẨU",
  "entries": [
    {
      "uid": "uid_chunk_XX",
      "id": "cha-me_xay-dung-thoi-quen_thiet-lap-sinh-hoat",
      "semantic_query": "Cha mẹ muốn xây dựng nền tảng thói quen...",
      "file_ref": "[[cha-me_xay-dung-thoi-quen_thiet-lap-sinh-hoat]]",
      "collapse_target": null,
      "internal_parents": ["uid_book"],
      "reason": "Nếu DISTINCT: Nêu điểm khác biệt. Nếu IDENTICAL: Nêu rõ trùng lặp với ai."
    }
  ]
}
```
- `collapse_target`: `null` (nếu DISTINCT), hoặc một uid hợp lệ lấy từ `anchors` hoặc từ các chunk khác trong cùng lô dữ liệu (nếu IDENTICAL).
- `internal_parents`: mảng chứa các uid hợp lệ làm cha của chunk này (từ `anchors` hoặc `items_to_process`).

## Phần 2B: Quét Ngoại Biên (External Match 3-Verdict — Batched)
Gọi script `prepare_audience_batches.py` để phân tách `unique_audiences` thành các lô dữ liệu nhỏ (xem SKILL.md Bước 2.2).
LLM lần lượt xử lý từng lô qua vòng lặp Get→Submit có khóa (xem SKILL.md Bước 2.3), đọc `_audience_index.yaml` và áp dụng 3-Verdict cho từng lô.
Áp dụng nghiêm ngặt lưới so khớp kép 1-1 Structural & Semantic khắt khe sau:

```text
NEW id (EN)             ──so sánh với──→  EXISTING id (Tín hiệu Chính: Structural/Skeleton Match)
NEW semantic_query (VN) ──so sánh với──→  EXISTING semantic_query (và mảng aliases) (Tín hiệu Phụ: Semantic ngầm định)
                                                ↓
                                            Verdict: IDENTICAL / DISTINCT / AMBIGUOUS
```

| Verdict | Hành Động | Cơ Chế Xử Lý Liên Kết Kép (Parent Array) |
|---|---|---|
| `IDENTICAL` | `merge` | Mảng Parent Cũ của file VẪN ĐƯỢC CHECK lại. Nếu LLM vừa phát hiện nhóm Parent mới **(CHỈ TỪ vòng quét nội bộ 2A)** mà file Cũ CHƯA CÓ → Ghi chèn lệnh **APPEND (Bổ sung)** list Parent mới đó vào thẳng file Cũ. Tuyệt đối không tự suy luận Parent mới từ Index cho file đã trùng. |
| `DISTINCT` | `create` | Truy rà toàn vòng Index xem *"Có gốc Audience hiện hữu nào bao trùm Job này không?"*. **CHÚ Ý:** Có thể có NHIỀU Parent bao trùm trực tiếp từ nhiều khía cạnh khác nhau (Vd: Khía cạnh Độ tuổi và Khía cạnh Chuyên môn). Tuy nhiên, **trên cùng một trục phả hệ**, tuyệt đối không vơ vét các Audience khổng lồ (Grandparent/Root) nếu đã chọn Parent trung gian. Nếu có, mảng Parent này lập tức hợp với mảng Parent Nội Bộ từ phần 2A. |
| `AMBIGUOUS` | `Human Gate`| Tạm dừng. Hỏi Chat: *"JTBD `[mới]` tương đồng `[[Cũ]]`. Chọn: (1) Hợp nhất / (2) Tạo mới?"*. Theo đó mà xử lý tiếp nhánh Merge/Create. |

> **🔥 QUY TẮC TỐI THƯỢNG: TRUY HỒI ĐỊNH DANH (Reference Substitution)**
> Bước này được thực hiện TỰ ĐỘNG bởi script `compile_decision_map.py` (Bước 2.4 trong SKILL.md). LLM KHÔNG CẦN tự thay thế biến. Chỉ cần xuất đúng `uid` trong `internal_parents` ở Bước 2.1 là đủ.
## Phần 3: Quyết Toán Decision Map (Tự động)

Sau khi LLM hoàn tất Bước 2.3 (toàn bộ batch đã submit PASS), gọi script `compile_decision_map.py` (Bước 2.4 trong SKILL.md).
Script tự động thực hiện:
1. Reference Substitution: Thay thế uid trong internal_parents bằng audience_filename thực tế.
2. Expand chunk_mapping: Sinh đầy đủ entries cho mọi chunk (kể cả chunk bị gộp nội bộ).
3. Resolve internal parents cho merge: Kiểm tra parent mới chưa có trong file cũ → đưa vào parent_audience.
4. Tính Level theo DAG: parent rỗng → big; parent big → little; parent little/micro → micro.
5. Ghi ra `audience_decision_map.json` đúng chuẩn schema hiện hành.
