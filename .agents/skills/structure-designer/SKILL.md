---
name: Structure Designer
description: Phase 4 — Thiết kế outline 5 sections, emotional arc, chọn closing combo với rotation check.
last_update: 04/05/2026 16:15 (GMT+7)
---

# Structure Designer (Phase 4)

> EXECUTION_KEY: 3687152a

## 1. Input Variables
Từ Bảng đen (Global Context), TUYỆT ĐỐI CHỈ truy xuất:
1. `Hook 3 phần` (Phase 3)
2. `Research Brief` (Phase 2)
3. `Wisdom Atoms` — Stories từ DIKW
4. `Knowledge/Information/Data Atoms` — Insight/Solution/Concept từ DIKW

## 2. Outline 5 Sections Bắt Buộc
**Story PHẢI đứng trước Deep Dive. Pivot đứng sau Deep Dive.** Phân bổ tổng 1500-1800 từ (KHÔNG quá 1800):

| Section | Mục đích | Độ dài | Word Count | VTS Value Thread | Emotional Arc | Atom Injection |
|---|---|---|---|---|---|---|
| **Hook** | Gây sốc/tò mò | 1-3 câu | 80-120 | Value Promise mạnh nhất | Empathy | Không giới hạn |
| **Story** | Đồng cảm với nỗi đau độc giả | 3-5 câu | 200-300 | Insight Identification | Empathy | Wisdom + Information |
| **Deep Dive** | Đào sâu giá trị cốt lõi | 60% bài | 700-900 | Pain Avoidance xen Value Promise | Tension → Insight | Knowledge + Data (ưu tiên) |
| **Pivot** | Xoay chiều, thách thức nhận thức | 3-5 câu | 200-300 | Social Proof + Value Promise | Action | Wisdom |
| **Closing** | Kết bài mạnh | 2-4 câu | 100-150 | Result Preview / Personal Commitment | Hope | N/A |

**Ghi chú Atom Mapping:**
- Wisdom atoms (Personal Stories) → Story hoặc Pivot (chỗ cần cảm xúc sâu).
- Knowledge atoms (Insight, Solutions/Concepts) → Deep Dive (chỗ cần trí tuệ).
- Information atoms (Concepts) → Story (mô tả nỗi đau).
- Data atoms (Quotes, Data-Points) → Rải đều, ưu tiên Deep Dive và Hook.

**Ghi chú Emotional Arc:** Deep Dive chia 2 pha: đầu = Tension (đẩy sâu vấn đề), cuối = Insight (Aha moment).

## 3. Hybrid Closing System (2 lớp)
Mỗi đoạn Closing PHẢI kết hợp **2 lớp**: 1 Emotional Tone + 1 Structural Technique.

### Lớp 1: Emotional Tone (CẢM XÚC kết bài)
| # | Tone | Mô tả | Khi nào dùng |
|---|------|-------|-------------|
| E1 | **Thoải Mái** | "Làm hết thì tuyệt, 1-2 cái cũng ok" | Bài nhiều steps, tránh áp lực |
| E2 | **Personal Commitment** | "Tôi đang đi con đường này" | Bài có personal story mạnh |
| E3 | **Hừng Hực** | Kể số liệu + cảm xúc thành công | Bài có success story/data |
| E4 | **Quote Đóng Đinh** | Câu nói expert + personal reflection | Bài có authority mạnh |
| E5 | **CTA Cộng Đồng** | Mời comment/tham gia/chia sẻ | Bài muốn conversation |
| E6 | **2 Con Đường** | So sánh 2 tương lai (nếu làm vs không) | Bài có contrast mạnh |

### Lớp 2: Structural Technique (CẤU TRÚC kết bài)
| # | Technique | Mô tả | Khi nào dùng |
|---|-----------|-------|-------------|
| S1 | **Call to Action** | Mời reader hành động cụ thể | Bài có solution/concept áp dụng ngay |
| S2 | **Reflection Question** | Hỏi reader tự suy ngẫm | Bài khai mở tư duy |
| S3 | **Future Vision** | Vẽ viễn cảnh tương lai | Bài có transformation promise |
| S4 | **Circle Back** | Quay lại Hook, khép vòng tròn | Bài có hook story mạnh |
| S5 | **Identity Statement** | Tái định nghĩa reader | Bài thay đổi belief |
| S6 | **Mic Drop** | Câu nói mạnh, kết đột ngột | Bài có climax ở cuối |

### Compatibility Matrix — Chỉ dùng combo có ✅
```
        S1-CTA  S2-Reflect  S3-Vision  S4-Circle  S5-Identity  S6-Mic
E1       ✅       ✅          ✅         ✅         ❌          ❌
E2       ❌       ✅          ✅         ✅         ✅          ✅
E3       ✅       ❌          ✅         ✅         ✅          ✅
E4       ❌       ✅          ✅         ✅         ✅          ✅
E5       ✅       ✅          ❌         ✅         ❌          ❌
E6       ✅       ✅          ✅         ❌         ✅          ✅
```

### Rotation Check
- Đọc `output/logs/production-log.md` → kiểm tra 2 bài gần nhất.
- **Emotional tone**: Không trùng 2 bài liên tiếp.
- **Structural technique**: Không trùng 2 bài liên tiếp.
- Cả 2 lớp đều phải rotate độc lập.

## 4. Format Output Bắt Buộc
Xuất Outline vào file `04-outline.md` tại Run Folder. Mỗi Section PHẢI ghi rõ:

```
## [Tên Section]
- Word count: [CON SỐ CỤ THỂ, KHÔNG DÙNG RANGE] từ
- Atoms: [Atom ID/loại nào được gán — VD: Wisdom (Personal Story từ Vault), Knowledge (Insight X)]
- VTS: [Value signal cụ thể]
- [Nội dung outline cho section này]

## Closing
- Word count: [N] từ
- Closing Combo: E[?] + S[?]
- VTS: [Value signal]
- [Nội dung outline]
```

⛔ **Word count PHẢI là 1 con số cụ thể** (VD: `250 từ`), KHÔNG ĐƯỢC ghi range (VD: `200-300 từ`).

## 5. [SCRIPTED VALIDATION]
Sau khi xuất xong Outline, chạy lệnh:
```powershell
powershell -ExecutionPolicy Bypass -File ".agents/skills/structure-designer/scripts/validate-outline.ps1" -OutlinePath "[Đường dẫn file Outline]"
```
- **PASS** (exit code = 0) → Chuyển Phase 5.
- **FAIL** → Sửa Outline theo lỗi script báo, chạy lại. Tối đa 3 lần retry.
- **FAIL 3 lần** → Dừng pipeline, escalate cho User.

**Ghi log:** `[Phase 4 Validation] Verdict: PASS/FAIL | Attempt: N/3`
