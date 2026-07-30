---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: xoa dịu cảm xúc của trẻ
audience_circumstance: khi trẻ mệt mỏi hoặc quấy khóc
parent_audience:
- '[[cha-me_ren-luyen-ky-luat-cho-con_khi-doi-mat-voi-nhung-hanh-vi-chua-tot-cua-tre-nho]]'
aliases:
- dỗ dành bé khi mệt
- an ủi con lúc quấy khóc
source_type: "book"
source_name: "Beyond the Rainbow Bridge - Nurturing our children from birth to seven (boi Barbara J. Patterson, Pamela Bradley, 2000)"
source_link: "[[Beyond the rainbow bridge#^chunk-22]]"
source_path: "02-sources/books/Beyond the rainbow bridge.md#^chunk-22"
---
# 🎯 cha mẹ muốn xoa dịu cảm xúc của trẻ khi trẻ mệt mỏi hoặc quấy khóc

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

