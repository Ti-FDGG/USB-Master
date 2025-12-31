cmake_minimum_required(VERSION 3.20)
project(usb_scanner)

# 1. 基础设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 2. 显式查找 Python 解释器和开发资源
# 这里的 Python_EXECUTABLE 会由 build.bat 传入
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# 3. 定位 pybind11
# 使用找到的 Python 解释器来确定 pybind11 的安装位置
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
find_package(pybind11 REQUIRED PATHS ${pybind11_DIR} NO_DEFAULT_PATH)

# 4. 定义扩展模块
pybind11_add_module(usb_scanner 
    python_binding.cpp
    USBScanner.cpp
)

# 5. 链接库
# 链接 Python 库和 Windows 的 SetupAPI
target_link_libraries(usb_scanner PRIVATE Python::Python setupapi)

# 6. Windows 特定配置
if(WIN32)
    add_definitions(-DUNICODE -D_UNICODE)
    
    # 设置输出文件名和后缀
    set_target_properties(usb_scanner PROPERTIES
        OUTPUT_NAME "usb_scanner"
        SUFFIX ".pyd"
    )

    # 编译选项：处理 UTF-8 编码避免中文乱码
    if(MSVC)
        target_compile_options(usb_scanner PRIVATE /W4 /utf-8)
    endif()
endif()

# 包含头文件目录
target_include_directories(usb_scanner PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})