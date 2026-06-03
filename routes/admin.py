#!/usr/bin/env python3
"""
管理员后台路由
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from datetime import datetime
import json

from models import db, Admin, AdminLog, Product, Category, Problem, QuickLookup, SolutionCard
from utils.auth import admin_auth

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin', static_folder='static/admin')

# ============ 认证相关 ============

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '')
    password = data.get('password', '')
    
    admin, error = admin_auth.authenticate(username, password)
    if admin:
        admin_auth.login_admin(admin)
        if request.is_json:
            return jsonify({'success': True, 'message': '登录成功'})
        return redirect(url_for('admin.dashboard'))
    else:
        if request.is_json:
            return jsonify({'success': False, 'message': error or '登录失败'}), 401
        flash(error or '用户名或密码错误', 'error')
        return redirect(url_for('admin.login'))

@admin_bp.route('/logout')
def logout():
    """管理员登出"""
    admin_auth.logout_admin()
    return redirect(url_for('admin.login'))

# ============ 仪表盘 ============

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_auth.login_required
def dashboard():
    """管理后台首页"""
    # 统计数据
    product_count = Product.query.count()
    problem_count = Problem.query.count()
    card_count = SolutionCard.query.count()
    category_count = Category.query.count()
    
    # 最近操作日志
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         product_count=product_count,
                         problem_count=problem_count,
                         card_count=card_count,
                         category_count=category_count,
                         recent_logs=recent_logs)

# ============ 产品管理 ============

@admin_bp.route('/products')
@admin_auth.login_required
def products():
    """产品列表"""
    products = Product.query.order_by(Product.sort_order, Product.id).all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/api/products', methods=['GET'])
@admin_auth.login_required
def api_products():
    """获取产品列表API"""
    products = Product.query.order_by(Product.sort_order, Product.id).all()
    return jsonify([p.to_dict() for p in products])

@admin_bp.route('/api/products', methods=['POST'])
@admin_auth.login_required
def create_product():
    """创建产品API"""
    data = request.get_json()
    
    product = Product(
        name=data.get('name', ''),
        description=data.get('description', ''),
        logo_data=data.get('logo_data', ''),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(product)
    db.session.commit()
    
    admin_auth.log_operation('create', 'product', product.id, {'name': product.name})
    
    return jsonify(product.to_dict()), 201

@admin_bp.route('/api/products/<int:product_id>', methods=['GET'])
@admin_auth.login_required
def get_product(product_id):
    """获取单个产品API"""
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@admin_bp.route('/api/products/<int:product_id>', methods=['PUT'])
@admin_auth.login_required
def update_product(product_id):
    """更新产品API"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.logo_data = data.get('logo_data', product.logo_data)
    product.sort_order = data.get('sort_order', product.sort_order)
    product.is_active = data.get('is_active', product.is_active)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'product', product.id, {'name': product.name})
    
    return jsonify(product.to_dict())

@admin_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
@admin_auth.login_required
def delete_product(product_id):
    """删除产品API"""
    product = Product.query.get_or_404(product_id)
    
    db.session.delete(product)
    db.session.commit()
    
    admin_auth.log_operation('delete', 'product', product_id, {'name': product.name})
    
    return jsonify({'success': True})

# ============ 分类管理 ============

@admin_bp.route('/categories')
@admin_auth.login_required
def categories():
    """分类列表"""
    categories = Category.query.order_by(Category.product_id, Category.sort_order).all()
    products = Product.query.all()
    return render_template('admin/categories.html', categories=categories, products=products)

@admin_bp.route('/api/categories', methods=['GET'])
@admin_auth.login_required
def api_categories():
    """获取分类列表API"""
    categories = Category.query.order_by(Category.product_id, Category.sort_order).all()
    return jsonify([c.to_dict() for c in categories])

@admin_bp.route('/api/categories', methods=['POST'])
@admin_auth.login_required
def create_category():
    """创建分类API"""
    data = request.get_json()
    
    category = Category(
        name=data.get('name', ''),
        description=data.get('description', ''),
        product_id=data.get('product_id'),
        sort_order=data.get('sort_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(category)
    db.session.commit()
    
    admin_auth.log_operation('create', 'category', category.id, {'name': category.name})
    
    return jsonify(category.to_dict()), 201

@admin_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@admin_auth.login_required
def update_category(category_id):
    """更新分类API"""
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.product_id = data.get('product_id', category.product_id)
    category.sort_order = data.get('sort_order', category.sort_order)
    category.is_active = data.get('is_active', category.is_active)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'category', category_id, {'name': category.name})
    
    return jsonify(category.to_dict())

@admin_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@admin_auth.login_required
def delete_category(category_id):
    """删除分类API"""
    category = Category.query.get_or_404(category_id)
    
    db.session.delete(category)
    db.session.commit()
    
    admin_auth.log_operation('delete', 'category', category_id, {'name': category.name})
    
    return jsonify({'success': True})

# ============ 问题管理 ============

@admin_bp.route('/problems')
@admin_auth.login_required
def problems():
    """问题列表"""
    problems = Problem.query.order_by(Problem.id.desc()).all()
    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin/problems.html', problems=problems, products=products, categories=categories)

@admin_bp.route('/api/problems', methods=['GET'])
@admin_auth.login_required
def api_problems():
    """获取问题列表API"""
    problems = Problem.query.order_by(Problem.id.desc()).all()
    return jsonify([p.to_dict() for p in problems])

@admin_bp.route('/api/problems', methods=['POST'])
@admin_auth.login_required
def create_problem():
    """创建问题API"""
    data = request.get_json()
    
    problem = Problem(
        title=data.get('title', ''),
        description=data.get('description', ''),
        solution=data.get('solution', ''),
        product_id=data.get('product_id'),
        category_id=data.get('category_id'),
        screenshot_path=data.get('screenshot_path', ''),
        image_references=data.get('image_references', '')
    )
    
    db.session.add(problem)
    db.session.commit()
    
    admin_auth.log_operation('create', 'problem', problem.id, {'title': problem.title})
    
    return jsonify(problem.to_dict()), 201

@admin_bp.route('/api/problems/<int:problem_id>', methods=['PUT'])
@admin_auth.login_required
def update_problem(problem_id):
    """更新问题API"""
    problem = Problem.query.get_or_404(problem_id)
    data = request.get_json()
    
    problem.title = data.get('title', problem.title)
    problem.description = data.get('description', problem.description)
    problem.solution = data.get('solution', problem.solution)
    problem.product_id = data.get('product_id', problem.product_id)
    problem.category_id = data.get('category_id', problem.category_id)
    problem.screenshot_path = data.get('screenshot_path', problem.screenshot_path)
    problem.image_references = data.get('image_references', problem.image_references)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'problem', problem_id, {'title': problem.title})
    
    return jsonify(problem.to_dict())

@admin_bp.route('/api/problems/<int:problem_id>', methods=['DELETE'])
@admin_auth.login_required
def delete_problem(problem_id):
    """删除问题API"""
    problem = Problem.query.get_or_404(problem_id)
    
    db.session.delete(problem)
    db.session.commit()
    
    admin_auth.log_operation('delete', 'problem', problem_id, {'title': problem.title})
    
    return jsonify({'success': True})

# ============ 解决方案卡片管理 ============

@admin_bp.route('/solution-cards')
@admin_auth.login_required
def solution_cards():
    """解决方案卡片列表"""
    cards = SolutionCard.query.order_by(SolutionCard.table_num, SolutionCard.sequence).all()
    return render_template('admin/solution_cards.html', cards=cards)

@admin_bp.route('/api/solution-cards', methods=['GET'])
@admin_auth.login_required
def api_solution_cards():
    """获取解决方案卡片API"""
    cards = SolutionCard.query.order_by(SolutionCard.table_num, SolutionCard.sequence).all()
    return jsonify([c.to_dict() for c in cards])

@admin_bp.route('/api/solution-cards', methods=['POST'])
@admin_auth.login_required
def create_solution_card():
    """创建解决方案卡片API"""
    data = request.get_json()
    
    card = SolutionCard(
        title=data.get('title', ''),
        table_num=data.get('table_num', 1),
        sequence=data.get('sequence', 0),
        fault_type=data.get('fault_type', ''),
        phenomenon=data.get('phenomenon', ''),
        steps=data.get('steps', ''),
        solution=data.get('solution', ''),
        supplement=data.get('supplement', '')
    )
    
    db.session.add(card)
    db.session.commit()
    
    admin_auth.log_operation('create', 'solution_card', card.id, {'title': card.title})
    
    return jsonify(card.to_dict()), 201

@admin_bp.route('/api/solution-cards/<int:card_id>', methods=['PUT'])
@admin_auth.login_required
def update_solution_card(card_id):
    """更新解决方案卡片API"""
    card = SolutionCard.query.get_or_404(card_id)
    data = request.get_json()
    
    card.title = data.get('title', card.title)
    card.table_num = data.get('table_num', card.table_num)
    card.sequence = data.get('sequence', card.sequence)
    card.fault_type = data.get('fault_type', card.fault_type)
    card.phenomenon = data.get('phenomenon', card.phenomenon)
    card.steps = data.get('steps', card.steps)
    card.solution = data.get('solution', card.solution)
    card.supplement = data.get('supplement', card.supplement)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'solution_card', card_id, {'title': card.title})
    
    return jsonify(card.to_dict())

@admin_bp.route('/api/solution-cards/<int:card_id>', methods=['DELETE'])
@admin_auth.login_required
def delete_solution_card(card_id):
    """删除解决方案卡片API"""
    card = SolutionCard.query.get_or_404(card_id)
    
    db.session.delete(card)
    db.session.commit()
    
    admin_auth.log_operation('delete', 'solution_card', card_id, {'title': card.title})
    
    return jsonify({'success': True})

# ============ 快速查询管理 ============

@admin_bp.route('/quick-lookups')
@admin_auth.login_required
def quick_lookups():
    """快速查询列表"""
    lookups = QuickLookup.query.order_by(QuickLookup.display_order, QuickLookup.id).all()
    products = Product.query.all()
    problems = Problem.query.all()
    return render_template('admin/quick_lookups.html', lookups=lookups, products=products, problems=problems)

@admin_bp.route('/api/quick-lookups', methods=['GET'])
@admin_auth.login_required
def api_quick_lookups():
    """获取快速查询列表API"""
    lookups = QuickLookup.query.order_by(QuickLookup.display_order, QuickLookup.id).all()
    return jsonify([l.to_dict() for l in lookups])

@admin_bp.route('/api/quick-lookups', methods=['POST'])
@admin_auth.login_required
def create_quick_lookup():
    """创建快速查询API"""
    data = request.get_json()
    
    lookup = QuickLookup(
        keyword=data.get('keyword', ''),
        product_id=data.get('product_id'),
        problem_id=data.get('problem_id'),
        display_order=data.get('display_order', 0),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(lookup)
    db.session.commit()
    
    admin_auth.log_operation('create', 'quick_lookup', lookup.id, {'keyword': lookup.keyword})
    
    return jsonify(lookup.to_dict()), 201

@admin_bp.route('/api/quick-lookups/<int:lookup_id>', methods=['PUT'])
@admin_auth.login_required
def update_quick_lookup(lookup_id):
    """更新快速查询API"""
    lookup = QuickLookup.query.get_or_404(lookup_id)
    data = request.get_json()
    
    lookup.keyword = data.get('keyword', lookup.keyword)
    lookup.product_id = data.get('product_id', lookup.product_id)
    lookup.problem_id = data.get('problem_id', lookup.problem_id)
    lookup.display_order = data.get('display_order', lookup.display_order)
    lookup.is_active = data.get('is_active', lookup.is_active)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'quick_lookup', lookup_id, {'keyword': lookup.keyword})
    
    return jsonify(lookup.to_dict())

@admin_bp.route('/api/quick-lookups/<int:lookup_id>', methods=['DELETE'])
@admin_auth.login_required
def delete_quick_lookup(lookup_id):
    """删除快速查询API"""
    lookup = QuickLookup.query.get_or_404(lookup_id)
    
    db.session.delete(lookup)
    db.session.commit()
    
    admin_auth.log_operation('delete', 'quick_lookup', lookup_id, {'keyword': lookup.keyword})
    
    return jsonify({'success': True})

# ============ 操作日志 ============

@admin_bp.route('/logs')
@admin_auth.login_required
def logs():
    """操作日志列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/api/logs', methods=['GET'])
@admin_auth.login_required
def api_logs():
    """获取操作日志API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })

# ============ 管理员管理 ============

@admin_bp.route('/profile')
@admin_auth.login_required
def profile():
    """管理员个人资料"""
    admin = admin_auth.get_current_admin()
    return render_template('admin/profile.html', admin=admin)

@admin_bp.route('/api/profile', methods=['PUT'])
@admin_auth.login_required
def update_profile():
    """更新管理员资料API"""
    admin = admin_auth.get_current_admin()
    data = request.get_json()
    
    admin.email = data.get('email', admin.email)
    
    # 修改密码
    new_password = data.get('password')
    if new_password:
        admin.password_hash = generate_password_hash(new_password)
    
    db.session.commit()
    
    admin_auth.log_operation('update', 'admin', admin.id, {'action': 'update_profile'})
    
    return jsonify(admin.to_dict())
