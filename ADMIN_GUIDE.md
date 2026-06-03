# 管理员后台使用指南

## 访问方式

管理员后台运行在独立的端口上，与主问题解决系统完全分离，互不影响。

### 访问地址
```
http://localhost:12002/login
```

### 默认账户
- **用户名**: admin
- **密码**: admin123

⚠️ **重要**: 首次登录后请立即修改密码！

## 启动方式

### 手动启动
```bash
cd /mnt/d/PROJECT/problem-solution-system
python3 admin_app.py
```

### 使用启动脚本
```bash
./scripts/start_admin.sh
```

### 后台运行
```bash
nohup python3 admin_app.py > admin.log 2>&1 &
```

## 功能说明

### 1. 仪表盘
- 显示系统统计数据（产品数、问题数、解决方案卡片数、分类数）
- 快捷操作入口
- 最近操作日志

### 2. 产品管理
- 添加、编辑、删除产品
- 设置产品启用/禁用状态
- 调整产品展示顺序

### 3. 分类管理
- 管理问题分类
- 为不同产品设置分类

### 4. 问题管理
- 添加、编辑、删除问题
- 编辑问题描述（支持富文本）
- 关联解决方案卡片
- 上传问题截图

### 5. 解决方案卡片管理
- 管理排查卡片
- 支持三个附表（物理环境、资产排查、网络问题）
- 编辑卡片内容（故障类型、现象、步骤、解决方案、补充信息）

### 6. 快速查询管理
- 管理快速查询关键词
- 设置关键词关联的问题
- 调整显示顺序

### 7. 操作日志
- 查看所有管理员操作记录
- 记录创建、更新、删除操作
- 记录登录/登出信息

## 安全建议

1. **修改默认密码**: 首次登录后立即修改
2. **定期备份数据库**: `db/problems.db`
3. **限制访问IP**: 在生产环境中限制管理员后台的访问IP
4. **使用HTTPS**: 在生产环境中使用HTTPS加密传输
5. **定期查看操作日志**: 监控管理员操作

## 端口说明

- **主应用**: 12001端口 - 问题解决系统（用户访问）
- **管理员后台**: 12002端口 - 管理后台（管理员访问）

两个系统共享同一个数据库，但运行在独立的Flask应用实例中，互不影响。

## 故障排除

### 端口被占用
如果12002端口被占用，修改 `admin_app.py` 中的端口号：
```python
admin_app.run(host='0.0.0.0', port=12003, debug=True)
```

### 数据库错误
确保 `db/problems.db` 文件存在且有读写权限。

### 模板找不到
确保 `templates/admin/` 目录存在且包含必要的模板文件。

## 默认管理员账户

系统首次启动时会自动创建默认管理员账户：
- 用户名: admin
- 密码: admin123

如需手动创建管理员，可以使用以下Python代码：
```python
from admin_app import init_db, db, Admin
from werkzeug.security import generate_password_hash

init_db()

admin = Admin(
    username='your_username',
    password_hash=generate_password_hash('your_password'),
    email='your@email.com',
    is_active=True
)
db.session.add(admin)
db.session.commit()
```

## 技术支持

如有问题，请联系杭州盾源科技有限公司技术支持团队。
