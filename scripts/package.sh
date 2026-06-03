#!/bin/bash
# 问题解决方案系统打包脚本
# 用途：清理无效文件并创建分发版本

PROJECT_DIR="/mnt/d/PROJECT/problem-solution-system"
OUTPUT_DIR="/mnt/d/PROJECT"
DATE=$(date +%Y%m%d)
PACKAGE_NAME="problem-solution-system-${DATE}.tar.gz"

echo "========================================"
echo "问题解决方案系统打包脚本"
echo "========================================"
echo ""

# 进入项目目录
cd "$PROJECT_DIR" || exit 1

echo "📁 当前目录: $(pwd)"
echo ""

# 清理步骤
echo "🧹 开始清理..."

# 1. 清理Python缓存
echo "  → 清理Python缓存..."
rm -rf __pycache__
rm -rf */__pycache__
rm -rf */*/__pycache__
rm -f *.pyc
rm -f */*.pyc

# 2. 清理日志文件
echo "  → 清理日志文件..."
rm -f app.log
rm -rf logs/*
touch app.log
touch logs/.gitkeep

# 3. 清理过时文档
echo "  → 清理过时文档..."
rm -f SSH_TROUBLESHOOTING_SUMMARY.md
rm -f IMPLEMENTATION.md
rm -f PROJECT_STRUCTURE.md
rm -f QUICK_LOOKUP_COMPLETION.md
rm -f LOG_SYSTEM.md
rm -f README_FEATURE.md

# 4. 清理历史脚本目录
echo "  → 清理历史脚本目录..."
rm -rf backup_cleanup/

# 5. 清理临时文件
echo "  → 清理临时文件..."
rm -f *.tmp
rm -f *.swp
rm -f *.swo
rm -f .DS_Store
rm -f Thumbs.db

echo "✅ 清理完成"
echo ""

# 显示清理后的文件结构
echo "📊 清理后的项目结构:"
echo "========================================"
du -sh * 2>/dev/null | sort -hr
echo "========================================"
echo ""

# 计算总大小
TOTAL_SIZE=$(du -sh . | awk '{print $1}')
echo "📦 项目总大小: $TOTAL_SIZE"
echo ""

# 创建压缩包
echo "🗜️  创建压缩包..."
cd "$OUTPUT_DIR" || exit 1

# 使用正确的tar语法 - 包含数据库
tar --exclude='problem-solution-system/__pycache__' \
    --exclude='problem-solution-system/*.log' \
    --exclude='problem-solution-system/logs/*' \
    --exclude='problem-solution-system/backup_cleanup' \
    --exclude='problem-solution-system/uploads/feedback/*' \
    -czf "$PACKAGE_NAME" \
    problem-solution-system/

if [ $? -eq 0 ]; then
    PACKAGE_SIZE=$(du -sh "$PACKAGE_NAME" | awk '{print $1}')
    echo "✅ 打包成功!"
    echo ""
    echo "📦 压缩包: $PACKAGE_NAME"
    echo "📊 压缩包大小: $PACKAGE_SIZE"
    echo "📁 保存位置: $OUTPUT_DIR/$PACKAGE_NAME"
    echo ""
    echo "📋 包含内容:"
    echo "  ✓ 核心应用文件 (app_single.py, admin_app.py, models.py)"
    echo "  ✓ 前端资源 (static/, templates/)"
    echo "  ✓ 路由和工具 (routes/, utils/)"
    echo "  ✓ 配置文件 (config.py, requirements.txt)"
    echo "  ✓ 启动脚本 (scripts/)"
    echo "  ✓ 文档 (README.md, DEPLOYMENT.md, ADMIN_GUIDE.md, USAGE.md)"
    echo "  ✓ 新增文档 (PACKAGE.md)"
    echo "  ✓ 数据库文件 (db/, instance/)"
    echo ""
echo "❌ 未包含:"
echo "  ✗ Python缓存 (__pycache__, *.pyc)"
echo "  ✗ 日志文件 (*.log, logs/*)"
echo "  ✗ 历史脚本 (backup_cleanup/)"
echo "  ✗ 过时文档 (SSH_TROUBLESHOOTING_SUMMARY.md 等)"
echo "  ✗ 用户上传 (uploads/feedback/)"
echo "  ✗ 虚拟环境 (venv/)"
    echo ""
    echo "🚀 部署说明:"
    echo "  1. 解压: tar -xzf $PACKAGE_NAME"
    echo "  2. 进入: cd problem-solution-system"
    echo "  3. 创建虚拟环境: python -m venv venv"
    echo "  4. 激活: source venv/bin/activate"
    echo "  5. 安装依赖: pip install -r requirements.txt"
    echo "  6. 启动用户端: python run.py"
    echo "  7. 启动管理端: python admin_app.py"
    echo ""
else
    echo "❌ 打包失败!"
    exit 1
fi
