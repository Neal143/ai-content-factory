---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giảm bớt xung đột và xây dựng mối quan hệ hòa thuận giữa các con
audience_circumstance: khi chúng tranh cãi, đánh nhau hoặc ghen tị tranh giành sự
  chú ý
vivid_circumstances: ["Phòng chơi ở nhà | Tiếng la hét, khóc lóc và đồ đạc rơi loảng xoảng | Hai đứa trẻ giằng co đồ chơi, tố cáo nhau đẩy ngã và tranh giành đúng sai với cha mẹ", "Phòng chơi ở nhà | Tiếng la hét, khóc lóc và đồ đạc rơi loảng xoảng | Hai đứa trẻ giằng co đồ chơi, tố cáo nhau đẩy ngã và tranh giành đúng sai với cha mẹ"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh hòa giải khi các con đánh nhau
- cha mẹ xử lý khi anh chị em ghen tị
keywords: []
---
# 🎯 Cha mẹ muốn giảm bớt xung đột và xây dựng mối quan hệ hòa thuận giữa các con khi chúng tranh cãi, đánh nhau hoặc ghen tị tranh giành sự chú ý

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

