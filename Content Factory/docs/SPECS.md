# SPECS: Hệ Thống AI Content Factory

## 1. Executive Summary
Hệ thống tài liệu hỗn hợp (Human + Machine Readable) chuẩn AWF, thiết kế riêng cho dự án AI Content Factory. Đóng vai trò là "Single Source of Truth" (Nguồn chân lý duy nhất) giúp cả team vận hành và các AI Agent nắm rõ quy trình, luật lệ và nhiệm vụ.

## 2. Kiến trúc Thư mục & Dữ liệu
```
Content Factory/
├── docs/                   # Tài liệu thiết kế (BRIEF, SPECS, Flowcharts)
├── output/runs/            # Run Folder: Nơi cách ly Artifacts sinh ra từng lần chạy
├── output/posts/           # Thành phẩm cuối cùng
├── vault/                  # Kho lưu trữ sự kiện/stories nguồn (Data Fact)
├── .agents/
│   ├── skills/             # Chứa SKILL.md, Scripts nội bộ, Reference Files
│   └── workflows/          # Luồng điều phối chính (VD: content-post.md)
```

## 3. Đặc tả Công nghệ (Technical Specs)

### 3.1. Polymorphic Regex Validation System
- Thay thế các đoạn code check `.Contains()` cứng nhắc bằng Regex đa hình.
- Phục vụ cho các script kiểm duyệt (như `validate-idea.ps1`), cho phép kiểm tra độ dài, cấu trúc câu, từ cấm một cách linh hoạt dựa trên file cấu hình thay vì hardcode bên trong file PowerShell.

### 3.2. Macro-Micro Diagram Pattern
- **Macro (LOD 1 - Workflow):** Sơ đồ lưu tại `docs/flowcharts/content-pipeline-macro.mmd`. Tập trung mô tả đường đi của dữ liệu (Run Folder) và các điểm giao cắt giữa các Phase (Sentinel).
- **Micro (LOD 2/3 - Skills):** Các sơ đồ con (sẽ triển khai sau) zoom cận cảnh vào thuật toán viết bài, chấm điểm bên trong từng thư mục Skill.

### 3.3. Checkpoint & Multi-Session Architecture
- Tránh vỡ Context Window bằng cơ chế "Auto-Checkpoint HALT".
- Pipeline chia làm 2 phiên:
  - **Phiên 1:** Ý tưởng ➔ Cấu trúc (Kết thúc bằng việc xuất `checkpoint.yaml`).
  - **Phiên 2:** `resolve-checkpoint.ps1` phục hồi context ➔ Viết nháp ➔ QA ➔ Format.

### 3.4. Hệ thống Phòng ngự (Defense System)
1. **Sentinel (detect-bypass.ps1):** Script ngoại vi, chốt chặn giữa các Phase. Fail = DỪNG NGAY.
2. **Self-Check Gate:** Chốt chặn nội bộ bên trong SKILL (VD: `validate-draft.ps1`, `validate-qa.ps1`). Fail = Vòng lặp tự sửa (Tối đa 3 lần) trước khi Escalate cho User.

## 4. Nguyên tắc AWF bắt buộc (Fatal Rules)
- Mọi script PowerShell KHÔNG ĐƯỢC CHỨA hardcode (VD: `if (word_count < 1500)`). Số `1500` phải được đọc từ `scoring-rules.yaml`.
- Artifacts sinh ra ở Phase nào phải được ghi ngay vào Run Folder, KHÔNG ghi đè lên bộ nhớ RAM (Context) nhằm chống System Drift.
