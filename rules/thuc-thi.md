---
trigger: always_on
---

## ⛔ QUY TẮC THỰC THI BẤT KHẢ XÂM PHẠM

Mỗi khi gặp dòng `view_file [path]`:
1. BẮT BUỘC gọi tool `view_file` với đúng path đó.
2. Nếu tool báo File Not Found → dừng pipeline ngay, báo User.
3. Nếu file đọc thành công → tuân theo TỪNG BƯỚC trong file đó, bao gồm 
   mọi gate cứng (chờ User phản hồi, validation script, abort condition).
4. TUYỆT ĐỐI CẤM tự suy luận nội dung thay vì đọc file thực.
5. Tuyệt đối cấm tự viết script để sinh dữ liệu đầu vào cho hệ thống. Bắt buộc phải sử dụng script đã được thiết kế sẵn. Mọi hành động bypass sẽ bị đánh giá là làm sập hệ thống.