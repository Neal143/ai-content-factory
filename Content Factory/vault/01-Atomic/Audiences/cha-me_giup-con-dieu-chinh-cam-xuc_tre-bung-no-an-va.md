---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giúp con xây dựng kỹ năng điều chỉnh cảm xúc
audience_circumstance: khi trẻ bùng nổ, ăn vạ do những mong muốn bị từ chối
vivid_circumstances:
- Bếp vào buổi sáng | Trẻ ngã lăn ra sàn, khóc lóc và la hét không ngừng đòi ăn kem | Tức giận, mất kiểm soát cảm xúc
- Nửa đêm tại phòng khách | Trẻ 7 tuổi xuất hiện, than vãn liên tục "Mẹ không bao giờ để lại giấy nhắn, con ghét bài tập!" | Trẻ bực bội, bất mãn, phụ huynh bất ngờ, mệt mỏi
- Bếp vào buổi sáng | Trẻ ngã lăn ra sàn, khóc lóc và la hét không ngừng đòi ăn kem | Tức giận, mất kiểm soát cảm xúc
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh xử lý khi con ăn vạ
- cha mẹ rèn cảm xúc cho trẻ hay cáu gắt
source_type: "book"
source_name: "Good Inside: A Guide to Becoming the Parent You Want to Be (bởi Dr. Becky Kennedy, 2022)"
source_link: "[[Good Inside]]"
source_path: "02-sources/books/Good Inside.md"
---
# 🎯 Cha mẹ muốn giúp con xây dựng kỹ năng điều chỉnh cảm xúc khi trẻ bùng nổ, ăn vạ do những mong muốn bị từ chối

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

