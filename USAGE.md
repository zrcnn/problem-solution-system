# 现场问题解决方案管理系统 - 使用文档

## 快速开始

### 1. 启动服务

```bash
cd /mnt/c/Users/86279/problem-solution-system
./service.sh start
```

### 2. 访问系统

打开浏览器访问：http://localhost:5000

### 3. 系统功能

#### 首页 - 产品选择
- 显示所有可用产品
- 当前产品：配置核查工具

#### 产品详情页
- **快速查询**：通过关键词快速定位问题
- **全量问题**：按分类浏览所有问题

#### 快速查询页
- 输入关键词搜索（如：IP、账密、SSH等）
- 实时显示匹配结果
- 点击结果查看详情

#### 全量问题页
- 按分类展示问题
- 支持分类筛选
- 支持关键词搜索

#### 问题详情页
- 完整问题描述
- 解决方案
- 相关截图（如有）

## 服务管理

```bash
# 查看服务状态
./service.sh status

# 启动服务
./service.sh start

# 停止服务
./service.sh stop

# 重启服务
./service.sh restart

# 查看日志
./service.sh logs
```

## 数据管理

### 数据库位置
`/mnt/c/Users/86279/problem-solution-system/problems.db`

### 重新初始化数据
```bash
./venv/bin/python init_db.py
```

## 系统配置

### 公司信息
- 公司名称：杭州盾源科技有限公司
- 系统名称：现场问题解决方案管理系统
- 版本：1.0.0

### 配置文件
`config.py` - 可以修改公司名称、系统标题等

## 技术架构

- **后端**: Flask (Python)
- **数据库**: SQLite
- **前端**: HTML5 + CSS3 + JavaScript
- **部署**: 支持WSL/Windows/Linux

## 常见问题

### Q: 服务无法启动
A: 检查端口5000是否被占用，运行 `./service.sh stop` 停止旧服务后再启动

### Q: 数据丢失
A: 运行 `./venv/bin/python init_db.py` 重新初始化数据库

### Q: 如何添加新产品
A: 在数据库中插入新产品记录，然后添加对应的问题数据

### Q: 如何修改公司信息
A: 编辑 `config.py` 文件中的 `COMPANY_NAME` 等配置

## 项目结构

```
problem-solution-system/
├── app_single.py        # 主应用（单文件版本）
├── run.py               # 生产启动脚本
├── service.sh           # 服务管理脚本
├── start.sh             # 快速启动脚本
├── config.py            # 配置文件
├── init_db.py           # 数据库初始化脚本
├── requirements.txt     # Python依赖
├── static/              # 静态资源
│   ├── css/style.css
│   └── js/main.js
├── templates/           # HTML模板
│   ├── base.html
│   ├── index.html
│   ├── product.html
│   ├── quick_lookup.html
│   ├── all_problems.html
│   └── problem_detail.html
├── problems.db          # SQLite数据库
└── venv/                # Python虚拟环境
```

## 技术支持

如有问题，请联系杭州盾源科技有限公司技术支持团队。

---

**杭州盾源科技有限公司** © 2024