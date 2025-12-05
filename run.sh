#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  TestFlow - 快速启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3"
    exit 1
fi
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node.js"
    exit 1
fi

# 2. 后端设置
echo -e "${BLUE}[1/4] 配置后端环境...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "安装后端依赖..."
    pip install -r requirements.txt > /dev/null 2>&1
else
    echo "虚拟环境已存在，跳过安装"
    source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo "创建默认配置文件..."
    cp .env.example .env
fi

# 3. 前端设置
echo -e "${BLUE}[2/4] 配置前端环境...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install > /dev/null 2>&1
else
    echo "前端依赖已安装，跳过安装"
fi

# 4. 启动服务
echo -e "${BLUE}[3/4] 启动服务...${NC}"

# 启动后端
cd ../backend
source .venv/bin/activate
nohup uvicorn app.main:app --reload --port 9000 > backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# 启动前端
cd ../frontend
nohup npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > frontend.pid

echo -e "${BLUE}[4/4] 启动完成！${NC}"
echo ""
echo -e "${GREEN}TestFlow 已启动${NC}"
echo "前端地址: http://localhost:3000"
echo "后端API:  http://localhost:9000"
echo ""
echo "停止服务请运行: ./stop.sh"
echo ""

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &> /dev/null
elif command -v open &> /dev/null; then
    open http://localhost:3000 &> /dev/null
fi
