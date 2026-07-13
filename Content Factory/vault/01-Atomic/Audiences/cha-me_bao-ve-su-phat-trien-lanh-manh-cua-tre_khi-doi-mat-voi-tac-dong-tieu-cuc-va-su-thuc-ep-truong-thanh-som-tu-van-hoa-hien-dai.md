---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: bảo vệ sự phát triển lành mạnh của trẻ
audience_circumstance: khi đối mặt với tác động tiêu cực và sự thúc ép trưởng thành sớm từ văn hóa hiện đại
parent_audience:
- '[[cha-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi]]'
aliases:
- giữ gìn tuổi thơ cho con trước áp lực xã hội
- nuôi dạy con chậm lại giữa thế giới vội vã
---
# 🎯 cha mẹ muốn bảo vệ sự phát triển lành mạnh của trẻ khi đối mặt với tác động tiêu cực và sự thúc ép trưởng thành sớm từ văn hóa hiện đại

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

