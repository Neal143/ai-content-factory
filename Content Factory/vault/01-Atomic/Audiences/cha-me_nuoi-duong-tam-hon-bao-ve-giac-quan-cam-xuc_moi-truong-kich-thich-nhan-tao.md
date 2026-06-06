---
aliases:
- bảo vệ cảm xúc của con khỏi kích thích môi trường
- chăm sóc đời sống tinh thần cho trẻ nhỏ hiện nay
audience_Job_performer: cha mẹ
audience_circumstance: khi môi trường xung quanh ngập tràn các kích thích nhân tạo
audience_level: little
audience_main_job: nuôi dưỡng tâm hồn và bảo vệ các giác quan cảm xúc của trẻ
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-toan-dien_tre-tu-so-sinh-den-bay-tuoi]]'
---
# 🎯 cha mẹ muốn nuôi dưỡng tâm hồn và bảo vệ các giác quan cảm xúc của trẻ khi môi trường xung quanh ngập tràn các kích thích nhân tạo

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

