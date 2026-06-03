from flask import Blueprint, render_template
from models import Product, Category, Problem

page_bp = Blueprint('pages', __name__)

@page_bp.route('/')
def index():
    products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
    return render_template('index.html', products=products)

@page_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@page_bp.route('/product/<int:product_id>/quick-lookup')
def quick_lookup(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('quick_lookup.html', product=product)

@page_bp.route('/product/<int:product_id>/problems')
def all_problems(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('all_problems.html', product=product, categories=categories)

@page_bp.route('/problem/<int:problem_id>')
def problem_detail(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    return render_template('problem_detail.html', problem=problem)