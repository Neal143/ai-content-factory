# 💡 BRIEF: Content-Post — Chế Độ Auto & Thử Nghiệm

**Tên file:** BRIEF.md
**Last update:** 17/05/2026 22:45 (GMT+7)
**Vai trò:** Tổng hợp kết quả brainstorm, là đầu vào cho `/plan`.
**Được sử dụng khi nào?:** Khi chạy `/plan` để thiết kế chi tiết tính năng.
**Output:** Bản tóm tắt ý tưởng đã thống nhất, sẵn sàng cho planning.
**Tóm tắt logic hoạt động:** Ghi nhận các quyết định kiến trúc, quy ước cấu trúc, và phạm vi thay đổi đã thống nhất trong phiên brainstorm.

---

## 1. VẤN ĐỀ CẦN GIẢI QUYẾT

Pipeline `content-post` hiện hardcode toàn bộ ràng buộc cấu trúc bài viết (số từ, số câu/đoạn, số phần...) trực tiếp trong prompt (SKILL.md) và script validation (validate-draft.ps1). Theo `hardcode_audit_report.md`, có 31 file liên quan, trong đó nhiều file chứa giá trị tĩnh trùng lặp.

**Hệ quả:**
- Không thể thử nghiệm cấu trúc bài viết mới mà không sửa code thủ công ở nhiều file.
- Rủi ro sai lệch giữa prompt và validator khi sửa thủ công.

## 2. GIẢI PHÁP ĐỀ XUẤT

Xây dựng tính năng `content-post` hỗ trợ **3 chế độ**:

| Chế độ | Mô tả |
|---|---|
| **Auto** | Chạy với bộ tham số mặc định (giữ nguyên giá trị hệ thống hiện tại) |
| **Thử nghiệm Basic** | User nhập các tham số cấu trúc vật lý (separator, số câu, cách ngắt) |
| **Thử nghiệm Nâng cao** | Bao gồm tất cả biến Basic + tham số ngữ nghĩa và nội dung (heading, word count, ngữ cảnh sử dụng chuỗi dài) |

**Kiến trúc thực thi:** Script `apply-profile.ps1` đọc tham số → validate input → patch chính xác các vị trí hardcode trong cả prompt lẫn script validation → pipeline chạy → restore về default.

## 3. QUY ƯỚC CẤU TRÚC BÀI VIẾT

### 3.1. Hệ thống phân cấp

```
Bài viết
 └── Phần (tách bằng marker ⁂)
      └── Đoạn (tách bằng 1 dòng trống)
           └── Chuỗi câu không xuống dòng / "đoạn nhỏ" (tách bằng xuống dòng, 0 dòng trống)
                └── Câu
                     └── Câu rất ngắn (< 4 từ)
```

| Cấp | Định nghĩa | Mối quan hệ |
|---|---|---|
| **Bài viết** | Nhiều **phần** gộp lại | 1 mục đích lớn, 1 vấn đề lớn, 1 thông điệp lớn |
| **Phần** | 1+ **đoạn** gộp lại | Support mục đích/vấn đề/thông điệp của bài viết |
| **Đoạn** | 1+ **chuỗi câu** gộp lại | Mọi đoạn phải khiến người đọc muốn đọc đoạn tiếp theo. Đoạn cuối mang CTA |
| **Chuỗi câu** (đoạn nhỏ) | 1+ **câu** viết liền không xuống dòng | Đơn vị trực quan ảnh hưởng trải nghiệm đọc |
| **Câu** | 1+ từ/tiếng kết hợp có nghĩa | Liên kết với nhau tạo chuỗi có ý nghĩa |
| **Câu rất ngắn** | Câu < 4 từ đơn/tiếng | 2 câu rất ngắn = 1 câu khi đếm. 1 câu rất ngắn lẻ = không tính |

### 3.2. Dấu hiệu phân tách (Mặc định - Auto)

Mỗi cấp phân tách gồm **3 thành phần kết hợp**: marker (có hoặc không) + số dòng trống phía trên + số dòng trống phía dưới.

| Ranh giới | Marker | Dòng trống trên | Dòng trống dưới | Output cuối (format-agent) |
|---|---|---|---|---|
| Tách phần | `⁂` | 1 | 1 | 2 dòng trống (xóa marker) |
| Tách đoạn | *(không)* | 1 | 0 | 1 dòng trống |
| Tách chuỗi câu trong đoạn | *(không)* | 0 | 0 | Xuống dòng trực tiếp |

### 3.3. Logic parse (3 bước, không nhập nhằng)

1. Nếu có marker → tách bằng marker → danh sách **phần**. Nếu không có marker → tách bằng N dòng trống liên tiếp.
2. Trong mỗi phần, tách bằng dòng trống → danh sách **đoạn**.
3. Trong mỗi đoạn, tách bằng xuống dòng → danh sách **chuỗi câu**.

## 4. BIẾN THỬ NGHIỆM

### 4.1. Thử nghiệm Basic

Mỗi biến separator (B1, B2, B4) gồm 3 thành phần: `marker` (text, để trống nếu không dùng) + `dòng_trống_trên` (số) + `dòng_trống_dưới` (số).

| # | Biến | Mô tả | Kiểu input | Giá trị Auto (mặc định) |
|---|---|---|---|---|
| B1 | Cách tách phần | Marker + dòng trống trên/dưới dùng để phân cách các phần | marker + x + y | marker=`⁂`, trên=`1`, dưới=`1` |
| B2 | Cách tách đoạn | Marker + dòng trống trên/dưới dùng để phân cách các đoạn trong 1 phần | marker + x + y | marker=*(không)*, trên=`1`, dưới=`0` |
| B3 | Số câu tối đa mỗi đoạn | Giới hạn số câu (đã quy đổi) trong 1 đoạn | x-y | `3-5` |
| B4 | Cách tách chuỗi câu trong đoạn | Marker + dòng trống trên/dưới dùng để ngắt giữa các chuỗi câu | marker + x + y | marker=*(không)*, trên=`0`, dưới=`0` |
| B5 | Số câu/chuỗi câu bình thường | Khoảng số câu (đã quy đổi) cho 1 chuỗi câu bình thường | x-y | `1-2` |
| B6 | Số câu/chuỗi câu dài | Khoảng số câu (đã quy đổi) cho 1 chuỗi câu dài | x-y | `3-5` |
| B7 | Số chuỗi câu dài mỗi bài | Bao nhiêu chuỗi câu dài được phép trong toàn bài | x-y | `3-5` |
| B8 | Title trong output | Bài viết có title trong output cuối không? | yes/no | `no` |
| B9 | Section heading trong output | Section có heading trong output cuối không? | yes/no | `no` |
| B10 | Paragraph heading trong output | Đoạn có heading trong output cuối không? | yes/no | `no` |

### 4.2. Thử nghiệm Nâng cao (bao gồm tất cả biến Basic +)

| # | Biến | Mô tả | Kiểu input | Giá trị Auto (mặc định) |
|---|---|---|---|---|
| A1 | Ngữ cảnh sử dụng chuỗi câu dài | Khi nào/dùng để làm gì/thể hiện điều gì khi viết chuỗi câu dài | text mô tả | *(chưa có — cần định nghĩa)* |
| A2 | Spacing heading section | Khoảng cách dòng trống trên/dưới heading section (chỉ có ý nghĩa khi B9=yes) | x + y | trên=`1`, dưới=`0` |
| A3 | Spacing heading đoạn | Khoảng cách dòng trống trên/dưới heading đoạn (chỉ có ý nghĩa khi B10=yes) | x + y | trên=`1`, dưới=`0` |
| A4 | Số từ toàn bài | Tổng số từ bài viết | x-y | `1500-1800` |
| A5 | Số từ mỗi phần | Số từ phân bổ cho từng phần | x-y mỗi phần | Hook `80-120`, Story `200-300`, Pivot `200-300`, Closing `100-150` |
| A6 | Số từ mỗi đoạn | Giới hạn số từ 1 đoạn | x-y | `max 400` |

## 5. QUY TẮC INPUT VÀ VALIDATION

### 5.1. Format input cho giá trị số

| User nhập | Script hiểu | Hợp lệ? |
|---|---|---|
| `3-5` | min=3, max=5 | ✅ |
| `3` | min=3, max=3 (tự dịch thành `3-3`) | ✅ |
| `5-3` | — | ❌ Bắt nhập lại (min > max) |
| `abc` | — | ❌ Bắt nhập lại |
| `-3` | — | ❌ Bắt nhập lại |
| `3-5-7` | — | ❌ Bắt nhập lại |

### 5.2. Ràng buộc logic giữa các biến

Script/Agent phải validate **sau khi user nhập xong tất cả** để đảm bảo tính nhất quán:

#### Ràng buộc nhóm Basic (B1–B7)

| # | Ràng buộc | Giải thích | Ví dụ vi phạm |
|---|---|---|---|
| R1 | B1 ≠ B2 (separator phải phân biệt được) | Parser không thể tách phần và đoạn nếu separator giống nhau. Quy tắc: cùng không marker → tổng dòng trống B1 > B2. Cùng có marker → marker phải khác nhau. Một có marker, một không → tự động OK | B1=(không marker, 1 trên, 0 dưới), B2=(không marker, 1 trên, 0 dưới) → trùng |
| R2 | B2 ≠ B4 (separator phải phân biệt được) | Tương tự R1 nhưng giữa cấp đoạn và chuỗi câu | B2=(không marker, 0, 0), B4=(không marker, 0, 0) → trùng |
| R3 | B3.max ≥ B5.max | Đoạn phải chứa được ít nhất 1 chuỗi câu bình thường đầy đủ | B3=`3-4`, B5=`3-5` → chuỗi 5 câu không vừa đoạn 4 câu |
| R4 | B3.max ≥ B6.max | Đoạn phải chứa được ít nhất 1 chuỗi câu dài | B3=`3-5`, B6=`6-8` → chuỗi dài 8 câu không vừa đoạn 5 câu |
| R5 | B6.min > B5.max | Chuỗi dài phải thực sự dài hơn chuỗi bình thường (không trùng khoảng) | B5=`3-5`, B6=`4-7` → chuỗi "dài" 4 câu trùng với bình thường |

#### Ràng buộc nhóm Nâng cao (A1–A6, bổ sung khi chọn Nâng cao)

| # | Ràng buộc | Giải thích | Ví dụ vi phạm |
|---|---|---|---|
| R6 | A4.min ≥ tổng A5.min | Bài ở mức tối thiểu phải đủ chỗ cho tất cả phần ở mức tối thiểu | A4=`1500-1800`, tổng A5.min=`1600` → min bài < min phần |
| R7 | tổng A5.max ≥ A4.min | Tất cả phần ở mức tối đa phải đủ từ để lấp đầy bài ở mức tối thiểu | A4=`1500-1800`, tổng A5.max=`1400` → max phần vẫn không đạt min bài |
| R8 | A6.max ≤ min(A5.max của mọi phần) | Đoạn không được dài hơn phần nhỏ nhất chứa nó. Lấy A5.max nhỏ nhất trong tất cả phần làm trần | A6=`400`, A5 Hook=`80-120` → 1 đoạn 400 từ vượt cả phần Hook 120 từ |

Khi phát hiện vi phạm → thông báo cụ thể ràng buộc nào bị vi phạm, biến nào xung đột → bắt user nhập lại các biến liên quan.

## 6. PHẠM VI THAY ĐỔI

### 6.1. File cần tạo mới
- `apply-profile.ps1` — Script: nhận input user, validate, patch, restore.
- `default-profile.json` — Bộ tham số mặc định Auto.

### 6.2. File cần sửa (dựa trên hardcode_audit_report.md)
- **Prompt (SKILL.md):** hook-engineer, structure-designer, voice-writer, qa-checker.
- **Validator (ps1):** validate-hook.ps1, validate-outline.ps1, validate-draft.ps1.
- **References:** writing-rules.md.
- **format-agent:** Thêm logic xử lý marker `⁂` → dòng trống, xử lý heading nếu có.
- **content-post.md (workflow):** Thêm bước chọn chế độ Auto / Basic / Nâng cao.

### 6.3. Cơ chế hoạt động

```
User chọn chế độ
       │
       ├── Auto → apply-profile.ps1 -Mode default
       │
       ├── Basic → Script hỏi user nhập 7 biến (B1–B7)
       │                    │
       │                    ▼
       │              Validate input format (x-y)
       │              Validate ràng buộc logic
       │                    │
       │              ┌─ Lỗi? → Thông báo + bắt nhập lại
       │              └─ OK? ─┐
       │                      │
       └── Nâng cao → Script hỏi thêm 6 biến (A1–A6)
                              │
                              ▼
                        Validate tổng thể
                              │
                        ┌─ Lỗi? → Thông báo + bắt nhập lại
                        └─ OK? ─┐
                                │
                                ▼
                         apply-profile.ps1 patch các file
                                │
                                ▼
                         Pipeline content-post chạy
                                │
                                ▼
                         apply-profile.ps1 restore về default
```

## 7. ĐÁNH GIÁ SƠ BỘ

- **Độ phức tạp:** Cao — nhiều biến, nhiều ràng buộc chéo, nhiều file cần patch, cần xử lý cả prompt lẫn logic validator.
- **Rủi ro chính:**
  - Audit report thiếu sót vị trí hardcode → prompt và validator lệch nhau.
  - Ràng buộc logic chưa cover hết → user nhập giá trị hợp lệ format nhưng vô lý về ngữ nghĩa.
- **Biện pháp giảm rủi ro:** Rà soát lại audit report trong phase planning; liệt kê đầy đủ ràng buộc logic.

## 8. BƯỚC TIẾP THEO

→ Chạy `/plan` để thiết kế chi tiết: cấu trúc file profile, danh sách chính xác vị trí patch cho từng biến, logic script apply-profile.ps1 (bao gồm input collection, validation, patch, restore).
