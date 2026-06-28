---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: khuyến khích con cái nói sự thật
audience_circumstance: khi phát hiện trẻ có hành vi che giấu hoặc phủ nhận lỗi lầm
vivid_circumstances: ["Phát hiện con làm sai hoặc che giấu sự thật | Nghe con liên tục chối bay chối biến | Trạng thái căng thẳng, sẵn sàng vạch trần lời nói dối của con", "Phát hiện con làm sai hoặc che giấu sự thật | Nghe con liên tục chối bay chối biến | Trạng thái căng thẳng, sẵn sàng vạch trần lời nói dối của con"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh dạy con tính trung thực
- cha mẹ xử lý khi trẻ nói dối
---
# 🎯 Cha mẹ muốn khuyến khích con cái nói sự thật khi phát hiện trẻ có hành vi che giấu hoặc phủ nhận lỗi lầm

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

