#!/usr/bin/env python3
"""
独立管理员后台应用 - 完整功能版
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os
import sys
import json
import jwt

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
class Config:
    SECRET_KEY = 'dev-secret-key-change-in-production'  # 用于ID加密，必须与app_single.py一致
    JWT_SECRET_KEY = 'jwt-secret-key-change-in-production'  # JWT专用密钥
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24小时过期
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db', 'problems.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# 创建独立的应用
admin_app = Flask('admin_app',
                  template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
                  static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
admin_app.config.from_object(Config)
db = SQLAlchemy(admin_app)

# 导入ID加密工具
from utils.encrypt import IDCrypt
id_crypt = IDCrypt(key=admin_app.config.get('SECRET_KEY', 'dev-secret-key-change-in-production'))

# JWT工具函数
def create_jwt_token(admin_id, username):
    """生成JWT token"""
    payload = {
        'admin_id': admin_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=admin_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, admin_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token

def verify_jwt_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, admin_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def jwt_required(f):
    """JWT认证装饰器 - 支持Header和Cookie两种方式"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 优先从Header中获取token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            if payload:
                request.current_admin = payload
                return f(*args, **kwargs)

        # 如果Header中没有，尝试从Cookie获取
        token = request.cookies.get('admin_token')
        if token:
            payload = verify_jwt_token(token)
            if payload:
                request.current_admin = payload
                return f(*args, **kwargs)

        # 都没有则返回401
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    return decorated_function

# 数据模型
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'))
    action = db.Column(db.String(50), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    logo_data = db.Column(db.Text)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系：删除产品时级联删除关联的分类和问题
    categories = db.relationship('Category', backref='product', lazy=True, cascade='all, delete-orphan')
    problems = db.relationship('Problem', backref='product', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    # 关系：删除分类时级联删除关联的问题
    problems = db.relationship('Problem', backref='category', lazy=True, cascade='all, delete-orphan')

class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    screenshot_path = db.Column(db.String(500))
    solution = db.Column(db.Text)
    image_references = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuickLookup(db.Model):
    __tablename__ = 'quick_lookup'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SolutionCard(db.Model):
    __tablename__ = 'solution_cards'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('card_categories.id'))
    table_num = db.Column(db.Integer, nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    fault_type = db.Column(db.String(255))
    phenomenon = db.Column(db.Text)
    steps = db.Column(db.Text)
    solution = db.Column(db.Text)
    supplement = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联到卡片分类
    card_category = db.relationship('CardCategory', backref='solution_cards')

class CardCategory(db.Model):
    """解决方案卡片分类模型"""
    __tablename__ = 'card_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProblemCard(db.Model):
    __tablename__ = 'problem_cards'
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('solution_cards.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)  # 产品ID
    product_name = db.Column(db.String(255), nullable=False)  # 产品名称（冗余存储）
    description = db.Column(db.Text, nullable=False)  # 问题描述
    image_paths = db.Column(db.Text)  # 多个文件的JSON数组：["type:path", ...]
    contact = db.Column(db.String(255))  # 联系方式（可选）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_processed = db.Column(db.Boolean, default=False)  # 是否已处理

# 认证装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# 记录操作日志
def log_action(action, target_type, target_id=None, details=None):
    log = AdminLog(
        admin_id=session.get('admin_id'),
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details) if details else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

# 路由
@admin_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('admin/login.html')

    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '')
    password = data.get('password', '')

    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password_hash, password):
        if not admin.is_active:
            error = "账户已被禁用"
        else:
            admin.last_login = datetime.utcnow()
            db.session.commit()

            log_action('login', 'admin', admin.id)

            # 生成JWT token
            token = create_jwt_token(admin.id, admin.username)

            if request.is_json:
                return jsonify({
                    'success': True,
                    'token': token,
                    'admin': {
                        'id': admin.id,
                        'username': admin.username
                    }
                })
            # 对于表单提交，仍然使用session作为后备
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('dashboard'))
    else:
        error = "用户名或密码错误"

    if request.is_json:
        return jsonify({'success': False, 'message': error}), 401
    flash(error, 'error')
    return redirect(url_for('login'))

@admin_app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@admin_app.route('/')
def index():
    # 如果已登录（有session），跳转到仪表盘；否则跳转到登录页
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@admin_app.route('/dashboard')
@jwt_required
def dashboard():
    product_count = Product.query.count()
    problem_count = Problem.query.count()
    card_count = SolutionCard.query.count()
    category_count = Category.query.count()
    feedback_count = Feedback.query.count()
    feedback_pending = Feedback.query.filter_by(is_processed=False).count()

    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                         product_count=product_count,
                         problem_count=problem_count,
                         card_count=card_count,
                         category_count=category_count,
                         feedback_count=feedback_count,
                         feedback_pending=feedback_pending,
                         recent_logs=recent_logs)

@admin_app.route('/products')
@jwt_required
def products():
    products = Product.query.order_by(Product.sort_order).all()
    # 转换为字典列表，使用加密ID
    products_data = []
    for p in products:
        products_data.append({
            'id': id_crypt.encrypt_product_id(p.id),
            'name': p.name,
            'description': p.description,
            'sort_order': p.sort_order,
            'is_active': p.is_active,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return render_template('admin/products.html', products=products_data)

# 产品管理 API
@admin_app.route('/api/products', methods=['GET'])
@jwt_required
def get_products():
    products = Product.query.order_by(Product.sort_order).all()
    return jsonify([{
        'id': id_crypt.encrypt_product_id(p.id),
        'raw_id': p.id,  # 添加原始数字ID，用于API参数传递
        'name': p.name,
        'description': p.description,
        'sort_order': p.sort_order,
        'is_active': p.is_active,
        'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for p in products])

@admin_app.route('/api/products', methods=['POST'])
@jwt_required
def create_product():
    data = request.get_json()
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    db.session.add(product)
    db.session.commit()
    log_action('create', 'product', product.id, {'name': product.name})
    return jsonify({'id': product.id, 'success': True})

@admin_app.route('/api/products/<string:product_id>', methods=['GET'])
@jwt_required
def get_product(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify({'error': 'Invalid product ID'}), 400
    product = Product.query.get_or_404(real_id)
    return jsonify({
        'id': id_crypt.encrypt_product_id(product.id),
        'name': product.name,
        'description': product.description,
        'sort_order': product.sort_order,
        'is_active': product.is_active
    })

@admin_app.route('/api/products/<string:product_id>', methods=['PUT'])
@jwt_required
def update_product(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify({'error': 'Invalid product ID'}), 400
    product = Product.query.get_or_404(real_id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.sort_order = data.get('sort_order', product.sort_order)
    product.is_active = data.get('is_active', product.is_active)
    db.session.commit()
    log_action('update', 'product', product.id, {'name': product.name})
    return jsonify({'success': True})

@admin_app.route('/api/products/<string:product_id>', methods=['DELETE'])
@jwt_required
def delete_product(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify({'error': 'Invalid product ID'}), 400
    product = Product.query.get_or_404(real_id)
    db.session.delete(product)
    db.session.commit()
    log_action('delete', 'product', product.id, {'name': product.name})
    return jsonify({'success': True})

@admin_app.route('/categories')
@jwt_required
def categories():
    product_id = request.args.get('product_id', type=int)

    query = Category.query
    if product_id:
        query = query.filter_by(product_id=product_id)

    categories = query.order_by(Category.sort_order).all()

    # 转换为字典列表，包含关联信息
    categories_data = []
    for c in categories:
        product = Product.query.get(c.product_id)
        categories_data.append({
            'id': c.id,
            'name': c.name,
            'description': c.description or '',
            'sort_order': c.sort_order,
            'is_active': c.is_active,
            'product_id': c.product_id,
            'product_name': product.name if product else '-'
        })

    return render_template('admin/categories.html', categories=categories_data)

# 分类管理 API
@admin_app.route('/api/categories', methods=['GET'])
@jwt_required
def get_categories():
    product_id = request.args.get('product_id', type=int)
    query = Category.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    categories = query.order_by(Category.sort_order).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'sort_order': c.sort_order,
        'is_active': c.is_active,
        'product_id': c.product_id
    } for c in categories])

@admin_app.route('/api/categories', methods=['POST'])
@jwt_required
def create_category():
    data = request.get_json()
    category = Category(
        name=data['name'],
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True),
        product_id=data['product_id']
    )
    db.session.add(category)
    db.session.commit()
    log_action('create', 'category', category.id, {'name': category.name})
    return jsonify({'id': category.id, 'success': True})

@admin_app.route('/api/categories/<int:category_id>', methods=['GET'])
@jwt_required
def get_category(category_id):
    category = Category.query.get_or_404(category_id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'sort_order': category.sort_order,
        'is_active': category.is_active,
        'product_id': category.product_id
    })

@admin_app.route('/api/categories/<int:category_id>', methods=['PUT'])
@jwt_required
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.sort_order = data.get('sort_order', category.sort_order)
    category.is_active = data.get('is_active', category.is_active)
    category.product_id = data.get('product_id', category.product_id)
    db.session.commit()
    log_action('update', 'category', category_id, {'name': category.name})
    return jsonify({'success': True})

@admin_app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@jwt_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    log_action('delete', 'category', category_id, {'name': category.name})
    return jsonify({'success': True})

@admin_app.route('/problems')
@jwt_required
def problems():
    product_id = request.args.get('product_id', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Problem.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    if category_id:
        query = query.filter_by(category_id=category_id)

    problems = query.order_by(Problem.created_at.desc()).all()

    # 转换为字典列表，包含关联信息
    problems_data = []
    for p in problems:
        product = Product.query.get(p.product_id)
        category = Category.query.get(p.category_id) if p.category_id else None
        problems_data.append({
            'id': id_crypt.encrypt_problem_id(p.id),  # 使用加密ID
            'title': p.title,
            'product_id': p.product_id,
            'product_name': product.name if product else '-',
            'category_id': p.category_id,
            'category_name': category.name if category else None,
            'description': p.description,
            'solution': p.solution,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('admin/problems.html', problems=problems_data)

# 问题管理 API
@admin_app.route('/api/problems', methods=['GET'])
@jwt_required
def get_problems():
    product_id = request.args.get('product_id', type=int)
    category_id = request.args.get('category_id', type=int)
    query = Problem.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    problems = query.order_by(Problem.created_at.desc()).all()
    result = []
    for p in problems:
        product = Product.query.get(p.product_id)
        category = Category.query.get(p.category_id) if p.category_id else None
        result.append({
            'id': id_crypt.encrypt_problem_id(p.id),
            'title': p.title,
            'product_id': p.product_id,
            'product_name': product.name if product else None,
            'category_id': p.category_id,
            'category_name': category.name if category else None,
            'description': p.description,
            'solution': p.solution,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(result)

@admin_app.route('/api/problems/<string:problem_id>', methods=['GET'])
@jwt_required
def get_problem(problem_id):
    real_id = id_crypt.decrypt_problem_id(problem_id)
    if real_id is None:
        return jsonify({'error': 'Invalid problem ID'}), 404
    problem = Problem.query.get(real_id)
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    # 获取关联的解决方案卡片
    problem_cards = ProblemCard.query.filter_by(problem_id=real_id).all()
    card_ids = [pc.card_id for pc in problem_cards]

    return jsonify({
        'id': id_crypt.encrypt_problem_id(problem.id),
        'title': problem.title,
        'product_id': problem.product_id,
        'category_id': problem.category_id,
        'description': problem.description,
        'solution': problem.solution,
        'created_at': problem.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'card_ids': card_ids  # 关联的卡片ID列表
    })

@admin_app.route('/api/problems', methods=['POST'])
@jwt_required
def create_problem():
    data = request.get_json()
    problem = Problem(
        title=data['title'],
        description=data.get('description', ''),
        product_id=data['product_id'],
        category_id=data.get('category_id'),
        solution=data.get('solution', '')
    )
    db.session.add(problem)
    db.session.commit()

    # 处理卡片关联
    card_ids = data.get('card_ids', [])
    for card_id in card_ids:
        pc = ProblemCard(problem_id=problem.id, card_id=card_id)
        db.session.add(pc)
    db.session.commit()

    log_action('create', 'problem', problem.id, {'title': problem.title, 'card_count': len(card_ids)})
    return jsonify({'id': problem.id, 'success': True})

@admin_app.route('/api/problems/<string:problem_id>', methods=['PUT'])
@jwt_required
def update_problem(problem_id):
    real_id = id_crypt.decrypt_problem_id(problem_id)
    if real_id is None:
        return jsonify({'error': 'Invalid problem ID'}), 404
    problem = Problem.query.get_or_404(real_id)
    data = request.get_json()
    problem.title = data.get('title', problem.title)
    problem.description = data.get('description', problem.description)
    problem.product_id = data.get('product_id', problem.product_id)
    problem.category_id = data.get('category_id', problem.category_id)
    problem.solution = data.get('solution', problem.solution)
    problem.updated_at = datetime.utcnow()

    # 处理卡片关联
    if 'card_ids' in data:
        # 删除旧的关联
        ProblemCard.query.filter_by(problem_id=real_id).delete()
        # 添加新的关联
        for card_id in data['card_ids']:
            pc = ProblemCard(problem_id=real_id, card_id=card_id)
            db.session.add(pc)

    db.session.commit()
    log_action('update', 'problem', real_id, {'title': problem.title})
    return jsonify({'success': True})

@admin_app.route('/api/problems/<string:problem_id>', methods=['DELETE'])
@jwt_required
def delete_problem(problem_id):
    real_id = id_crypt.decrypt_problem_id(problem_id)
    if real_id is None:
        return jsonify({'error': 'Invalid problem ID'}), 404
    problem = Problem.query.get_or_404(real_id)
    db.session.delete(problem)
    db.session.commit()
    log_action('delete', 'problem', real_id, {'title': problem.title})
    return jsonify({'success': True})

@admin_app.route('/solution-cards')
@jwt_required
def solution_cards():
    table_num = request.args.get('table_num', 1, type=int)
    cards = SolutionCard.query.filter_by(table_num=table_num).order_by(SolutionCard.sequence).all()

    cards_data = [{
        'id': id_crypt.encrypt_card_id(c.id),
        'table_num': c.table_num,
        'sequence': c.sequence,
        'title': c.title,
        'fault_type': c.fault_type,
        'phenomenon': c.phenomenon,
        'steps': c.steps,
        'solution': c.solution,
        'supplement': c.supplement
    } for c in cards]

    return render_template('admin/solution_cards.html', cards=cards_data, current_table=table_num)

# 解决方案卡片 API
@admin_app.route('/api/solution-cards', methods=['GET'])
@jwt_required
def get_solution_cards():
    table_num = request.args.get('table_num', type=int)
    category_id = request.args.get('category_id', type=int)
    query = SolutionCard.query
    if table_num:
        query = query.filter_by(table_num=table_num)
    if category_id:
        query = query.filter_by(category_id=category_id)
    cards = query.order_by(SolutionCard.table_num, SolutionCard.sequence).all()
    return jsonify([{
        'id': id_crypt.encrypt_card_id(c.id),
        'category_id': c.category_id,
        'category_name': c.card_category.name if c.card_category else None,
        'table_num': c.table_num,
        'sequence': c.sequence,
        'title': c.title,
        'fault_type': c.fault_type,
        'phenomenon': c.phenomenon,
        'steps': c.steps,
        'solution': c.solution,
        'supplement': c.supplement
    } for c in cards])

@admin_app.route('/api/solution-cards', methods=['POST'])
@jwt_required
def create_solution_card():
    data = request.get_json()
    card = SolutionCard(
        category_id=data.get('category_id'),
        table_num=data['table_num'],
        sequence=data['sequence'],
        title=data['title'],
        fault_type=data.get('fault_type', ''),
        phenomenon=data.get('phenomenon', ''),
        steps=data.get('steps', ''),
        solution=data.get('solution', ''),
        supplement=data.get('supplement', '')
    )
    db.session.add(card)
    db.session.commit()
    log_action('create', 'solution_card', card.id, {'title': card.title})
    return jsonify({'id': card.id, 'success': True})

@admin_app.route('/api/solution-cards/<string:card_id>', methods=['GET'])
@jwt_required
def get_solution_card(card_id):
    # 解密卡片ID
    real_id = id_crypt.decrypt_card_id(card_id)
    if real_id is None:
        return jsonify({'error': 'Invalid card ID'}), 400
    card = SolutionCard.query.get_or_404(real_id)
    return jsonify({
        'id': id_crypt.encrypt_card_id(card.id),
        'category_id': card.category_id,
        'category_name': card.card_category.name if card.card_category else None,
        'table_num': card.table_num,
        'sequence': card.sequence,
        'title': card.title,
        'fault_type': card.fault_type,
        'phenomenon': card.phenomenon,
        'steps': card.steps,
        'solution': card.solution,
        'supplement': card.supplement
    })

@admin_app.route('/api/solution-cards/<string:card_id>', methods=['PUT'])
@jwt_required
def update_solution_card(card_id):
    # 解密卡片ID
    real_id = id_crypt.decrypt_card_id(card_id)
    if real_id is None:
        return jsonify({'error': 'Invalid card ID'}), 400
    card = SolutionCard.query.get_or_404(real_id)
    data = request.get_json()
    card.category_id = data.get('category_id', card.category_id)
    card.table_num = data.get('table_num', card.table_num)
    card.sequence = data.get('sequence', card.sequence)
    card.title = data.get('title', card.title)
    card.fault_type = data.get('fault_type', card.fault_type)
    card.phenomenon = data.get('phenomenon', card.phenomenon)
    card.steps = data.get('steps', card.steps)
    card.solution = data.get('solution', card.solution)
    card.supplement = data.get('supplement', card.supplement)
    db.session.commit()
    log_action('update', 'solution_card', card.id, {'title': card.title})
    return jsonify({'success': True})

@admin_app.route('/api/solution-cards/<string:card_id>', methods=['DELETE'])
@jwt_required
def delete_solution_card(card_id):
    # 解密卡片ID
    real_id = id_crypt.decrypt_card_id(card_id)
    if real_id is None:
        return jsonify({'error': 'Invalid card ID'}), 400
    card = SolutionCard.query.get_or_404(real_id)
    db.session.delete(card)
    db.session.commit()
    log_action('delete', 'solution_card', card.id, {'title': card.title})
    return jsonify({'success': True})

# 快速查询 API
@admin_app.route('/api/quick-lookups', methods=['GET'])
@jwt_required
def get_quick_lookups():
    product_id = request.args.get('product_id', type=int)
    query = QuickLookup.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    lookups = query.order_by(QuickLookup.display_order).all()
    return jsonify([{
        'id': l.id,
        'product_id': l.product_id,
        'problem_id': l.problem_id,
        'keyword': l.keyword,
        'display_order': l.display_order,
        'is_active': l.is_active
    } for l in lookups])

@admin_app.route('/api/quick-lookups', methods=['POST'])
@jwt_required
def create_quick_lookup():
    data = request.get_json()
    lookup = QuickLookup(
        product_id=data['product_id'],
        problem_id=data['problem_id'],
        keyword=data['keyword'],
        display_order=data.get('display_order', 0),
        is_active=data.get('is_active', True)
    )
    db.session.add(lookup)
    db.session.commit()
    log_action('create', 'quick_lookup', lookup.id, {'keyword': lookup.keyword})
    return jsonify({'id': lookup.id, 'success': True})

@admin_app.route('/api/quick-lookups/<int:lookup_id>', methods=['PUT'])
@jwt_required
def update_quick_lookup(lookup_id):
    lookup = QuickLookup.query.get_or_404(lookup_id)
    data = request.get_json()
    lookup.product_id = data.get('product_id', lookup.product_id)
    lookup.problem_id = data.get('problem_id', lookup.problem_id)
    lookup.keyword = data.get('keyword', lookup.keyword)
    lookup.display_order = data.get('display_order', lookup.display_order)
    lookup.is_active = data.get('is_active', lookup.is_active)
    db.session.commit()
    log_action('update', 'quick_lookup', lookup_id, {'keyword': lookup.keyword})
    return jsonify({'success': True})

@admin_app.route('/api/quick-lookups/<int:lookup_id>', methods=['DELETE'])
@jwt_required
def delete_quick_lookup(lookup_id):
    lookup = QuickLookup.query.get_or_404(lookup_id)
    db.session.delete(lookup)
    db.session.commit()
    log_action('delete', 'quick_lookup', lookup_id, {'keyword': lookup.keyword})
    return jsonify({'success': True})

# 操作日志 API
@admin_app.route('/api/logs', methods=['GET'])
@jwt_required
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(limit).all()
    return jsonify([{
        'id': l.id,
        'admin_id': l.admin_id,
        'action': l.action,
        'target_type': l.target_type,
        'target_id': l.target_id,
        'details': l.details,
        'ip_address': l.ip_address,
        'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for l in logs])

# 初始化数据库
def init_db():
    with admin_app.app_context():
        db.create_all()

        # 创建默认管理员
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('HDYKJ-2024'),
                email='admin@example.com',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("默认管理员账户已创建：admin / HDYKJ-2024")
        else:
            # 如果管理员存在但密码不是新的，更新密码
            if not check_password_hash(admin.password_hash, 'HDYKJ-2024'):
                admin.password_hash = generate_password_hash('HDYKJ-2024')
                db.session.commit()
                print("管理员密码已更新为：HDYKJ-2024")

# ========== 卡片分类管理 ==========
@admin_app.route('/card-categories')
@jwt_required
def card_categories_page():
    return render_template('admin/card_categories.html')

@admin_app.route('/api/card-categories', methods=['GET'])
@jwt_required
def get_card_categories():
    categories = CardCategory.query.order_by(CardCategory.sort_order, CardCategory.id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'sort_order': c.sort_order,
        'is_active': c.is_active,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'card_count': len(c.solution_cards)
    } for c in categories])

@admin_app.route('/api/card-categories', methods=['POST'])
@jwt_required
def create_card_category():
    data = request.get_json()
    category = CardCategory(
        name=data['name'],
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    db.session.add(category)
    db.session.commit()
    log_action('create', 'card_category', category.id, {'name': category.name})
    return jsonify({'success': True, 'id': category.id})

@admin_app.route('/api/card-categories/<int:category_id>', methods=['GET'])
@jwt_required
def get_card_category(category_id):
    category = CardCategory.query.get_or_404(category_id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'sort_order': category.sort_order,
        'is_active': category.is_active
    })

@admin_app.route('/api/card-categories/<int:category_id>', methods=['PUT'])
@jwt_required
def update_card_category(category_id):
    category = CardCategory.query.get_or_404(category_id)
    data = request.get_json()
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.sort_order = data.get('sort_order', category.sort_order)
    category.is_active = data.get('is_active', category.is_active)
    db.session.commit()
    log_action('update', 'card_category', category.id, {'name': category.name})
    return jsonify({'success': True})

@admin_app.route('/api/card-categories/<int:category_id>', methods=['DELETE'])
@jwt_required
def delete_card_category(category_id):
    category = CardCategory.query.get_or_404(category_id)
    name = category.name
    # 检查是否有关联的卡片
    if category.solution_cards:
        return jsonify({'success': False, 'error': '该分类下还有卡片，无法删除'}), 400
    db.session.delete(category)
    db.session.commit()
    log_action('delete', 'card_category', category_id, {'name': name})
    return jsonify({'success': True})

# 反馈管理路由
@admin_app.route('/feedback')
@jwt_required
def feedback():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_processed = request.args.get('is_processed', type=lambda v: v == 'true')

    query = Feedback.query

    if is_processed is not None:
        query = query.filter_by(is_processed=is_processed)

    feedbacks = query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    feedbacks_data = []
    for f in feedbacks.items:
        # 解析文件列表
        import json
        files = []
        if f.image_paths:
            try:
                files = json.loads(f.image_paths)
            except:
                files = []

        # 计算剩余清理时间（10天后清理）
        cleanup_days = 10
        days_remaining = None
        if f.created_at:
            from datetime import datetime, timedelta
            cleanup_date = f.created_at + timedelta(days=cleanup_days)
            now = datetime.utcnow()
            if cleanup_date > now:
                delta = cleanup_date - now
                days_remaining = delta.days
            else:
                days_remaining = 0

        feedbacks_data.append({
            'id': f.id,
            'product_id': f.product_id,
            'product_name': f.product_name,
            'description': f.description,
            'files': files,  # [(type, path), ...]
            'contact': f.contact or '-',
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_processed': f.is_processed,
            'days_remaining': days_remaining
        })

    return render_template('admin/feedback.html',
                         feedbacks=feedbacks_data,
                         pagination=feedbacks,
                         current_page=page,
                         is_processed_filter=is_processed)

# 反馈管理API
@admin_app.route('/api/feedback', methods=['GET'])
@jwt_required
def get_feedback():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    is_processed = request.args.get('is_processed', type=lambda v: v == 'true')

    query = Feedback.query

    if is_processed is not None:
        query = query.filter_by(is_processed=is_processed)

    feedbacks = query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    feedbacks_data = []
    for f in feedbacks.items:
        # 解析文件列表
        import json
        files = []
        if f.image_paths:
            try:
                files = json.loads(f.image_paths)
            except:
                files = []

        # 计算剩余清理时间（10天后清理）
        cleanup_days = 10
        days_remaining = None
        if f.created_at:
            from datetime import datetime, timedelta
            cleanup_date = f.created_at + timedelta(days=cleanup_days)
            now = datetime.utcnow()
            if cleanup_date > now:
                delta = cleanup_date - now
                days_remaining = delta.days
            else:
                days_remaining = 0

        feedbacks_data.append({
            'id': f.id,
            'product_id': f.product_id,
            'product_name': f.product_name,
            'description': f.description,
            'files': files,  # [(type, path), ...]
            'contact': f.contact,
            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_processed': f.is_processed,
            'days_remaining': days_remaining
        })

    return jsonify({
        'items': feedbacks_data,
        'total': feedbacks.total,
        'pages': feedbacks.pages,
        'current_page': feedbacks.page,
        'per_page': per_page
    })

@admin_app.route('/api/feedback/<int:feedback_id>', methods=['PUT'])
@jwt_required
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    data = request.get_json()

    if 'is_processed' in data:
        feedback.is_processed = data['is_processed']

    db.session.commit()
    log_action('update', 'feedback', feedback_id, {'is_processed': feedback.is_processed})
    return jsonify({'success': True})

@admin_app.route('/api/feedback/<int:feedback_id>', methods=['DELETE'])
@jwt_required
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    log_action('delete', 'feedback', feedback_id, {'product_name': feedback.product_name})
    return jsonify({'success': True})

@admin_app.route('/feedback-images/<path:filename>')
def serve_feedback_image(filename):
    """提供反馈截图（不需要认证，因为是通过img标签加载）"""
    try:
        # 获取上传目录，默认为项目下的uploads/feedback
        basedir = os.path.abspath(os.path.dirname(__file__))
        upload_dir = os.path.join(basedir, 'uploads', 'feedback')

        filepath = os.path.join(upload_dir, filename)

        if not os.path.exists(filepath):
            return 'Image not found', 404

        # 检测文件类型
        if filename.lower().endswith('.png'):
            content_type = 'image/png'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif filename.lower().endswith('.gif'):
            content_type = 'image/gif'
        else:
            content_type = 'application/octet-stream'

        with open(filepath, 'rb') as f:
            image_data = f.read()

        return make_response(image_data, 200, {'Content-Type': content_type})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return 'Error', 500

if __name__ == '__main__':
    init_db()
    admin_app.run(host='0.0.0.0', port=12002, debug=True)
