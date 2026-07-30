---
audience_level: big
audience_Job_performer: Cha mẹ
audience_main_job: nuôi dạy những đứa trẻ kiên cường và xây dựng mối quan hệ gia đình gắn kết
audience_circumstance: khi phải đối mặt với những hành vi khó khăn và cảm xúc bùng nổ của con trẻ
vivid_circumstances: []
vivid_circumstances_reserve: []
parent_audience: []
aliases:
- phụ huynh muốn con tự lập và gắn kết gia đình
- người làm cha mẹ muốn rèn tính kiên cường cho con
source_type: "book"
source_name: "Good Inside: A Guide to Becoming the Parent You Want to Be (bởi Dr. Becky Kennedy, 2022)"
source_link: "[[Good Inside#^book-overview]]"
source_path: "02-sources/books/Good Inside.md#^book-overview"
---
# 🎯 Cha mẹ muốn nuôi dạy những đứa trẻ kiên cường và xây dựng mối quan hệ gia đình gắn kết khi phải đối mặt với những hành vi khó khăn và cảm xúc bùng nổ của con trẻ

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

