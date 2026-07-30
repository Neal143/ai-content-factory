---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: giúp con nhận thức tính tạm thời của cảm xúc
audience_circumstance: khi con đang bị mắc kẹt và choáng ngợp bởi sự tức giận, sợ hãi hoặc buồn bã
vivid_circumstances:
- Khi trẻ đang khóc lóc ỉ ôi vì một chuyện tồi tệ vừa xảy ra | Bố mẹ ngồi cạnh an ủi | Trẻ đinh ninh rằng mình sẽ mãi buồn bã và ghét bỏ mọi thứ xung quanh
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh
- người hướng dẫn con
source_type: "book"
source_name: "The Whole-Brain Child (bởi Daniel J. Siegel & Tina Payne Bryson, 2011)"
source_link: "[[The Whole-Brain Child#^chunk-10]]"
source_path: "02-sources/books/The Whole-Brain Child.md#^chunk-10"
---
# 🎯 cha mẹ muốn giúp con nhận thức tính tạm thời của cảm xúc khi con đang bị mắc kẹt và choáng ngợp bởi sự tức giận, sợ hãi hoặc buồn bã

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

