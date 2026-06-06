---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: Người muốn giúp con tách rời khỏi cha mẹ một cách bình an
audience_circumstance: khi trẻ khóc lóc, bám víu lúc đi học hoặc khi cha mẹ vắng mặt.
vivid_circumstances: []
vivid_circumstances_reserve: []
parent_audience: []
aliases:
- Người muốn giúp con tách rời khỏi cha mẹ một cách bình an
---
# 🎯 Cha mẹ muốn Người muốn giúp con tách rời khỏi cha mẹ một cách bình an khi trẻ khóc lóc, bám víu lúc đi học hoặc khi cha mẹ vắng mặt.

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

