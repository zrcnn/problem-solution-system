#!/usr/bin/env python3
"""
单文件Flask应用，避免多模块导入导致的SQLAlchemy实例冲突
"""

import os
import base64
import re
import hashlib
import hmac
import time
import uuid
from flask import Flask, Blueprint, request, jsonify, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename

# 导入日志系统
from utils import get_logger, init_app_logger

# 配置
class Config:
    COMPANY_NAME = "杭州盾源科技有限公司"
    SYSTEM_TITLE = "现场问题解决方案管理系统"
    SYSTEM_VERSION = "1.0.0"
    SECRET_KEY = 'dev-secret-key-change-in-production'  # 用于ID加密
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db', 'problems.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'dev-secret-key-change-in-production'
    
    # 文件上传配置
    # 开发环境：项目目录下的uploads
    # 生产环境：/var/lib/problem-solution/uploads/feedback
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads', 'feedback'))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB（支持多文件和压缩包）
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', '7z', 'tar', 'gz'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz'}
    
    # 日志配置
    # 生产环境：/var/log/problem-solution/
    LOG_DIR = os.environ.get('LOG_DIR', os.path.join(basedir, 'logs'))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 初始化
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
CORS(app)

# 导入ID加密工具（必须在app创建之后）
from utils.encrypt import IDCrypt
id_crypt = IDCrypt(key=app.config.get('SECRET_KEY', 'dev-secret-key'))

# 初始化日志系统
logger = init_app_logger(app)

# 请求日志中间件
@app.before_request
def before_request():
    """记录请求开始"""
    request.start_time = time.time()
    logger.debug(f"请求开始: {request.method} {request.path}")

@app.after_request
def after_request(response):
    """记录请求完成"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.log_request(
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration=duration,
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    return response

# 辅助函数：检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar', '7z', 'tar', 'gz'})

def allowed_image(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})

def allowed_archive(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_ARCHIVE_EXTENSIONS', {'zip', 'rar', '7z', 'tar', 'gz'})

# 辅助函数：确保上传目录存在
def ensure_upload_dir():
    upload_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir

# 数据模型
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    logo_data = db.Column(db.Text)  # Base64编码的logo图片
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    categories = db.relationship('Category', backref='product', lazy=True)
    problems = db.relationship('Problem', backref='product', lazy=True)
    quick_lookups = db.relationship('QuickLookup', backref='product', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    
    problems = db.relationship('Problem', backref='category', lazy=True)

class Problem(db.Model):
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    quick_lookups = db.relationship('QuickLookup', backref='problem', lazy=True)

class QuickLookup(db.Model):
    __tablename__ = 'quick_lookup'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

class SolutionCard(db.Model):
    """解决方案卡片 - 对应附表1/2/3中的每一行详细排查内容"""
    __tablename__ = 'solution_cards'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('card_categories.id'))  # 自定义分类
    table_num = db.Column(db.Integer, nullable=False)  # 1, 2, 3 (附表编号，保留兼容)
    sequence = db.Column(db.Integer, nullable=False)  # 附表中的序列号
    title = db.Column(db.String(500), nullable=False)  # 故障现象/问题标题
    fault_type = db.Column(db.String(255))  # 故障类型（附表1/2）/ 问题类型
    phenomenon = db.Column(db.Text)  # 故障现象说明（附表1）/ 具体问题描述（附表2）/ 问题（附表3）
    steps = db.Column(db.Text)  # 排查操作步骤（附表1/2）/ 排查方法（附表3）
    solution = db.Column(db.Text)  # 解决方案
    supplement = db.Column(db.Text)  # 补充信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.String(100), unique=True, nullable=False)  # 如 "ID_3CD8D91A48784E648F7D9C817E1518BB"
    image_data = db.Column(db.Text, nullable=False)  # Base64编码的图片数据
    content_type = db.Column(db.String(50), default='image/png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# 数据模型
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

# ID加密/解密工具
class IDCodec:
    """将数字ID编码为短字符串，避免暴露真实ID"""
    
    # 自定义字符集（62个字符：数字+大小写字母）
    CHARSET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    BASE = len(CHARSET)
    
    @staticmethod
    def encode(num):
        """将数字编码为字符串"""
        if num == 0:
            return IDCodec.CHARSET[0]
        
        encoded = ''
        while num:
            num, rem = divmod(num, IDCodec.BASE)
            encoded = IDCodec.CHARSET[rem] + encoded
        return encoded
    
    @staticmethod
    def decode(encoded):
        """将字符串解码为数字"""
        num = 0
        for char in encoded:
            num = num * IDCodec.BASE + IDCodec.CHARSET.index(char)
        return num
    
    @staticmethod
    def encrypt_id(problem_id):
        """加密问题ID"""
        # 添加一个简单的混淆：异或一个固定值
        obfuscated = problem_id ^ 0x5A5A  # 23130
        return IDCodec.encode(obfuscated)
    
    @staticmethod
    def decrypt_id(encrypted_id):
        """解密问题ID"""
        try:
            obfuscated = IDCodec.decode(encrypted_id)
            return obfuscated ^ 0x5A5A
        except:
            return None

# 页面路由
page_bp = Blueprint('pages', __name__)

@page_bp.context_processor
def inject_products():
    """在所有页面模板中注入products变量，用于base.html显示logo"""
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    # 转换为加密ID的字典列表
    products_data = [{
        'id': id_crypt.encrypt_product_id(p.id),
        'name': p.name,
        'logo': p.logo_data
    } for p in products]
    return dict(products=products_data)

# API路由
api_bp = Blueprint('api', __name__)

@api_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    return jsonify([{
        'id': id_crypt.encrypt_product_id(p.id),
        'name': p.name,
        'logo': p.logo_data
    } for p in products])

@api_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify({'error': 'Invalid product ID'}), 404
    product = Product.query.get_or_404(real_id)
    return jsonify({
        'id': id_crypt.encrypt_product_id(product.id),
        'name': product.name,
        'description': product.description,
        'logo': product.logo_data,
        'categories': [{
            'id': c.id,
            'name': c.name
        } for c in product.categories]
    })

@api_bp.route('/products/<product_id>/quick-lookup', methods=['GET'])
def get_quick_lookup(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify([]), 404
    keyword = request.args.get('q', '')
    query = QuickLookup.query.filter_by(product_id=real_id, is_active=True)
    
    if keyword:
        query = query.filter(QuickLookup.keyword.contains(keyword))
    
    quick_lookups = query.order_by(QuickLookup.display_order).all()
    
    results = []
    for ql in quick_lookups:
        problem = Problem.query.get(ql.problem_id)
        if problem:
            results.append({
                'id': ql.id,
                'keyword': ql.keyword,
                'problem': {
                    'id': id_crypt.encrypt_problem_id(problem.id),  # 加密ID
                    'title': problem.title,
                    'description': problem.description[:100] if problem.description else '',
                    'category': problem.category.name if problem.category else None
                }
            })
    
    return jsonify(results)


@api_bp.route('/products/<product_id>/categories', methods=['GET'])
def get_product_categories(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify([]), 404
    
    # 获取该产品的所有分类，以及每个分类下的问题数
    categories = Category.query.filter_by(product_id=real_id, is_active=True).order_by(Category.sort_order).all()
    results = []
    for c in categories:
        problem_count = Problem.query.filter_by(category_id=c.id).count()
        results.append({
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'problem_count': problem_count
        })
    return jsonify(results)

# 获取分类下的所有问题
@api_bp.route('/categories/<int:category_id>/problems', methods=['GET'])
def get_category_problems(category_id):
    # 获取该分类下的所有问题
    problems = Problem.query.filter_by(category_id=category_id).order_by(Problem.created_at.desc()).all()
    results = []
    for p in problems:
        results.append({
            'id': id_crypt.encrypt_problem_id(p.id),
            'title': p.title,
            'description': p.description[:200] if p.description else '',
            'category': p.category.name if p.category else None
        })
    return jsonify(results)
@api_bp.route('/products/<product_id>/problems', methods=['GET'])
def get_problems(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return jsonify([]), 404
    
    # 获取该产品下的所有问题
    problems = Problem.query.filter_by(product_id=real_id).order_by(Problem.created_at.desc()).all()
    
    results = []
    for p in problems:
        results.append({
            'id': id_crypt.encrypt_problem_id(p.id),
            'title': p.title,
            'description': p.description[:200] if p.description else '',
            'category': p.category.name if p.category else None,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(results)

@api_bp.route('/problems/<encrypted_id>', methods=['GET'])
def get_problem_detail(encrypted_id):
    # 解密ID
    problem_id = id_crypt.decrypt_problem_id(encrypted_id)
    if problem_id is None:
        return jsonify({'error': 'Invalid problem ID'}), 404
    
    problem = Problem.query.get_or_404(problem_id)
    
    solutions = []
    related_cards = []  # 关联的解决方案卡片
    
    if problem.category:
        if problem.category.name == '报错快速查询':
            # 快速查询类型：解析solution中的引用，找到关联的解决方案卡片
            if problem.solution:  # solution列包含"附表X-Y 标题"格式的引用
                references = problem.solution.split('\n')
                for ref in references:
                    ref = ref.strip()
                    if not ref:
                        continue
                    
                    # 解析引用格式：附表X-Y 标题
                    match = re.match(r'附表(\d+)-(\d+)\s+(.*)', ref)
                    if match:
                        table_num = int(match.group(1))
                        entry_num = int(match.group(2))
                        entry_title = match.group(3)
                        
                        # 查找对应的解决方案卡片
                        card = SolutionCard.query.filter_by(
                            table_num=table_num,
                            sequence=entry_num
                        ).first()
                        
                        if card:
                            related_cards.append({
                                'id': id_crypt.encrypt_card_id(card.id),  # 加密ID
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
            
            solutions.append({
                'type': 'quick_lookup',
                'cards': related_cards
            })
        else:
            # 普通问题类型：直接显示描述和解决方案
            solutions.append({
                'type': 'normal',
                'description': problem.description,
                'solution': problem.solution if problem.solution else ''
            })
    
    # Build description with image if present
    desc_with_image = problem.description if problem.description else ''
    if problem.image_references:
        img_tag = f'<img src="/api/images/{problem.image_references}" alt="问题截图" style="max-width:100%; height:auto;">'
        if desc_with_image:
            desc_with_image += '\n' + img_tag
        else:
            desc_with_image = img_tag
    
    return jsonify({
        'id': id_crypt.encrypt_problem_id(problem.id),  # 返回加密ID
        'title': problem.title,
        'description': desc_with_image,
        'category': problem.category.name if problem.category else None,
        'screenshot': problem.screenshot_path,
        'solutions': solutions,
        'related_cards': related_cards  # 返回关联的解决方案卡片
    })

@api_bp.route('/images/<image_id>', methods=['GET'])
def get_image(image_id):
    """返回存储的图片"""
    image = Image.query.filter_by(image_id=image_id).first_or_404()
    return (
        base64.b64decode(image.image_data),
        200,
        {'Content-Type': image.content_type}
    )

@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """提交用户反馈（支持多文件和压缩包）"""
    try:
        # 获取表单数据
        product_id = request.form.get('product_id')
        product_name = request.form.get('product_name')
        description = request.form.get('description')
        contact = request.form.get('contact', '')
        
        if not product_id or not product_name or not description:
            return jsonify({'error': '缺少必填参数'}), 400
        
        # 解密产品ID
        real_product_id = id_crypt.decrypt_product_id(product_id)
        if real_product_id is None:
            # 如果不是加密ID，尝试直接作为整数
            try:
                real_product_id = int(product_id)
            except (ValueError, TypeError):
                return jsonify({'error': '无效的产品ID'}), 400
        
        # 处理多文件上传
        uploaded_files = []  # 存储 (type, path) 元组
        
        # 处理 images 字段（多文件）
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    if allowed_image(file.filename):
                        upload_dir = ensure_upload_dir()
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
                        filepath = os.path.join(upload_dir, unique_filename)
                        file.save(filepath)
                        uploaded_files.append(('image', os.path.join('uploads', 'feedback', unique_filename)))
                    else:
                        logger.warning(f"不允许的图片类型: {file.filename}")
        
        # 处理 archives 字段（多文件）
        if 'archives' in request.files:
            files = request.files.getlist('archives')
            for file in files:
                if file and file.filename:
                    if allowed_archive(file.filename):
                        upload_dir = ensure_upload_dir()
                        filename = secure_filename(file.filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
                        filepath = os.path.join(upload_dir, unique_filename)
                        file.save(filepath)
                        uploaded_files.append(('archive', os.path.join('uploads', 'feedback', unique_filename)))
                    else:
                        logger.warning(f"不允许的压缩包类型: {file.filename}")
        
        # 保存文件列表为JSON
        import json
        image_paths_json = json.dumps(uploaded_files) if uploaded_files else None
        
        # 保存到数据库
        feedback = Feedback(
            product_id=real_product_id,
            product_name=product_name,
            description=description,
            image_paths=image_paths_json,
            contact=contact
        )
        db.session.add(feedback)
        db.session.commit()
        
        logger.info(f"收到反馈: 产品={product_name}, 文件数={len(uploaded_files)}, ID={feedback.id}")
        
        return jsonify({
            'success': True,
            'message': '反馈提交成功，我们会尽快处理'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交反馈失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': '提交失败，请稍后重试'}), 500

@api_bp.route('/feedback-images/<path:filename>')
def serve_feedback_image(filename):
    """提供反馈截图"""
    try:
        upload_dir = app.config.get('UPLOAD_FOLDER', os.path.join(app.config.get('basedir', '.'), 'uploads', 'feedback'))
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
        logger.error(f"提供截图失败 {filename}: {str(e)}")
        return 'Error', 500

@page_bp.route('/')
def index():
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    # 转换为加密ID的字典列表
    products_data = [{
        'id': id_crypt.encrypt_product_id(p.id),
        'name': p.name,
        'logo': p.logo_data
    } for p in products]
    return render_template('index.html', products=products_data)

@page_bp.route('/product/<product_id>')
def product_detail(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return 'Invalid product ID', 404
    product = Product.query.get_or_404(real_id)
    # 传递加密ID给模板
    return render_template('product.html', product={'id': product_id, 'name': product.name, 'logo_data': product.logo_data, 'description': product.description}, encrypted_id=product_id)

@page_bp.route('/product/<product_id>/quick-lookup')
def quick_lookup(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return 'Invalid product ID', 404
    product = Product.query.get_or_404(real_id)
    # 传递加密ID给模板
    return render_template('quick_lookup.html', product={'id': product_id, 'name': product.name}, encrypted_id=product_id)

@page_bp.route('/product/<product_id>/problems')
def all_problems(product_id):
    # 解密产品ID
    real_id = id_crypt.decrypt_product_id(product_id)
    if real_id is None:
        return 'Invalid product ID', 404
    product = Product.query.get_or_404(real_id)
    categories = Category.query.order_by(Category.sort_order).all()
    # 传递加密ID给模板
    return render_template('all_problems.html', product={'id': product_id, 'name': product.name}, categories=categories, encrypted_id=product_id)

@page_bp.route('/problem/<encrypted_id>')
def problem_detail(encrypted_id):
    # 解密ID
    problem_id = id_crypt.decrypt_problem_id(encrypted_id)
    if problem_id is None:
        return 'Invalid problem ID', 404
    
    problem = Problem.query.get_or_404(problem_id)
    # 传递加密ID和problem对象给模板
    return render_template('problem_detail.html', problem=problem, encrypted_id=encrypted_id)

# 新增：分类问题页面路由
@page_bp.route('/category/<int:category_id>/problems')
def category_problems(category_id):
    return render_template('category_problems.html', category_id=category_id)

# 注册蓝图
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(page_bp)

# 创建数据库表
with app.app_context():
    db.create_all()

# 自动清理超过10天的截图文件
def cleanup_old_feedback_images():
    """清理超过10天的反馈截图"""
    try:
        import glob
        
        upload_dir = app.config.get('UPLOAD_FOLDER')
        if not os.path.exists(upload_dir):
            # 尝试创建目录（生产环境可能需要手动创建）
            try:
                os.makedirs(upload_dir, exist_ok=True)
                logger.info(f"创建上传目录: {upload_dir}")
            except Exception as e:
                logger.warning(f"无法创建上传目录 {upload_dir}: {str(e)}")
            return
        
        # 获取当前时间10天前的时间戳
        cutoff_time = time.time() - (10 * 24 * 60 * 60)  # 10天
        
        # 遍历上传目录中的所有文件
        for filepath in glob.glob(os.path.join(upload_dir, '*')):
            if os.path.isfile(filepath):
                # 检查文件修改时间
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        logger.info(f"清理过期截图: {filepath}")
                    except Exception as e:
                        logger.error(f"删除文件失败 {filepath}: {str(e)}")
    except Exception as e:
        logger.error(f"清理过期截图时出错: {str(e)}")

# 在应用启动时执行一次清理
with app.app_context():
    cleanup_old_feedback_images()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=12001)
