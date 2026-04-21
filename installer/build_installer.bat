@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 数律智检 · 安装包构建工具

echo.
echo ================================================================
echo   数律智检 - 安装包构建工具 (专业版)
echo   将生成标准 Windows 安装程序 (.exe)
echo ================================================================
echo.

:: ── 步骤 0：依赖检测 ──────────────────────────────────────────────────────

echo [0/5] 检测构建依赖...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请确保开发机已安装 Python 3.11+
    goto :error
)

:: 检测 Inno Setup Compiler
set ISCC_PATH=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if !ISCC_PATH!=="" (
    echo [警告] 未检测到 Inno Setup 6
    echo 请前往 https://jrsoftware.org/isdl.php 下载安装 Inno Setup 6
    echo 安装后重新运行此脚本。
    goto :error
)
echo OK.


:: ── 步骤 1：构建前端 ──────────────────────────────────────────────────────

echo.
echo [1/5] 编译前端资源 (npm run build)...
cd /d "%~dp0..\admin_frontend"
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    goto :error
)
cd /d "%~dp0"
echo OK.


:: ── 步骤 2：构建便携 Python 环境 ─────────────────────────────────────────

echo.
echo [2/5] 构建便携 Python 环境 (这将下载并安装所有依赖，约 5-10 分钟)...

set BUILD_DIR=%~dp0..\build\portable_env
if exist "%BUILD_DIR%" (
    echo 发现已有构建缓存，跳过重复构建。如需强制重建请删除 build\portable_env 文件夹。
    goto :step3
)

:: 下载 Python 3.11 嵌入式包
echo 正在下载 Python 3.11 嵌入式运行环境...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%TEMP%\python_embed.zip' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo [错误] 下载 Python 嵌入包失败，请检查网络连接
    goto :error
)

:: 解压到构建目录
mkdir "%BUILD_DIR%"
powershell -Command "Expand-Archive -Path '%TEMP%\python_embed.zip' -DestinationPath '%BUILD_DIR%' -Force"

:: 配置 pip (嵌入式 Python 默认不含 pip)
echo 正在为便携 Python 配置 pip...
:: 修改 python311._pth 允许 site-packages
powershell -Command "(Get-Content '%BUILD_DIR%\python311._pth') -replace '#import site', 'import site' | Set-Content '%BUILD_DIR%\python311._pth'"

:: 下载并安装 pip
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py' -UseBasicParsing"
"%BUILD_DIR%\python.exe" "%TEMP%\get-pip.py" --no-warn-script-location

:: 安装所有项目依赖 (直接安装到便携 Python 的 site-packages)
echo 正在安装项目依赖 (请耐心等待)...
"%BUILD_DIR%\python.exe" -m pip install ^
    fastapi uvicorn[standard] python-dotenv python-multipart ^
    openai llama-index-core llama-index-vector-stores-chroma ^
    llama-index-embeddings-huggingface chromadb sentence-transformers ^
    psutil pywebview ^
    --no-warn-script-location ^
    -q

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    goto :error
)

:step3

:: ── 步骤 3：生成轻量级桌面启动器 EXE ────────────────────────────────────

echo.
echo [3/5] 生成轻量级启动器 EXE...

:: 使用 pyinstaller 只打包这个极简的 launcher.py（无 AI 依赖，体积极小，不会报错）
pip install pyinstaller >nul 2>&1
python -m PyInstaller ^
    --name "数律智检" ^
    --windowed ^
    --noconsole ^
    --onefile ^
    --distpath "%~dp0assets" ^
    "%~dp0launcher.py"

if %errorlevel% neq 0 (
    echo [错误] 启动器 EXE 生成失败
    goto :error
)
echo OK.


:: ── 步骤 4：编译安装包 ────────────────────────────────────────────────────

echo.
echo [4/5] 使用 Inno Setup 编译安装向导...

mkdir "%~dp0..\dist_installer" 2>nul
!ISCC_PATH! "%~dp0installer.iss"
if %errorlevel% neq 0 (
    echo [错误] Inno Setup 编译失败，请检查 installer.iss 配置
    goto :error
)


:: ── 步骤 5：完成 ─────────────────────────────────────────────────────────

echo.
echo [5/5] 构建完成！
echo.
echo ================================================================
echo   安装包已生成：
echo   dist_installer\数律智检_Setup_v1.0.0.exe
echo.
echo   用户只需双击该文件即可完成安装。
echo   支持通过"控制面板 - 程序和功能"完整卸载。
echo ================================================================
echo.
pause
goto :end

:error
echo.
echo ================================================================
echo   [构建失败] 请根据以上错误信息进行修正后重试。
echo ================================================================
pause
exit /b 1

:end
exit /b 0
