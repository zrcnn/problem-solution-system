#!/usr/bin/env python3
"""
生产环境启动脚本
"""

from app_single import app, db

if __name__ == '__main__':
    # 确保数据库表已创建
    with app.app_context():
        db.create_all()
    
    # 启动应用
    app.run(
        debug=False,
        host='0.0.0.0',
        port=12001,
        threaded=True
    )