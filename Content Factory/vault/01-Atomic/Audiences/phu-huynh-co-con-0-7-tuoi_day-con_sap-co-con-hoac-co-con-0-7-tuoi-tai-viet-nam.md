---
audience_level: big
audience_Job_performer: Phu huynh sap co con hoac co con tu 0-7 tuoi
audience_main_job: Thiet lap nen tang phat trien cho con
audience_circumstance: Sap co con hoac co con tu 0-7 tuoi, song o Viet Nam
vivid_circumstances: []
vivid_circumstances_reserve: []
parent_audience: []
aliases:
- cha-me_tao-lap-nen-tang-phat-trien-khoe-manh-va-toan-dien-cho-con-cai_khi-tre-dang-buoc-vao-giai-doan-tu-so-sinh-den-bay-tuoi
source_type: "User"
source_name: "Persona Interview"
source_link: "[[../../../personas/Vuon-ong-steiner/audience.yaml]]"
source_path: "../personas/Vuon-ong-steiner/audience.yaml"
---

# 🎯 Phu huynh co con 0-7 tuoi muon Thiet lap nen tang phat trien cho con trong boi canh sap co con hoac co con 0-7 tuoi tai Viet Nam

## 🧠 Buc tranh Tam ly (Insights)
*(Khu vuc hien thi tu dong toan bo Insights dang bam re vao tap khach hang nay)*
```dataview
TABLE insight_type, source_name
FROM "01-Atomic/Insights"
WHERE contains(belongs_to_audience, this.file.link)
```

## 💊 Kho Giai phap (Solutions)
*(Truy van tu dong cac Solutions/Concepts dang phuc vu Insights thuoc tep Audience nay)*
```dataview
TABLE knowledge_type, source_name
FROM "01-Atomic/Solutions" OR "01-Atomic/Concepts"
FLATTEN supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```

## 📖 Kho Evidences
*(Truy van tu dong cac Data-Points, Stories, Quotes lien doi voi tep Audience nay)*
```dataview
TABLE type, source_name
FROM "01-Atomic/Data-Points" OR "01-Atomic/Stories" OR "01-Atomic/Quotes"
FLATTEN supports_knowledge AS sk
FLATTEN sk.supports_insight AS si
WHERE contains(si.belongs_to_audience, this.file.link)
```
