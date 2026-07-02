---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giải mã nguyên nhân thực sự đằng sau những tiếng khóc của con
audience_circumstance: khi trẻ bất ngờ rơi nước mắt hoặc có biểu hiện khóc lóc thái
  quá
vivid_circumstances: ["Ngay tại nhà | Cha báo tin con trượt đội bóng chày và thấy con rơm rớm nước mắt | Người cha bối rối, lưỡng lự không biết nên nói gì hay đánh lạc hướng để xoa dịu nỗi đau của con.", "Ngay tại nhà | Cha báo tin con trượt đội bóng chày và thấy con rơm rớm nước mắt | Người cha bối rối, lưỡng lự không biết nên nói gì hay đánh lạc hướng để xoa dịu nỗi đau của con."]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh xử lý khi con hay khóc
- cha mẹ dỗ trẻ khóc nhè
---
# 🎯 Cha mẹ muốn giải mã nguyên nhân thực sự đằng sau những tiếng khóc của con khi trẻ bất ngờ rơi nước mắt hoặc có biểu hiện khóc lóc thái quá

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

