# XAMPP MySQL Setup Guide

## 1️⃣ Chuẩn bị XAMPP

### Tải và cài đặt

- Tải XAMPP từ: https://www.apachefriends.org
- Cài đặt vào ổ C (hoặc ổ khác tùy ý)
- Đảm bảo chọn **MySQL** khi cài đặt

### Khởi động MySQL

1. Mở **XAMPP Control Panel**
2. Tìm dòng **MySQL**
3. Nhấp nút **Start** (button sẽ chuyển thành Stop khi chạy)
4. Port mặc định: **3306**

> **Lưu ý:** MySQL không có password mặc định (user: `root`, password: `` trống)

---

## 2️⃣ Tạo Database

### Cách 1: Qua phpMyAdmin (GUI)

1. Mở browser: http://localhost/phpmyadmin
2. Đăng nhập (username: `root`, password: trống)
3. Tab **Databases**
4. Nhập tên: `ai_translation`
5. Charset: `utf8mb4_unicode_ci`
6. Nhấn **Create**

### Cách 2: Qua Command Line (CLI)

```bash
mysql -u root
```

Trong MySQL CLI:

```sql
CREATE DATABASE ai_translation DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

---

## 3️⃣ Cập nhật Cấu hình Ứng dụng

### File: `backend/.env`

```dotenv
DATABASE_URL=mysql+pymysql://root:@localhost:3306/ai_translation
```

### File: `backend/config.py`

```python
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/ai_translation')
```

### File: `backend/requirements.txt`

```
PyMySQL==1.1.0
```

---

## 4️⃣ Cài đặt Dependencies

```bash
cd backend
pip install -r requirements.txt
pip install PyMySQL==1.1.0 --force-reinstall
```

---

## 5️⃣ Tạo Database & Bảng

### Kiểm tra kết nối MySQL (tùy chọn)

```bash
cd backend
python connect_db.py --check
```

### Tạo database và bảng

```bash
cd backend
python connect_db.py
```

Script sẽ:

- ✅ Kiểm tra/tạo database `ai_translation` nếu chưa có
- ✅ Tạo các bảng (`user`, `translation`, `payment`) nếu chưa tồn tại

---

## 6️⃣ Khởi động Server

```bash
python run.py
```

Server sẽ chạy tại: **http://127.0.0.1:5000**

---

## 🔧 Troubleshooting

### MySQL không chạy

```
❌ MySQL connection failed
```

**Giải pháp:**

1. Kiểm tra XAMPP Control Panel → MySQL status
2. Nếu không chạy, nhấn **Start**
3. Kiểm tra port: `netstat -an | findstr 3306`

### Access Denied

```
❌ Access denied for user 'root'@'localhost'
```

**Giải pháp:**

- Mặc định XAMPP MySQL không có password
- Kiểm tra .env: `DATABASE_URL=mysql+pymysql://root:@localhost:3306/ai_translation`
- Dấu `:` sau `root` rồi để trống (không có mật khẩu)

### Can't connect to MySQL server

```
❌ Can't connect to MySQL server on 'localhost'
```

**Giải pháp:**

1. XAMPP MySQL chưa chạy → nhấn Start
2. Port khác → thay đổi trong .env
3. Firewall block → tạm tắt hoặc whitelist port 3306

### Database not found

```
❌ Unknown database 'ai_translation'
```

**Giải pháp:**

```bash
# Chạy script setup để tự động tạo database và bảng
cd backend
python connect_db.py
```

---

## ✅ Xác nhận Hoàn thành

### Via phpMyAdmin

1. Mở: http://localhost/phpmyadmin
2. Left sidebar: chọn **ai_translation**
3. Nên thấy 3 bảng: `user`, `translation`, `payment`

### Via MySQL CLI

```bash
mysql -u root ai_translation
```

```sql
SHOW TABLES;
DESCRIBE user;
SELECT COUNT(*) FROM user;
EXIT;
```

---

## 📝 Tài liệu Thêm

- XAMPP Official: https://www.apachefriends.org/docs
- PyMySQL Docs: https://pymysql.readthedocs.io
- SQLAlchemy MySQL: https://docs.sqlalchemy.org/en/20/dialects/mysql.html
