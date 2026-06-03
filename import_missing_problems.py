#!/usr/bin/env python3
"""
从原始Excel导入缺失的问题，并建立与解决方案卡片的关联
使用urllib方式，避免依赖requests
"""
import pandas as pd
import urllib.request
import urllib.error
import json
import re
import http.cookiejar

def import_missing_problems():
    excel_path = '/mnt/c/Users/86279/Desktop/现场问题解决方案.xls'
    admin_base_url = 'http://localhost:12002'
    
    # 设置cookie处理器
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    # 先登录管理后台
    login_data = json.dumps({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
    req = urllib.request.Request(
        f'{admin_base_url}/login',
        data=login_data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        response = opener.open(req)
        result = json.loads(response.read().decode('utf-8'))
        if not result.get('success'):
            print('登录失败')
            return
        print('✓ 管理后台登录成功')
    except urllib.error.HTTPError as e:
        print(f'登录失败: {e.code} {e.reason}')
        return
    
    # 读取Excel
    df_quick = pd.read_excel(excel_path, sheet_name='报错快速查询')
    
    # 获取产品信息
    req = urllib.request.Request(f'{admin_base_url}/api/products')
    response = opener.open(req)
    products = json.loads(response.read().decode('utf-8'))
    product = next((p for p in products if p['name'] == '配置核查工具'), None)
    if not product:
        print('错误：找不到"配置核查工具"产品')
        return
    
    product_id = product['raw_id']
    print(f'产品: {product["name"]} (ID: {product_id})')
    
    # 获取分类列表
    req = urllib.request.Request(f'{admin_base_url}/api/categories')
    response = opener.open(req)
    categories = json.loads(response.read().decode('utf-8'))
    category = next((c for c in categories if c['name'] == '报错快速查询' and c['product_id'] == product_id), None)
    
    if not category:
        # 创建分类
        cat_data = json.dumps({
            'name': '报错快速查询',
            'product_id': product_id,
            'sort_order': 1,
            'is_active': True
        }).encode('utf-8')
        req = urllib.request.Request(
            f'{admin_base_url}/api/categories',
            data=cat_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        response = opener.open(req)
        category = json.loads(response.read().decode('utf-8'))
        print(f'✓ 创建分类: {category["name"]} (ID: {category["id"]})')
    else:
        print(f'分类: {category["name"]} (ID: {category["id"]})')
    
    category_id = category['id']
    
    # 获取现有问题列表
    req = urllib.request.Request(f'{admin_base_url}/api/problems')
    response = opener.open(req)
    existing_problems = json.loads(response.read().decode('utf-8'))
    existing_titles = {p['title'] for p in existing_problems}
    
    print(f'现有问题数: {len(existing_problems)}')
    for title in existing_titles:
        print(f'  - {title}')
    print()
    
    # 获取所有解决方案卡片
    req = urllib.request.Request(f'{admin_base_url}/api/solution-cards')
    response = opener.open(req)
    all_cards = json.loads(response.read().decode('utf-8'))
    
    # 遍历Excel中的所有问题
    imported_count = 0
    for idx, row in df_quick.iterrows():
        title = row['问题']
        solution_refs = row['解决方法']
        
        # 如果问题已存在，跳过
        if title in existing_titles:
            print(f'跳过已存在问题: {title}')
            continue
        
        # 创建新问题
        problem_data = json.dumps({
            'title': title,
            'description': f'关于"{title}"的问题描述',
            'solution': solution_refs,
            'product_id': product_id,
            'category_id': category_id
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f'{admin_base_url}/api/problems',
            data=problem_data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        try:
            response = opener.open(req)
            problem = json.loads(response.read().decode('utf-8'))
            imported_count += 1
            print(f'✓ 导入问题: {title}')
            
            # 解析解决方案卡片引用并关联
            refs = re.findall(r'附表([1-3])-(\d+)', solution_refs)
            if refs:
                print(f'  关联解决方案卡片:')
                for appendix_num, seq_num in refs:
                    appendix_num = int(appendix_num)
                    seq_num = int(seq_num)
                    
                    # 查找对应的卡片
                    card = next((c for c in all_cards if c['table_num'] == appendix_num and c['sequence'] == seq_num), None)
                    
                    if card:
                        print(f'    ✓ 附表{appendix_num}-{seq_num}: {card["title"]}')
                    else:
                        print(f'    ✗ 附表{appendix_num}-{seq_num}: 卡片不存在')
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            print(f'✗ 导入失败: {title} - {e.code} {e.reason} {error_body}')
        
        print()
    
    # 最终统计
    req = urllib.request.Request(f'{admin_base_url}/api/problems')
    response = opener.open(req)
    final_problems = json.loads(response.read().decode('utf-8'))
    
    print(f'\n=== 导入完成 ===')
    print(f'新导入问题数: {imported_count}')
    print(f'配置核查工具总问题数: {len([p for p in final_problems if p.get("product_id") == product_id])}')
    
    # 显示所有问题
    product_problems = [p for p in final_problems if p.get('product_id') == product_id]
    for p in sorted(product_problems, key=lambda x: x['id']):
        print(f'  - {p["title"]}')

if __name__ == '__main__':
    import_missing_problems()
