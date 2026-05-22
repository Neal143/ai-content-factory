---
description: Công cụ nhập và cấu trúc câu chuyện cá nhân vào Vault
---

# 📖 Workflow: Ngân hàng câu chuyện (Story Bank)

> **LỆNH**: `/story-bank` [Nội dung kể thô] hoặc `/story-bank extract`

Quy trình này giúp biến các mảnh chuyện vụn vặt thành Câu Chuyện theo mô hình 5 phần (S-P-T-O-L) chuẩn mực, lưu trữ dưới dạng Atomic note để tái sử dụng lâu dài.

// turbo-all

## Hướng dẫn thực thi

### Bước 1: Xác định Nguồn
Hỏi/xác định ý định của user:
- **Kể mới**: User kể 1 mẩu chuyện trực tiếp trong chat.
- **Trích xuất tự động (Extract)**: Quét các bài viết cũ trong Vault tìm ra file có chứa câu chuyện chưa được bóc tách.

### Bước 2: Kích hoạt Phân tích Kép (Story Architect)
Kích hoạt duy nhất skill `story-architect`:
1. Chuyển raw input (hoặc file extract) cho agent.
2. Ép agent thực thi Output Kép sinh ra 2 NODE VẬT LÝ độc lập (Graph-based Atomization):
   - **File A (Node Tầng 3 - Lesson):** Trích xuất phần L (Lesson). Bắt buộc chọn 1 trong 8 `knowledge_type` (framework, principle, mental_model, v.v.). Lưu vào `Solutions/` hoặc `Concepts/`. Dựa vào Pillar để tìm và cấy thẻ `supports_insight` trỏ ngang về Tầng 2.
   - **File B (Node Tầng 4 - Story):** Lưu TRỌN VẸN toàn bộ 5 phần S-P-T-O-L của Câu chuyện (tuyệt đối không cắt bỏ Lesson). Cấy thẻ `supports_knowledge` KHÓA THẲNG ĐÍCH DANH về File A vừa sinh ra.
3. Nếu có câu nói hay → trích nguyên văn vào phần `📌 Câu hay trích dẫn` ở File B.
4. Tích hợp Reverse-Sync (Chống rác): Đọc và thực thi module `topic_manager.md` tại chỗ để đẩy `topics` mới vào `topic_map.yaml` - Tuyệt đối không dừng lại hỏi User rườm rà.

### Bước 3: POKA-YOKE Checks
Trước khi lưu, kiểm tra:
```
⛔⛔ Story KHÔNG CÓ protagonist → REJECT
⛔ Story KHÔNG CÓ turning point rõ ràng → YÊU CẦU user bổ sung
⛔ File B (Story) KHÔNG CÓ `supports_knowledge` trỏ về File A → REJECT
⛔ Confidence < 0.5 → KHÔNG xử lý, yêu cầu user xác minh
✅ Graph Links phải khép kín. File A phải có node trỏ nếu nó là Solution/Concept.
```

### Bước 4: Đặt tên file + Lưu trữ
Đặt tên theo convention: `{category}-story-{slug}.md`

**11 categories:**
| Category | Chủ đề |
|----------|--------|
| `career` | Sự nghiệp, công việc |
| `content` | Viết bài, content creation |
| `productivity` | Năng suất, tập trung |
| `mindset` | Tư duy, tâm lý |
| `relationship` | Quan hệ, networking |
| `decision` | Ra quyết định |
| `learning` | Học tập |
| `business` | Kinh doanh |
| `marketing` | Marketing, bán hàng |
| `writing` | Viết lách |
| `life` | Cuộc sống, trải nghiệm cá nhân |

Lưu File A vào thư mục DIKW tương ứng (Insight/Solution vd: `01-Atomic/Insights/`).
Lưu File B vào `vault/01-Atomic/Stories/`. Tên file: `{category}-story-{slug}.md`

### Bước 5: Báo cáo
Report cho user:
- Tên file đã tạo
- SubType + Topics
- Câu tóm tắt 1 dòng
- Confidence score
- **Tổng số story atoms trong vault hiện tại**

---

## Tips cho User (hiển thị khi user lần đầu dùng `/story-bank`)

1. **Kể chi tiết cảm xúc**: "lúc đó tôi thấy..." — càng raw càng tốt
2. **Nhắc đến số liệu**: "3 tháng", "tăng 40%", "12k shares"
3. **Nhắc đến bước ngoặt**: điều gì khiến bạn thay đổi hướng?
4. **Không cần văn vẻ**: Agent sẽ rewrite theo Voice DNA khi inject vào bài