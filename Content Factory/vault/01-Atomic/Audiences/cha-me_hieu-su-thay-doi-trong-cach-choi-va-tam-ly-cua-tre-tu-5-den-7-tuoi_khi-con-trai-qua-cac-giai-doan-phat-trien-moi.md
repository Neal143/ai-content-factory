---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: hiểu sự thay đổi trong cách chơi và tâm lý của trẻ từ 5 đến 7 tuổi
audience_circumstance: khi con trải qua các giai đoạn phát triển mới
parent_audience:
- '[[cha-me_tao-moi-truong-nuoi-duong-tri-tuong-tuong-va-su-phat-trien-tri-tue-cho-tre-thong-qua-vui-choi-tu-do_khi-nuoi-day-tre-trong-giai-doan-tu-0-den-7-tuoi]]'
aliases:
- nắm bắt tâm lý vui chơi của trẻ tiền tiểu học
- đồng hành cùng sự biến đổi tâm lý của bé 5-7 tuổi
source_type: "book"
source_name: "Beyond the Rainbow Bridge - Nurturing our children from birth to seven (boi Barbara J. Patterson, Pamela Bradley, 2000)"
source_link: "[[Beyond the rainbow bridge#^chunk-10]]"
source_path: "02-sources/books/Beyond the rainbow bridge.md#^chunk-10"
---
# 🎯 cha mẹ muốn hiểu sự thay đổi trong cách chơi và tâm lý của trẻ từ 5 đến 7 tuổi khi con trải qua các giai đoạn phát triển mới

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

