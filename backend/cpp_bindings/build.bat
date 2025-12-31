@echo off
setlocal enabledelayedexpansion

REM --- 配置区域 ---
REM 假设 venv 文件夹在 cpp_bindings 的上一级目录
set "MODULE_DIR=%CD%"
set "PYTHON_EXE=%MODULE_DIR%\..\venv\Scripts\python.exe"
set "BUILD_DIR=build"
set "SRC_DIR=src"
set "OUTPUT_DIR=%MODULE_DIR%"

REM 检查 Python 路径是否存在
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Could not find venv Python at: %PYTHON_EXE%
    pause
    exit /b 1
)

REM 清理指令
if /I "%1"=="clean" (
    echo Cleaning...
    if exist %BUILD_DIR% rd /s /q %BUILD_DIR%
    if exist "%OUTPUT_DIR%\usb_scanner.pyd" del /q "%OUTPUT_DIR%\usb_scanner.pyd"
    echo Clean done.
    goto end
)

echo [1/3] Using Python: %PYTHON_EXE%

REM 创建并进入构建目录
if not exist %BUILD_DIR% mkdir %BUILD_DIR%
cd %BUILD_DIR%

echo [2/3] Configuring CMake...
cmake ..\%SRC_DIR% -G "Visual Studio 17 2022" -A x64 ^
    -DPython_EXECUTABLE="%PYTHON_EXE%" ^
    -DCMAKE_BUILD_TYPE=Release

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CMake configuration failed!
    pause
    exit /b 1
)

echo [3/3] Building Release version...
cmake --build . --config Release

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM 复制生成的 pyd 到模块目录（cpp_bindings）
if exist "Release\usb_scanner.pyd" (
    copy /Y "Release\usb_scanner.pyd" "..\usb_scanner.pyd"
    echo.
    echo [SUCCESS] Module copied to: %OUTPUT_DIR%\usb_scanner.pyd
) else (
    echo [ERROR] .pyd file not found in Release folder.
)

cd ..

:end
pause