---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: rèn luyện kỹ năng hồi tưởng để củng cố trí nhớ và sự thấu hiểu cảm xúc cho con
audience_circumstance: khi tương tác cùng con hằng ngày
vivid_circumstances:
- Trong xe ô tô hoặc trên bàn ăn | Cha mẹ đặt câu hỏi khơi gợi chuyện ở trường | Trẻ ngập ngừng hoặc chỉ kể lể ngắn gọn
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh
- người trò chuyện cùng con
source_type: "book"
source_name: "The Whole-Brain Child (bởi Daniel J. Siegel & Tina Payne Bryson, 2011)"
source_link: "[[The Whole-Brain Child#^chunk-09]]"
source_path: "02-sources/books/The Whole-Brain Child.md#^chunk-09"
---
# 🎯 cha mẹ muốn rèn luyện kỹ năng hồi tưởng để củng cố trí nhớ và sự thấu hiểu cảm xúc cho con khi tương tác cùng con hằng ngày

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

