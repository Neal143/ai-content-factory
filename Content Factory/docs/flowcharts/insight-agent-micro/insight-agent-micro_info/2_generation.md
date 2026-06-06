## read_atoms
> ⛔ **FATAL RULE:** Với MỌI atom từ Vault trong Gói DIKW, BẮT BUỘC dùng `view_file`
> với **Atom path** (cột 1 bảng Gói DIKW) để đọc file vật lý. Cấm tóm tắt từ memory.

## gen_brief
### Bước 3: Xuất Research Brief

Output file `02-research-brief.md` theo đúng format:

#### Evidence List (Studies & Numbers)

Với mỗi data-point atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]**
[Paste TOÀN BỘ body text của atom, NGUYÊN VĂN]

Không có atom từ vault → `[Atom: none]` + ghi fact với nguồn rõ ràng.

**Số liệu cụ thể (≥5):**
- [số + đơn vị]: [mô tả ngắn] `[Atom: [path — PHẢI TRÙNG với path trong Evidence List]]`
- [số + đơn vị]: [mô tả ngắn] `[Atom: none]`  ← nếu từ nguồn ngoài vault

#### Expert Quotes

Với mỗi quote atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]**
[Paste TOÀN BỘ body text của atom, NGUYÊN VĂN]
— [Tên tác giả], [Credential ngắn]

Không có atom từ vault → trích dẫn từ sách/nguồn đã xuất bản, ghi rõ nguồn.

#### Story List

Với mỗi story atom trong Gói DIKW:
**[Atom: [Atom path từ Gói DIKW]]** | source: [vault/famous/book]
**[Situation]** [Nội dung <situation> từ atom, nguyên văn]
**[Problem]** [Nội dung <problem> từ atom, nguyên văn]
**[Turning Point]** [Nội dung <turning_point> từ atom, nguyên văn]
**[Outcome]** [Nội dung <outcome> từ atom, nguyên văn]
**[Lesson]** [Nội dung <lesson> từ atom, nguyên văn]

Không có atom từ vault → dùng famous world/published book, ghi rõ nguồn, `[Atom: none]`.

#### SAS & KCS Status
- SAS status: PASS / FAIL
- KCS status: PASS / FAIL

#### Knowledge Credibility System (KCS)
[Framework + Origin/Achievement/Scale đủ theo chuẩn KCS]
