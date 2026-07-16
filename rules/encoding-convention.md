---
trigger: always_on
---

## Encoding Convention cho Python Scripts

1. **Mọi file `.md` trong Vault:** Đọc bằng `encoding='utf-8-sig'`, Ghi bằng `encoding='utf-8'`.
2. **File JSON/YAML nội bộ** (manifest, batch, log): Dùng `encoding='utf-8'` cho cả đọc và ghi.
3. **Mọi `print()` trong script Python:** BẮT BUỘC dùng tiếng Việt không dấu. Cấm tiếng Việt có dấu.
4. **Khi frontmatter parse thất bại** trên file `.md` tồn tại: BẮT BUỘC in log `[WARN]` hoặc `[ERR]`. Cấm `return False/continue` im lặng.
