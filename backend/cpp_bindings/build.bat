@echo off
REM Windows构建脚本

REM 如果传入 clean 参数，则执行清理并退出
if /I "%1"=="clean" goto clean

echo Creating build directory...
if not exist build mkdir build
cd build

echo Configuring CMake...
cmake .. -DCMAKE_BUILD_TYPE=Release

if %ERRORLEVEL% NEQ 0 (
    echo CMake configuration failed!
    pause
    exit /b 1
)

echo Building...
cmake --build . --config Release

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b 1
)

REM 返回到 cpp_bindings 目录
cd ..

REM 将生成的 pyd 文件复制到 backend 目录
set "PYD_SRC=..\Release\usb_scanner.pyd"
set "PYD_DST=..\usb_scanner.pyd"

if exist "%PYD_SRC%" (
    copy /Y "%PYD_SRC%" "%PYD_DST%"
    echo Copied usb_scanner.pyd to backend directory: %PYD_DST%
) else (
    echo Warning: %PYD_SRC% not found, usb_scanner.pyd was not copied.
)

echo Build completed successfully!
pause
goto end

:clean
echo Cleaning build artifacts...

REM 删除 CMake 构建目录
if exist build (
    rd /s /q build
)

REM 删除 backend\Release 下的 pyd
if exist "..\Release\usb_scanner.pyd" (
    del /q "..\Release\usb_scanner.pyd"
)

REM 删除 backend 目录下的 pyd
if exist "..\usb_scanner.pyd" (
    del /q "..\usb_scanner.pyd"
)

echo Clean completed.
pause

:end
