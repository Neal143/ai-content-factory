---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: bảo vệ sức khỏe và thúc đẩy sự phát triển toàn diện của trẻ
audience_circumstance: khi chăm sóc trẻ nhỏ trong sinh hoạt hàng ngày
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi]]'
aliases:
- chăm sóc thể chất và tinh thần cho con
- nuôi dưỡng trẻ lớn khôn mỗi ngày
vivid_circumstances: ["Mùa đông hoặc khi trời lạnh | Trẻ nói không lạnh dù chạm vào da thấy lạnh | Trẻ chưa phát triển hoàn toàn cảm nhận nhiệt độ bên trong"]
keywords: []
---
# 🎯 cha mẹ muốn bảo vệ sức khỏe và thúc đẩy sự phát triển toàn diện của trẻ khi chăm sóc trẻ nhỏ trong sinh hoạt hàng ngày

## 🧠 Bức tranh Tâm lý (Insights)
*(Khu vực hiển thị tự động toàn bộ Insights đang bám rễ vào tập khách hàng này)*
```dataview
TABLE insight_type, source_name
FROM "01-Atomic/Insights"
WHERE contains(belongs_to_audience, this.file.link)
```

## 💊 Kho Giải pháp (Solutions)
*(Truy vấn tự động các Solutions/Concepts đang phục vụ Insights thuộc tệp Audience này)*
```dataview
TABLE knowledge_type, source_name
FROM "01-Atomic/Solutions" OR "01-Atomic/Concepts"
FLATTEN supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```

## 📖 Kho Evidences
*(Truy vấn tự động các Data-Points, Stories, Quotes liên đới với tệp Audience này)*
```dataview
TABLE type, source_name
FROM "01-Atomic/Data-Points" OR "01-Atomic/Stories" OR "01-Atomic/Quotes"
FLATTEN supports_knowledge AS sk
FLATTEN sk.supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```

