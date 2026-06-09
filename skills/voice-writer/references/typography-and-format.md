<!--
Tên file: typography-and-format.md
Last update: 09/06/2026 15:30 (GMT+7)
Vai trò: Hướng dẫn viết hoa, dấu câu và định dạng văn xuôi.
Được sử dụng khi nào: Khi AI thực hiện viết bài nháp (draft).
Output là gì: Bài viết đúng chuẩn chính tả/typography tiếng Việt.
Tóm tắt logic hoạt động: Quy chuẩn viết hoa tiếng Việt (không dùng Title Case); quy tắc dùng dấu câu sát từ trước cách từ sau, cấm em-dash và Oxford comma; cấm bullet point trong văn xuôi storytelling; cung cấp grep pattern quét tự động và checklist.
-->

# Typography & Format
**Module:** check/typography

## 1. Viết hoa & Tiêu đề
**Viết hoa — Không Title Case:**
Tiếng Việt CHỈ viết hoa chữ cái đầu tiên, KHÔNG viết hoa mỗi từ.
```
✅ Chủ tịch nước          ❌ Chủ Tịch Nước
✅ Bộ trưởng Bộ Giáo dục  ❌ Bộ Trưởng Bộ Giáo Dục
```
**Viết hoa khi:**
- Tên riêng người: Nguyễn Văn An
- Địa danh: Hà Nội, sông Hồng (❌ Sông Hồng)
- Chức danh kèm tổ chức: Bộ trưởng Bộ Giáo dục
- Sau dấu hai chấm trích dẫn: Ông ta nói: "Đây là..."

**Tiêu đề:**
- **H1:** `# TIÊU ĐỀ IN HOA` hoặc viết hoa chữ đầu.
- **H2+ — LUÔN:** Chỉ viết hoa chữ cái đầu tiên.
- **Không dùng dấu hai chấm trong tiêu đề:** ❌ `Vibe coding: lỗi không phải ở AI` ✅ `Vibe coding - Lỗi không phải ở AI`
- **Cấm headers trong storytelling/blog:** Viết liền mạch, không chia `## Giới thiệu` hay `## Kết luận`.

## 2. Dấu Câu — Khác tiếng Anh
**Dấu câu [. , ! ? : ; ...] LUÔN:** Sát từ trước, cách từ sau.
**Ngoặc đơn ():** Cách ngoài, sát trong.
**Gạch ngang (-):** Cách hai bên. Ngoại lệ compound noun: `người-mà-ai-cũng-biết`.

**Dấu hai chấm (:)**
Hạn chế tối đa. Chỉ dùng cho giờ (14:30), trích dẫn trực tiếp, liệt kê. Các trường hợp khác thay bằng từ nối (là, rằng, thì, mà, nên).

**Oxford comma `, và`**
- **Cấm.** (❌ `sạch hơn, và đúng hơn` ✅ `sạch hơn và đúng hơn`).

**Dấu phẩy giữa tính từ bổ nghĩa**
- Khi cùng bổ nghĩa cho một thực thể, không dùng dấu phẩy (❌ `Sự truth hiển nhiên, không thể phủ nhận.` ✅ `Sự truth hiển nhiên không thể phủ nhận.`)

**Em-dash `—`**
- **Cấm.** Thay bằng gạch ngang ` - ` (cách hai bên), từ nối (tức là, nghĩa là), hoặc ngoặc đơn. 
- Max 3 dấu ba chấm (...) và 3 dấu chấm than (!) mỗi bài.

## 3. Văn Xuôi — Prose Format
**Cấm bullet points trong thân văn:**
- Không dùng list bullet để giải thích. Chỉ dùng cho: docs, reports, checklists.

**Inline Enumeration:**
- 3-4 items: "Một là... Hai là..."
- ≥ 5 items: "(1), (2), (3)"

**Đa dạng ký hiệu nối câu:** Luân phiên dấu phẩy, ngoặc, ngắt câu, từ nối.

## Grep Patterns (Tổng hợp)
| Pattern | Search | Quy tắc |
|---------|--------|---------|
| Title Case heading | `^##? [A-ZÀÁẢÃẠ].*[A-ZÀÁẢÃẠ]` | Nghi Title Case |
| Colon in heading | `^#.*: ` | Cấm dấu hai chấm |
| Em-dash | `—` | Cấm. Thay ` - ` |
| Oxford comma | `, và ` | Cấm |
| Colon sau mệnh | `: ` | Thay từ nối |
| Space trước dấu | ` ,` / ` .` / ` !` / ` ?` | Cấm |
| Bullet in prose | `^- ` hoặc `^\* ` | Cấm trong giải thích |
| Headers in blog | `^## ` | Cấm trong storytelling |

## Checklist
- [ ] Viết hoa chỉ chữ đầu, không Title Case
- [ ] Tiêu đề không dấu hai chấm
- [ ] Dấu câu sát trước, cách sau
- [ ] Ngoặc đơn cách ngoài, sát trong
- [ ] Gạch ngang cách hai bên, không có em-dash `—`
- [ ] Không có Oxford comma `, và`
- [ ] Tính từ bổ nghĩa liên tiếp không dùng dấu phẩy
- [ ] Không dùng bullet trong thân văn giải thích

> FILE_KEY: 4b8e6ad2
