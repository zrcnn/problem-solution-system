#!/bin/bash
# 管理员后台启动脚本

cd /mnt/d/PROJECT/problem-solution-system

echo "正在启动管理员后台..."
echo "访问地址: http://localhost:12002/admin/login"
echo "默认账户: admin / admin123"
echo ""

python3 admin_app.py
