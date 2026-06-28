---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giúp con kiểm soát nỗi sợ hãi
audience_circumstance: khi con hoảng loạn trước một tình huống hoặc sự vật cụ thể
vivid_circumstances: ["Tại một buổi cắm trại | Con la hét, khóc lóc và bám chặt lấy bố khi thấy đống lửa trại | Bố bực bội cố gắng dùng logic giải thích rằng ngọn lửa rất vui và không đáng sợ", "Tại một buổi cắm trại | Con la hét, khóc lóc và bám chặt lấy bố khi thấy đống lửa trại | Bố bực bội cố gắng dùng logic giải thích rằng ngọn lửa rất vui và không đáng sợ"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh trấn an khi con hoảng sợ
- cha mẹ giúp con vượt qua nỗi sợ
---
# 🎯 Cha mẹ muốn giúp con kiểm soát nỗi sợ hãi khi con hoảng loạn trước một tình huống hoặc sự vật cụ thể

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

