---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: khiến con cái hợp tác thực hiện các yêu cầu
audience_circumstance: khi trẻ đang phớt lờ lời nói của họ
vivid_circumstances: ["Trong nhà | Mẹ bực tức hét lên \"Con có đang nghe mẹ nói không?\" vì con phớt lờ yêu cầu | Trẻ đóng băng phòng thủ, mẹ tức giận và kiệt sức.", "Trong nhà | Mẹ bực tức hét lên \"Con có đang nghe mẹ nói không?\" vì con phớt lờ yêu cầu | Trẻ đóng băng phòng thủ, mẹ tức giận và kiệt sức."]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh muốn con nghe lời
- cha mẹ trị tính không chịu nghe lời của con
---
# 🎯 Cha mẹ muốn khiến con cái hợp tác thực hiện các yêu cầu khi trẻ đang phớt lờ lời nói của họ

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

