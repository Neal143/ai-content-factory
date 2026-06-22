# Migrations

Thu muc nay chua cac script cap nhat cau truc `vault/` va `personas/` khi he thong nang cap phien ban.

## Quy tac dat ten
- Format: `NNN_mo-ta-ngan.ps1` (VD: `001_add-dlq-folder.ps1`)
- So thu tu tang dan, khong duoc trung, khong duoc nhay so

## Quy tac viet script
- Nhan tham so `$FactoryRoot` (duong dan goc factory)
- BAT BUOC idempotent (kiem tra truoc khi tao/doi ten/di chuyen)
- Tra exit code 0 = thanh cong, khac 0 = that bai
- Dung tieng Anh hoac tieng Viet khong dau trong comment
- Khi them folder moi, dong thoi cap nhat workflow onboarding cho user moi

## Vi du tao folder moi
```powershell
param([string]$FactoryRoot)
$target = Join-Path $FactoryRoot "vault\05-NewSection"
if (-not (Test-Path $target)) { New-Item -Path $target -ItemType Directory -Force | Out-Null }
exit 0
```

## Vi du doi ten folder
```powershell
param([string]$FactoryRoot)
$old = Join-Path $FactoryRoot "vault\03-Content"
$new = Join-Path $FactoryRoot "vault\03-Published"
if ((Test-Path $old) -and (-not (Test-Path $new))) { Rename-Item -Path $old -NewName "03-Published" }
exit 0
```
