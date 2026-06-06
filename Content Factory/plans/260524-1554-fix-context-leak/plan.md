# Plan: Fix Context Leak (Data Normalization & Workflow Pipeline)
Created: 24/05/2026 15:54 (GMT+7)
Last Update: 24/05/2026 16:55 (GMT+7)
Status: ✅ Complete
Role: Khắc phục lỗi lấy nhầm dữ liệu (Atoms) từ sách khác bằng cách áp dụng chuẩn hóa Data và Context Constraint. Đạt chuẩn world-class: Không over-engineering, không phá vỡ logic viết bài tự do (freestyle).

## Overview & System Integrity Check
Vấn đề cốt lõi: Thiếu Context Constraint và ID định danh, dẫn đến rò rỉ dữ liệu chéo nguồn.
**Bảo vệ Hệ thống (Zero-breakage Architecture):**
1. **Dữ liệu**: Bổ sung bộ đôi khóa ngoại (`source_type`, `source_id`). Bắt buộc Backup 100% trước khi migrate.
2. **Luồng tự do (Freestyle)**: Việc ghi và lọc theo `Target_Source_ID` sẽ có tính **Có điều kiện (Conditional)**. Nếu người dùng yêu cầu viết một bài báo chung chung không dựa trên sách cụ thể, hệ thống sẽ bỏ qua màng lọc ID. Ngăn chặn tuyệt đối việc khóa cứng hệ thống (Hard-lock).
3. **Over-engineering check**: Không xây dựng hệ cơ sở dữ liệu riêng, tận dụng trực tiếp YAML Frontmatter hiện có của Markdown. Gọn, nhẹ, dễ duy trì.

## Phases

| Phase | Name | Status | Progress |
|-------|------|--------|----------|
| 01 | Data Migration (Chuẩn hóa Atomic cũ có Backup) | ✅ Complete | 100% |
| 02 | Update Extractors (Cập nhật chuẩn đầu vào AI) | ✅ Complete | 100% |
| 03 | Update Semantic Router (Trích xuất ID có điều kiện) | ✅ Complete | 100% |
| 04 | Update DIKW Bridge (Lọc Kép có điều kiện bypass) | ✅ Complete | 100% |

## Quick Commands
- All Phases Complete. Next step: /save_brain

