@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo.
echo ================================================================
echo   Shulv - Professional Installer Builder
echo ================================================================
echo.

rem --- Step 0: Detection ---
echo [0/5] Detecting dependencies...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    exit /b 1
)

set ISCC_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "D:\Inno Setup 6\ISCC.exe" (
    set ISCC_PATH="D:\Inno Setup 6\ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo [ERROR] Inno Setup 6 not found!
    echo Please install it to D:\Inno Setup 6 or C:\Program Files\Inno Setup 6
    exit /b 1
)
echo OK. (ISCC: %ISCC_PATH%)

rem --- Step 1: Frontend ---
echo.
echo [1/5] Building frontend (npm run build)...
cd /d "%~dp0..\admin_frontend"
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed!
    exit /b 1
)
cd /d "%~dp0"
echo OK.

rem --- Step 2: Portable Python ---
echo.
echo [2/5] Building portable Python environment (This may take 5-10 mins)...

set BUILD_DIR=%~dp0..\build\portable_env
if exist "%BUILD_DIR%" (
    echo Found existing build cache, skipping. Delete build\portable_env to rebuild.
    goto :step3
)

echo Downloading Python 3.11 embeddable package...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%%TEMP%%\python_embed.zip' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to download Python!
    exit /b 1
)

mkdir "%BUILD_DIR%"
powershell -Command "Expand-Archive -Path '%%TEMP%%\python_embed.zip' -DestinationPath '%BUILD_DIR%' -Force"

echo Configuring pip for portable Python...
powershell -Command "(Get-Content '%BUILD_DIR%\python311._pth') -replace '#import site', 'import site' | Set-Content '%BUILD_DIR%\python311._pth'"

powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%%TEMP%%\get-pip.py' -UseBasicParsing"
"%BUILD_DIR%\python.exe" "%%TEMP%%\get-pip.py" --no-warn-script-location

echo Installing project dependencies from requirements.txt...
"%BUILD_DIR%\python.exe" -m pip install -r "%~dp0..\backend\requirements.txt" --no-warn-script-location -q

if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed!
    exit /b 1
)

:step3
rem --- Step 3: Launcher ---
echo.
echo [3/5] Building launcher EXE...
python -m PyInstaller ^
    --name "数律智检" ^
    --windowed ^
    --noconsole ^
    --onefile ^
    --distpath "%~dp0assets" ^
    "%~dp0launcher.py"

if %errorlevel% neq 0 (
    echo [ERROR] Launcher build failed!
    exit /b 1
)
echo OK.

rem --- Step 4: Final Package ---
echo.
echo [4/5] Compining final Setup.exe with Inno Setup...
mkdir "%~dp0..\dist_installer" 2>nul
%ISCC_PATH% "%~dp0installer.iss"
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed!
    exit /b 1
)

rem --- Step 5: Done ---
echo.
echo [5/5] Success!
echo Result: dist_installer\数律智检_Setup_v1.0.0.exe
echo.
exit /b 0
