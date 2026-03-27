#!/bin/bash
# TCM Web 应用管理脚本
# 用法: ./start_web.sh {start|stop|restart|status}

set -e

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"
BACKEND_LOG="$SCRIPT_DIR/logs/backend.log"
FRONTEND_LOG="$SCRIPT_DIR/logs/frontend.log"
BACKEND_PORT=8000
FRONTEND_PORT=8501

# 创建日志目录
mkdir -p "$(dirname "$BACKEND_LOG")"

# 获取进程 ID
get_backend_pid() {
    if [ -f "$BACKEND_PID_FILE" ]; then
        cat "$BACKEND_PID_FILE"
    fi
}

get_frontend_pid() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        cat "$FRONTEND_PID_FILE"
    fi
}

# 检查进程是否运行
is_backend_running() {
    local pid=$(get_backend_pid)
    [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1
}

is_frontend_running() {
    local pid=$(get_frontend_pid)
    [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1
}

# 检查端口是否被占用
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
}

# 启动后端
start_backend() {
    if is_backend_running; then
        echo "✅ 后端服务已在运行 (PID: $(get_backend_pid))"
        return 0
    fi

    if check_port $BACKEND_PORT; then
        echo "⚠️  端口 $BACKEND_PORT 已被占用，尝试使用现有后端..."
        return 0
    fi

    echo "🚀 启动后端服务..."
    cd "$SCRIPT_DIR"
    nohup python run_server.py > "$BACKEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$BACKEND_PID_FILE"
    sleep 2

    if is_backend_running; then
        echo "✅ 后端服务启动成功 (PID: $pid)"
    else
        echo "❌ 后端服务启动失败"
        rm -f "$BACKEND_PID_FILE"
        return 1
    fi
}

# 停止后端
stop_backend() {
    if ! is_backend_running; then
        rm -f "$BACKEND_PID_FILE"
        return 0
    fi

    local pid=$(get_backend_pid)
    echo "🛑 停止后端服务 (PID: $pid)..."
    kill $pid 2>/dev/null || true

    local count=0
    while is_backend_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    if is_backend_running; then
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi

    rm -f "$BACKEND_PID_FILE"
    echo "✅ 后端服务已停止"
}

# 启动前端
start_frontend() {
    if is_frontend_running; then
        echo "✅ 前端服务已在运行 (PID: $(get_frontend_pid))"
        return 0
    fi

    if check_port $FRONTEND_PORT; then
        echo "❌ 端口 $FRONTEND_PORT 已被占用"
        lsof -i:$FRONTEND_PORT
        return 1
    fi

    echo "🚀 启动前端服务..."
    cd "$FRONTEND_DIR"
    nohup streamlit run app.py --server.port $FRONTEND_PORT > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID_FILE"
    sleep 3

    if is_frontend_running; then
        echo "✅ 前端服务启动成功 (PID: $pid)"
        echo "   访问地址: http://localhost:$FRONTEND_PORT"
    else
        echo "❌ 前端服务启动失败"
        rm -f "$FRONTEND_PID_FILE"
        return 1
    fi
}

# 停止前端
stop_frontend() {
    if ! is_frontend_running; then
        rm -f "$FRONTEND_PID_FILE"
        return 0
    fi

    local pid=$(get_frontend_pid)
    echo "🛑 停止前端服务 (PID: $pid)..."
    kill $pid 2>/dev/null || true

    local count=0
    while is_frontend_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    if is_frontend_running; then
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi

    rm -f "$FRONTEND_PID_FILE"
    echo "✅ 前端服务已停止"
}

# 启动所有服务
start() {
    echo "=========================================="
    echo "  启动 TCM 中医辨证论治系统"
    echo "=========================================="
    echo ""

    start_backend
    echo ""
    start_frontend

    echo ""
    echo "=========================================="
    echo "✅ 系统启动完成"
    echo "=========================================="
    echo "   前端: http://localhost:$FRONTEND_PORT"
    echo "   后端: http://localhost:$BACKEND_PORT"
    echo "   文档: http://localhost:$BACKEND_PORT/docs"
    echo ""
}

# 停止所有服务
stop() {
    echo "=========================================="
    echo "  停止 TCM 中医辨证论治系统"
    echo "=========================================="
    echo ""

    stop_frontend
    stop_backend

    echo ""
    echo "✅ 系统已停止"
}

# 重启所有服务
restart() {
    echo "🔄 重启系统..."
    stop
    sleep 2
    start
}

# 显示状态
status() {
    echo "=========================================="
    echo "  TCM 中医辨证论治系统状态"
    echo "=========================================="
    echo ""

    echo "【后端服务】"
    if is_backend_running; then
        local pid=$(get_backend_pid)
        echo "状态: ✅ 运行中"
        echo "PID:  $pid"
        echo "端口: $BACKEND_PORT"
        ps -p $pid -o pid,%mem,%cpu,etime 2>/dev/null | tail -1 || true
    else
        echo "状态: ❌ 未运行"
        if check_port $BACKEND_PORT; then
            echo "⚠️  端口被占用:"
            lsof -i:$BACKEND_PORT
        fi
    fi

    echo ""
    echo "【前端服务】"
    if is_frontend_running; then
        local pid=$(get_frontend_pid)
        echo "状态: ✅ 运行中"
        echo "PID:  $pid"
        echo "端口: $FRONTEND_PORT"
        echo "地址: http://localhost:$FRONTEND_PORT"
        ps -p $pid -o pid,%mem,%cpu,etime 2>/dev/null | tail -1 || true
    else
        echo "状态: ❌ 未运行"
        if check_port $FRONTEND_PORT; then
            echo "⚠️  端口被占用:"
            lsof -i:$FRONTEND_PORT
        fi
    fi

    echo ""
    echo "日志文件:"
    echo "  后端: $BACKEND_LOG"
    echo "  前端: $FRONTEND_LOG"
}

# 显示日志
logs() {
    local service="${2:-}"
    case "$service" in
        backend)
            tail -f "$BACKEND_LOG"
            ;;
        frontend)
            tail -f "$FRONTEND_LOG"
            ;;
        *)
            echo "用法: $0 logs {backend|frontend}"
            echo ""
            echo "  监控后端日志: $0 logs backend"
            echo "  监控前端日志: $0 logs frontend"
            ;;
    esac
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
        logs "$@"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动前后端服务"
        echo "  stop    - 停止前后端服务"
        echo "  restart - 重启前后端服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看实时日志"
        echo ""
        echo "示例:"
        echo "  $0 start          # 启动系统"
        echo "  $0 status         # 查看状态"
        echo "  $0 logs backend   # 查看后端日志"
        exit 1
        ;;
esac
