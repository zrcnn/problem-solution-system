#!/bin/bash
# 现场问题解决方案管理系统 - 启动脚本

echo "正在启动 杭州盾源科技有限公司 - 现场问题解决方案管理系统..."

# 进入项目目录
cd /mnt/c/Users/86279/problem-solution-system

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "错误：虚拟环境不存在，请先运行 python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查数据库
if [ ! -f "instance/problems.db" ]; then
    echo "数据库不存在，正在初始化..."
    python init_db.py
fi

# 启动应用
echo "启动应用服务..."
echo "访问地址：http://localhost:5000"
echo "按 Ctrl+C 停止服务"

python run.py