@echo off
chcp 65001 >nul
echo ========================================
echo   TestFlow - 快速启动脚本
echo ========================================
echo.

REM 1. 检查环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

REM 2. 后端设置
echo [1/4] 配置后端环境...
cd backend
if not exist .venv (
    echo 创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate

REM 检查依赖是否安装（通过检查 uvicorn 是否存在）
.venv\Scripts\pip.exe show uvicorn >nul 2>&1
if errorlevel 1 (
    echo [调试] 当前 Python 路径:
    where python
    echo 安装后端依赖...
    set PYTHONUTF8=1
    .venv\Scripts\pip.exe install --no-cache-dir -r ..\requirements.txt
) else (
    echo 后端依赖已安装，跳过
)

REM 检查.env
if not exist .env (
    echo 创建默认配置文件...
    copy .env.example .env >nul
)

REM 3. 前端设置
echo [2/4] 配置前端环境...
cd ..\frontend
if not exist node_modules (
    echo 安装前端依赖...
    call npm install >nul 2>&1
) else (
    echo 前端依赖已安装，跳过安装
)

REM 4. 启动服务
echo [3/4] 启动服务...
echo.

REM 启动后端
cd ..\backend
start "TestFlow Backend" cmd /k "call .venv\Scripts\activate && uvicorn app.main:app --reload --port 9000"

REM 启动前端
cd ..\frontend
start "TestFlow Frontend" cmd /k "npm run dev"

echo [4/4] 启动完成！
echo.
echo ========================================
echo   TestFlow 已启动
echo ========================================
echo.
echo 前端地址: http://localhost:3000
echo 后端API:  http://localhost:9000
echo.
echo 提示: 关闭弹出的命令行窗口即可停止服务
echo.

timeout /t 3 >nul
start http://localhost:3000
pause
