<!--
Tên file: anti-ai-rules.md
Last update: 09/06/2026 15:30 (GMT+7)
Vai trò: Hướng dẫn phát hiện dấu vết AI và tối ưu văn phong tự nhiên.
Được sử dụng khi nào: Khi AI thực hiện viết bài nháp (draft).
Output là gì: Bài viết tự nhiên, không mắc các pattern bị cấm và các lỗi over-formatting.
Tóm tắt logic hoạt động: Cung cấp các mẫu cấu trúc câu mang dấu vết AI (Anti-AI patterns) kèm ví dụ sửa đổi; liệt kê các dấu hiệu AI nâng cao, các grep pattern phát hiện lặp từ/kí tự đặc biệt và danh sách checklist kiểm định.
-->

# Anti-AI Rules & Authenticity
**Module:** check/anti-ai

## 1. Anti-AI Patterns — các Pattern bị cấm

### ⛔ AUTO-FAIL (2 patterns — phát hiện 1 cái = fail ngay)
| # | Pattern | Ví dụ ❌ | Sửa ✅ |
|---|---------|--------|------|
| 1 | **Dash Connector** | "Sáng - gym - ăn healthy" | "Sáng dậy sớm rồi tập gym" |
| 2 | **Micro-Staccato** | "Đổi đời luôn. Một. Viết ra giấy." | Merge thành câu dài flowing tự nhiên |

### ⚠️ HIGH-RISK (5 patterns — cộng dồn ≥ 3 = fail)
| # | Pattern | Ví dụ ❌ | Sửa ✅ |
|---|---------|--------|------|
| 3 | **QA Pattern** | "Kết quả? Bất ngờ lắm." | Narrative bridge tự nhiên |
| 4 | **Numbered Lists** | "1. Làm A. 2. Làm B." | Viết thành prose tự nhiên |
| 5 | **Logic Symbols** | "X + Y = Thành công" | Diễn đạt bằng câu văn |
| 6 | **Generic Transitions** | "Đầu tiên... Tiếp theo... Cuối cùng..." | Transition tự nhiên, đa dạng |
| 7 | **Metaphor Stack** | 3+ ẩn dụ chồng chất trong 1 đoạn | Max 1 ẩn dụ/đoạn |

## 2. Các dấu hiệu nhận biết AI khác

### Over-formatting
```
❌ **Điểm 1**: Bla bla / **Điểm 2**: Bla bla / **Kết luận**: ...
✅ Điểm thứ nhất là... Tiếp theo, chúng ta thấy... Cuối cùng...
```

### Nhãn kiểu AI
```
❌ "Key insights:", "Note:", "Summary:"
✅ "Điểm nổi bật:", "Lưu ý:", "Tóm lại:"
```

### Dấu hiệu AI nâng cao
| Pattern | Mô tả | Cách phát hiện |
|---------|--------|----------------|
| **Paragraph uniformity** | Đoạn văn đều đặn 80-120 từ | Đếm số câu/đoạn — nếu quá đều → sai |
| **Transition overuse** | Lạm dụng "Tuy nhiên", "Bên cạnh đó" | >3 lần/bài cùng 1 từ nối → sai |
| **Cautious hedging** | Quá nhiều "có thể", "thường" | Nếu mọi claim đều hedge → thiếu cam kết |
| **Balanced structure** | Mỗi point phát triển đều đặn | Real writing: có ý nói nhiều, ý lướt qua |
| **Professional smoothness** | Quá mượt mà, thiếu gồ ghề | Real writing: có chỗ rough, quirky |
| **Artificial chaos** | Cố viết "tự nhiên" nhưng random có kiểm soát | Grammar vẫn hoàn hảo dù văn "rối" |

## Grep Patterns (Tổng hợp)
| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Transition overuse | `Tuy nhiên,` | >3 lần/bài → nghi AI |
| Transition overuse | `Bên cạnh đó,` | >3 lần/bài → nghi AI |
| Transition overuse | `Ngoài ra,` | >3 lần/bài → nghi AI |
| Transition overuse | `Hơn nữa,` | >3 lần/bài → nghi AI |
| AI labels | `Key ` / `Note:` / `Summary:` | Cấm — dùng tiếng Việt |
| Over-formatting | `**` trong content storytelling | Nghi over-formatting |
| Exclamation spam | `!` | >2 lần liên tiếp → nghi AI |
| Emoji | `🚀` / `✨` / `💡` (ngoài formula box) | Nghi AI-generated |

## Checklist
- [ ] Không vi phạm Anti-AI Patterns
- [ ] Không có nhãn AI (Key, Note, Summary)
- [ ] Không over-formatting (bold labels trong storytelling)
- [ ] Đoạn văn biến thiên (không đều nhau)
- [ ] Từ nối đa dạng (không lặp >3 lần)
- [ ] Không quá mượt mà — có chỗ rough tự nhiên

### 3. Hạn chế cấu trúc rập khuôn của AI
Tránh lạm dụng các câu mở đầu hoặc từ nối sáo rỗng, mang tính chất khuôn mẫu thường thấy ở văn bản AI sinh ra (ví dụ: các câu rủ rê người đọc cùng khám phá một vấn đề, các câu hỏi tu từ chung chung ở đầu bài, hay các từ đệm phô trương sự thật hiển nhiên). Hãy vào đề trực tiếp hoặc sử dụng phong cách diễn đạt linh hoạt của Persona.

> FILE_KEY:
