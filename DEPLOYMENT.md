# 现场问题解决方案管理系统 - 部署文档

## 系统概述

现场问题解决方案管理系统是为杭州盾源科技有限公司的配置核查工具产品配套的问题管理和解决方案查询系统。

### 主要功能
- 用户端：问题查询、解决方案查看、反馈提交
- 管理端：产品管理、问题管理、解决方案卡片管理、反馈管理

### 技术栈
- 后端：Flask + SQLAlchemy
- 数据库：SQLite
- 前端：HTML/CSS/JavaScript

---

## 部署环境要求

### 系统要求
- Python 3.8+
- pip 包管理工具
- 推荐使用 Ubuntu 20.04+ 或 CentOS 7+

### 依赖包
```bash
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
PyJWT==2.8.0
Werkzeug==2.3.7
```

---

## 安装步骤

### 1. 克隆代码
```bash
git clone <repository-url>
cd problem-solution-system
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
# 首次启动应用时会自动创建数据库
python app_single.py
```

---

## 生产环境部署

### 目录结构规划

推荐的生产环境目录结构：

```
/var/lib/problem-solution/
├── uploads/
│   └── feedback/           # 用户反馈截图存储
├── db/
│   └── problems.db         # SQLite数据库
└── logs/                   # 应用日志

# 或者日志单独存放
/var/log/problem-solution/  # 系统日志
```

### 环境变量配置

系统支持通过环境变量配置关键路径：

| 环境变量 | 说明 | 默认值 | 生产环境示例 |
|---------|------|--------|-------------|
| `UPLOAD_FOLDER` | 截图上传目录 | `./uploads/feedback` | `/var/lib/problem-solution/uploads/feedback` |
| `LOG_DIR` | 日志目录 | `./logs` | `/var/log/problem-solution` |
| `LOG_LEVEL` | 日志级别 | `INFO` | `WARNING` |
| `SECRET_KEY` | 加密密钥 | `dev-secret-key-change-in-production` | **必须修改** |

### 部署步骤

#### 1. 创建目录并设置权限
```bash
# 创建数据目录
sudo mkdir -p /var/lib/problem-solution/uploads/feedback
sudo mkdir -p /var/lib/problem-solution/db
sudo mkdir -p /var/log/problem-solution

# 设置权限（假设使用www-data用户运行）
sudo chown -R www-data:www-data /var/lib/problem-solution
sudo chown -R www-data:www-data /var/log/problem-solution

# 设置目录权限
sudo chmod -R 755 /var/lib/problem-solution
sudo chmod -R 755 /var/log/problem-solution
```

#### 2. 配置环境变量
创建环境变量文件 `/etc/problem-solution.env`：
```bash
UPLOAD_FOLDER=/var/lib/problem-solution/uploads/feedback
LOG_DIR=/var/log/problem-solution
LOG_LEVEL=WARNING
SECRET_KEY=your-production-secret-key-here
```

#### 3. 使用Gunicorn运行（推荐）
```bash
# 安装Gunicorn
pip install gunicorn

# 启动用户端（端口12001）
gunicorn -w 4 -b 127.0.0.1:12001 \
    --env-file /etc/problem-solution.env \
    app_single:app \
    --daemon \
    --pid /var/run/problem-solution-user.pid

# 启动管理端（端口12002）
gunicorn -w 2 -b 127.0.0.1:12002 \
    --env-file /etc/problem-solution.env \
    admin_app:admin_app \
    --daemon \
    --pid /var/run/problem-solution-admin.pid
```

#### 4. 配置Nginx反向代理
创建Nginx配置文件 `/etc/nginx/sites-available/problem-solution`：

```nginx
upstream user_backend {
    server 127.0.0.1:12001;
}

upstream admin_backend {
    server 127.0.0.1:12002;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 用户端
    location / {
        proxy_pass http://user_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 管理端（建议添加额外的访问控制）
    location /admin/ {
        proxy_pass http://admin_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态文件（可选，提高性能）
    location /static/ {
        alias /path/to/your/project/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/problem-solution /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. 使用Systemd管理（可选）
创建Systemd服务文件 `/etc/systemd/system/problem-solution-user.service`：

```ini
[Unit]
Description=Problem Solution System - User End
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/problem-solution-system
EnvironmentFile=/etc/problem-solution.env
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:12001 app_single:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

创建管理端服务文件 `/etc/systemd/system/problem-solution-admin.service`：

```ini
[Unit]
Description=Problem Solution System - Admin End
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/problem-solution-system
EnvironmentFile=/etc/problem-solution.env
ExecStart=/path/to/venv/bin/gunicorn -w 2 -b 127.0.0.1:12002 admin_app:admin_app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable problem-solution-user
sudo systemctl enable problem-solution-admin
sudo systemctl start problem-solution-user
sudo systemctl start problem-solution-admin
```

---

## 开发环境部署

### 快速启动
```bash
# 克隆代码
git clone <repository-url>
cd problem-solution-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动用户端（端口12001）
python app_single.py

# 在另一个终端启动管理端（端口12002）
python admin_app.py
```

### 访问地址
- 用户端：http://localhost:12001
- 管理端：http://localhost:12002
- 默认管理员账号：admin / admin123

---

## 系统维护

### 数据库备份
```bash
# 备份数据库
cp /var/lib/problem-solution/db/problems.db /backup/problems_$(date +%Y%m%d).db

# 恢复数据库
cp /backup/problems_20240101.db /var/lib/problem-solution/db/problems.db
```

### 日志查看
```bash
# 查看应用日志
tail -f /var/log/problem-solution/app.log

# 查看Gunicorn日志
tail -f /var/log/gunicorn/problem-solution-user.log
tail -f /var/log/gunicorn/problem-solution-admin.log
```

### 截图清理
系统会自动清理超过10天的反馈截图，无需手动干预。

如需手动清理：
```bash
find /var/lib/problem-solution/uploads/feedback -type f -mtime +10 -delete
```

### 监控检查
```bash
# 检查服务状态
sudo systemctl status problem-solution-user
sudo systemctl status problem-solution-admin

# 检查端口监听
netstat -tlnp | grep :12001
netstat -tlnp | grep :12002

# 检查磁盘空间
df -h /var/lib/problem-solution
```

---

## 安全建议

### 1. 修改默认密钥
**必须**修改 `SECRET_KEY` 环境变量，使用强随机密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 启用HTTPS
在生产环境中，强烈建议使用HTTPS：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # ... 其他配置
}
```

### 3. 管理端访问控制
建议为管理端添加额外的访问控制：
```nginx
location /admin/ {
    # IP白名单
    allow 192.168.1.0/24;
    deny all;
    
    # 或者添加HTTP Basic Auth
    auth_basic "Admin Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://admin_backend/;
    # ...
}
```

### 4. 定期更新依赖
```bash
pip list --outdated
pip install --upgrade flask sqlalchemy
```

---

## 故障排除

### 常见问题

#### 1. 端口已被占用
```bash
# 查看端口占用
lsof -i :12001
lsof -i :12002

# 杀死占用端口的进程
kill -9 <PID>
```

#### 2. 权限错误
```bash
# 检查目录权限
ls -la /var/lib/problem-solution/

# 修复权限
sudo chown -R www-data:www-data /var/lib/problem-solution
sudo chmod -R 755 /var/lib/problem-solution
```

#### 3. 数据库锁定
```bash
# 检查数据库文件
ls -la /var/lib/problem-solution/db/problems.db

# 重启服务释放锁
sudo systemctl restart problem-solution-user
sudo systemctl restart problem-solution-admin
```

#### 4. 上传文件失败
```bash
# 检查上传目录
ls -la /var/lib/problem-solution/uploads/feedback/

# 检查磁盘空间
df -h

# 检查Nginx配置中的client_max_body_size
client_max_body_size 16M;
```

### 日志分析
```bash
# 查看错误日志
grep ERROR /var/log/problem-solution/app.log

# 查看最近的启动日志
tail -100 /var/log/problem-solution/app.log

# 实时监控日志
tail -f /var/log/problem-solution/app.log
```

---

## 升级指南

### 从旧版本升级
```bash
# 备份当前版本
cp -r /path/to/problem-solution-system /backup/problem-solution-system-$(date +%Y%m%d)

# 备份数据库
cp /var/lib/problem-solution/db/problems.db /backup/problems.db

# 拉取新版本
cd /path/to/problem-solution-system
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 重启服务
sudo systemctl restart problem-solution-user
sudo systemctl restart problem-solution-admin
```

---

## 技术支持

如遇到部署问题，请联系：
- 技术支持邮箱：support@duunyuan.com
- 公司内部文档：[内部Wiki链接]

---

**文档版本**: 1.0  
**最后更新**: 2026-05-28  
**适用版本**: v1.0.0+
