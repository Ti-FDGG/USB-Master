"""
Pydantic 数据模型
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class USBDeviceInfo(BaseModel):
    """
    USB 设备信息（与 C++ 版 USBDeviceInfo 结构体完全一致）

    对应 C++ 定义：
        struct USBDeviceInfo {
            std::string devicePath;
            std::string serialNumber;
            std::string deviceGUID;
            std::string description;
            std::string manufacturer;
            std::string product;
            std::string deviceClass;
            std::string deviceInstanceId;
            std::string vendorId;
            std::string productId;
            std::string busNumber;
            std::string portNumber;
            std::string speed;
            std::string version;
        };
    """

    # 字段命名与 C++ 结构体保持完全一致
    devicePath: str
    serialNumber: str
    deviceGUID: str

    description: str
    manufacturer: str
    product: str
    deviceClass: str
    deviceInstanceId: str
    vendorId: str
    productId: str

    busNumber: str
    portNumber: str
    speed: str
    version: str

    model_config = ConfigDict(from_attributes=True)


class FileEntry(BaseModel):
    """文件条目"""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None  # 文件大小（字节），目录为 None
    modified_time: float  # 修改时间（Unix 时间戳）
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "test.txt",
                "path": "D:\\test.txt",
                "is_directory": False,
                "size": 1024,
                "modified_time": 1234567890.0
            }
        }


class DriveInfo(BaseModel):
    """驱动器信息"""
    path: str  # 驱动器路径
    label: str  # 驱动器标签
    total_space: int  # 总空间（字节）
    free_space: int  # 可用空间（字节）
    type: str  # 类型：removable, fixed, network
    
    class Config:
        json_schema_extra = {
            "example": {
                "path": "D:\\",
                "label": "USB Drive",
                "total_space": 16000000000,
                "free_space": 8000000000,
                "type": "removable"
            }
        }


class SystemInfo(BaseModel):
    """系统信息"""
    username: str
    uptime_seconds: int
    platform: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "uptime_seconds": 3600,
                "platform": "Windows"
            }
        }

