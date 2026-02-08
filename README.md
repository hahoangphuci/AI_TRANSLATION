# AI Translation System - Giữ Định Dạng Gốc

Hệ thống dịch văn bản và tài liệu sử dụng trí tuệ nhân tạo tiên tiến, giữ nguyên 100% định dạng gốc.

## 🎯 Tính Năng Chính

### ✨ Dịch Văn Bản

- Dịch tức thời với 100+ ngôn ngữ
- Tự động phát hiện ngôn ngữ nguồn
- Đếm ký tự (giới hạn 5000)
- Hoán đổi ngôn ngữ nhanh
- Sao chép/tải xuống kết quả

### 📄 Dịch Tài Liệu - Giữ Định Dạng

- Hỗ trợ: PDF, Word, Excel, PowerPoint, TXT
- Kéo thả file hoặc chọn file
- Giữ nguyên 100% định dạng gốc
- Upload nhiều file cùng lúc
- Giới hạn 50MB/file

### 📊 Lịch Sử Dịch Thuật

- Lưu tất cả bản dịch
- Xem lại bản dịch cũ
- Quản lý và xóa lịch sử
- Hiển thị thời gian thực

### 🖼️ Dịch Ảnh (OCR)

- Upload hoặc dán ảnh (Ctrl+V) để OCR lấy chữ
- Dịch kết quả OCR như văn bản bình thường
- Khuyến nghị cấu hình `OCR_LANGS_DEFAULT=eng+vie` cho ảnh tiếng Việt

### 🔐 Bảo Mật & Xác Thực

- Đăng nhập Google OAuth
- JWT Authentication
- Mã hóa dữ liệu
- Bảo mật tuyệt đối

## 🛠️ Công Nghệ Sử Dụng

- **Backend**: Python 3.10, Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: MySQL
- **Authentication**: JWT, Google OAuth 2.0
- **AI Services**: OpenAI GPT, DeepL API
- **Container**: Docker & Docker Compose
- **Payment**: SePay.vn integration

## 🚀 Cài Đặt & Chạy

### Yêu cầu hệ thống

- Python 3.10+
- Node.js (cho development)
- Docker & Docker Compose
- MySQL

### 1. Clone repository

```bash
git clone https://github.com/duyvo26/ai-translation-system.git
cd ai-translation-system
```

### 2. Cấu hình môi trường

```bash
# Backend
cd backend
cp .env.example .env
# Chỉnh sửa .env với API keys của bạn

# Frontend
cd ../frontend
cp .env.example .env
```

### 3. Chạy với Docker (Khuyến nghị)

```bash
docker-compose up --build
```

### 4. Hoặc chạy local

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python run.py

# Frontend (mở terminal mới)
cd frontend
python -m http.server 8000  # Hoặc dùng Live Server extension
```

### 5. Truy cập

- Frontend: http://localhost:80 hoặc http://localhost:8000
- Backend API: http://localhost:5000
- Database: localhost:3306

## 🧩 Cấu hình OCR (Tesseract)

OCR dùng `pytesseract` nhưng máy bạn cần cài thêm **Tesseract OCR** (binary) thì mới chạy được.

### Windows

- Cài Tesseract OCR
- Sau khi cài, làm 1 trong 2 cách:
  - Thêm Tesseract vào `PATH` (mở terminal mới sau khi thêm PATH)
  - Hoặc set biến trong `backend/.env`:

```env
# Ví dụ Windows
TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
OCR_LANGS_DEFAULT=eng+vie
```

Nếu OCR báo thiếu ngôn ngữ `vie`, hãy đảm bảo language data tiếng Việt được cài kèm trong Tesseract.

## 🔧 Cấu Hình API Keys

Chỉnh sửa file `backend/.env`:

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=mysql://translator:translator123@localhost/translation_db
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OPENAI_API_KEY=your-openai-api-key
DEEPL_API_KEY=your-deepl-api-key
SEPAY_API_KEY=your-sepay-api-key
SEPAY_SECRET=your-sepay-secret
```

## 📱 Giao Diện

### 🎨 Thiết Kế

- **Gradient Background**: Màu sắc bắt mắt với gradient động
- **Glassmorphism**: Hiệu ứng kính mờ hiện đại
- **Responsive**: Hoàn hảo trên mọi thiết bị
- **Animations**: Hiệu ứng mượt mà, tương tác
- **Font Awesome**: Icons đẹp và chuyên nghiệp

### 📱 Responsive Design

- Mobile-first approach
- Tablet và desktop optimization
- Touch-friendly interactions

## 🔒 Bảo Mật

- JWT tokens cho API authentication
- Google OAuth 2.0 cho user login
- Password hashing (nếu cần)
- CORS protection
- Input validation
- SQL injection prevention

## 💰 Tích Hợp Thanh Toán

- **SePay.vn**: Cổng thanh toán Việt Nam
- Hỗ trợ QR code payment
- Webhook notifications
- Transaction logging

## 🚀 Triển Khai Production

### Với AAPanel

1. Upload code lên server
2. Cấu hình domain
3. Setup SSL certificate
4. Configure reverse proxy
5. Setup MySQL database
6. Run Docker containers

### Environment Variables Production

```env
FLASK_ENV=production
DATABASE_URL=mysql://user:password@host:port/db
FRONTEND_URL=https://yourdomain.com
```

## 📊 API Documentation

### Authentication

```
POST /api/auth/google
POST /api/auth/profile
```

### Translation

```
POST /api/translation/text
POST /api/translation/document
GET  /api/translation/history
```

### Payment

```
POST /api/payment/create
GET  /api/payment/status/{id}
```

### History

```
GET  /api/history
DEL  /api/history/{id}
```

## 🤝 Đóng Góp

1. Fork project
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Liên Hệ

**Duy Vo** - duyvo26@github.com

Project Link: [https://github.com/duyvo26/ai-translation-system](https://github.com/duyvo26/ai-translation-system)

---

⭐ **Nếu project này hữu ích, hãy cho chúng tôi một ngôi sao!**
