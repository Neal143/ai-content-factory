---
name: post-ki-product-tagger
description: "Bước 3/4 của PostClassifierAgent: Trích xuất các ứng viên Topic thuộc 4 nhóm (1. Knowledge [8 loại], 2. Insight [9 loại], 3. Product, 4. Event) bám chặt vào Core Thesis & JTBD đã khóa, kèm trích dẫn nguyên văn evidence."
last_update: 10/11/2026 19:50 (GMT+7)
---

# Post Knowledge, Insight, Product & Event Candidate Extractor Skill (Bước 3/4)

> **Tên file**: .agents/skills/post-ki-product-tagger/SKILL.md
> **Last update**: 10/11/2026 19:50 (GMT+7)
> **Vai trò**: Đọc nội dung bài viết sạch, dựa trên `core_thesis`, `post_format` (Bước 1) và `locked_jtbd` (Bước 2) để trích xuất các ứng viên Topic thuộc 4 nhóm: `knowledge_candidates`, `insight_candidates`, `product_candidates`, `event_candidates` kèm câu trích dẫn nguyên văn (`evidence`).
> **Sử dụng khi**: Được gọi ở Bước 3 bởi `PostClassifierAgent` / `classify_vault_posts.py`.
> **Output**: JSON chứa 4 mảng đối tượng ứng viên (`label`, `sub_type`, `evidence`).
> **Tóm tắt logic hoạt động**: Áp dụng mỏ neo kép (`core_thesis` + `locked_jtbd`) -> Lọc qua 8 loại Knowledge, 9 loại Insight, Product thương mại và 3 loại Event -> Áp dụng trần số lượng 1-1-1 cho bài đơn luận điểm, luật Umbrella Aggregation cho bài `listicle`/`summary`, và luật khái quát hóa cho bài `news` -> Đính kèm `evidence` nguyên văn từ thân bài chính.

## 1. MỎ NEO KÉP & QUY TẮC TRẦN SỐ LƯỢNG THEO `post_format`
1. **Mỏ neo Kép (`core_thesis` + `locked_jtbd`)**: Mọi ứng viên Topic BẮT BUỘC phải phản ánh trực tiếp `core_thesis` (luận điểm chính chiếm $\ge 70\%$ bài viết) và phục vụ trực tiếp cho `locked_jtbd`. Cấm trích xuất từ ví dụ mở bài, chi tiết liệt kê thoáng qua hoặc phần dẫn nhập.
2. **Độ dài `label`**: Cụm danh từ khái quát tiếng Việt có dấu chuẩn, dài **4–12 từ** (có khả năng tái sử dụng cho $\ge 3$ bài viết cùng chủ đề; không chép nguyên câu văn dài hay khẩu hiệu cảm tính).
3. **Quy tắc Trần Số Lượng & Hình thái Bài viết**:
   - **Bài `deep_dive`**: Tối đa **1** `knowledge_candidates`, **1** `insight_candidates`, **1** `product_candidates`, **1** `event_candidates`.
   - **Bài `listicle` / `summary` (Umbrella Aggregation Rule)**:
     - ⛔ **CẤM** bóc từng gạch đầu dòng (`1, 2, 3...`) thành nhiều topic nhỏ lẻ.
     - **BẮT BUỘC** gom toàn bộ các mục liệt kê thành **1 Umbrella Knowledge Topic duy nhất** ở `knowledge_candidates` (thuộc `sub_type`: `"framework"`, `"typology"`, hoặc `"actionable_rule"`, ví dụ: `"Sáu nhu cầu nền tảng nuôi dưỡng tuổi thơ lành mạnh"`) và tối đa **1** `insight_candidates` chung của toàn bài.
     - ⛔ **CẤM** gắn tên sách, tên bài giảng hoặc tên tác giả/diễn giả được tóm tắt (VD: *Yuval Noah Harari*) vào `product_candidates`.
   - **Bài `news` (Tin tức / Sự kiện)**:
     - Trích xuất **1** `event_candidates` (đã khái quát hóa để dùng chung $\ge 3$ bài) + **1** `insight_candidates` (`fear`, `myth`, `pain_point` của độc giả trước tin tức đó) + tối đa **1** `knowledge_candidates` (`trend` hoặc `principle` nếu bài có phân tích chuyên môn; trả về `[]` nếu thuần điểm tin).

## 2. BỐN NHÓM ỨNG VIÊN TOPIC & BẮT BUỘC TRÍCH DẪN `evidence`
- **Nhóm 1 — `knowledge_candidates`**: `sub_type` bắt buộc thuộc `["philosophy", "principle", "concept", "mental_model", "framework", "actionable_rule", "typology", "trend"]`. Nếu bài không giải thích cơ chế/phương pháp rõ ràng $\rightarrow$ trả về `[]`.
- **Nhóm 2 — `insight_candidates`**: `sub_type` bắt buộc thuộc `["desire", "fear", "pain_point", "barrier", "belief", "likes", "dislikes", "pitfall", "myth"]`.
- **Nhóm 3 — `product_candidates`**: `sub_type: "product"`. Chỉ trích xuất khi thân bài chính giới thiệu/bán trực tiếp sản phẩm, dịch vụ, lớp học, khóa học, học bổng thương mại cụ thể (chuẩn hóa tên thương hiệu đối thủ về danh từ loại hình chung 3–8 từ). **CẤM** lấy phương pháp giáo dục chung (*Giáo dục Steiner*, *Montessori*), tên cuốn sách trích dẫn, hoặc tên Fanpage/trường của tác giả ở chữ ký làm `product`. Nếu không có $\rightarrow$ trả về `[]`.
- **Nhóm 4 — `event_candidates`**: `sub_type` thuộc `["social_trend", "seasonal_milestone", "community_event"]`. Khái quát hóa tên sự kiện (4–10 từ, bỏ ngày giờ/địa chỉ cụ thể). Nếu không có $\rightarrow$ trả về `[]`.
- **`evidence` (Bắt buộc)**: Mỗi ứng viên phải trích dẫn nguyên văn 1 câu có thật trong thân bài chính (tối thiểu 5 từ) làm bằng chứng.

## 3. BẢNG CHI TIẾT NHẬN DIỆN SUB-TYPE

### A. 8 Loại Tri thức (`sub_type` của `knowledge_candidates`)
| Sub-type | Dấu hiệu nhận diện trong bài viết |
| :--- | :--- |
| `philosophy` | Tiền đề cốt lõi, tư tưởng chủ đạo không cần chứng minh của tác giả. |
| `principle` | Quan hệ nhân quả bất biến *"X → Y"*. |
| `concept` | Định nghĩa mới hoặc làm rõ bản chất một sự vật/hiện tượng. |
| `mental_model` | Lăng kính nhìn nhận vấn đề, phép loại suy chuyển đổi nhận thức. |
| `framework` | Hệ thống các bước tuần tự (Bước 1, Bước 2...) hoặc cấu trúc giải quyết vấn đề. |
| `actionable_rule` | Chỉ dẫn hành động trực tiếp *"Hãy làm X, tránh làm Y"*. |
| `typology` | Phân chia một tập lớn thành các nhóm nhỏ có đặc trưng riêng biệt. |
| `trend` | Nhận định về xu hướng vận động, biến đổi trong tương lai. |

### B. 9 Loại Tử huyệt Tâm lý (`sub_type` của `insight_candidates`)
| Sub-type | Bản chất tâm lý của Audience đối với Main Job |
| :--- | :--- |
| `desire` | Động lực tiến tới, hình mẫu kết quả mà Audience hằng mong ước. |
| `fear` | Lo sợ về hậu quả tồi tệ nếu làm sai hoặc thất bại trong Main Job. |
| `pain_point` | Sự bức bối, kiệt sức, bất lực đang diễn ra ngay lúc này. |
| `barrier` | Trở ngại thực tế (tâm lý, thời gian, tài chính, rào cản xã hội) cản trở thực hiện Main Job. |
| `belief` | Quan điểm sống hoặc niềm tin sâu sắc chi phối quyết định của Audience. |
| `likes` | Điều Audience cảm thấy dễ chịu, hào hứng đón nhận. |
| `dislikes` | Điều khiến Audience phản cảm, muốn tránh xa. |
| `pitfall` | Cách làm sai lầm/độc hại phổ biến mà Audience tự chuốc lấy khi làm Main Job. |
| `myth` | Kiến thức/thói quen sai lệch mà số đông tin sái cổ nhưng bị bài viết vạch trần. |

## 4. ĐỊNH DẠNG JSON ĐẦU RA
Chỉ trả về JSON theo cấu trúc:
```json
{
  "knowledge_candidates": [
    {
      "label": "Sáu nhu cầu nền tảng nuôi dưỡng tuổi thơ lành mạnh",
      "sub_type": "framework",
      "evidence": "Ăn uống, vui chơi, vận động, nghỉ ngơi và đi ngủ vào những khoảng thời gian tương đối ổn định giúp trẻ có cảm giác an toàn"
    }
  ],
  "insight_candidates": [
    {
      "label": "Cạm bẫy lấp kín lịch trình của trẻ bằng các lớp học thêm",
      "sub_type": "pitfall",
      "evidence": "Đừng lấp kín lịch trình của con bằng quá nhiều hoạt động, lớp học hay những trải nghiệm mà người lớn cho rằng sẽ tốt"
    }
  ],
  "product_candidates": [],
  "event_candidates": []
}
```
