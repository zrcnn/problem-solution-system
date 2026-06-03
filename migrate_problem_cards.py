"""
添加 problem_cards 关联表 - 支持问题与解决方案卡片的多对多关系
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_app import admin_app as app, db
from models import ProblemCard

with app.app_context():
    # 创建新表
    db.create_all()
    print("Migration completed.")
    
    # 验证表是否存在
    with db.engine.connect() as conn:
        result = conn.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='problem_cards'"))
        row = result.fetchone()
        if row:
            print("Table 'problem_cards' exists and is ready to use.")
        else:
            print("Warning: Table 'problem_cards' may not have been created properly.")
