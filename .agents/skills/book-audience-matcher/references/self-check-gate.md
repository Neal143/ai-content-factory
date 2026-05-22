---
name: Self-Check Gate — Audience Decision Map
description: >
  Quy trình kiểm tra tính toàn vẹn của Audience Decision Map trước khi trả về Workflow.
  Được gọi cuối Giai đoạn 3 của book-audience-matcher.
---

# Self-Check Gate — Audience Decision Map

Quét toàn bộ Decision Map In-Memory. **CHUNK Giai đoạn 4** nếu bất kỳ điều kiện nào vi phạm:

| Điều kiện | Lỗi nếu vi phạm |
|-----------|-----------------|
| Mọi entry có `audience_filename` ≠ null/empty | File không được ghi thành công |
| Mọi entry (dù tạo mới hay merge) đều có `parent_audience` là mảng (Array) | Lỗi định dạng DAG Parent |
| Mọi `action: create` có `audience_level` ∈ {big/little/micro} | Level không được suy ra |
| File vật lý tồn tại tại `01-Atomic/Audiences/[audience_filename].md` (với nguyên vẹn đuôi `.md`) | Write failed silently |
| Số entry = 1 (book) + N chunk hợp lệ (trừ `[NO_JTBD_FOUND]`) | Parse/skip sai |

## Tầng 1 — Auto-Repair (thử trước)

- `audience_filename` null, `action: merge`:
  - Pre-check: `file_ref` ≠ null và có dạng `[[...]]` — nếu không → thẳng Tầng 2.
  - Strip `[[` `]]` từ `file_ref`, lấy phần file_ref. Nếu có subfolder path (`Folder/File`) → chỉ lấy phần sau dấu `/`.
- `audience_filename` null, `action: create`:
  - Pre-check: `audience_level` VÀ `parent_audience` của entry đó đều đã hợp lệ — nếu có bất kỳ field nào trong 2 field này bị lỗi → thẳng Tầng 2 (không auto-repair file broken).
  - Nếu pass pre-check: re-apply logic Giai đoạn 3 cho entry đó (đọc `audience-structure.md`, dựng In-Memory từ data gốc, write lại). Giới hạn 1 lần retry — fail lần 2 → Tầng 2.
- `parent_audience` null và `audience_level` invalid cùng lúc → **thẳng Tầng 2** (co-dependency, không auto-repair được).
- `parent_audience` null hoặc rỗng, sai format:
  - **Re-evaluate Phả Hệ:** Yêu cầu AI dò lại cả 2 nhánh:
    - **Nội bộ (Phần 2A):** Có chunk/book nào trong phiên đang xử lý bao trùm Job này không?
    - **Ngoại biên (Phần 2B):** Quét lại toàn bộ `_audience_index.yaml`, có audience nào có Job bao trùm Job này không?
  - Tham chiếu thu được gộp thành mảng `["[[...]]"]`. 
  - **Fallback:** Nếu KHÔNG dò ra được parent nào (cả nội lẫn ngoại), gán mảng parent rỗng `[]` (hàm ý chính nó là gốc).
- `audience_level` invalid:
  - Nếu `parent_audience` là mảng rỗng `[]` → Level mặc định là `big`.
  - Nếu `parent_audience` có parent → Truy xuất level của tất cả các parent, chọn ra level thấp nhất. Áp dụng bảng phái sinh: Parent thấp nhất là big → gán `little`; Parent thấp nhất là little hoặc micro → gán `micro`.
- File vật lý không tồn tại:
  - Kiểm tra xem AI có vô tình lưu file không đuôi (tức mở rộng rỗng, vd: `.../nguoi-moi-di-lam`) hay không. Nếu có, lập tức Rename bằng cách thêm đuôi `.md` vào và pass.
  - Nếu file không tồn tại ở cả 2 dạng: Chỉ re-write nếu dữ liệu In-Memory còn nguyên vẹn (tất cả fields hợp lệ). Nhấn mạnh yêu cầu ".md".
  - 1 lần retry — fail lần 2 → Tầng 2.

## Tầng 2 — Human Gate (nếu Auto-Repair thất bại)

- In ra Chat: entry nào lỗi, field nào sai, giá trị hiện tại.
- **CHUNK** Giai đoạn 4 cho đến khi User confirm đã fix.
- **Không có quarantine** — không được skip bất kỳ entry nào.

**Count mismatch → thẳng lên Human Gate** (không auto-repair):
> *"Phát hiện N_expected entries nhưng Decision Map chỉ có N_actual. Kiểm tra lại file nguồn và Giai đoạn 1."*
