---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: phá vỡ sự kháng cự bướng bỉnh và thái độ xa lánh của con
audience_circumstance: khi trẻ vừa làm sai một việc gì đó
vivid_circumstances:
- Con giấu đồ chơi của em khiến em khóc nhưng kiên quyết từ chối xin lỗi, hoặc con nói dối trắng trợn về việc bị loại khỏi đội bóng
- Con giấu đồ chơi của em khiến em khóc nhưng kiên quyết từ chối xin lỗi, hoặc con nói dối trắng trợn về việc bị loại khỏi đội bóng
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh đối phó khi con bướng bỉnh
- cha mẹ xử lý khi con cố chấp
---
# 🎯 Cha mẹ muốn phá vỡ sự kháng cự bướng bỉnh và thái độ xa lánh của con khi trẻ vừa làm sai một việc gì đó

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

