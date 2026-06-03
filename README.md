# 现场问题解决方案管理系统

杭州盾源科技有限公司开发的现场问题查询和管理平台。

## 功能特性

- **产品选择**：支持多产品线管理
- **快速查询**：关键词搜索，快速定位问题
- **全量问题**：按分类浏览所有问题
- **问题详情**：完整的问题描述和解决方案
- **品牌定制**：支持公司名称和logo配置

## 快速开始

### 安装依赖

```bash
cd /mnt/c/Users/86279/problem-solution-system
python3 -m venv venv
./venv/bin/pip install -r requirements.txt --break-system-packages
```

### 初始化数据库

```bash
./venv/bin/python init_db.py
```

### 启动应用

```bash
./start.sh
```

或者手动启动：

```bash
./venv/bin/python run.py
```

### 访问系统

打开浏览器访问：http://localhost:5000

## 项目结构

```
problem-solution-system/
├── app_single.py        # 主应用（单文件版本）
├── run.py               # 生产启动脚本
├── start.sh             # 启动脚本
├── config.py            # 配置文件
├── init_db.py           # 数据库初始化
├── requirements.txt     # 依赖包
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
└── instance/
    └── problems.db      # SQLite数据库
```

## 技术栈

- **后端**：Flask + SQLAlchemy
- **数据库**：SQLite
- **前端**：原生HTML/CSS/JavaScript
- **部署**：支持WSL/Windows/Linux

## 数据来源

系统数据来自桌面文件：`现场问题解决方案.xls`

包含以下分类：
- 报错快速查询
- 物理环境问题现场排查
- 被核查资产现场问题排查
- 网络问题排查

## 公司信息

**杭州盾源科技有限公司**

---

如有问题，请联系技术支持。