---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: thiết lập ranh giới kỷ luật với con cái
audience_circumstance: khi trẻ phản kháng, tức giận hoặc có thái độ thô lỗ
vivid_circumstances:
- Phòng khách/Cửa ra vào | Trẻ hét lên "Con không lạnh, con không mặc áo khoác", cha mẹ khăng khăng ép buộc | Căng thẳng, đối đầu, bực tức
- Phòng khách/Cửa ra vào | Trẻ hét lên "Con không lạnh, con không mặc áo khoác", cha mẹ khăng khăng ép buộc | Căng thẳng, đối đầu, bực tức
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- người nuôi con muốn giữ kỷ luật khi con cãi lại
- phụ huynh cần đặt quy tắc khi con hỗn láo
---
# 🎯 Cha mẹ muốn thiết lập ranh giới kỷ luật với con cái khi trẻ phản kháng, tức giận hoặc có thái độ thô lỗ

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

