---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: xây dựng nền tảng thói quen và nhịp điệu sống lành mạnh cho con
audience_circumstance: khi thiết lập các thói quen sinh hoạt hàng ngày trong gia đình
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi]]'
aliases:
- tạo lập nhịp điệu sinh hoạt cho trẻ
- rèn luyện thói quen sống lành mạnh tại nhà
keywords: []
---
# 🎯 cha mẹ muốn xây dựng nền tảng thói quen và nhịp điệu sống lành mạnh cho con khi thiết lập các thói quen sinh hoạt hàng ngày trong gia đình

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

