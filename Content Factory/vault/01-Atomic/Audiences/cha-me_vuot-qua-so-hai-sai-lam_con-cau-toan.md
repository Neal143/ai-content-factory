---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: giúp con vượt qua sự sợ hãi khi mắc sai lầm
audience_circumstance: khi con thể hiện thái độ cứng nhắc, cáu gắt hoặc sụp đổ ngay khi không đạt được kết quả hoàn hảo
vivid_circumstances:
- Khi bé Freya (5 tuổi) viết sai chính tả | Bé liên tục tẩy xóa, tức giận và hét lên "Con ghét viết" | Mẹ bối rối không biết làm sao
- Khi bé Freya (5 tuổi) viết sai chính tả | Bé liên tục tẩy xóa, tức giận và hét lên "Con ghét viết" | Mẹ bối rối không biết làm sao
vivid_circumstances_reserve: []
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh trị chứng cầu toàn của con
- cha mẹ giúp trẻ sợ sai
source_type: "book"
source_name: "Good Inside: A Guide to Becoming the Parent You Want to Be (bởi Dr. Becky Kennedy, 2022)"
source_link: "[[Good Inside]]"
source_path: "02-sources/books/Good Inside.md"
---
# 🎯 Cha mẹ muốn giúp con vượt qua sự sợ hãi khi mắc sai lầm khi con thể hiện thái độ cứng nhắc, cáu gắt hoặc sụp đổ ngay khi không đạt được kết quả hoàn hảo

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

