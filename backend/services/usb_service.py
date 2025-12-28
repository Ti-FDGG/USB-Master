"""
USB 设备服务
"""
import platform
from typing import List, Optional
import asyncio

from models.schemas import USBDeviceInfo

# 根据平台导入不同的 USB 库
if platform.system() == "Windows":
    try:
        import pywinusb.hid as hid
        HAS_WINUSB = True
    except ImportError:
        HAS_WINUSB = False
        print("Warning: pywinusb not available, USB detection may be limited")
    
    try:
        import usb.core
        import usb.util
        HAS_PYUSB = True
    except ImportError:
        HAS_PYUSB = False
        print("Warning: pyusb not available, USB detection may be limited")
else:
    # Linux/Mac
    try:
        import usb.core
        import usb.util
        HAS_PYUSB = True
    except ImportError:
        HAS_PYUSB = False
        print("Warning: pyusb not available, USB detection may be limited")
    HAS_WINUSB = False


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
            # 方法1: 使用 pyusb（如果可用）
            if HAS_PYUSB:
                try:
                    pyusb_devices = await self._scan_pyusb()
                    for dev in pyusb_devices:
                        if dev.device_id not in device_ids_seen:
                            devices.append(dev)
                            device_ids_seen.add(dev.device_id)
                except Exception as e:
                    print(f"Warning: pyusb scan failed: {e}")
            
            # 方法2: 使用 pywinusb（Windows HID 设备）
            if HAS_WINUSB and platform.system() == "Windows":
                try:
                    winusb_devices = await self._scan_winusb()
                    for dev in winusb_devices:
                        if dev.device_id not in device_ids_seen:
                            devices.append(dev)
                            device_ids_seen.add(dev.device_id)
                except Exception as e:
                    print(f"Warning: pywinusb scan failed: {e}")
            
            # 方法3: 使用 WMI（Windows 备选方案）
            if platform.system() == "Windows" and len(devices) == 0:
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
            
            # 方法4: 使用注册表（Windows 最后备选）
            if platform.system() == "Windows" and len(devices) == 0:
                try:
                    from services.usb_service_windows import scan_usb_devices_registry
                    reg_devices = await scan_usb_devices_registry()
                    for dev in reg_devices:
                        if dev.device_id not in device_ids_seen:
                            devices.append(dev)
                            device_ids_seen.add(dev.device_id)
                except Exception as e:
                    print(f"Warning: Registry scan failed: {e}")
        except Exception as e:
            print(f"Error in scan_devices: {e}")
            import traceback
            traceback.print_exc()
        
        # 更新缓存
        async with self._cache_lock:
            self.devices_cache = devices
        
        print(f"USB scan completed: found {len(devices)} device(s)")
        return devices
    
    async def _scan_pyusb(self) -> List[USBDeviceInfo]:
        """使用 pyusb 扫描设备"""
        devices = []
        
        try:
            # 在后台线程中运行，避免阻塞
            loop = asyncio.get_event_loop()
            
            def find_devices():
                try:
                    return list(usb.core.find(find_all=True))
                except Exception as e:
                    print(f"Error in usb.core.find: {e}")
                    return []
            
            usb_devices = await loop.run_in_executor(None, find_devices)
            
            for dev in usb_devices:
                try:
                    device_info = await self._get_device_info_pyusb(dev)
                    if device_info:
                        devices.append(device_info)
                except Exception as e:
                    # 某些设备可能无法访问，跳过
                    print(f"Warning: Could not get info for device: {e}")
                    continue
        except Exception as e:
            print(f"Error scanning USB devices with pyusb: {e}")
            import traceback
            traceback.print_exc()
        
        return devices
    
    async def _get_device_info_pyusb(self, dev) -> Optional[USBDeviceInfo]:
        """从 pyusb 设备获取信息"""
        try:
            # 获取字符串描述符（需要设备已打开，某些设备可能失败）
            manufacturer = "Unknown"
            product = "Unknown"
            serial = "Unknown"
            
            try:
                if dev.iManufacturer:
                    manufacturer = usb.util.get_string(dev, dev.iManufacturer)
                if dev.iProduct:
                    product = usb.util.get_string(dev, dev.iProduct)
                if dev.iSerialNumber:
                    serial = usb.util.get_string(dev, dev.iSerialNumber)
            except:
                pass
            
            # 判断 USB 速度（根据设备描述符）
            speed = "USB 2.0"
            if hasattr(dev, 'speed'):
                if dev.speed == 3:  # USB_SPEED_SUPER
                    speed = "USB 3.0"
                elif dev.speed == 2:  # USB_SPEED_HIGH
                    speed = "USB 2.0"
                elif dev.speed == 1:  # USB_SPEED_FULL
                    speed = "USB 1.1"
            
            device_id = f"{dev.bus:03d}:{dev.address:03d}"
            
            return USBDeviceInfo(
                device_id=device_id,
                vendor_id=f"0x{dev.idVendor:04X}",
                product_id=f"0x{dev.idProduct:04X}",
                manufacturer=manufacturer,
                product=product,
                serial_number=serial or "N/A",
                bus_number=dev.bus,
                address=dev.address,
                speed=speed,
                usb_version=f"{dev.bcdUSB >> 8}.{(dev.bcdUSB >> 4) & 0x0F}.{dev.bcdUSB & 0x0F}"
            )
        except Exception as e:
            return None
    
    async def _scan_winusb(self) -> List[USBDeviceInfo]:
        """使用 pywinusb 扫描设备（Windows HID 设备）"""
        devices = []
        
        try:
            loop = asyncio.get_event_loop()
            hid_devices = await loop.run_in_executor(None, lambda: list(hid.find_all_hid_devices()))
            
            for dev in hid_devices:
                try:
                    device_info = USBDeviceInfo(
                        device_id=f"hid_{dev.vendor_id}_{dev.product_id}",
                        vendor_id=f"0x{dev.vendor_id:04X}",
                        product_id=f"0x{dev.product_id:04X}",
                        manufacturer=dev.manufacturer or "Unknown",
                        product=dev.product_name or "Unknown",
                        serial_number=dev.serial_number or "N/A",
                        bus_number=0,  # HID 设备没有总线号
                        address=0,
                        speed="USB 2.0",  # HID 通常是 USB 2.0
                        usb_version="2.0"
                    )
                    devices.append(device_info)
                except:
                    continue
        except Exception as e:
            print(f"Error scanning HID devices: {e}")
        
        return devices
    
    async def get_device_by_id(self, device_id: str) -> Optional[USBDeviceInfo]:
        """根据设备 ID 获取设备信息"""
        devices = await self.get_all_devices()
        for device in devices:
            if device.device_id == device_id:
                return device
        return None

