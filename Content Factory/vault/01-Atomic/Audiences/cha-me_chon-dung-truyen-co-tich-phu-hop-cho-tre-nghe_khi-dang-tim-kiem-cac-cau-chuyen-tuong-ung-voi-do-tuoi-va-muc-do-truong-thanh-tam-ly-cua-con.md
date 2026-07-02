---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: chọn đúng truyện cổ tích phù hợp cho trẻ nghe
audience_circumstance: khi đang tìm kiếm các câu chuyện tương ứng với độ tuổi và mức
  độ trưởng thành tâm lý của con
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi]]'
aliases:
- kể chuyện cổ tích cho con ngủ
- chọn truyện đọc cho bé theo độ tuổi
keywords: []
---
# 🎯 cha mẹ muốn chọn đúng truyện cổ tích phù hợp cho trẻ nghe khi đang tìm kiếm các câu chuyện tương ứng với độ tuổi và mức độ trưởng thành tâm lý của con

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

