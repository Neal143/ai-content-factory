---
audience_level: little
audience_Job_performer: cha mẹ
audience_main_job: giúp trẻ đối mặt và tích hợp các ký ức đau buồn
audience_circumstance: khi trẻ có biểu hiện né tránh hoặc sợ hãi việc nhắc lại chuyện
  cũ
vivid_circumstances: ["Đang chế tạo xe đua gỗ | Khuôn mặt hiện lên vẻ sợ hãi khi được yêu cầu đối mặt | Từ chối, né tránh nhắc lại chuyện ở công viên"]
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh
- người chăm sóc
---
# 🎯 cha mẹ muốn giúp trẻ đối mặt và tích hợp các ký ức đau buồn khi trẻ có biểu hiện né tránh hoặc sợ hãi việc nhắc lại chuyện cũ

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

