from flask import Blueprint, request, jsonify
from models import Product, Category, Problem, QuickLookup, SolutionCard, AdminLog
import re
import traceback

# 延迟导入db, app, id_crypt以避免循环导入
def _get_app_components():
    from app_single import app, id_crypt
    # 使用models模块的db实例，而不是从app_single重新导入
    from models import db
    return db, app, id_crypt

api_bp = Blueprint('api', __name__)

# 产品相关API
@api_bp.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
        return jsonify([{
            'id': p.id,
            'name': p.name
        } for p in products])
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'categories': [{
                'id': c.id,
                'name': c.name
            } for c in product.categories]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 快速查询API
@api_bp.route('/products/<int:product_id>/quick-lookup', methods=['GET'])
def get_quick_lookup(product_id):
    try:
        keyword = request.args.get('q', '')
        query = QuickLookup.query.filter_by(product_id=product_id, is_active=True)

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
                        'id': problem.id,
                        'title': problem.title,
                        'description': problem.description[:100] if problem.description else '',
                        'category': problem.category.name if problem.category else None
                    }
                })

        return jsonify(results)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 全量问题API - 返回问题和解决方案卡片
@api_bp.route('/products/<int:product_id>/problems', methods=['GET'])
def get_problems(product_id):
    try:
        category_id = request.args.get('category')
        keyword = request.args.get('q', '')

        # 1. 获取所有问题（Problem）
        problem_query = Problem.query.filter_by(product_id=product_id)
        if category_id:
            problem_query = problem_query.filter_by(category_id=category_id)
        if keyword:
            problem_query = problem_query.filter(
                (Problem.title.contains(keyword)) |
                (Problem.description.contains(keyword))
            )
        problems = problem_query.all()

        # 2. 获取所有解决方案卡片（SolutionCard）
        cards = SolutionCard.query.all()  # 卡片没有product_id关联，获取全部

        # 3. 合并结果
        results = []

        # 添加问题到结果
        for problem in problems:
            results.append({
                'type': 'problem',
                'id': problem.id,
                'title': problem.title,
                'description': problem.description[:200] if problem.description else '',
                'solution': problem.solution[:200] if problem.solution else '',
                'category': problem.category.name if problem.category else None
            })

        # 添加解决方案卡片到结果
        for card in cards:
            results.append({
                'type': 'card',
                'id': card.id,
                'table_num': card.table_num,
                'sequence': card.sequence,
                'title': card.title,
                'fault_type': card.fault_type,
                'phenomenon': card.phenomenon,
                'steps': card.steps,
                'solution': card.solution,
                'supplement': card.supplement
            })

        return jsonify(results)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 问题详情API
@api_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_detail(problem_id):
    try:
        problem = Problem.query.get_or_404(problem_id)

        # 获取关联的解决方案
        solutions = []
        if problem.category:
            if problem.category.name == '报错快速查询':
                # 从解决方法字段提取关联的卡片引用
                if problem.solution:
                    # problem.solution 包含类似 "附表2-1 核查设备 / 系统不在配置核查工具兼容范围内\n附表2-2 ..."
                    references = problem.solution.split('\n')
                    cards = []
                    for ref in references:
                        ref = ref.strip()
                        if not ref:
                            continue
                        # 解析 "附表X-Y 标题" 格式
                        # 例如: "附表2-1 核查设备 / 系统不在配置核查工具兼容范围内"
                        try:
                            # 提取表号和序号
                            match = re.match(r'附表(\d)-(\d+)\s*(.*)', ref)
                            if match:
                                table_num = int(match.group(1))
                                sequence = int(match.group(2))
                                title_filter = match.group(3).strip()

                                # 从 solution_cards 表中查找匹配的卡片
                                card = SolutionCard.query.filter_by(
                                    table_num=table_num,
                                    sequence=sequence
                                ).first()

                                if card:
                                    cards.append(card)
                        except Exception as e:
                            # 如果解析失败，尝试通过标题模糊匹配
                            if ref:
                                card = SolutionCard.query.filter(
                                    SolutionCard.title.contains(ref[:30])
                                ).first()
                                if card:
                                    cards.append(card)

                    if cards:
                        solutions.append({
                            'type': 'quick_lookup',
                            'cards': [card.to_dict() for card in cards]
                        })
            else:
                # 普通问题类型：直接显示描述和解决方案
                solutions.append({
                    'type': 'normal',
                    'description': problem.description,
                    'solution': problem.solution if problem.solution else ''
                })

        # 同时获取通过多对多关系关联的卡片
        if hasattr(problem, 'solution_cards') and problem.solution_cards:
            cards_data = [card.to_dict() for card in problem.solution_cards]
            if cards_data:
                # 检查是否已经存在 quick_lookup 类型
                has_quick_lookup = any(s.get('type') == 'quick_lookup' for s in solutions)
                if not has_quick_lookup:
                    solutions.append({
                        'type': 'quick_lookup',
                        'cards': cards_data
                    })
                else:
                    # 合并到现有的 quick_lookup 中
                    for sol in solutions:
                        if sol.get('type') == 'quick_lookup':
                            sol['cards'].extend(cards_data)
                            break

        return jsonify({
            'id': problem.id,
            'title': problem.title,
            'description': problem.description,
            'category': problem.category.name if problem.category else None,
            'screenshot': problem.screenshot_path,
            'solutions': solutions
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# 分类API
@api_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.order_by(Category.sort_order).all()
        return jsonify([{
            'id': c.id,
            'name': c.name
        } for c in categories])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ 解决方案卡片API ============

@api_bp.route('/products/<int:product_id>/solution-cards', methods=['GET'])
def get_product_solution_cards(product_id):
    """获取产品关联的所有解决方案卡片"""
    try:
        db, app, id_crypt = _get_app_components()

        # 验证产品是否存在
        product = Product.query.get_or_404(product_id)

        # 获取所有解决方案卡片，按表号和序号排序
        cards = SolutionCard.query.order_by(
            SolutionCard.table_num,
            SolutionCard.sequence
        ).all()

        # 按表号分组
        cards_by_table = {}
        for card in cards:
            table_key = f"表{card.table_num}"
            if table_key not in cards_by_table:
                cards_by_table[table_key] = []
            cards_by_table[table_key].append(card)

        # 构建响应
        result = {
            'product': {
                'id': product.id,
                'name': product.name
            },
            'total_cards': len(cards),
            'tables': []
        }

        # 按表号顺序添加
        for table_key in sorted(cards_by_table.keys()):
            table_cards = cards_by_table[table_key]
            table_data = {
                'table_name': table_key,
                'table_num': table_cards[0].table_num,
                'card_count': len(table_cards),
                'cards': [{
                    'id': card.id,
                    'table_num': card.table_num,
                    'sequence': card.sequence,
                    'title': card.title,
                    'fault_type': card.fault_type,
                    'phenomenon': card.phenomenon,
                    'steps': card.steps,
                    'solution': card.solution,
                    'supplement': card.supplement,
                    'category': card.card_category.name if card.card_category else None
                } for card in table_cards]
            }
            result['tables'].append(table_data)

        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
