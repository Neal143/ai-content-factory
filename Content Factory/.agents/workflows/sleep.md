---
description: Đưa máy tính vào trạng thái Sleep ngay lập tức
trigger: match
---

# Workflow: Sleep Computer

> **Tên file**: sleep.md
> **Last update**: 16/07/2026 00:33 (GMT+7)
> **Vai trò**: Tự động hóa quá trình đưa máy tính vào trạng thái Sleep thông qua lệnh PowerShell an toàn.
> **Sử dụng khi**: Khi người dùng gọi lệnh `/sleep` hoặc có nhu cầu đưa máy vào giấc ngủ ngay lập tức.
> **Output**: Kích hoạt thành công chế độ Sleep của phần cứng, đảm bảo an toàn cho các tác vụ khác.
> **Tóm tắt logic hoạt động**: Kích hoạt `run_command` gọi hàm `.NET Framework` (`[System.Windows.Forms.Application]::SetSuspendState`), bỏ qua Hibernate, và sau khi máy tính thức dậy, xuất thông báo hoàn thành.

**Mục đích:** Kích hoạt chế độ Sleep cho máy tính của User ngay lập tức thông qua lệnh PowerShell an toàn (tránh bị lỗi nhầm sang Hibernate hoặc bị chặn).

## 1. Context
User muốn cho máy tính ngủ (Sleep) để nghỉ ngơi hoặc treo máy chờ một tác vụ kết thúc.

## 2. Lệnh thực thi (Core execution)
Sử dụng tool `run_command` chạy đoạn script PowerShell dưới đây. Lệnh này gọi trực tiếp API hệ thống `SetSuspendState` để đảm bảo máy tính rơi vào trạng thái ngủ sâu (Suspend):

```powershell
Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)
```

## 3. Các bước thực hiện (Steps)
1. **Thông báo:** Báo cho User biết máy tính chuẩn bị đi ngủ.
2. **Kích hoạt lệnh:** Gọi `run_command` với script PowerShell ở phần (2). Thời gian chờ (WaitMsBeforeAsync) có thể thiết lập ở mức 500ms để đảm bảo lệnh được fire thành công vào background.
3. **Chào đón (sau khi Wake-up):** Sau khi máy tính ngủ và được User đánh thức dậy (hoàn thành background task), Agent chủ động gửi một lời chào báo cáo lệnh Sleep đã hoàn tất thành công.
