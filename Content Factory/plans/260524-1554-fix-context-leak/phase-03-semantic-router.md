# Phase 03: Update Semantic Router (Ghi nhận Ràng buộc Nguồn)
Last Update: 24/05/2026 16:55 (GMT+7)
Status: ✅ Complete
Dependencies: Phase 02

## Objective
Sửa `semantic-router/SKILL.md` để bóc tách thông tin Nguồn (hỗ trợ Array). Không dùng Regex phức tạp dễ gãy, mà dùng System Prompt kết hợp Parser.

## Directions (100% Error-free guarantee)
1. **Xác định vị trí sửa**: `.agents/skills/semantic-router/SKILL.md`.
2. **Logic Trích Xuất An Toàn:**
   - **Vị trí 1 (Metadata Frontmatter của SKILL.md)**: Cập nhật biến đầu ra `output` ở phần frontmatter của tệp tin.
     - *Trước khi sửa*:
       ```markdown
       output: Blackboard 6 biến: Target_Pillar, Target_Audience, topic, Is_Novel_Angle, Persona_Path, resolved_jtbd.
       ```
     - *Sau khi sửa*:
       ```markdown
       output: Blackboard 8 biến: Target_Pillar, Target_Audience, topic, Is_Novel_Angle, Persona_Path, resolved_jtbd, Target_Source_Type, Target_Source_IDs.
       ```
   - **Vị trí 2 (Bổ sung Bước trích xuất Nguồn trước Bước 9)**: Chèn thêm một thủ tục trích xuất nguồn sau Bước 8 và trước Bước 9.
     - *Nội dung bổ sung*:
       ```markdown
       ### Thủ tục phụ: Trích xuất Ràng buộc Nguồn (Source Constraint Extraction)
       Từ chuỗi yêu cầu nội dung của người dùng, phân tích xem có nhắc đến một hoặc nhiều nguồn sách cụ thể không (ví dụ: "dựa trên sách Good Inside", "từ sách Good Inside và The Whole-Brain Child"):
       1. Nếu có:
          - Đặt `Target_Source_Type` = "book".
          - Chuyển tên sách thành slug dạng lowercase không dấu (ví dụ: "Good Inside" -> "good-inside", "The Whole-Brain Child" -> "the-whole-brain-child").
          - Đặt `Target_Source_IDs` = danh sách mảng các slug (ví dụ: `["good-inside"]` hoặc `["good-inside", "the-whole-brain-child"]`).
       2. Nếu viết tự do (freestyle, không chỉ định sách cụ thể):
          - Đặt `Target_Source_Type` = null.
          - Đặt `Target_Source_IDs` = [].
       ```
   - **Vị trí 3 (Bước 9: Đóng gói Blackboard)**: Cập nhật Bước 9 để ghi 2 biến mới vào `00-blackboard.yaml`.
     - *Trước khi sửa*:
       ```markdown
       ## Bước 9: Đóng gói Blackboard
       
       Output 6 biến:
       - `topic`: 1 string ID duy nhất
       - `Target_Pillar`: Tên Pillar
       - `Target_Audience`: Audience ID (string), danh sách Audience IDs (YAML array), hoặc rỗng (Novel Angle)
       - `Is_Novel_Angle`: True / False
       - `Persona_Path`: Đường dẫn thư mục persona (đã xác định ở Bước 3 của workflow bởi `validate-persona.ps1`)
       - `resolved_jtbd`: Block JTBD gồm `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `source_audience`. Có khi single audience hoặc Novel Angle. Chưa có khi multi-audience (DIKW Bridge bổ sung).
       ```
     - *Sau khi sửa*:
       ```markdown
       ## Bước 9: Đóng gói Blackboard
       
       Output 8 biến:
       - `topic`: 1 string ID duy nhất
       - `Target_Pillar`: Tên Pillar
       - `Target_Audience`: Audience ID (string), danh sách Audience IDs (YAML array), hoặc rỗng (Novel Angle)
       - `Is_Novel_Angle`: True / False
       - `Persona_Path`: Đường dẫn thư mục persona (đã xác định ở Bước 3 của workflow bởi `validate-persona.ps1`)
       - `resolved_jtbd`: Block JTBD gồm `audience_Job_performer`, `audience_main_job`, `audience_circumstance`, `source_audience`. Có khi single audience hoặc Novel Angle. Chưa có khi multi-audience (DIKW Bridge bổ sung).
       - `Target_Source_Type`: "book" hoặc null
       - `Target_Source_IDs`: Mảng YAML chứa danh sách slug nguồn (ví dụ: `["good-inside"]` hoặc `[]`)
       ```

## Files to Create/Modify
- `.agents/skills/semantic-router/SKILL.md`

---
Next Phase: phase-04-dikw-bridge.md

