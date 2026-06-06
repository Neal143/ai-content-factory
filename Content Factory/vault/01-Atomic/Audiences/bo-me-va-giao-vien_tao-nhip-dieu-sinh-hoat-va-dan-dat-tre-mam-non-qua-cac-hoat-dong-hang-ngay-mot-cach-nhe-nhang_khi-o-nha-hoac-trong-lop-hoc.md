---
aliases:
- dẫn dắt trẻ qua hoạt động hàng ngày
- tạo nhịp điệu cho trẻ mầm non
audience_Job_performer: bố mẹ và giáo viên
audience_circumstance: khi ở nhà hoặc trong lớp học
audience_level: little
audience_main_job: tạo nhịp điệu sinh hoạt và dẫn dắt trẻ mầm non qua các hoạt động
  hàng ngày một cách nhẹ nhàng
parent_audience:
- '[[bo-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi]]'
---
# 🎯 bố mẹ và giáo viên muốn tạo nhịp điệu sinh hoạt và dẫn dắt trẻ mầm non qua các hoạt động hàng ngày một cách nhẹ nhàng khi ở nhà hoặc trong lớp học

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

