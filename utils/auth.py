#!/usr/bin/env python3
"""
管理员功能模块
提供管理员认证、权限控制和操作日志功能
"""

import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, redirect, url_for, jsonify, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash

class AdminAuth:
    """管理员认证类"""
    
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db
        if app is not None and db is not None:
            self.init_app(app, db)
    
    def init_app(self, app, db):
        self.app = app
        self.db = db
        
        # 注册管理员路由
        from routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        
        # 初始化数据库表
        self.create_tables()
        
        # 创建默认管理员（如果不存在）
        self.create_default_admin()
    
    def create_tables(self):
        """创建管理员相关表"""
        with self.app.app_context():
            self.db.create_all()
    
    def create_default_admin(self):
        """创建默认管理员账户"""
        from models import Admin
        
        with self.app.app_context():
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),  # 首次登录后需修改
                    email='admin@example.com',
                    is_active=True
                )
                self.db.session.add(admin)
                self.db.session.commit()
                print("默认管理员账户已创建：admin / admin123")
    
    def login_required(self, f):
        """登录验证装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_id' not in session:
                if request.is_xhr or request.path.startswith('/api/'):
                    return jsonify({'error': '未授权访问', 'code': 401}), 401
                return redirect(url_for('admin.login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    
    def log_operation(self, action, target_type, target_id, details=None):
        """记录操作日志"""
        from models import AdminLog
        
        admin_id = session.get('admin_id')
        
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=request.remote_addr
        )
        
        with self.app.app_context():
            self.db.session.add(log)
            self.db.session.commit()
    
    def get_current_admin(self):
        """获取当前管理员信息"""
        from models import Admin
        
        admin_id = session.get('admin_id')
        if admin_id:
            with self.app.app_context():
                return Admin.query.get(admin_id)
        return None
    
    def authenticate(self, username, password):
        """验证用户名密码"""
        from models import Admin
        
        with self.app.app_context():
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password_hash, password):
                if not admin.is_active:
                    return None, "账户已被禁用"
                return admin, None
            return None, "用户名或密码错误"
    
    def login_admin(self, admin):
        """管理员登录"""
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        session.permanent = True
        
        # 更新最后登录时间
        admin.last_login = datetime.utcnow()
        with self.app.app_context():
            self.db.session.commit()
        
        # 记录登录日志
        self.log_operation('login', 'admin', admin.id, {'ip': request.remote_addr})
    
    def logout_admin(self):
        """管理员登出"""
        admin_id = session.get('admin_id')
        if admin_id:
            self.log_operation('logout', 'admin', admin_id)
        session.clear()

# 全局实例
admin_auth = AdminAuth()
