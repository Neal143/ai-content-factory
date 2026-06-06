---
aliases:
- rèn tính tự giác cho con thông qua giao tiếp hàng ngày
- dạy con nghe lời khi đưa ra yêu cầu
audience_Job_performer: cha mẹ
audience_circumstance: khi đưa ra các yêu cầu hàng ngày cho trẻ
audience_level: little
audience_main_job: thiết lập kỷ luật và giao tiếp hiệu quả
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-toan-dien_tre-tu-so-sinh-den-bay-tuoi]]'
vivid_circumstances: ["Tại hội chợ trường học | Người mẹ liên tục hỏi con muốn ăn ở đâu | Đứa trẻ hai tuổi bật khóc vì áp lực", "Tại hội chợ trường học | Người mẹ liên tục hỏi con muốn ăn ở đâu | Đứa trẻ hai tuổi bật khóc vì áp lực"]
---
# 🎯 cha mẹ muốn thiết lập kỷ luật và giao tiếp hiệu quả khi đưa ra các yêu cầu hàng ngày cho trẻ

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

