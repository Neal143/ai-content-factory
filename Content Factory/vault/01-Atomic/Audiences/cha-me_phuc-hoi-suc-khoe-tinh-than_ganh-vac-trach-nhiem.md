---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: phục hồi sức khỏe tinh thần và bảo vệ bản sắc cá nhân
audience_circumstance: khi đang gánh vác trách nhiệm nuôi dạy con cái mỗi ngày
vivid_circumstances:
- Thời điểm cuối ngày mệt mỏi | Trẻ phản đối, khóc lóc, vòi vĩnh khi cha mẹ muốn đi bộ một mình hoặc đi ăn cùng bạn bè | Cha mẹ cảm thấy kiệt sức, tội lỗi và chịu áp lực phải hy sinh toàn bộ thời gian cho con
- Thời điểm cuối ngày mệt mỏi | Trẻ phản đối, khóc lóc, vòi vĩnh khi cha mẹ muốn đi bộ một mình hoặc đi ăn cùng bạn bè | Cha mẹ cảm thấy kiệt sức, tội lỗi và chịu áp lực phải hy sinh toàn bộ thời gian cho con
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh muốn lấy lại năng lượng
- cha mẹ chăm sóc bản thân khi nuôi con
---
# 🎯 Cha mẹ muốn phục hồi sức khỏe tinh thần và bảo vệ bản sắc cá nhân khi đang gánh vác trách nhiệm nuôi dạy con cái mỗi ngày

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

