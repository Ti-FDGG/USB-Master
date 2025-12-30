cmake_minimum_required(VERSION 3.20)
project(usb_scanner)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 执行 python 获取 pybind11 的安装路径
execute_process(
    COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# 查找Python和pybind11
find_package(pybind11 REQUIRED)
pybind11_add_module(usb_scanner 
    python_binding.cpp
    USBScanner.cpp
)

# Windows特定设置
if(WIN32)
    # 设置Unicode支持
    add_definitions(-DUNICODE -D_UNICODE)
    
    # 链接Windows系统库
    target_link_libraries(usb_scanner PRIVATE setupapi)
    
    # 设置输出目录为Python包目录（backend目录）
    # 这样Python可以直接导入模块
    set_target_properties(usb_scanner PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../"
        OUTPUT_NAME "usb_scanner"
        SUFFIX ".pyd"
    )
endif()

# 包含目录
target_include_directories(usb_scanner PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# 编译选项
if(MSVC)
    # 使用UTF-8编码，解决中文注释和字符串的编码问题
    target_compile_options(usb_scanner PRIVATE /W4 /utf-8)
else()
    target_compile_options(usb_scanner PRIVATE -Wall -Wextra)
endif()

