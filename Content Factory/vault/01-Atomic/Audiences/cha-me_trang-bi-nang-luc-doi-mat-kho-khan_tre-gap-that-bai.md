---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: trang bị năng lực đối mặt với khó khăn cho con
audience_circumstance: khi trẻ gặp thất bại hoặc bộc lộ những cảm xúc tiêu cực
vivid_circumstances: ["Khi con khóc lóc vì tháp đồ chơi liên tục bị đổ hoặc con phàn nàn vì chạy chậm nhất lớp | Cha mẹ cuống cuồng nói lời an ủi, đánh lạc hướng hoặc vội vàng làm hộ con | Cảm thấy xót xa, lo lắng và muốn dập tắt ngay sự khó chịu của con", "Con đang xếp hình và không ghép được một mảnh | Bực bội ném mảnh ghép đi | Than vãn: \"Con rất tệ, con ghét nó\"", "Khi con khóc lóc vì tháp đồ chơi liên tục bị đổ hoặc con phàn nàn vì chạy chậm nhất lớp | Cha mẹ cuống cuồng nói lời an ủi, đánh lạc hướng hoặc vội vàng làm hộ con | Cảm thấy xót xa, lo lắng và muốn dập tắt ngay sự khó chịu của con"]
vivid_circumstances_reserve: ["Con đang xếp hình và không ghép được một mảnh | Bực bội ném mảnh ghép đi | Than vãn: \"Con rất tệ, con ghét nó\""]
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh muốn dạy con kiên cường
- cha mẹ giúp con đối mặt thất bại
keywords: []
---
# 🎯 Cha mẹ muốn trang bị năng lực đối mặt với khó khăn cho con khi trẻ gặp thất bại hoặc bộc lộ những cảm xúc tiêu cực

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

