---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: xoa dịu và điều chỉnh cảm xúc của con
audience_circumstance: khi trẻ bùng nổ dữ dội và cự tuyệt sự giúp đỡ
vivid_circumstances:
- Phòng chơi | Trẻ la hét "Tránh ra, con ghét mẹ!" khi bị nhắc nhở | Mẹ bực bội, bất lực
- Phòng chơi | Trẻ la hét "Tránh ra, con ghét mẹ!" khi bị nhắc nhở | Mẹ bực bội, bất lực
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh dỗ trẻ khóc thét
- cha mẹ xử lý khi con từ chối giúp đỡ
---
# 🎯 Cha mẹ muốn xoa dịu và điều chỉnh cảm xúc của con khi trẻ bùng nổ dữ dội và cự tuyệt sự giúp đỡ

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

