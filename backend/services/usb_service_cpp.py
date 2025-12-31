"""
Windows USB 设备检测（使用 C++ usb_scanner 模块）

通过 pybind11 绑定的 usb_scanner.pyd 调用 C++ 实现，返回与 C++ 结构体
USBDeviceInfo 完全一致的数据模型。
"""

from typing import List
import asyncio

from models.schemas import USBDeviceInfo


def _scan_usb_devices_cpp_sync() -> List[USBDeviceInfo]:
    """
    在同步上下文中调用 C++ USBScanner，并返回 Pydantic USBDeviceInfo 列表。
    """
    try:
        from cpp_bindings.usb_scanner import USBScanner  # type: ignore[import]
    except ImportError as e:
        raise RuntimeError(
            "usb_scanner 模块未找到，请确认已在 cpp_bindings 目录下编译生成 usb_scanner.pyd"
        ) from e

    scanner = USBScanner()
    cpp_devices = scanner.scanUSBDevices()

    devices: List[USBDeviceInfo] = []
    for d in cpp_devices:
        # 利用 Pydantic 的 from_attributes 支持，直接从 C++ 对象属性构造
        devices.append(USBDeviceInfo.model_validate(d))

    return devices


async def scan_usb_devices_cpp() -> List[USBDeviceInfo]:
    """
    异步封装：在事件循环的线程池中调用同步扫描函数。
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _scan_usb_devices_cpp_sync)


