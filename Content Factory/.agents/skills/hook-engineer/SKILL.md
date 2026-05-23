---
name: Hook Engineer
description: Skill Phase 3 — Thiết kế câu mở đầu (Hook) theo 15 công thức, chấm điểm và kiểm tra rotation.
---

# Hook Engineer Skill (Phase 3)

> EXECUTION_KEY: e58361c4

## Điều kiện Đầu vào
Từ Global Context, trích xuất 4 khối dữ liệu:
1. **`Research Brief`** — Sản phẩm Phase 2 (Insight Agent).
2. **`Insight Atom gốc`** — Lõi Logic của câu Hook (từ nguyên liệu DIKW).
3. **`Minified JSON Vivid Payload`** — Lớp áo Cảm giác phân rã (từ nguyên liệu DIKW).
4. **`resolved_jtbd`** — 3 biến JTBD đã resolve từ `00-blackboard.yaml`.

## Nguyên tắc Cốt lõi

### 1. Dynamic Synonym Synthesis (JTBD Phân Rã & Anti-AI)
Đọc `resolved_jtbd` từ `00-blackboard.yaml` (Đầu vào #4). KHÔNG dùng Static String Concatenation cho 3 tham số JTBD. Phải biến thiên từng biến số theo ngữ cảnh:
- `audience_Job_performer` → đại từ/danh từ linh hoạt (VD: 'bố mẹ', 'phụ huynh', 'chúng ta')
- `audience_main_job` → động từ/cụm tương đồng (VD: 'thiết lập nếp', 'tập tự ngủ')
- `audience_circumstance` → trạng từ/cụm trỏ bối cảnh (VD: 'giai đoạn này', 'đối với độ tuổi sơ sinh')

→ Nếu Hook chứa JTBD tĩnh nguyên khung → Reject (Anti-AI).

### 2. Dual-Input Extrapolation (Hooking Kép & Chống Văn mẫu)
Hook PHẢI kết hợp: **Bề chìm Logic** (`Insight Atom gốc`) + **Lớp vỏ Cảm giác** (`Minified JSON Vivid Payload`). 2 kịch bản:
- **Có Vivid Payload:** Trích Neo Cảm giác từ JSON → phóng tác tình tiết vệ tinh. CẤM phát minh ẩn dụ ngoại lai.
- **Không có Vivid Payload:** Dùng Logic gốc làm lưỡi câu; HOẶC tự phóng tác qua 5 giác quan (VD: 'mắt thâm quầng', 'tiếng khóc xé tai'). CẤM văn mẫu sáo rỗng (VD: 'con thuyền giữa bão').

## Thực thi

1. Đọc `.agents/skills/hook-engineer/references/hook-formulas.md` (15 công thức).
   > ⛔ **FATAL RULE:** PHẢI dùng tool đọc thành công. File Not Found → DỪNG + BÁO USER. Cấm hallucinate.

2. Chọn 1 formula phù hợp nhất với topic + research data.

3. **Rotation Check**: Đọc `output/logs/hook-history.md` → formula này đã dùng trong 2 bài gần nhất? Nếu trùng → đổi formula.

4. Viết 3 phiên bản Hook, **áp dụng triệt để 2 Nguyên tắc Cốt lõi** (JTBD Phân Rã + Hooking Kép).

5. Chấm điểm 3 phiên bản theo bảng dưới. Chọn bản điểm cao nhất.

   | # | Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
   |---|----------|--------|--------|--------|
   | 1 | Sting (Đau) | Không gây cảm xúc | Hơi nhói | Đau đến mức PHẢI đọc tiếp |
   | 2 | Curiosity Gap | Đoán được nội dung | Hơi tò mò | Không thể không click |
   | 3 | Specificity | Chung chung | Có 1 chi tiết cụ thể | Rất cụ thể (số, tên, tình huống) |
   | 4 | Brevity | > 20 từ | 16-20 từ | ≤ 15 từ (core hook) |
   | 5 | Vivid Extrapolation | Bịa ẩn dụ ngoại lai/sáo rỗng (VD: 'con thuyền giữa bão') | Logic khô khan, thiếu giác quan | Bám rễ Vivid gốc (KB1) hoặc phóng tác giác quan trực diện (KB2) |

   **Verdict:** ≥ 8 điểm → PASS. < 8 → viết lại.

6. Xuất **Hook** theo cấu trúc sau, kèm điểm số:
   - **Formula**: FXX
   - **Core Hook**: Câu hook chính (≤ 15 từ)
   - **Promise**: 1-2 câu hứa hẹn giá trị cho reader
   - **Authority Tease**: Nhá tên expert/data sẽ dùng trong bài

7. **[SCRIPTED VALIDATION]** Chạy:
   ```powershell
   powershell -ExecutionPolicy Bypass -File ".agents/skills/hook-engineer/scripts/validate-hook.ps1" -HookPath "[Đường dẫn file Hook vừa xuất]"
   ```

### Self-Check Gate
- Script bước 7 exit code = 0 (0 FAIL) + Scoring bước 5 ≥ 8 → **PASS** → Chuyển Phase 4.
- Nếu FAIL → quay lại bước 4, viết lại hook với formula khác. Tối đa 2 lần retry.
- FAIL 2 lần → dừng pipeline, escalate User.
- **Ghi log:** `[Phase 3 Self-Check] Verdict: PASS/REVISE | Attempt: N/2`
