# Huong dan su dung Inbox

Day la noi ban ghi chep nhanh y tuong, kien thuc, trich dan... vao **dung file** tuong ung.
He thong se tu dong xu ly va chuyen hoa chung thanh Atoms trong `vault/01-Atomic/`.

## Cach ghi

Mo file tuong ung voi loai noi dung ban muon ghi, viet noi dung vao:

| File | Ghi gi vao day? | Vi du |
|------|-----------------|-------|
| `Insights.md` | Goc nhin sau, nhan xet phan bien | "Nguoi ta nghi X nhung thuc ra Y vi..." |
| `Solutions.md` | Mo hinh, cong thuc, phuong phap | "3 buoc de vuot qua bat an: 1)... 2)... 3)..." |
| `Concepts.md` | Dinh nghia, khai niem | "Deliberate Practice la viec luyen tap co chu dich..." |
| `Quotes.md` | Trich dan tu sach/chuyen gia | "Charlie Munger: Invert, always invert" |
| `Data-Points.md` | So lieu, thong ke | "Theo Harvard 2019, 73% stress den tu..." |
| `Stories.md` | Cau chuyen ca nhan co buoc ngoat | "Nam 2019 toi mat sach tien, sau do..." |
| `Uncategorized.md` | Khong biet phan loai gi | Ghi dai, he thong tu phan loai |

## Quy tac ghi
- Moi y tuong cach nhau boi 1 dong trong hoac dau `---`.
- Khong can viet YAML frontmatter. Chi can viet noi dung thuan.
- Ghi xong, chay lenh `/process-inbox` de he thong xu ly.

## He thong xu ly nhu the nao?
1. **Doc** noi dung tu cac file tren.
2. **Tach** thanh cac khoi doc lap.
3. **Chuyen** cho skill xu ly (inbox-processor hoac story-architect).
4. **Tao Atoms** luu vao `vault/01-Atomic/[Type]/` voi ten file `USER_[slug].md`.
5. **Luu log** noi dung goc vao `Processed/[Ten_File].md` (kem thoi gian va backlink).
6. **Xoa trang** noi dung trong file goc de san sang cho lan ghi tiep.

> **Luu y:** Cac file trong thu muc nay **khong bao gio bi xoa**. Chi noi dung ben trong bi lam rong sau khi xu ly.
