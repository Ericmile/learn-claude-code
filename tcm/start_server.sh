#!/bin/bash
# TCM Agent API 管理脚本
# 用法: ./start_server.sh {start|stop|restart|status}

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
BACKEND_DIR="$SCRIPT_DIR/backend"
PID_FILE="$SCRIPT_DIR/.backend.pid"
LOG_FILE="$SCRIPT_DIR/logs/backend.log"
HOST="0.0.0.0"
PORT=8000

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 获取进程 ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

# 检查进程是否运行
is_running() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        return 1
    fi
    ps -p "$pid" > /dev/null 2>&1
}

# 检查端口是否被占用
check_port() {
    lsof -ti:$PORT > /dev/null 2>&1
}

# 启动服务
start() {
    if is_running; then
        echo "✅ 后端服务已在运行中 (PID: $(get_pid))"
        return 0
    fi

    if check_port; then
        echo "❌ 端口 $PORT 已被占用"
        echo "请检查是否有其他进程占用该端口:"
        lsof -i:$PORT
        return 1
    fi

    echo "🚀 启动 TCM Agent API 后端服务..."
    echo "   API 地址: http://localhost:$PORT"
    echo "   API 文档: http://localhost:$PORT/docs"
    echo ""

    cd "$SCRIPT_DIR"
    nohup python run_server.py > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # 等待启动
    sleep 2

    if is_running; then
        echo "✅ 后端服务启动成功 (PID: $pid)"
        echo "   日志文件: $LOG_FILE"
        return 0
    else
        echo "❌ 后端服务启动失败"
        echo "   查看日志: tail -f $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    if ! is_running; then
        echo "⚠️  后端服务未运行"
        rm -f "$PID_FILE"
        return 0
    fi

    local pid=$(get_pid)
    echo "🛑 停止后端服务 (PID: $pid)..."

    kill $pid 2>/dev/null || true

    # 等待进程结束
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    if is_running; then
        echo "⚠️  进程未响应，强制终止..."
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi

    rm -f "$PID_FILE"
    echo "✅ 后端服务已停止"
}

# 重启服务
restart() {
    echo "🔄 重启后端服务..."
    stop
    sleep 1
    start
}

# 显示状态
status() {
    echo "=========================================="
    echo "  TCM Agent API 后端服务状态"
    echo "=========================================="
    echo ""

    if is_running; then
        local pid=$(get_pid)
        echo "状态: ✅ 运行中"
        echo "PID:  $pid"
        echo "端口: $PORT"
        echo "地址: http://localhost:$PORT"
        echo "文档: http://localhost:$PORT/docs"
        echo ""
        echo "进程信息:"
        ps -p $pid -o pid,ppid,cmd,%mem,%cpu,etime || true
    else
        echo "状态: ❌ 未运行"
        if check_port; then
            echo "⚠️  端口 $PORT 被其他进程占用:"
            lsof -i:$PORT
        fi
    fi

    echo ""
    echo "日志文件: $LOG_FILE"
    echo "PID 文件: $PID_FILE"
}

# 显示日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
    fi
}

# 主逻辑
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动后端服务"
        echo "  stop    - 停止后端服务"
        echo "  restart - 重启后端服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac
