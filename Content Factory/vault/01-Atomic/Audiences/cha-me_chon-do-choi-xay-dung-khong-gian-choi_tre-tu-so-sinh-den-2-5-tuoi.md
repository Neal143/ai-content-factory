---
aliases:
- mua đồ chơi an toàn cho trẻ sơ sinh
- thiết kế góc chơi cho bé dưới 2.5 tuổi
audience_Job_performer: cha mẹ
audience_circumstance: khi chăm sóc con từ sơ sinh đến 2,5 tuổi
audience_level: little
audience_main_job: chọn đồ chơi và xây dựng không gian chơi lành mạnh
parent_audience:
- '[[cha-me_nuoi-duong-tri-tuong-tuong-tri-tue-vui-choi_tre-tu-0-den-7-tuoi]]'
vivid_circumstances: ["Trong nhà bếp | Trẻ liên tục lôi xoong nồi và bát ra khỏi tủ | Trẻ say sưa chơi quanh quẩn bên chân cha mẹ", "Trong nhà bếp | Trẻ liên tục lôi xoong nồi và bát ra khỏi tủ | Trẻ say sưa chơi quanh quẩn bên chân cha mẹ"]
---
# 🎯 cha mẹ muốn chọn đồ chơi và xây dựng không gian chơi lành mạnh khi chăm sóc con từ sơ sinh đến 2,5 tuổi

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

