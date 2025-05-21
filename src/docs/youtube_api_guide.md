# Hướng dẫn sử dụng YouTube Data API

Tài liệu này cung cấp hướng dẫn cơ bản để kết nối và thu thập dữ liệu từ YouTube thông qua YouTube Data API v3.

---

## 1. Đăng ký và lấy API Key

1. Truy cập: [https://console.developers.google.com](https://console.developers.google.com)
2. Tạo một project mới.
3. Kích hoạt API: `YouTube Data API v3`.
4. Tạo API Key tại mục **Credentials**.

---

## 2. Giới hạn quota

Mỗi API Key có **quota 10.000 đơn vị/ngày**. Một số ví dụ:

| Endpoint                             | Mô tả                        | Quota |
|-------------------------------------|------------------------------|-------|
| `videos.list`                       | Lấy thông tin video          | 1     |
| `commentThreads.list`               | Lấy bình luận của video      | 1     |
| `search.list`                       | Tìm kiếm video               | 100   |

---

## 3. Endpoint phổ biến

### 🔹 Lấy danh sách bình luận (`commentThreads.list`)

**URL endpoint:**

