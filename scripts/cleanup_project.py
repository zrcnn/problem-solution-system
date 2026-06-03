#!/usr/bin/env python3
"""
项目清理脚本
清理无用、过期或临时的Python脚本和文件
保留核心运行文件和重要文档
"""

import os
import shutil
from datetime import datetime

def cleanup_project():
    project_dir = '/mnt/d/PROJECT/problem-solution-system'
    
    # 分类文件
    files_to_keep = {
        # 核心运行文件
        'core': [
            'app_single.py',      # 主应用
            'config.py',          # 配置文件
            'run.py',             # 运行入口
        ],
        
        # 重要文档
        'docs': [
            'README.md',
            'README_FEATURE.md',
            'USAGE.md',
            'IMPLEMENTATION.md',
            'SSH_TROUBLESHOOTING_SUMMARY.md',
            'QUICK_LOOKUP_COMPLETION.md',
        ],
        
        # 启动脚本
        'scripts': [
            'start.sh',
            'service.sh',
        ],
        
        # 数据库文件
        'database': [
            'problems.db',
        ],
        
        # 依赖文件
        'deps': [
            'requirements.txt',
        ],
        
        # 目录
        'directories': [
            'static',
            'templates',
            'routes',
        ]
    }
    
    # 要删除的临时/过期文件
    files_to_remove = [
        # 数据迁移和修复脚本（已完成任务）
        'check_excel.py',
        'fix_descriptions.py',
        'fix_descriptions_final.py',
        'import_excel.py',
        'import_excel_v2.py',
        'init_db.py',
        'migrate_db.py',
        'migrate_images.py',
        'migrate_logo.py',
        'parse_refs.py',
        'rebuild_db.py',
        'restore_descriptions.py',
        'verify_fix.py',
        
        # 临时测试文件
        'test_fix.py',
        'test_access.html',
        'test_problem_detail.html',
        
        # 我们创建的临时脚本（任务已完成）
        'add_quick_lookup_keywords.py',
        'add_ssh_troubleshooting_cards.py',
        'cleanup_quick_lookup.py',
        'complete_original_cards.py',
        'complete_ssh_troubleshooting.py',
        'final_cleanup.py',
        'update_all_descriptions.py',
        'update_problem_description.py',
        'update_problem_solutions.py',
    ]
    
    # 创建备份目录
    backup_dir = os.path.join(project_dir, 'backup_cleanup')
    os.makedirs(backup_dir, exist_ok=True)
    
    print("=== 项目清理开始 ===")
    print(f"备份目录: {backup_dir}\n")
    
    # 统计
    removed_count = 0
    removed_size = 0
    
    # 删除指定文件
    for filename in files_to_remove:
        filepath = os.path.join(project_dir, filename)
        if os.path.exists(filepath):
            # 获取文件大小
            file_size = os.path.getsize(filepath)
            
            # 移动到备份目录
            backup_path = os.path.join(backup_dir, filename)
            shutil.move(filepath, backup_path)
            
            removed_count += 1
            removed_size += file_size
            print(f"✓ 已移除: {filename} ({file_size} 字节)")
    
    # 清理空的__pycache__目录
    pycache_dir = os.path.join(project_dir, '__pycache__')
    if os.path.exists(pycache_dir):
        try:
            shutil.rmtree(pycache_dir)
            print(f"✓ 已清理: __pycache__ 目录")
        except Exception as e:
            print(f"✗ 清理 __pycache__ 失败: {e}")
    
    # 清理日志文件（可选）
    log_file = os.path.join(project_dir, 'app.log')
    if os.path.exists(log_file):
        # 如果日志文件大于10MB，则清空
        if os.path.getsize(log_file) > 10 * 1024 * 1024:
            with open(log_file, 'w') as f:
                f.write('')
            print(f"✓ 已清空: app.log (文件过大)")
    
    print(f"\n=== 清理完成 ===")
    print(f"移除文件数: {removed_count}")
    print(f"释放空间: {removed_size} 字节 ({removed_size/1024:.2f} KB)")
    print(f"备份位置: {backup_dir}")
    
    # 显示保留的重要文件
    print(f"\n=== 保留的核心文件 ===")
    for category, files in files_to_keep.items():
        if files:
            print(f"\n{category.upper()}:")
            for f in files:
                filepath = os.path.join(project_dir, f)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"  ✓ {f} ({size} 字节)")
                else:
                    print(f"  ✗ {f} (不存在)")

if __name__ == "__main__":
    cleanup_project()
