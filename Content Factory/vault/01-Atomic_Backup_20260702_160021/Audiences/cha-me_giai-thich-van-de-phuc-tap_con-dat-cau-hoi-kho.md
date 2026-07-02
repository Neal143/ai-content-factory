---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giải thích những vấn đề phức tạp, nhạy cảm
audience_circumstance: khi con cái đặt câu hỏi khó hoặc chứng kiến sự kiện gây bối
  rối
vivid_circumstances: ["Phòng bếp | Bố mẹ cãi vã lớn tiếng, nét mặt giận dữ | Trẻ đang ăn trưa, im lặng nhưng mang nỗi sợ bên trong", "Phòng bếp | Bố mẹ cãi vã lớn tiếng, nét mặt giận dữ | Trẻ đang ăn trưa, im lặng nhưng mang nỗi sợ bên trong"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh trả lời câu hỏi khó của con
- cha mẹ giải thích chuyện nhạy cảm cho trẻ
---
# 🎯 Cha mẹ muốn giải thích những vấn đề phức tạp, nhạy cảm khi con cái đặt câu hỏi khó hoặc chứng kiến sự kiện gây bối rối

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

