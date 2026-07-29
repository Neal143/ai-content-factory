---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: duy trì ranh giới an toàn và sự kết nối
audience_circumstance: khi con cái phản kháng và bùng nổ cảm xúc
vivid_circumstances:
- Buổi chiều tối tại nhà | Con la hét khóc lóc đòi mẹ khi mẹ phải bắt đầu làm việc | Bề ngoài có vẻ hỗn loạn, mẹ dễ hoang mang và tự trách mình
- Buổi chiều tối tại nhà | Con la hét khóc lóc đòi mẹ khi mẹ phải bắt đầu làm việc | Bề ngoài có vẻ hỗn loạn, mẹ dễ hoang mang và tự trách mình
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh muốn giữ nguyên tắc nhưng không mất kết nối
- cha mẹ muốn thiết lập kỷ luật trong lúc con khóc lóc
source_type: "book"
source_name: "Good Inside: A Guide to Becoming the Parent You Want to Be (bởi Dr. Becky Kennedy, 2022)"
source_link: "[[Good Inside]]"
source_path: "02-sources/books/Good Inside.md"
---
# 🎯 Cha mẹ muốn duy trì ranh giới an toàn và sự kết nối khi con cái phản kháng và bùng nổ cảm xúc

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

