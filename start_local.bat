@echo off
title 数律智检 · 本地一键启动程序
chcp 65001 >nul

echo ============================================================
echo      数律智检 - 基层治理风险研判平台 (本地版)
echo ============================================================
echo.

:: 1. 检查 Docker 运行状态
echo [1/3] 正在检测 Docker 运行环境...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 未检测到 Docker 正在运行！
    echo 请先启动 "Docker Desktop"，等待其就绪后再运行此脚本。
    pause
    exit /b
)
echo OK.

:: 2. 检查 .env 文件
if not exist .env (
    echo.
    echo [警告] 缺失 .env 配置文件！
    echo 正在从模板为您复制 .env.local...
    if exist .env.local (
        copy .env.local .env >nul
        echo 已自动创建 .env 文件，请确保其中填入了 DeepSeek API Key。
    ) else (
        echo [错误] 未找到 .env.local 模板文件，请手动创建 .env。
        pause
        exit /b
    )
)

:: 3. 启动容器
echo.
echo [2/3] 正在构建并拉起系统容器 (这可能需要几分钟)...
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [错误] 容器启动失败，请检查 Docker 或网络设置。
    pause
    exit /b
)

:: 4. 完成并打开浏览器
echo.
echo [3/3] 服务启动成功！正在为您打开管理大屏...
timeout /t 3 >nul
start http://localhost/

echo.
echo ============================================================
echo    系统已就绪！请不要关闭此窗口以保持背景运行。
echo    您可以直接在浏览器中使用系统。
echo    停止系统：请按下 Ctrl+C 或直接关闭此窗口。
echo ============================================================
echo.
pause
