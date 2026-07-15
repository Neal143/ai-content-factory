---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: tổ chức một lễ kỷ niệm sinh nhật nuôi dưỡng tâm hồn và gắn kết thiêng liêng
audience_circumstance: khi trẻ bước sang tuổi mới
parent_audience:
- '[[phu-huynh-co-con-0-7-tuoi_day-con_sap-co-con-hoac-co-con-0-7-tuoi-tai-viet-nam]]'
aliases:
- chuẩn bị sinh nhật ý nghĩa cho con
- tổ chức sinh nhật kiểu Waldorf cho bé
---
# 🎯 cha mẹ muốn tổ chức một lễ kỷ niệm sinh nhật nuôi dưỡng tâm hồn và gắn kết thiêng liêng khi trẻ bước sang tuổi mới

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

