---
aliases:
- nuôi dạy theo tính cách riêng của con
- áp dụng giáo dục phù hợp với đặc điểm từng trẻ
audience_Job_performer: cha mẹ
audience_circumstance: khi đối mặt với những tính cách và hành vi khác biệt của từng
  đứa trẻ
audience_level: little
audience_main_job: cá nhân hóa phương pháp giáo dục
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-toan-dien_tre-tu-so-sinh-den-bay-tuoi]]'
---
# 🎯 cha mẹ muốn cá nhân hóa phương pháp giáo dục khi đối mặt với những tính cách và hành vi khác biệt của từng đứa trẻ

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

