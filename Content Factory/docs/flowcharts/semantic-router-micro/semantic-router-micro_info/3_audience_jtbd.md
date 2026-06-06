## CheckAuth1
### Bước 6: Gán Pillar cho Novel Angle
- Đã có `Target_Pillar`: Gán trực tiếp.
- Ủy quyền: Đọc `pillars.yaml`, tự chọn Pillar phù hợp nhất. Hỏi User xác nhận.
  - ⛔ STOP — CHỜ USER XÁC NHẬN. KHÔNG tự ý tiếp tục.

**JTBD Resolution (Novel Angle):** Đọc `[Persona_Path]/audience.yaml` → trích `audience_Job_performer`, `audience_main_job`, `audience_circumstance` → ghi vào blackboard key `resolved_jtbd`. `source_audience: "big"`.

`Is_Novel_Angle = True` → **Bước 7**.

## CheckAuth2
### Bước 7: Kiểm tra trùng Pillar (Muộn)
Chỉ áp dụng khi User ủy quyền ở Bước 1 (đã qua Bước 2 → bỏ qua bước này).
→ Thực hiện **Pillar Duplicate Check**. Bước kế: **Bước 9**.

## CheckAudience
### Bước 8: Phân giải Audience & JTBD
Dựa vào `Target_Audience` từ Bước 3 hoặc Bước 5:
- Parent + Child Audience cùng trúng → chốt Parent.
- Audience ngang hàng → In CLI, chờ User chọn 1 hoặc gõ `ALL`.
  - ⛔ STOP — CHỜ USER PHẢN HỒI. KHÔNG tự chọn.
  - User chọn 1 → `Target_Audience` = string (bare slug, không `[[]]`).
  - User chọn `ALL` → resolve danh sách audience IDs cụ thể (bare slug). `Target_Audience` = YAML array. KHÔNG ghi string "ALL".

**JTBD Resolution:**
- **Single audience**: `view_file` tại `vault/01-Atomic/Audiences/[Target_Audience].md` → trích `audience_Job_performer`, `audience_main_job`, `audience_circumstance` → ghi `resolved_jtbd` vào blackboard. `source_audience` = audience ID.
- **Multi-audience**: CHƯA ghi `resolved_jtbd` (DIKW Bridge resolve sau Anchor-First).

`Is_Novel_Angle = False` → **Bước 9**.

## WriteBB
### Bước 9: Đóng gói Blackboard
Output 6 biến:
- `topic`: 1 string ID duy nhất
- `Target_Pillar`: Tên Pillar
- `Target_Audience`: Audience ID (string), danh sách Audience IDs (YAML array), hoặc rỗng (Novel Angle)
- `Is_Novel_Angle`: True / False
- `Persona_Path`: Đường dẫn thư mục persona (đã xác định ở Bước 3 của workflow bởi `validate-persona.ps1`)
- `resolved_jtbd`: Block JTBD gồm `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `source_audience`. Có khi single audience hoặc Novel Angle. Chưa có khi multi-audience (DIKW Bridge bổ sung).

Sau khi ghi `00-blackboard.yaml`, BẮT BUỘC append 1 dòng dưới cùng: `# execution_key: [giá trị EXECUTION_KEY từ SKILL.md]`
