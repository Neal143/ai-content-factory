---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: Phụ huynh muốn khuyến khích con cái nói sự thật
audience_circumstance: khi phát hiện trẻ có hành vi che giấu hoặc phủ nhận lỗi lầm.
vivid_circumstances: []
vivid_circumstances_reserve: []
parent_audience: []
aliases:
- Phụ huynh muốn khuyến khích con cái nói sự thật
---
# 🎯 Cha mẹ muốn Phụ huynh muốn khuyến khích con cái nói sự thật khi phát hiện trẻ có hành vi che giấu hoặc phủ nhận lỗi lầm.

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

