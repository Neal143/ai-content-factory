---
aliases:
- xây dựng không gian chơi phát triển kỹ năng cho trẻ
- bố trí góc chơi và đồ chơi kích thích trí tưởng tượng
audience_Job_performer: cha mẹ
audience_circumstance: khi thiết lập không gian sống và chọn mua đồ chơi cho con
audience_level: little
audience_main_job: tạo ra môi trường vui chơi giúp trẻ phát triển trí tưởng tượng
  và kỹ năng sống
parent_audience:
- '[[cha-me_nuoi-duong-tri-tuong-tuong-tri-tue-vui-choi_tre-tu-0-den-7-tuoi]]'
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

