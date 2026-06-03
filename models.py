#!/usr/bin/env python3
"""
数据模型定义
包含管理员、操作日志等模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    """管理员用户模型"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 关系
    logs = db.relationship('AdminLog', backref='admin', lazy=True)
    
    def __repr__(self):
        return f'<Admin {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class AdminLog(db.Model):
    """管理员操作日志模型"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, logout
    target_type = db.Column(db.String(50))  # product, problem, solution_card, category, quick_lookup
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON格式的详细信息
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminLog {self.action} on {self.target_type}:{self.target_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 导入其他模型（从app_single.py分离出来的）
class Product(db.Model):
    """产品模型"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    logo_data = db.Column(db.Text)  # Base64编码的logo图片
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    categories = db.relationship('Category', backref='product', lazy=True, cascade='all, delete-orphan')
    problems = db.relationship('Problem', backref='product', lazy=True, cascade='all, delete-orphan')
    quick_lookups = db.relationship('QuickLookup', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'logo_data': self.logo_data,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category_count': len(self.categories),
            'problem_count': len(self.problems)
        }

class Category(db.Model):
    """问题分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    
    # 关系
    problems = db.relationship('Problem', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'product_id': self.product_id,
            'problem_count': len(self.problems)
        }

class Problem(db.Model):
    """问题模型"""
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    screenshot_path = db.Column(db.String(500))
    solution = db.Column(db.Text)
    image_references = db.Column(db.Text)  # DISPIMG image IDs, comma-separated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    quick_lookups = db.relationship('QuickLookup', backref='problem', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Problem {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'category_id': self.category_id,
            'title': self.title,
            'description': self.description,
            'screenshot_path': self.screenshot_path,
            'solution': self.solution,
            'image_references': self.image_references,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'quick_lookup_count': len(self.quick_lookups)
        }

class QuickLookup(db.Model):
    """快速查询模型"""
    __tablename__ = 'quick_lookup'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuickLookup {self.keyword}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'problem_id': self.problem_id,
            'keyword': self.keyword,
            'display_order': self.display_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CardCategory(db.Model):
    """解决方案卡片分类模型"""
    __tablename__ = 'card_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    solution_cards = db.relationship('SolutionCard', backref='card_category', lazy=True)
    
    def __repr__(self):
        return f'<CardCategory {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'card_count': len(self.solution_cards)
        }

class SolutionCard(db.Model):
    """解决方案卡片模型"""
    __tablename__ = 'solution_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('card_categories.id'))  # 自定义分类
    table_num = db.Column(db.Integer, nullable=False)  # 1, 2, 3 (附表编号，保留兼容)
    sequence = db.Column(db.Integer, nullable=False)  # 附表中的序列号
    title = db.Column(db.String(500), nullable=False)
    fault_type = db.Column(db.String(255))
    phenomenon = db.Column(db.Text)
    steps = db.Column(db.Text)
    solution = db.Column(db.Text)
    supplement = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 多对多关系：问题关联的卡片
    problems = db.relationship('Problem', secondary='problem_cards', backref=db.backref('solution_cards', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SolutionCard {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.card_category.name if self.card_category else None,
            'table_num': self.table_num,
            'sequence': self.sequence,
            'title': self.title,
            'fault_type': self.fault_type,
            'phenomenon': self.phenomenon,
            'steps': self.steps,
            'solution': self.solution,
            'supplement': self.supplement,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProblemCard(db.Model):
    """问题与解决方案卡片的多对多关联表"""
    __tablename__ = 'problem_cards'
    
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('solution_cards.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProblemCard problem_id={self.problem_id} card_id={self.card_id}>'
