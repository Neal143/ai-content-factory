---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giúp con tách rời khỏi cha mẹ một cách bình an
audience_circumstance: khi trẻ khóc lóc, bám víu lúc đi học hoặc khi cha mẹ vắng mặt
vivid_circumstances:
- Tại cửa lớp mầm non | Trẻ khóc thét, ôm chặt lấy chân cha mẹ không chịu buông | Cha mẹ bối rối, không biết làm sao để dứt ra.
- Tại cửa lớp mầm non | Trẻ khóc thét, ôm chặt lấy chân cha mẹ không chịu buông | Cha mẹ bối rối, không biết làm sao để dứt ra.
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh xử lý hội chứng bám mẹ
- cha mẹ giúp con quen đi học
source_type: "book"
source_name: "Good Inside: A Guide to Becoming the Parent You Want to Be (bởi Dr. Becky Kennedy, 2022)"
source_link: "[[Good Inside#^chunk-28]]"
source_path: "02-sources/books/Good Inside.md#^chunk-28"
---
# 🎯 Cha mẹ muốn giúp con tách rời khỏi cha mẹ một cách bình an khi trẻ khóc lóc, bám víu lúc đi học hoặc khi cha mẹ vắng mặt

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

