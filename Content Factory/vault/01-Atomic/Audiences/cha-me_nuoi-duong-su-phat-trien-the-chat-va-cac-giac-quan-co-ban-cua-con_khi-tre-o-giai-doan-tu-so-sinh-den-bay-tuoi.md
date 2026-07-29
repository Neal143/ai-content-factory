---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: nuôi dưỡng sự phát triển thể chất và các giác quan cơ bản của con
audience_circumstance: khi trẻ ở giai đoạn từ sơ sinh đến bảy tuổi
parent_audience:
- '[[phu-huynh-co-con-0-7-tuoi_day-con_sap-co-con-hoac-co-con-0-7-tuoi-tai-viet-nam]]'
aliases:
- chăm sóc thể chất và giác quan cho trẻ mầm non
- hỗ trợ phát triển giác quan 7 năm đầu đời
vivid_circumstances:
- Trẻ chập chững khám phá trong nhà | Va vấp vào các đồ vật xung quanh | Khát khao mãnh liệt được chạm vào mọi thứ
source_type: "book"
source_name: "Beyond the Rainbow Bridge - Nurturing our children from birth to seven (boi Barbara J. Patterson, Pamela Bradley, 2000)"
source_link: "[[Beyond the rainbow bridge]]"
source_path: "02-sources/books/Beyond the rainbow bridge.md"
---
# 🎯 cha mẹ muốn nuôi dưỡng sự phát triển thể chất và các giác quan cơ bản của con khi trẻ ở giai đoạn từ sơ sinh đến bảy tuổi

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

