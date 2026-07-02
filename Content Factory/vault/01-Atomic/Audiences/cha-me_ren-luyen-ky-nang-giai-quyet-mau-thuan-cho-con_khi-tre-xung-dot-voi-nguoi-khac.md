---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: rèn luyện kỹ năng giải quyết mâu thuẫn cho con
audience_circumstance: khi trẻ xảy ra xung đột với người khác
vivid_circumstances: ["Tại bàn làm việc | Bé gái 7 tuổi tức giận bước đến mách rằng em trai vừa gọi mình là đồ ngốc | Khăng khăng khẳng định em trai vô cớ chửi mình"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh
- người phân xử mâu thuẫn
keywords: []
---
# 🎯 cha mẹ muốn rèn luyện kỹ năng giải quyết mâu thuẫn cho con khi trẻ xảy ra xung đột với người khác

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

