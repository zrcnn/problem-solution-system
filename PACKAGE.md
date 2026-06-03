# 问题解决方案系统 - 打包清单

## 项目信息
- **项目名称**: 现场问题解决方案管理系统
- **版本**: 1.0.0
- **公司**: 杭州盾源科技有限公司
- **产品**: 配置核查工具
- **打包日期**: 2026-05-28

## 核心文件（必需）

### 应用主文件
- `app_single.py` - 用户端主应用（27KB）
- `admin_app.py` - 管理端主应用（41KB）
- `models.py` - 数据模型（11KB）
- `config.py` - 配置文件（688B）
- `run.py` - 用户端启动脚本（331B）

### 路由和工具
- `routes/` - 路由模块目录
- `utils/` - 工具模块目录

### 前端资源
- `static/` - 静态资源（CSS、JS、图片）
- `templates/` - HTML模板

### 依赖
- `requirements.txt` - Python依赖列表

### 文档
- `README.md` - 项目说明
- `DEPLOYMENT.md` - 部署文档（9.7KB）
- `ADMIN_GUIDE.md` - 管理员指南
- `USAGE.md` - 使用说明

### 启动脚本
- `scripts/start.sh` - 用户端启动脚本
- `scripts/start_admin.sh` - 管理端启动脚本
- `scripts/service.sh` - 服务管理脚本

## 可选文件（开发/维护用）

### 数据库相关
- `db/` - 数据库文件（1.6MB）
- `instance/` - SQLite数据库实例

### 上传文件
- `uploads/` - 用户上传的截图和反馈（2.2MB）
  - `uploads/feedback/` - 反馈截图（10天内）

### 日志
- `logs/` - 应用日志
- `app.log` - 主日志文件

### 迁移和工具脚本
- `migrate_*.py` - 数据库迁移脚本
- `import_missing_problems.py` - 数据导入脚本
- `backup_cleanup/` - 历史清理脚本（可删除）

### 缓存和临时文件
- `__pycache__/` - Python字节码缓存（可删除）
- `venv/` - Python虚拟环境（符号链接，不需打包）

## 清理建议

### 可以删除的文件
1. `backup_cleanup/` - 历史数据清理脚本（已完成使命）
2. `__pycache__/` - Python缓存（重新生成）
3. `*.log` - 日志文件（可选清理）
4. `SSH_TROUBLESHOOTING_SUMMARY.md` - 临时问题总结
5. `IMPLEMENTATION.md` - 实现文档（已过时）
6. `PROJECT_STRUCTURE.md` - 项目结构（已过时）
7. `QUICK_LOOKUP_COMPLETION.md` - 功能完成报告
8. `LOG_SYSTEM.md` - 日志系统文档
9. `README_FEATURE.md` - 功能说明（已整合到DEPLOYMENT.md）

### 建议保留的文件
1. `DEPLOYMENT.md` - 完整部署指南
2. `ADMIN_GUIDE.md` - 管理员操作指南
3. `README.md` - 项目简介
4. `USAGE.md` - 使用说明
5. `requirements.txt` - 依赖列表

## 打包命令

### 创建干净的分发版本
```bash
# 进入项目目录
cd /mnt/d/PROJECT/problem-solution-system

# 删除缓存和临时文件
rm -rf __pycache__
rm -rf *.pyc
rm -f app.log
rm -rf logs/*

# 删除过时文档
rm -f SSH_TROUBLESHOOTING_SUMMARY.md
rm -f IMPLEMENTATION.md
rm -f PROJECT_STRUCTURE.md
rm -f QUICK_LOOKUP_COMPLETION.md
rm -f LOG_SYSTEM.md
rm -f README_FEATURE.md

# 删除历史脚本目录
rm -rf backup_cleanup/

# 创建压缩包
cd /mnt/d/PROJECT/
tar -czf problem-solution-system-$(date +%Y%m%d).tar.gz \
    problem-solution-system/ \
    --exclude='problem-solution-system/__pycache__' \
    --exclude='problem-solution-system/*.log' \
    --exclude='problem-solution-system/logs/*' \
    --exclude='problem-solution-system/backup_cleanup'

echo "打包完成: problem-solution-system-$(date +%Y%m%d).tar.gz"
```

## 部署说明

### 快速部署
1. 解压到目标目录
2. 创建虚拟环境: `python -m venv venv`
3. 安装依赖: `source venv/bin/activate && pip install -r requirements.txt`
4. 配置环境变量（可选）
5. 启动服务:
   - 用户端: `python run.py` (端口12001)
   - 管理端: `python admin_app.py` (端口12002)

### 详细部署指南
参见 `DEPLOYMENT.md` 文档。

## 数据库说明

- **类型**: SQLite
- **位置**: `instance/app.db`
- **大小**: 约1.6MB
- **包含表**: Product, Solution, Image, Feedback, Admin

### 初始数据
- 产品列表：配置核查工具
- 管理员账户：admin / HDYKJ-2024

## 反馈功能

### 用户端
- 多图片上传（PNG, JPG, GIF）
- 压缩包上传（ZIP, RAR, 7Z, TAR, GZ）
- 文件大小限制：50MB
- 自动清理：10天

### 管理端
- 反馈列表管理
- 图片弹窗查看
- 压缩包下载
- 剩余清理时间显示
- 状态标记（待处理/已处理）

## 联系方式

- **公司**: 杭州盾源科技有限公司
- **产品**: 配置核查工具
- **技术支持**: 通过管理端反馈系统

---

**打包完成时间**: 2026-05-28
**打包版本**: v1.0.0
**总大小**: 约5MB（不含数据库和上传文件）
