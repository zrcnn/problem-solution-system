# Git版本管理配置指南

## 概述

本文档说明如何配置问题解决方案系统的Git版本管理，实现本地开发、服务器部署和GitHub仓库的三方同步。

## 仓库信息

- **GitHub仓库**: https://github.com/zrcnn/problem-solution-system
- **本地路径**: `/mnt/d/PROJECT/problem-solution-system`
- **服务器路径**: `/root/problem-solution-system`
- **认证方式**: GitHub Personal Access Token (已配置)

## 配置步骤

### 1. 本地开发环境配置（已完成）

```bash
# 进入项目目录
cd /mnt/d/PROJECT/problem-solution-system

# 配置Git用户信息
git config --global user.name "zrcnn"
git config --global user.email "862795773@qq.com"

# 添加远程仓库（已完成）
git remote add origin https://github.com/zrcnn/problem-solution-system.git

# 推送到GitHub（已完成）
git push -u origin main --force
```

### 2. 服务器环境配置

在服务器上执行以下命令：

```bash
# SSH登录服务器
ssh root@124.222.67.226 -i /mnt/c/Users/86279/.ssh/id_ed25519

# 进入项目目录
cd /root/problem-solution-system

# 配置Git用户信息
git config --global user.name "zrcnn"
git config --global user.email "862795773@qq.com"

# 初始化Git仓库（如果尚未初始化）
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Initial commit: problem-solution-system"

# 添加远程仓库
git remote add origin https://github.com/zrcnn/problem-solution-system.git

# 重命名分支为main
git branch -M main

# 推送到GitHub
git push -u origin main --force
```

### 3. .gitignore配置

项目已包含完整的`.gitignore`文件，排除以下内容：

- Python缓存文件（`*.pyc`, `__pycache__/`）
- 虚拟环境（`venv/`）
- 数据库文件（`*.db`, `*.sqlite`）
- 日志文件（`*.log`, `logs/`）
- 上传文件（`uploads/`）
- 环境配置文件（`.env`）
- IDE配置文件
- CodeGraph索引（`.codegraph/`）

## 日常工作流程

### 本地开发 → GitHub

```bash
# 1. 在本地进行代码更改
# 编辑文件...

# 2. 查看更改
git status
git diff

# 3. 暂存更改
git add .

# 4. 提交更改
git commit -m "描述你的更改"

# 5. 推送到GitHub
git push origin main
```

### 服务器更新 → GitHub

```bash
# 1. SSH登录服务器
ssh root@124.222.67.226 -i /mnt/c/Users/86279/.ssh/id_ed25519

# 2. 进入项目目录
cd /root/problem-solution-system

# 3. 查看更改
git status

# 4. 暂存并提交
git add .
git commit -m "服务器端更改描述"

# 5. 推送到GitHub
git push origin main
```

### 同步服务器到本地

如果服务器有最新更改，需要同步到本地：

```bash
# 在本地开发机器上
cd /mnt/d/PROJECT/problem-solution-system

# 拉取最新更改
git pull origin main

# 如果有冲突，解决冲突后提交
# git mergetool 或手动编辑冲突文件
# git add <resolved_files>
# git commit -m "解决合并冲突"
```

### 同步本地到服务器

如果本地有最新更改，需要同步到服务器：

```bash
# 在服务器上
cd /root/problem-solution-system

# 拉取最新更改
git pull origin main

# 重启应用（如果需要）
# 停止服务
# pkill -f "python.*app_single.py"
# pkill -f "python.*admin_app.py"

# 启动服务
source venv/bin/activate
python run.py &
python admin_app.py &
```

## 分支策略

### 主分支

- **main**: 生产环境分支，始终与服务器部署版本保持一致

### 开发分支（可选）

如果需要功能开发，可以创建开发分支：

```bash
# 创建开发分支
git checkout -b develop

# 推送开发分支
git push -u origin develop

# 在服务器上切换到开发分支
cd /root/problem-solution-system
git fetch origin
git checkout develop
git pull origin develop
```

## 版本标签

发布重要版本时创建标签：

```bash
# 创建版本标签
git tag -a v1.0.0 -m "正式发布版本"

# 推送标签
git push origin v1.0.0

# 查看所有标签
git tag -l
```

## 故障排除

### 问题1: 推送被拒绝

如果推送被拒绝，通常是因为远程有本地没有的提交：

```bash
# 先拉取远程更改
git pull origin main

# 解决冲突（如果有）
# 然后再次推送
git push origin main
```

### 问题2: 合并冲突

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突
# 编辑后标记为已解决
git add <resolved_file>

# 完成合并
git commit -m "解决合并冲突"
```

### 问题3: 需要强制推送（谨慎使用）

只有在确定要覆盖远程历史时才使用：

```bash
git push origin main --force
```

**警告**: 这会覆盖远程分支的历史，确保其他协作者知道。

## 安全注意事项

1. **Token安全**: GitHub Personal Access Token已保存在Git配置中，不要将其提交到仓库
2. **敏感数据**: 确保`.gitignore`正确配置，避免提交数据库、密码等敏感信息
3. **备份**: 定期备份重要数据，Git不是备份系统

## 自动化部署（可选）

可以配置Git hooks实现自动部署：

```bash
# 在服务器上创建post-receive钩子
cd /root/problem-solution-system/.git/hooks
cat > post-receive << 'EOF'
#!/bin/bash
GIT_DIR=/root/problem-solution-system/.git
WORK_TREE=/root/problem-solution-system

git --git-dir=$GIT_DIR --work-tree=$WORK_TREE checkout -f
echo "部署完成！"
EOF

chmod +x post-receive
```

这样每次推送到GitHub时，服务器会自动更新代码。

## 联系支持

如有问题，请联系：
- GitHub: zrcnn
- 邮箱: 862795773@qq.com

---

**最后更新**: 2026-06-03
**文档版本**: 1.0
