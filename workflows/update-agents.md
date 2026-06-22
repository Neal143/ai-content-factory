---
description: 🔄 Cap nhat he thong .agents len phien ban moi nhat tu GitHub
---

# WORKFLOW: /update-agents

Ban la **Antigravity Update Manager**. Nhiem vu: Tai phien ban moi nhat cua thu muc `.agents` tu GitHub ve may cua User, thay the hoan toan thu muc cu de dam bao dong bo tuyet doi voi ban goc.

> **CANH BAO:** Workflow nay se XOA TOAN BO noi dung thu muc `.agents` hien tai va THAY THE bang phien ban moi nhat tu GitHub. Bat ky file nao User tu y sua ben trong `.agents/` se bi mat. Du lieu ca nhan (`vault/`, `personas/`) KHONG bi anh huong.

## Giai doan 1: Xac nhan truoc khi cap nhat

1. Thong bao cho User: "Workflow nay se thay the toan bo thu muc `.agents` bang phien ban moi nhat tu GitHub. Du lieu `vault/` va `personas/` cua ban se KHONG bi anh huong. Ban co muon tiep tuc khong?"
2. Dung va doi cau tra loi tu User.
3. Neu User tu choi: Ket thuc ngay lap tuc.

## Giai doan 2: Xac dinh duong dan

1. Xac dinh duong dan tuyet doi cua thu muc `.agents` hien tai. Thu muc nay chinh la thu muc CHA cua file workflow ban dang doc.
   - Vi du: Neu ban dang doc file tai `D:\MyFactory\.agents\workflows\update-agents.md` thi thu muc `.agents` la `D:\MyFactory\.agents`.
2. Xac dinh thu muc CHA cua `.agents` (goi la `FACTORY_ROOT`).
   - Vi du: `D:\MyFactory`
3. Luu ca 2 duong dan nay de su dung o cac buoc sau.

## Giai doan 3: Tai ban moi nhat

1. Chay lenh tai repo ve thu muc tam:
   ```
   git clone --depth 1 https://github.com/Neal143/ai-content-factory.git "[FACTORY_ROOT]/.agents_update_temp"
   ```
2. Neu lenh clone that bai (mat mang, sai URL, v.v.): Bao loi cho User va DUNG LAI. KHONG duoc tiep tuc sang Giai doan 4.

## Giai doan 4: Thay the

1. **Sao luu (An toan):** Doi ten thu muc `.agents` hien tai thanh `.agents_backup`:
   ```powershell
   Rename-Item -Path "[FACTORY_ROOT]\.agents" -NewName ".agents_backup"
   ```
2. **Chuyen doi:** Doi ten thu muc vua tai ve thanh `.agents` chinh thuc:
   ```powershell
   Rename-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -NewName ".agents"
   ```
3. **Don rac Git:** Xoa thu muc `.git` ben trong `.agents` moi (vi no la san pham cua lenh clone, User khong can):
   ```powershell
   Remove-Item -Path "[FACTORY_ROOT]\.agents\.git" -Recurse -Force
   ```

## Giai doan 5: Kiem tra va Don dep

1. Kiem tra nhanh thu muc `.agents` moi co ton tai cac thu muc con bat buoc khong: `workflows/`, `skills/`, `agents/`, `scripts/`.
2. **Neu THANH CONG (du 4 thu muc con):**
   - Xoa thu muc sao luu: `Remove-Item -Path "[FACTORY_ROOT]\.agents_backup" -Recurse -Force`
   - Chay migration tu dong:
     ```powershell
     powershell -ExecutionPolicy Bypass -File "[FACTORY_ROOT]\.agents\scripts\run-migrations.ps1" -FactoryRoot "[FACTORY_ROOT]"
     ```
   - Neu migration bao loi (exit code khac 0): Thong bao cho User "⚠️ Cap nhat .agents thanh cong nhung co migration that bai. Hay bao lai cho tac gia he thong."
   - Bao cao: "✅ Da cap nhat `.agents` thanh cong len phien ban moi nhat!"
3. **Neu THAT BAI (thieu thu muc con):**
   - Khoi phuc ban sao luu:
     ```powershell
     Remove-Item -Path "[FACTORY_ROOT]\.agents" -Recurse -Force
     Rename-Item -Path "[FACTORY_ROOT]\.agents_backup" -NewName ".agents"
     ```
   - Bao loi: "❌ Cap nhat that bai. He thong da tu dong khoi phuc ve phien ban cu. Khong co du lieu nao bi mat."
   - Don rac: `Remove-Item -Path "[FACTORY_ROOT]\.agents_update_temp" -Recurse -Force -ErrorAction SilentlyContinue`
