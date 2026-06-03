#!/bin/bash
# 现场问题解决方案管理系统 - 系统服务脚本

PIDFILE="/tmp/problem-solution.pid"
LOGFILE="/tmp/problem-solution.log"
APP_DIR="/mnt/c/Users/86279/problem-solution-system"

case "$1" in
    start)
        echo "正在启动现场问题解决方案管理系统..."
        cd $APP_DIR
        
        # 检查是否已经运行
        if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
            echo "服务已经在运行中 (PID: $(cat $PIDFILE))"
            exit 0
        fi
        
        # 启动应用
        nohup ./venv/bin/python run.py > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
        
        sleep 2
        
        # 检查启动是否成功
        if curl -s http://localhost:5000/api/products > /dev/null; then
            echo "✅ 服务启动成功！"
            echo "访问地址：http://localhost:5000"
            echo "进程ID：$(cat $PIDFILE)"
        else
            echo "❌ 服务启动失败，请查看日志：$LOGFILE"
            exit 1
        fi
        ;;
    
    stop)
        echo "正在停止服务..."
        if [ -f "$PIDFILE" ]; then
            PID=$(cat "$PIDFILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                sleep 2
                echo "✅ 服务已停止 (PID: $PID)"
            else
                echo "服务未运行"
            fi
            rm -f "$PIDFILE"
        else
            echo "PID文件不存在，服务可能未运行"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    
    status)
        if [ -f "$PIDFILE" ] && kill -0 $(cat "$PIDFILE") 2>/dev/null; then
            echo "✅ 服务正在运行 (PID: $(cat $PIDFILE))"
            echo "访问地址：http://localhost:5000"
            curl -s http://localhost:5000/api/products | python3 -m json.tool
        else
            echo "❌ 服务未运行"
        fi
        ;;
    
    logs)
        if [ -f "$LOGFILE" ]; then
            tail -50 "$LOGFILE"
        else
            echo "日志文件不存在"
        fi
        ;;
    
    *)
        echo "用法：$0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac