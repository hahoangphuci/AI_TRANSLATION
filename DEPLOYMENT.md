# 🚀 Hướng Dẫn Triển Khai Production

## 📋 Yêu Cầu Server

- **OS**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB+)
- **CPU**: 1 core (khuyến nghị 2 cores+)
- **Disk**: 20GB+ (cho database và uploads)
- **Domain**: Đã cấu hình DNS trỏ về server IP

## 🛠️ Cài Đặt AAPanel

### 1. Cài đặt AAPanel

```bash
# Ubuntu/Debian
curl -sSL https://www.aapanel.com/script/install-ubuntu_6.0_en.sh | bash

# CentOS
curl -sSL https://www.aapanel.com/script/install-6.0_en.sh | bash
```

### 2. Truy cập AAPanel

- URL: `http://your-server-ip:8888`
- Username/Password: Hiển thị sau khi cài đặt

### 3. Cấu hình cơ bản

1. **Cập nhật panel**: Software Store > Updates
2. **Cài đặt Nginx**: Software Store > Web Server > Nginx
3. **Cài đặt MySQL**: Software Store > Database > MySQL 8.0
4. **Cài đặt PHP**: Software Store > Programming > PHP 8.1
5. **Cài đặt Docker**: Software Store > Tools > Docker Manager

## 🌐 Cấu Hình Domain & SSL

### 1. Thêm Website

1. Website > Add Site
2. Domain: `yourdomain.com`
3. Root: `/www/wwwroot/yourdomain.com`
4. PHP: Không chọn (sẽ dùng Docker)

### 2. Cấu hình SSL

1. Website > yourdomain.com > SSL
2. Let's Encrypt > Apply
3. Domain: `yourdomain.com` và `www.yourdomain.com`

### 3. Cấu hình Nginx

Website > yourdomain.com > Config > Nginx Config:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /www/server/panel/vhost/cert/yourdomain.com/fullchain.pem;
    ssl_certificate_key /www/server/panel/vhost/cert/yourdomain.com/privkey.pem;

    # Frontend (Static Files)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Downloads
    location /downloads/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

## 🐳 Triển Khai với Docker

### 1. Upload Code

```bash
# Upload project files to server
scp -r AI_TRANSLATION_PRO_TIEN_PHONG_TT_VL_2026/ root@your-server-ip:/www/wwwroot/
```

### 2. Cấu hình Environment

```bash
cd /www/wwwroot/AI_TRANSLATION_PRO_TIEN_PHONG_TT_VL_2026

# Backend .env
cp backend/.env.example backend/.env
nano backend/.env  # Chỉnh sửa với production values

# Frontend .env
cp frontend/.env.example frontend/.env
nano frontend/.env
```

### 3. Build và Run Docker Containers

```bash
# Build images
docker-compose build

# Run containers
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Cấu hình Firewall

Trong AAPanel > Security > Firewall:

- Cho phép ports: 80, 443, 5000, 3306 (internal only)
- Block tất cả ports khác

## 🗄️ Cấu Hình Database

### 1. Tạo Database

AAPanel > Database > MySQL > Add Database:

- Database Name: `translation_db`
- Username: `translator`
- Password: `secure_password_123`

### 2. Import Schema

```bash
mysql -u translator -p translation_db < backend/schema.sql
```

### 3. Backup Database

AAPanel > Database > MySQL > Backup

## 🔧 Cấu Hình Production

### Environment Variables (Production)

```env
# backend/.env
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-production-key
DATABASE_URL=mysql://translator:secure_password_123@localhost:3306/translation_db
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-client-secret
OPENAI_API_KEY=your-production-openai-key
DEEPL_API_KEY=your-production-deepl-key
SEPAY_API_KEY=your-production-sepay-key
SEPAY_SECRET=your-production-sepay-secret
FRONTEND_URL=https://yourdomain.com

# frontend/.env
REACT_APP_GOOGLE_CLIENT_ID=your-production-google-client-id
REACT_APP_API_BASE_URL=https://yourdomain.com/api
```

### SSL Configuration

```bash
# Force HTTPS redirect
# Thêm vào nginx config:
if ($scheme != "https") {
    return 301 https://$server_name$request_uri;
}
```

## 📊 Monitoring & Logs

### 1. AAPanel Monitoring

- Dashboard > Server Status
- Website > yourdomain.com > Logs

### 2. Docker Logs

```bash
# View container logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. Application Logs

```bash
# Backend logs
docker exec -it ai-translation-backend tail -f /app/app.log

# Nginx access logs
tail -f /www/wwwlogs/yourdomain.com.log
```

## 🔄 Backup & Recovery

### 1. Automated Backup

AAPanel > Cron > Add Task:

```bash
# Daily backup at 2 AM
0 2 * * * docker exec ai-translation-db mysqldump -u translator -p'password' translation_db > /www/backup/translation_db_$(date +\%Y\%m\%d).sql
```

### 2. File Backup

```bash
# Backup uploads and downloads
tar -czf /www/backup/uploads_$(date +\%Y\%m\%d).tar.gz /www/wwwroot/AI_TRANSLATION_PRO_TIEN_PHONG_TT_VL_2026/backend/uploads/
tar -czf /www/backup/downloads_$(date +\%Y\%m\%d).tar.gz /www/wwwroot/AI_TRANSLATION_PRO_TIEN_PHONG_TT_VL_2026/backend/downloads/
```

### 3. Recovery

```bash
# Restore database
mysql -u translator -p translation_db < /www/backup/translation_db_20241201.sql

# Restore files
tar -xzf /www/backup/uploads_20241201.tar.gz -C /
```

## 🚨 Troubleshooting

### Common Issues

1. **Container không start**

```bash
docker-compose logs
# Check for port conflicts or missing environment variables
```

2. **Database connection failed**

```bash
# Check MySQL service
docker exec -it ai-translation-db mysql -u translator -p
# Verify credentials in .env
```

3. **SSL certificate issues**

- AAPanel > Website > SSL > Reapply certificate
- Check domain DNS configuration

4. **High memory usage**

```bash
# Limit container resources in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

5. **Slow loading**

- Enable Nginx caching
- Optimize images
- Use CDN for static files

## 🔒 Security Best Practices

1. **Update regularly**: AAPanel, Docker images, dependencies
2. **Firewall**: Chỉ mở ports cần thiết
3. **SSL**: Luôn sử dụng HTTPS
4. **Backups**: Định kỳ và test recovery
5. **Monitoring**: Theo dõi logs và performance
6. **Access control**: Sử dụng strong passwords, 2FA

## 📞 Support

Nếu gặp vấn đề trong quá trình triển khai:

1. Check logs: `docker-compose logs`
2. AAPanel documentation: https://www.aapanel.com/
3. GitHub Issues: https://github.com/duyvo26/ai-translation-system/issues

---

🎉 **Chúc mừng! Hệ thống đã được triển khai thành công!**
