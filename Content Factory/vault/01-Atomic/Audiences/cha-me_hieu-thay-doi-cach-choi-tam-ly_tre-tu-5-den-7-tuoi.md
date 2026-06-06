---
aliases:
- nắm bắt tâm lý vui chơi của trẻ 5-7 tuổi
- theo dõi sự phát triển tâm sinh lý của trẻ mẫu giáo lớn
audience_Job_performer: cha mẹ
audience_circumstance: khi con trải qua các giai đoạn phát triển mới
audience_level: little
audience_main_job: hiểu sự thay đổi trong cách chơi và tâm lý của trẻ từ 5 đến 7 tuổi
parent_audience:
- '[[cha-me_nuoi-duong-tri-tuong-tuong-tri-tue-vui-choi_tre-tu-0-den-7-tuoi]]'
---
# 🎯 cha mẹ muốn hiểu sự thay đổi trong cách chơi và tâm lý của trẻ từ 5 đến 7 tuổi khi con trải qua các giai đoạn phát triển mới

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

