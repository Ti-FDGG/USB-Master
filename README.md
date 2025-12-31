# USB Master

北京理工大学计算机科学与技术大三上学期汇编语言与接口技术课程实验

USB 总线及挂载设备测试实验系统 - 一个基于 C++ Setup API + FastAPI + React 的 USB 设备扫描与监控平台。

## 项目简介

USB Master 是一个用于扫描、监控和管理 USB 设备的 Web 应用系统。系统采用前后端分离架构，后端使用 Python FastAPI 和 C++ 绑定实现高性能的 USB 设备扫描，前端使用 React + TypeScript 提供现代化的用户界面。

## 核心功能

- **USB 设备扫描**：使用 C++ 实现底层 USB 设备扫描，提供详细的设备信息
- **实时监控**：通过 WebSocket 实时推送 USB 设备插拔事件
- **文件管理**：浏览和管理 USB 存储设备中的文件
- **系统信息**：显示当前系统状态和运行信息

## 技术栈

### 后端
- **框架**：FastAPI 0.104.1
- **语言**：Python 3.8+
- **USB 扫描**：C++ (USBScanner.cpp) + pybind11 绑定
- **异步服务器**：Uvicorn
- **数据验证**：Pydantic 2.5.0

### 前端
- **框架**：React 19.2.1
- **语言**：TypeScript 5.8
- **构建工具**：Vite 6.2
- **UI 组件**：Lucide React

## 项目结构

```
usb-master/
├── backend/                 # 后端服务
│   ├── api/                # API 路由
│   │   ├── usb.py         # USB 设备 API
│   │   ├── files.py       # 文件管理 API
│   │   └── system.py      # 系统信息 API
│   ├── services/          # 业务逻辑层
│   │   ├── usb_service.py        # USB 服务（主入口）
│   │   ├── usb_service_cpp.py    # C++ 绑定封装
│   │   ├── file_service.py       # 文件服务
│   │   └── monitor_service.py    # USB 监控服务
│   ├── models/            # 数据模型
│   │   └── schemas.py     # Pydantic 模型定义
│   ├── cpp_bindings/      # C++ 绑定模块
│   │   ├── src/           # C++ 源代码
│   │   │   ├── USBScanner.h
│   │   │   ├── USBScanner.cpp
│   │   │   └── python_binding.cpp
│   │   └── build.bat      # 构建脚本
│   ├── main.py           # FastAPI 应用入口
│   └── requirements.txt  # Python 依赖
└── frontend/              # 前端应用
    ├── components/       # React 组件
    │   ├── UsbMonitor.tsx    # USB 监控组件
    │   └── FileManager.tsx   # 文件管理组件
    ├── utils/            # 工具函数
    │   ├── api.ts        # API 客户端
    │   └── formatters.ts # 格式化工具
    ├── App.tsx           # 主应用组件
    └── package.json      # 前端依赖

```

## 快速开始

### 环境要求

- **操作系统**：Windows 10/11
- **Python**：3.8 或更高版本
- **Node.js**：18 或更高版本
- **C++ 编译器**：Visual Studio Build Tools 或 MinGW（用于编译 C++ 绑定）
- **CMake**：3.20 或更高版本

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

4. 编译 C++ 绑定模块：
```bash
cd cpp_bindings
build.bat
cd ..
```

5. 启动后端服务：
```bash
python main.py
```

后端服务将在 `http://localhost:8000` 启动，API 文档可在 `http://localhost:8000/docs` 访问。

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 `http://localhost:5173` 启动。

## API 端点

### USB 设备
- `GET /api/usb/devices` - 获取所有 USB 设备列表
- `GET /api/usb/devices/{device_id}` - 获取特定设备详情
- `POST /api/usb/scan` - 手动触发设备扫描
- `WS /api/usb/ws/monitor` - WebSocket 实时监控

### 文件管理
- `GET /api/files/drives` - 获取所有驱动器
- `GET /api/files/list` - 列出目录内容
- `GET /api/files/download` - 下载文件

### 系统信息
- `GET /api/system/info` - 获取系统信息

## 开发说明

### C++ 绑定编译

项目使用 pybind11 将 C++ USB 扫描功能绑定到 Python。编译步骤：

1. 确保已安装 CMake 和 C++ 编译器
2. 运行 `backend/cpp_bindings/build.bat`
3. 生成的 `.pyd` 文件将用于 Python 导入

### 数据模型

Python 的 `USBDeviceInfo` 模型与 C++ 的 `USBDeviceInfo` 结构体完全一致，包括以下字段：
- `devicePath`, `serialNumber`, `deviceGUID`
- `description`, `manufacturer`, `product`
- `deviceClass`, `deviceInstanceId`
- `vendorId`, `productId`
- `busNumber`, `portNumber`
- `speed`, `version`

## 许可证

本项目仅供学习和研究使用。