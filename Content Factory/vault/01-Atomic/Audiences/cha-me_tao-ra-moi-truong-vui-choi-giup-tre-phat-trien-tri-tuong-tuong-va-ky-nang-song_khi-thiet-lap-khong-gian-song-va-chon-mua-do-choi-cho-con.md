---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: tạo ra môi trường vui chơi giúp trẻ phát triển trí tưởng tượng
  và kỹ năng sống
audience_circumstance: khi thiết lập không gian sống và chọn mua đồ chơi cho con
parent_audience:
- '[[cha-me_tao-moi-truong-nuoi-duong-tri-tuong-tuong-va-su-phat-trien-tri-tue-cho-tre-thong-qua-vui-choi-tu-do_khi-nuoi-day-tre-trong-giai-doan-tu-0-den-7-tuoi]]'
aliases:
- sắp xếp góc chơi tự do cho bé
- mua sắm đồ chơi kích thích sáng tạo
---
# 🎯 cha mẹ muốn tạo ra môi trường vui chơi giúp trẻ phát triển trí tưởng tượng và kỹ năng sống khi thiết lập không gian sống và chọn mua đồ chơi cho con

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

