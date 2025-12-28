"""
Pydantic 数据模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class USBDeviceInfo(BaseModel):
    """USB 设备信息"""
    device_id: str
    vendor_id: str
    product_id: str
    manufacturer: str
    product: str
    serial_number: str
    bus_number: int
    address: int
    speed: str  # "USB 1.1", "USB 2.0", "USB 3.0"
    usb_version: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "001:002",
                "vendor_id": "0x1234",
                "product_id": "0x5678",
                "manufacturer": "SanDisk",
                "product": "USB Flash Drive",
                "serial_number": "1234567890",
                "bus_number": 1,
                "address": 2,
                "speed": "USB 3.0",
                "usb_version": "3.0"
            }
        }


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

