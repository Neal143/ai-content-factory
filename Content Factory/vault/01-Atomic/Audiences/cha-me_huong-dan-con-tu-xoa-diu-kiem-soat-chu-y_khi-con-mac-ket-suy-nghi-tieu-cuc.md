---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: hướng dẫn con cách tự xoa dịu và kiểm soát sự chú ý
audience_circumstance: khi con bị mắc kẹt vào những suy nghĩ, cảm giác tiêu cực hoặc
  lo âu
vivid_circumstances: []
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh
- người hỗ trợ con
keywords: []
---
# 🎯 cha mẹ muốn hướng dẫn con cách tự xoa dịu và kiểm soát sự chú ý khi con bị mắc kẹt vào những suy nghĩ, cảm giác tiêu cực hoặc lo âu

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

