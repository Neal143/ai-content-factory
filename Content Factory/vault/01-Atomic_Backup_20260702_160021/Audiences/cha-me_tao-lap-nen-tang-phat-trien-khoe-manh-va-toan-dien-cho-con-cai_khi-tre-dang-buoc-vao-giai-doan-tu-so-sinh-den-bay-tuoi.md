---
audience_level: big
audience_Job_performer: cha mẹ
audience_main_job: tạo lập nền tảng phát triển khỏe mạnh và toàn diện cho con cái
audience_circumstance: khi trẻ đang bước vào giai đoạn từ sơ sinh đến bảy tuổi
parent_audience: []
aliases:
- nuôi dưỡng trẻ từ 0 đến 7 tuổi
- giúp con phát triển toàn diện những năm đầu đời
---
# 🎯 cha mẹ muốn tạo lập nền tảng phát triển khỏe mạnh và toàn diện cho con cái khi trẻ đang bước vào giai đoạn từ sơ sinh đến bảy tuổi

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

