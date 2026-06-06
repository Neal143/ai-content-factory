## read_inputs
**1. Input Variables**
Từ Bảng đen (Global Context), TUYỆT ĐỐI CHỈ truy xuất:
1. `Hook 3 phần` (Phase 3)
2. `Research Brief` (Phase 2)
3. `Wisdom Atoms` — Stories từ DIKW
4. `Knowledge/Information/Data Atoms` — Insight/Solution/Concept từ DIKW

## design_outline
**2. Outline 5 Phần Bắt Buộc**
**Story PHẢI đứng trước Deep Dive. Pivot đứng sau Deep Dive.** Phân bổ tổng 1500-1800 từ (KHÔNG quá 1800):

| Phần | Mục đích | Độ dài | Word Count | VTS Value Thread | Emotional Arc | Atom Injection |
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

## apply_closing
**3. Hybrid Closing System (2 lớp)**
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
```text
        S1-CTA  S2-Reflect  S3-Vision  S4-Circle  S5-Identity  S6-Mic
E1       ✅       ✅          ✅         ✅         ❌          ❌
E2       ❌       ✅          ✅         ✅         ✅          ✅
E3       ✅       ❌          ✅         ✅         ✅          ✅
E4       ❌       ✅          ✅         ✅         ✅          ✅
E5       ✅       ✅          ❌         ✅         ❌          ❌
E6       ✅       ✅          ✅         ❌         ✅          ✅
```

## write_output
**4. Format Output Bắt Buộc**
Xuất Outline vào file `04-outline.md` tại Run Folder. Mỗi Section PHẢI ghi rõ:

```text
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

## check_word_count
Check 1: Kiểm tra bằng regex `(\d+)\s*(?:tu|từ|words)`.
Tổng Word Allocation phải nằm trong khoảng 1500-1800 từ.

## check_rotation
### Rotation Check
- Đọc `output/logs/production-log.md` → kiểm tra 2 bài gần nhất.
- **Emotional tone**: Không trùng 2 bài liên tiếp.
- **Structural technique**: Không trùng 2 bài liên tiếp.
- Cả 2 lớp đều phải rotate độc lập.

## check_nomenclature
Check 3: Kiểm tra các từ khóa nội bộ cấm xuất hiện (đảm bảo không bị dò rỉ thuật ngữ).
Nếu outline chứa chữ "Framework", trả về FAIL. Bắt buộc dùng "Solution" hoặc "Concept".

## check_atoms
Check 4: Đảm bảo tính minh bạch của nguồn nguyên liệu.
- Phần `Story` phải có dòng `Atoms: ...`
- Phần `Deep Dive` phải có dòng `Atoms: ...`
Nếu thiếu ở 1 trong 2 phần (hoặc cả hai) sẽ trả về FAIL.

## fail_validation
Tích lũy các lỗi từ Word count, Rotation, Nomenclature, Atoms (Exit Code = 1). Báo lỗi và ghi log `[Phase 4 Validation] Verdict: FAIL | Attempt: N/3`.

## pass_validation
Nếu qua được tất cả 4 bước kiểm tra (Exit Code = 0). Báo lỗi và ghi log `[Phase 4 Validation] Verdict: PASS`.

## check_retry
Script đếm số lần sửa lỗi (Attempt). Giới hạn sửa lỗi là 3 lần.

## retry_fix
Yêu cầu AI dựa vào kết quả script Validation để sửa lại file `04-outline.md` và chạy test lại.

## escalate
Nếu sửa lỗi quá 3 lần vẫn FAIL, kịch bản Validation sẽ báo lỗi và quy trình pipeline bị dừng lại, chờ User quyết định.
