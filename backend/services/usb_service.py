"""
USB 设备服务（仅支持 Windows）
"""
from typing import List, Optional
import asyncio

from models.schemas import USBDeviceInfo

class USBService:
    """USB 设备服务类"""
    
    def __init__(self):
        self.devices_cache: List[USBDeviceInfo] = []
        self._cache_lock = asyncio.Lock()
    
    async def get_all_devices(self) -> List[USBDeviceInfo]:
        """获取所有 USB 设备"""
        async with self._cache_lock:
            return self.devices_cache.copy()
    
    async def scan_devices(self) -> List[USBDeviceInfo]:
        """扫描 USB 设备"""
        devices = []
        device_ids_seen = set()  # 用于去重
        
        try:
            # 当前策略：优先使用 WMI 方式扫描 USB 设备
            try:
                from services.usb_service_windows import scan_usb_devices_wmi
                wmi_devices = await scan_usb_devices_wmi()
                for dev in wmi_devices:
                    if dev.device_id not in device_ids_seen:
                        devices.append(dev)
                        device_ids_seen.add(dev.device_id)
            except Exception as e:
                print(f"Warning: WMI scan failed: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"Error in scan_devices: {e}")
            import traceback
            traceback.print_exc()
        
        # 更新缓存
        async with self._cache_lock:
            self.devices_cache = devices
        
        print(f"USB scan completed: found {len(devices)} device(s)")
        return devices

    async def get_device_by_id(self, device_id: str) -> Optional[USBDeviceInfo]:
        """根据设备 ID 获取设备信息"""
        devices = await self.get_all_devices()
        for device in devices:
            if device.device_id == device_id:
                return device
        return None

