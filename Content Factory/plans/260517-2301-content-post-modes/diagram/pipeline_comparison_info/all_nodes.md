## writing_now
**Giá trị cố định hiện tại (hardcode trong code):**
- Tổng bài: 1500–1800 từ
- Mỗi đoạn: 3–5 câu
- Không có heading giữa các phần
- Các phần tách bằng dòng trống, không có marker
- Không có khái niệm "chuỗi câu dài" vs "chuỗi câu bình thường"
- Số từ mỗi phần: Hook 80-120, Story 200-300, Deep Dive 700-900, Pivot 200-300, Closing 100-150

Muốn thay đổi bất kỳ giá trị nào → phải sửa tay 31 file → rủi ro prompt và validator lệch nhau.

## qa_now
Chấm điểm dựa trên ngưỡng cố định:
- Bài < 1500 từ hoặc > 1800 từ → FAIL
- Đoạn < 3 câu hoặc > 5 câu → FAIL
- Đoạn > 400 từ → FAIL
- Có heading (#) → FAIL

Không có cách nào thay đổi ngưỡng mà không sửa code.

## structure_now
Phân bổ số từ cố định cho 5 phần:
- Hook: 80–120 từ
- Story: 200–300 từ
- Deep Dive: 700–900 từ
- Pivot: 200–300 từ
- Closing: 100–150 từ
- Tổng: 1500–1800 từ (không quá 1800)

## format_now
Chỉ strip 2 comment kỹ thuật:
- `<!-- execution_key: ... -->`
- `<!-- ref_keys: ... -->`

Không xử lý marker phân cách phần (chưa tồn tại). Không xử lý heading (không cho phép).

## clean
Dọn dẹp tự động các thay đổi tạm thời từ lần chạy trước (nếu pipeline bị crash giữa chừng mà chưa kịp khôi phục). Nếu không có gì cần dọn → bỏ qua, không lỗi.

## choose
User chọn 1 trong 3 chế độ:

| Chế độ | Mô tả | Số tham số user nhập |
|---|---|---|
| **Auto** | Mọi giá trị giữ nguyên như hiện tại | 0 (không hỏi) |
| **Thử nghiệm Basic** | Tùy chỉnh cấu trúc vật lý | 7 biến (B1–B7) |
| **Thử nghiệm Nâng cao** | Tùy chỉnh toàn diện | 13 biến (B1–B7 + A1–A6) |

## ask_params
AI hỏi user qua chat. Danh sách câu hỏi đầy đủ:

**Basic (B1–B7):**

| # | Câu hỏi | Format trả lời | Mặc định |
|---|---|---|---|
| B1 | Cách tách phần — marker, dòng trống trên, dòng trống dưới | marker + số + số | `⁂`, 1, 1 |
| B2 | Cách tách đoạn — marker, dòng trống trên, dòng trống dưới | marker + số + số | *(không)*, 1, 0 |
| B3 | Số câu mỗi đoạn | min-max | 3-5 |
| B4 | Cách tách chuỗi câu — marker, dòng trống trên, dòng trống dưới | marker + số + số | *(không)*, 0, 0 |
| B5 | Số câu mỗi chuỗi bình thường | min-max | 3-5 |
| B6 | Số câu mỗi chuỗi dài | min-max | 6-8 |
| B7 | Số chuỗi dài mỗi bài | min-max | 0-2 |

**Nâng cao (thêm A1–A6):**

| # | Câu hỏi | Format trả lời | Mặc định |
|---|---|---|---|
| A1 | Ngữ cảnh sử dụng chuỗi dài (khi nào, dùng để làm gì) | text mô tả | *(cần định nghĩa)* |
| A2 | Phần có heading không? Nếu có: dòng trống trên/dưới heading | yes/no + số | no |
| A3 | Đoạn có heading không? Nếu có: dòng trống trên/dưới heading | yes/no + số | no |
| A4 | Số từ toàn bài | min-max | 1500-1800 |
| A5 | Số từ mỗi phần (Hook, Story, Deep Dive, Pivot, Closing) | min-max × 5 | 80-120, 200-300, 700-900, 200-300, 100-150 |
| A6 | Số từ tối đa mỗi đoạn | số | 400 |

## validate_json
Kiểm tra 8 ràng buộc logic sau khi user nhập xong tất cả:

**Nhóm Basic (R1–R5):**

| # | Ràng buộc | Giải thích |
|---|---|---|
| R1 | B1 ≠ B2 | Separator phần phải phân biệt được với separator đoạn. Cùng không marker → tổng dòng trống B1 > B2. Cùng có marker → marker phải khác. Một có, một không → OK. |
| R2 | B2 ≠ B4 | Separator đoạn phải phân biệt được với separator chuỗi câu. Logic tương tự R1. |
| R3 | B3.max ≥ B5.max | Đoạn phải chứa được ít nhất 1 chuỗi câu bình thường đầy đủ. |
| R4 | B3.max ≥ B6.max | Đoạn phải chứa được ít nhất 1 chuỗi câu dài. |
| R5 | B6.min > B5.max | Chuỗi dài phải thực sự dài hơn chuỗi bình thường (khoảng không trùng). |

**Nhóm Nâng cao (R6–R8, chỉ check khi chọn Nâng cao):**

| # | Ràng buộc | Giải thích |
|---|---|---|
| R6 | A4.min ≥ tổng A5.min | Bài ở mức tối thiểu phải đủ chỗ cho tất cả phần ở mức tối thiểu. |
| R7 | tổng A5.max ≥ A4.min | Tất cả phần ở mức tối đa phải đủ từ để lấp đầy bài ở mức tối thiểu. |
| R8 | A6.max ≤ min(A5.max) | Đoạn không được dài hơn phần nhỏ nhất chứa nó. |

Vi phạm bất kỳ ràng buộc nào → báo cụ thể ràng buộc nào, biến nào xung đột → yêu cầu user sửa.

## patch
Cập nhật tạm thời các file hướng dẫn viết (prompt) để phản ánh cấu hình user chọn.

**Cơ chế:**
1. Pre-flight check: xác minh TẤT CẢ vị trí cần sửa đều tồn tại trong file. Thiếu 1 → dừng toàn bộ.
2. Backup mỗi file gốc (tạo bản sao `.bak`).
3. Thay thế chuỗi cũ bằng chuỗi mới.

**Danh sách file bị patch:**
- `voice-writer/SKILL.md` — số từ tổng, số câu/đoạn, separator
- `voice-writer/references/writing-rules.md` — số từ tổng, số câu/chuỗi
- `structure-designer/SKILL.md` — số từ tổng, số từ/phần (chỉ Nâng cao)

## auto_copy
Copy file cấu hình mặc định (`default.json` → `active.json`). Không hỏi thêm, không patch (vì giá trị = mặc định).

## writing
**Prompt (`voice-writer/SKILL.md`, `writing-rules.md`):**
- Auto → giữ nguyên text gốc: "1500-1800 từ", "3-5 câu/đoạn".
- Thử nghiệm → script sửa trực tiếp text: "1500-1800" → giá trị user nhập. Restore về bản gốc sau pipeline.
- Thêm marker `⁂` giữa các phần (thay vì chỉ dòng trống) — AI đọc hướng dẫn mới trong prompt đã patch.

## qa
**Validator (`validate-draft.ps1`) — refactor vĩnh viễn:**
- Thay tất cả ngưỡng hardcode (`3`, `5`, `400`, `1500`, `1800`) bằng đọc từ `active.json`.
- Auto → giá trị mặc định (kết quả giống hệt hiện tại). Các check mới về chuỗi câu chỉ **cảnh báo** (WARN), không block pipeline.
- Thử nghiệm → check theo giá trị user nhập. Vi phạm → **block** (FAIL).
- Thêm 3 check mới: số câu/chuỗi bình thường (B5), số câu/chuỗi dài (B6), số chuỗi dài/bài (B7).
- Thêm quy tắc đếm câu mới: 2 câu rất ngắn (< 4 từ) = 1 câu khi đếm.

## structure
**Prompt (`structure-designer/SKILL.md`):**
- Auto/Basic → giữ nguyên: "Phân bổ tổng 1500-1800 từ", Hook 80-120, Story 200-300, Deep Dive 700-900, Pivot 200-300, Closing 100-150.
- Nâng cao → script sửa trực tiếp text trong file: "1500-1800" → giá trị user nhập (A4), từng phần cũng sửa tương ứng (A5). Restore về bản gốc sau pipeline.

**Validator (`validate-outline.ps1`):**
- Refactor vĩnh viễn: thay `1500` và `1800` hardcode bằng đọc từ `active.json`.
- Mọi chế độ đều dùng giá trị từ profile (Auto = giá trị mặc định, Thử nghiệm = giá trị user nhập).

## format
**Thay đổi so với hiện tại:**
- Strip thêm marker phân cách phần `⁂` (cùng danh sách với execution_key và ref_keys).
- Thay marker bằng dòng trống (mặc định 2 dòng, đọc từ profile).
- Nếu profile cho phép heading (`section_headings.enabled = true`) → giữ nguyên heading trong output cuối.

## restore
Khôi phục toàn bộ file hướng dẫn về bản gốc (từ backup `.bak`):
1. Copy `.bak` → file gốc.
2. Xóa `.bak`.

Đảm bảo sau mỗi lần chạy, hệ thống trở về trạng thái ban đầu — lần chạy tiếp theo ở chế độ Auto sẽ không "dính" cấu hình thử nghiệm.

## profile_db
File `profiles/active.json` — nguồn cấu hình trung tâm cho toàn bộ pipeline.

**Ai tạo file này?**
- Chế độ Auto → AI agent copy từ `default.json`.
- Chế độ Thử nghiệm → AI agent tạo từ câu trả lời của user.

**Ai đọc file này?**
Hai nhóm đối tượng đọc, mỗi nhóm theo cơ chế khác:

| Đối tượng | Cơ chế | Tính chất |
|---|---|---|
| **Prompt files** (SKILL.md, writing-rules.md) | Patch tạm thời bởi `apply-profile.ps1` → restore sau pipeline | Tạm thời — file gốc không bị thay đổi vĩnh viễn |
| **Validator scripts** (validate-draft.ps1, validate-outline.ps1, validate-format.ps1) | Refactor code vĩnh viễn để đọc trực tiếp từ JSON | Vĩnh viễn — code được sửa 1 lần, không cần patch/restore |

**Tại sao 2 cơ chế khác nhau?**
- Prompt là ngôn ngữ tự nhiên — không thể đọc JSON. Phải patch text trực tiếp.
- Script PowerShell — có thể đọc JSON bằng `ConvertFrom-Json`. Refactor vĩnh viễn sạch hơn.
