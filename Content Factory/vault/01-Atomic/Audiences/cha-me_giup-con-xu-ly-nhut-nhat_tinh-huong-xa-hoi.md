---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giúp con cái xử lý sự nhút nhát
audience_circumstance: khi chúng ngập ngừng, trốn tránh trong các tình huống xã hội hoặc đám đông
vivid_circumstances:
- Tại một bữa tiệc sinh nhật nhộn nhịp | Trẻ khóc lóc trốn sau lưng mẹ trong khi các bạn đang chơi | Mẹ bực bội, cảm thấy xấu hổ và tội lỗi.
- Tại một bữa tiệc sinh nhật nhộn nhịp | Trẻ khóc lóc trốn sau lưng mẹ trong khi các bạn đang chơi | Mẹ bực bội, cảm thấy xấu hổ và tội lỗi.
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh giúp trẻ nhút nhát
- cha mẹ rèn tự tin cho con rụt rè
---
# 🎯 Cha mẹ muốn giúp con cái xử lý sự nhút nhát khi chúng ngập ngừng, trốn tránh trong các tình huống xã hội hoặc đám đông

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

