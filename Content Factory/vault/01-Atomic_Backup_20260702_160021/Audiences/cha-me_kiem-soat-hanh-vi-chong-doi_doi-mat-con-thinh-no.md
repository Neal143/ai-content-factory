---
audience_level: little
audience_Job_performer: Cha mẹ
audience_main_job: kiểm soát những hành vi chống đối của con cái mà không làm tổn
  thương lòng tự trọng của chúng
audience_circumstance: khi đối mặt với những cơn thịnh nộ hoặc lời nói gây tổn thương
  từ trẻ
vivid_circumstances: ["Khi con cái gào thét \"Con ghét mẹ! Mẹ là người mẹ tồi tệ nhất thế giới!\" | Cha mẹ bàng hoàng, đau lòng và tức giận | Cuốn vào vòng xoáy mắng mỏ, dằn vặt bản thân.", "Thời điểm bị từ chối một mong muốn | Đứa trẻ hét lớn \"Con ghét gia đình này! Mẹ là người tồi tệ nhất!\" | Phụ huynh cảm thấy bị xúc phạm, tức giận, muốn la mắng trừng phạt ngay lập tức", "Bàn ăn gia đình | Nhăn mặt dữ tợn, thè lưỡi, la hét \"Có!\" | Tức giận, phẫn nộ vì không đồng ý với quy tắc ăn uống."]
vivid_circumstances_reserve: ["Khi con cái gào thét \"Con ghét mẹ! Mẹ là người mẹ tồi tệ nhất thế giới!\" | Cha mẹ bàng hoàng, đau lòng và tức giận | Cuốn vào vòng xoáy mắng mỏ, dằn vặt bản thân.", "Thời điểm bị từ chối một mong muốn | Đứa trẻ hét lớn \"Con ghét gia đình này! Mẹ là người tồi tệ nhất!\" | Phụ huynh cảm thấy bị xúc phạm, tức giận, muốn la mắng trừng phạt ngay lập tức"]
parent_audience:
- '[[cha-me_nuoi-day-tre-kien-cuong_doi-mat-hanh-vi-kho-khan]]'
aliases:
- phụ huynh muốn trị thói chống đối của con
- cha mẹ cần xử lý khi con nổi giận vô cớ
---
# 🎯 Cha mẹ muốn kiểm soát những hành vi chống đối của con cái mà không làm tổn thương lòng tự trọng của chúng khi đối mặt với những cơn thịnh nộ hoặc lời nói gây tổn thương từ trẻ

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

