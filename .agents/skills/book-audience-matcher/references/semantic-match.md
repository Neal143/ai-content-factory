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

## Phần 1: Chuẩn bị Query (In-Memory Variables)
Từ JTBD object đã được calibrate ở Giai đoạn 1, LLM tự sinh **3 giá trị** trong working memory (không gọi script ngoài) CHO TOÀN BỘ nhóm sách (Book + toàn bộ Chunks). Đây là 3 tham biến cấu trúc bắt buộc phải được duy trì xuyên suốt mọi vòng lặp Giai đoạn 2 và 3, nghiêm cấm lược bỏ:
1. `id`: English snake_case, giữ nguyên chuẩn cấu trúc 3 phần JTBD: `[job_performer]_[main_job]_[circumstance]`. VD: `new_employee_time_management_first_job`
2. `semantic_query`: Câu tiếng Việt ghép từ 3 field JTBD. VD: *"Người mới đi làm muốn quản lý thời gian khi bắt đầu công việc"*
3. `file_ref`: Wikilink chứa tên file vật lý sẽ tạo (nếu action = create). BẮT BUỘC tuân thủ **Quy Tắc Đặt Tên File (Naming Convention)** sau:
   - Dấu gạch ngang (`-`) nối các từ trong cùng 1 thành phần JTBD.
   - Dấu gạch dưới (`_`) phân tách 3 thành phần JTBD với nhau.
   - Tiếng Việt không dấu, không ký tự đặc biệt, toàn bộ viết thường.
   - **Cú pháp:** `[[[job_performer-slug]_[main_job-slug]_[circumstance-slug]]]`
   - **Ví dụ:** `[[nguoi-moi-di-lam_quan-ly-thoi-gian_bat-dau-cong-viec]]`

## Phần 2A: Quét Nội Bộ (Internal Dedup & Parent-Child)
Thuật toán phân kỳ mảng Input (1 Book + N Chunks) thành 1 lô (Batch). Toàn bộ thuật toán nội bộ chạy In-Memory. Tại vòng này, BẮT BUỘC áp dụng lưới lọc kép khắt khe để đối chiếu chéo tuần tự các entry với nhau:
- **Tín hiệu Chính:** So khớp `id` (nếu `id` giống nhau hoàn toàn, khả năng cực cao là cùng 1 Audience).
- **Tín hiệu Phụ:** So khớp `semantic_query` (đọc câu tiếng Việt để verify lại chắc chắn 2 Job này là một).
1. **Lọc Trùng Lặp (IDENTICAL):** Chunk nào có cặp tín hiệu kép (`id` + `semantic_query`) trùng khớp hoàn toàn với Book hoặc Chunk phía trước → Collapse (gộp chung cụm, mượn chung định danh Unique nhóm).
2. **Xử Lý Mơ Hồ (AMBIGUOUS):** Nếu 2 entry có `semantic_query` na ná nhau làm LLM phân vân, BẮT BUỘC kích hoạt Human Gate: *"Khối nội bộ `[Chunk A]` khá giống `[Chunk B]`. Bạn muốn: (1) Gộp chung / (2) Tách riêng?"*. (Gộp thì làm như bước 1, Tách thì làm như bước 3).
3. **Khởi Tạo Parent Nội Bộ (DISTINCT):** Những cặp KHÁC NHAU, LLM phải tự rà: *"Job của entry nào trực tiếp bao trùm Job của entry kia?"*. Nếu có quan hệ bao trùm, lập tức lưu biến Parent Nội Bộ cho Chunk con đó.
3. **Output Phase 2A (Cấu trúc In-Memory):** Để chống trôi ngữ cảnh (hallucination), hệ thống BẮT BUỘC duy trì cấu trúc JSON nháp sau trong bộ nhớ trước khi mang đi quét Index (GĐ 2B):
   ```json
   {
     "unique_audiences": [
       {
         "id": "new_employee_time_management...",
         "semantic_query": "Người mới đi làm...",
         "file_ref": "[[nguoi-moi-di-lam...]]",
         "internal_parents": ["[[parent_file_ref]]"] // Link tới parent nội bộ (nếu có)
       }
     ],
     "chunk_mapping": {
       "book": "id_1",
       "chunk_01": "id_1", // Gộp chung vào nhóm book (do trùng lặp)
       "chunk_02": "id_2"  // Distinct
     }
   }
   ```

## Phần 2B: Quét Ngoại Biên (External Match 3-Verdict)
Đem Cụm Audience Liên Hiệp quét ngang cối dữ liệu `vault/01-Atomic/Audiences/_audience_index.yaml`.
Áp dụng nghiêm ngặt lưới so khớp kép 1-1 Structural & Semantic khắt khe sau:

```text
NEW id (EN)             ──so sánh với──→  EXISTING id (Tín hiệu Chính: Structural/Skeleton Match)
NEW semantic_query (VN) ──so sánh với──→  EXISTING semantic_query (Tín hiệu Phụ: Semantic ngầm định)
                                                ↓
                                            Verdict: IDENTICAL / DISTINCT / AMBIGUOUS
```

| Verdict | Hành Động | Cơ Chế Xử Lý Liên Kết Kép (Parent Array) |
|---|---|---|
| `IDENTICAL` | `merge` | Mảng Parent Cũ của file VẪN ĐƯỢC CHECK lại. Nếu LLM vừa phát hiện nhóm Parent mới **(CHỈ TỪ vòng quét nội bộ 2A)** mà file Cũ CHƯA CÓ → Ghi chèn lệnh **APPEND (Bổ sung)** list Parent mới đó vào thẳng file Cũ. Tuyệt đối không tự suy luận Parent mới từ Index cho file đã trùng. |
| `DISTINCT` | `create` | Truy rà toàn vòng Index xem *"Có gốc Audience hiện hữu nào bao trùm Job này không?"*. **CHÚ Ý:** Có thể có NHIỀU Parent bao trùm trực tiếp từ nhiều khía cạnh khác nhau (Vd: Khía cạnh Độ tuổi và Khía cạnh Chuyên môn). Tuy nhiên, **trên cùng một trục phả hệ**, tuyệt đối không vơ vét các Audience khổng lồ (Grandparent/Root) nếu đã chọn Parent trung gian. Nếu có, mảng Parent này lập tức hợp với mảng Parent Nội Bộ từ phần 2A. |
| `AMBIGUOUS` | `Human Gate`| Tạm dừng. Hỏi Chat: *"JTBD `[mới]` tương đồng `[[Cũ]]`. Chọn: (1) Hợp nhất / (2) Tạo mới?"*. Theo đó mà xử lý tiếp nhánh Merge/Create. |

> **🔥 QUY TẮC TỐI THƯỢNG: TRUY HỒI ĐỊNH DANH (Reference Substitution)**
> Sau khi Quét Ngoại Biên, mọi đường truyền Parent Nội Bộ mang nợ (Vd: Chunk -> Book) phải được Reference-Check sang bản thể định danh cuối.
> **Ví dụ:** Vòng 2A báo Chunk B mang Parent là Book A. Vòng 2B báo Book A sẽ MERGE thành `file_X`. Lúc này, mảng Parent của Chunk B **BẮT BUỘC ĐƯỢC CHỈ ĐỊNH ĐỔI THÀNH `file_X`** chứ không được phép giữ tên file A (vì file A không bao giờ sinh ra sinh lý, tạo ra Link ảo Broken).
## Phần 3: Quyết Toán Decision Map & Quản Trị Phả Hệ Động (DAG)

Cấp độ Level của Audience KHÔNG PHỤ THUỘC vào định nghĩa Job trừu tượng, mà bắt buộc ép áp chiếu bằng Bảng Phái Sinh Mảng Parent (Theo lý thuyết DAG mô tả ở Phần Mở Đầu). Định dạng trả về của `parent_audience` luôn luôn là Mảng chuỗi array `["[[slug]]"]`.

**Phần 3A: Quy trình Merge (Verdict IDENTICAL hoặc Chọn 1)**
- `action` = `merge`
- Trích xuất trả Decision Map với `audience_filename` = `file_ref` của Audience đã khớp.
- Lấy luôn giá trị `audience_level` hiện tại đang cấu hình của Audience bị trùng (đọc từ `_audience_index.yaml`).
- **Lệnh Append Parent (Bổ sung Phả Hệ):** Bằng việc đối chiếu Parent vừa tìm được ở **Phần 2A (Nội bộ)** với mảng Parent hiện tại của Audience bị trùng trong file `_audience_index.yaml`, nếu LLM phát hiện có Parent mới chưa từng được ghi nhận trong Index, ĐÓNG GÓI mảng Parent mới đó vào biến `parent_audience` của chuỗi JSON Decision Map Output. Nhờ biến này, Giai đoạn 3 sẽ nạp thêm mảng này vào file vật lý cũ. Ngược lại, nếu không có cập nhật gì mới, trả về giá trị mảng rỗng `parent_audience: []` trong file JSON Output (hàm ý Không kích hoạt Append, TUYỆT ĐỐI không phải là xóa gốc rễ parent cũ của file).

**Phần 3B: Quy trình Create (Verdict DISTINCT hoặc Chọn 2)**
- `action` = `create`
- Trích xuất Decision Map với `audience_filename` = `file_ref` gốc sinh tại Phần 1 thuần.
- Chốt mảng `parent_audience` dưới dạng mảng gom kết `Parent Nội Bộ (Phần 2A)` + `Parent Ngoại Biên Bao Trùm Trực Tiếp (Phần 2B)`. Mọi kết quả lưới này buộc phải thông qua màng lọc Reference Substitution ngăn ngừa Broken Link.
- Khởi xướng toán tử Phái Sinh Level: Đọc duyệt Level của các Parent thu được. Chọn ra level min nhất, đối sánh Bảng Ánh Xạ Level Mở Đầu để ra được Cấp Bậc Cuối Cùng (Nếu mảng Parent trống `[]` -> Big; parent big -> little; parent little/micro -> micro).
