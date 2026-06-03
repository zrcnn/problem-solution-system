#!/usr/bin/env python3
"""
数据库迁移脚本：添加卡片分类功能
- 创建 card_categories 表
- 为 solution_cards 表添加 category_id 字段
- 迁移现有数据（将 table_num 1,2,3 映射到对应的分类）
"""

import os
import sys
import sqlite3

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'problems.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 创建 card_categories 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ card_categories 表已创建")
        
        # 2. 检查是否已有默认分类
        cursor.execute('SELECT COUNT(*) FROM card_categories')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # 创建默认分类
            default_categories = [
                ('物理环境', '物理环境问题现场排查', 1),
                ('资产排查', '被核查资产现场问题排查', 2),
                ('网络问题', '网络问题排查', 3)
            ]
            cursor.executemany(
                'INSERT INTO card_categories (name, description, sort_order) VALUES (?, ?, ?)',
                default_categories
            )
            print("✓ 已创建默认分类：物理环境、资产排查、网络问题")
        else:
            print(f"ℹ 已存在 {count} 个分类，跳过默认分类创建")
        
        # 3. 为 solution_cards 表添加 category_id 字段（如果不存在）
        cursor.execute("PRAGMA table_info(solution_cards)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category_id' not in columns:
            cursor.execute('ALTER TABLE solution_cards ADD COLUMN category_id INTEGER')
            print("✓ 已为 solution_cards 表添加 category_id 字段")
        else:
            print("ℹ solution_cards 表已存在 category_id 字段")
        
        # 4. 迁移现有数据：根据 table_num 设置 category_id
        cursor.execute('SELECT COUNT(*) FROM solution_cards')
        card_count = cursor.fetchone()[0]
        
        if card_count > 0:
            # 获取所有分类
            cursor.execute('SELECT id, sort_order FROM card_categories ORDER BY sort_order')
            categories = cursor.fetchall()
            
            # 更新每张卡片的 category_id
            updated_count = 0
            for cat_id, sort_order in categories:
                table_num = sort_order  # table_num 1,2,3 对应 sort_order
                cursor.execute(
                    'UPDATE solution_cards SET category_id = ? WHERE table_num = ?',
                    (cat_id, table_num)
                )
                updated_count += cursor.rowcount
            
            conn.commit()
            print(f"✓ 已迁移 {updated_count} 张卡片的分类")
        else:
            print("ℹ 没有需要迁移的卡片")
        
        conn.commit()
        print("\n迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ 迁移失败：{e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
