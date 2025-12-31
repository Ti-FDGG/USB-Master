"""
USB 设备服务（仅支持 Windows）

使用 C++ usb_scanner 实现 USB 设备扫描。
"""
from typing import List, Optional
import asyncio

from models.schemas import USBDeviceInfo
from services.usb_service_cpp import scan_usb_devices_cpp


def make_device_id(device: USBDeviceInfo) -> str:
    """
    基于设备关键属性生成稳定的设备 ID，用于按 ID 查询和去重。
    注意：此 ID 仅在 Python 层使用，C++ 模型本身不包含该字段。
    """
    # 使用与前端类似的组合键策略
    parts = [
        device.vendorId or "",
        device.productId or "",
        device.serialNumber or "",
        device.busNumber or "",
        device.portNumber or "",
        device.devicePath or "",
    ]
    return "|".join(parts)


class USBService:
    """USB 设备服务类（基于 C++ usb_scanner 实现）"""

    def __init__(self):
        self.devices_cache: List[USBDeviceInfo] = []
        self._cache_lock = asyncio.Lock()

    async def get_all_devices(self) -> List[USBDeviceInfo]:
        """获取所有 USB 设备（返回缓存）"""
        async with self._cache_lock:
            return self.devices_cache.copy()

    async def scan_devices(self) -> List[USBDeviceInfo]:
        """扫描 USB 设备（使用 C++ usb_scanner）"""
        devices: List[USBDeviceInfo] = []
        seen_ids = set()

        try:
            cpp_devices = await scan_usb_devices_cpp()
            for dev in cpp_devices:
                dev_id = make_device_id(dev)
                if dev_id in seen_ids:
                    continue
                seen_ids.add(dev_id)
                devices.append(dev)
        except Exception as e:
            print(f"Error in scan_devices (C++ usb_scanner): {e}")
            import traceback

            traceback.print_exc()

        # 更新缓存
        async with self._cache_lock:
            self.devices_cache = devices

        print(f"USB scan completed (C++): found {len(devices)} device(s)")
        return devices

    async def get_device_by_id(self, device_id: str) -> Optional[USBDeviceInfo]:
        """根据设备 ID 获取设备信息（基于 make_device_id 生成的组合键）"""
        devices = await self.get_all_devices()
        for device in devices:
            if make_device_id(device) == device_id:
                return device
        return None
