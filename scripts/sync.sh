#!/bin/bash
# 快速同步脚本 - 用于本地和服务器之间的代码同步

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="/mnt/d/PROJECT/problem-solution-system"
REMOTE_USER="root"
REMOTE_HOST="124.222.67.226"
REMOTE_KEY="/mnt/c/Users/86279/.ssh/id_ed25519"
REMOTE_DIR="/root/problem-solution-system"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_REPO="https://github.com/zrcnn/problem-solution-system.git"

# 函数：打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查是否在正确的目录
check_project_dir() {
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    cd "$PROJECT_DIR"
}

# 函数：检查Git配置
check_git_config() {
    if ! git config user.name >/dev/null 2>&1; then
        print_warning "配置Git用户信息..."
        git config --global user.name "zrcnn"
        git config --global user.email "862795773@qq.com"
    fi
}

# 函数：同步到GitHub
sync_to_github() {
    print_info "同步到GitHub..."

    # 检查远程仓库
    if ! git remote get-url origin >/dev/null 2>&1; then
        git remote add origin "$GITHUB_REPO"
    fi

    # 查看状态
    git status

    # 询问是否提交更改
    read -p "是否提交当前更改? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "输入提交信息: " commit_msg
        git commit -m "$commit_msg"
    fi

    # 推送
    read -p "是否推送到GitHub? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push origin main
        print_success "已推送到GitHub"
    fi
}

# 函数：同步服务器
sync_server() {
    print_info "同步到服务器..."

    # SSH命令
    SSH_CMD="ssh -i $REMOTE_KEY -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST"

    # 检查服务器连接
    if ! $SSH_CMD "echo '连接成功'" >/dev/null 2>&1; then
        print_error "无法连接到服务器"
        exit 1
    fi

    # 在服务器上执行同步
    print_info "在服务器上执行同步..."
    $SSH_CMD "cd $REMOTE_DIR && git fetch origin && git reset --hard origin/main"

    if [ $? -eq 0 ]; then
        print_success "服务器同步完成"
    else
        print_error "服务器同步失败"
    fi
}

# 函数：从服务器拉取
pull_from_server() {
    print_info "从服务器拉取最新更改..."

    # 临时克隆到临时目录
    TEMP_DIR="/tmp/problem-solution-sync"
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"

    # 使用rsync同步
    SSH_CMD="ssh -i $REMOTE_KEY -o StrictHostKeyChecking=no"
    rsync -avz --delete -e "$SSH_CMD" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" "$TEMP_DIR/"

    # 比较差异
    print_info "比较差异..."
    diff -r "$PROJECT_DIR" "$TEMP_DIR" --brief

    if [ $? -eq 0 ]; then
        print_success "本地和服务器代码一致"
    else
        print_warning "发现差异，是否覆盖本地文件? (y/n) "
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rsync -avz --delete -e "$SSH_CMD" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/" "$PROJECT_DIR/"
            print_success "本地代码已更新"
        fi
    fi

    rm -rf "$TEMP_DIR"
}

# 函数：显示菜单
show_menu() {
    clear
    echo "================================"
    echo "  问题解决方案系统 - Git同步工具"
    echo "================================"
    echo ""
    echo "1. 同步到GitHub"
    echo "2. 同步到服务器"
    echo "3. 从服务器拉取"
    echo "4. 查看状态"
    echo "5. 退出"
    echo ""
}

# 主函数
main() {
    check_project_dir
    check_git_config

    while true; do
        show_menu
        read -p "请选择操作 (1-5): " choice

        case $choice in
            1)
                sync_to_github
                ;;
            2)
                sync_server
                ;;
            3)
                pull_from_server
                ;;
            4)
                git status
                ;;
            5)
                print_info "退出"
                exit 0
                ;;
            *)
                print_error "无效选择"
                ;;
        esac

        echo ""
        read -p "按回车键继续..."
    done
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
