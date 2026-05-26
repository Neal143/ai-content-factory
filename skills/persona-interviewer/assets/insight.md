---
type: insight
insight_type: "{{type}}"
topics: {{topics}}
source_id: "persona-interview"
belongs_to_audience: "[[{{target_audience}}]]"
status: processed
created: "{{date}}"
source_type: "User"
source_name: "Persona Interview"
confidence: 1.0
vivid_insights: []
vivid_insights_reserve: []
---

# {{type}}: {{name}}

## 1. Nội dung text thô (Raw payload)
{{raw_payload}}

## 2. Giải thích / Luận điểm (Insightful explain)
{{llm_explain}}

## 3. Liên kết mở rộng


<!-- ==========================================
VÍ DỤ MINH HỌA 1 FILE INSIGHT HOÀN CHỈNH SAU KHI RENDER
(Đoạn này được đưa vào trong thẻ comment để ẩn trên giao diện đọc của Obsidian)

---
type: insight
insight_type: "PAIN_POINT"
insight_name: "Sợ bị công nghệ AI cướp mất miếng cơm"
belongs_to_audience: "[[Content_Creator_Bất_an_trước_làn_sóng_GenAI]]"
status: processed
created: "2026-03-30"
source_type: "User"
source_name: "Persona Interview"
confidence: 1.0
---

# PAIN_POINT: Sợ bị công nghệ AI cướp mất miếng cơm

## 1. Nội dung text thô (Raw payload)
Dạo này tôi thấy ChatGPT với Claude viết lách mượt quá. Đọc xong tôi thực sự hoang mang, sợ rằng với tốc độ này thì 1-2 năm nữa nghề Content Creator truyền thống sẽ bị xóa sổ. Khách hàng giờ thà bỏ tiền cho công cụ AI giá rẻ thay vì trả lương cho mình...

## 2. Giải thích / Luận điểm (Insightful explain)
-> LUẬN ĐIỂM: Khủng hoảng niềm tin & Nỗi sợ bị đào thải (Career Obsolescence). 
Người dùng không ghét công nghệ, mà họ sợ hãi vì cảm thấy AI đang từ vị thế "công cụ hỗ trợ" bước lên thành "đối thủ cạnh tranh giá rẻ" đe dọa sinh kế trực tiếp. Pain Point cốt lõi này dựng lên hàng rào phòng thủ tâm lý, khiến họ từ chối thích nghi với hệ sinh thái mới.

## 3. Liên kết mở rộng
========================================== -->

<!--
Tên file: insight.md
Last update: 27/05/2026 00:15 (GMT+7)
Vai trò: Template Markdown cho các file Atomic Insight của hệ thống DIKW
Được sử dụng khi nào: Khi script generate_insights.py thực hiện render các câu hỏi phỏng vấn Persona thành các file Atomic Insight
Output: File .md chứa đầy đủ frontmatter Schema B mới và thân bài của Insight
Tóm tắt logic hoạt động: Chứa cấu trúc Obsidian-ready frontmatter và các placeholder (type, topics, target_audience, raw_payload, llm_explain) để script tự động thay thế bằng dữ liệu thực tế thu được từ quá trình phỏng vấn persona.
-->

