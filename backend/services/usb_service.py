"""
USB 设备服务（仅支持 Windows）
"""
from typing import List, Optional
import asyncio

from models.schemas import USBDeviceInfo

# 目前暂时仅使用 WMI 方式扫描 USB 设备
# 保留 pyusb / pywinusb 相关导入代码，后续如有需要可重新启用
# try:
#     import pywinusb.hid as hid
#     HAS_WINUSB = True
# except ImportError:
#     HAS_WINUSB = False
#     print("Warning: pywinusb not available, USB detection may be limited")
#
# try:
#     import usb.core
#     import usb.util
#     HAS_PYUSB = True
# except ImportError:
#     HAS_PYUSB = False
#     print("Warning: pyusb not available, USB detection may be limited")


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

            # 如果 WMI 扫描失败或结果为空，可选地使用注册表作为最后备选
            if len(devices) == 0:
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
    
    # async def _scan_pyusb(self) -> List[USBDeviceInfo]:
    #     """使用 pyusb 扫描设备"""
    #     devices = []
    #     usb_devices = []
        
    #     try:
    #         # 在后台线程中运行，避免阻塞
    #         loop = asyncio.get_event_loop()
            
    #         def find_devices():
    #             try:
    #                 return list(usb.core.find(find_all=True))
    #             except Exception as e:
    #                 print(f"Error in usb.core.find: {e}")
    #                 return []
            
    #         usb_devices = await loop.run_in_executor(None, find_devices)
            
    #         # 处理每个设备，确保资源释放
    #         for dev in usb_devices:
    #             try:
    #                 device_info = await self._get_device_info_pyusb(dev)
    #                 if device_info:
    #                     devices.append(device_info)
    #             except Exception as e:
    #                 # 某些设备可能无法访问，跳过
    #                 print(f"Warning: Could not get info for device: {e}")
    #                 continue
    #             finally:
    #                 # 确保设备资源被释放
    #                 try:
    #                     # 如果设备已打开，尝试关闭它
    #                     if dev.is_kernel_driver_active(0) is False:
    #                         # 设备可能被我们或其他程序打开，尝试重置
    #                         try:
    #                             usb.util.release_interface(dev, 0)
    #                         except:
    #                             pass
    #                 except:
    #                     # 忽略释放错误，继续处理下一个设备
    #                     pass
    #     except Exception as e:
    #         print(f"Error scanning USB devices with pyusb: {e}")
    #         import traceback
    #         traceback.print_exc()
    #     finally:
    #         # 清理所有设备资源
    #         for dev in usb_devices:
    #             try:
    #                 # 尝试释放设备资源
    #                 if hasattr(dev, '_ctx') and dev._ctx:
    #                     try:
    #                         usb.util.dispose_resources(dev)
    #                     except:
    #                         pass
    #             except:
    #                 pass
        
    #     return devices
    
    # async def _get_device_info_pyusb(self, dev) -> Optional[USBDeviceInfo]:
    #     """从 pyusb 设备获取信息，确保资源正确释放"""
    #     # 获取字符串描述符（需要设备已打开，某些设备可能失败）
    #     manufacturer = "Unknown"
    #     product = "Unknown"
    #     serial = "Unknown"
        
    #     # 使用上下文管理器确保资源释放
    #     # 注意：我们不主动打开设备，避免锁定
    #     # 只在设备不需要内核驱动且可以安全打开时才尝试获取字符串
    #     try:
    #         # 检查设备是否使用内核驱动
    #         # 如果使用内核驱动，我们不打开它，避免与系统驱动冲突
    #         needs_kernel_driver = False
    #         try:
    #             needs_kernel_driver = dev.is_kernel_driver_active(0)
    #         except:
    #             # 某些设备可能不支持此检查，假设需要内核驱动
    #             needs_kernel_driver = True
            
    #         # 只有在不需要内核驱动时才尝试打开设备获取字符串
    #         if not needs_kernel_driver:
    #             loop = asyncio.get_event_loop()
                
    #             def safe_get_strings():
    #                 """安全地获取字符串描述符，确保资源释放"""
    #                 device_opened = False
    #                 interface_claimed = False
    #                 interface_num = 0
    #                 strings = {}
                    
    #                 try:
    #                     # 尝试打开设备
    #                     try:
    #                         dev.open()
    #                         device_opened = True
    #                     except Exception as e:
    #                         # 设备可能已被其他程序打开，直接返回空字典
    #                         return strings
                        
    #                     # 尝试获取接口（某些设备需要）
    #                     try:
    #                         usb.util.claim_interface(dev, 0)
    #                         interface_claimed = True
    #                         interface_num = 0
    #                     except:
    #                         # 接口可能已被占用，继续尝试获取字符串
    #                         pass
                        
    #                     # 获取字符串描述符
    #                     if dev.iManufacturer:
    #                         try:
    #                             strings['manufacturer'] = usb.util.get_string(dev, dev.iManufacturer)
    #                         except:
    #                             pass
    #                     if dev.iProduct:
    #                         try:
    #                             strings['product'] = usb.util.get_string(dev, dev.iProduct)
    #                         except:
    #                             pass
    #                     if dev.iSerialNumber:
    #                         try:
    #                             strings['serial'] = usb.util.get_string(dev, dev.iSerialNumber)
    #                         except:
    #                             pass
                        
    #                     return strings
    #                 finally:
    #                     # 确保释放所有资源
    #                     try:
    #                         if interface_claimed:
    #                             try:
    #                                 usb.util.release_interface(dev, interface_num)
    #                             except:
    #                                 pass
    #                     except:
    #                         pass
                        
    #                     try:
    #                         if device_opened:
    #                             try:
    #                                 dev.close()
    #                             except:
    #                                 pass
    #                     except:
    #                         pass
                
    #             # 使用超时执行（3秒超时，避免长时间锁定）
    #             try:
    #                 strings = await asyncio.wait_for(
    #                     loop.run_in_executor(None, safe_get_strings),
    #                     timeout=3.0
    #                 )
    #                 manufacturer = strings.get('manufacturer', 'Unknown')
    #                 product = strings.get('product', 'Unknown')
    #                 serial = strings.get('serial', 'Unknown')
    #             except asyncio.TimeoutError:
    #                 print(f"Warning: Timeout getting strings for device {dev.bus}:{dev.address}")
    #             except Exception as e:
    #                 print(f"Warning: Error getting strings: {e}")
    #         else:
    #             # 设备使用内核驱动，尝试不打开设备直接获取字符串
    #             # 这通常不会工作，但某些情况下可能可以
    #             try:
    #                 if dev.iManufacturer:
    #                     manufacturer = usb.util.get_string(dev, dev.iManufacturer)
    #                 if dev.iProduct:
    #                     product = usb.util.get_string(dev, dev.iProduct)
    #                 if dev.iSerialNumber:
    #                     serial = usb.util.get_string(dev, dev.iSerialNumber)
    #             except:
    #                 # 如果失败，使用默认值（这是正常的，因为设备未打开）
    #                 pass
    #     except Exception as e:
    #         # 获取字符串失败，使用默认值
    #         print(f"Warning: Error getting device strings: {e}")
        
    #     # 判断 USB 速度（根据设备描述符）
    #     speed = "USB 2.0"
    #     try:
    #         if hasattr(dev, 'speed'):
    #             if dev.speed == 3:  # USB_SPEED_SUPER
    #                 speed = "USB 3.0"
    #             elif dev.speed == 2:  # USB_SPEED_HIGH
    #                 speed = "USB 2.0"
    #             elif dev.speed == 1:  # USB_SPEED_FULL
    #                 speed = "USB 1.1"
    #     except:
    #         pass
        
    #     try:
    #         device_id = f"{dev.bus:03d}:{dev.address:03d}"
            
    #         return USBDeviceInfo(
    #             device_id=device_id,
    #             vendor_id=f"0x{dev.idVendor:04X}",
    #             product_id=f"0x{dev.idProduct:04X}",
    #             manufacturer=manufacturer,
    #             product=product,
    #             serial_number=serial or "N/A",
    #             bus_number=dev.bus,
    #             address=dev.address,
    #             speed=speed,
    #             usb_version=f"{dev.bcdUSB >> 8}.{(dev.bcdUSB >> 4) & 0x0F}.{dev.bcdUSB & 0x0F}"
    #         )
    #     except Exception as e:
    #         print(f"Error in _get_device_info_pyusb: {e}")
    #         return None
    
    # async def _scan_winusb(self) -> List[USBDeviceInfo]:
    #     """使用 pywinusb 扫描设备（Windows HID 设备）"""
    #     devices = []
    #     hid_devices = []
        
    #     try:
    #         loop = asyncio.get_event_loop()
            
    #         def find_hid_devices():
    #             try:
    #                 return list(hid.find_all_hid_devices())
    #             except Exception as e:
    #                 print(f"Error in hid.find_all_hid_devices: {e}")
    #                 return []
            
    #         hid_devices = await loop.run_in_executor(None, find_hid_devices)
            
    #         for dev in hid_devices:
    #             try:
    #                 device_info = USBDeviceInfo(
    #                     device_id=f"hid_{dev.vendor_id}_{dev.product_id}",
    #                     vendor_id=f"0x{dev.vendor_id:04X}",
    #                     product_id=f"0x{dev.product_id:04X}",
    #                     manufacturer=dev.manufacturer or "Unknown",
    #                     product=dev.product_name or "Unknown",
    #                     serial_number=dev.serial_number or "N/A",
    #                     bus_number=0,  # HID 设备没有总线号
    #                     address=0,
    #                     speed="USB 2.0",  # HID 通常是 USB 2.0
    #                     usb_version="2.0"
    #                 )
    #                 devices.append(device_info)
    #             except Exception as e:
    #                 print(f"Warning: Could not process HID device: {e}")
    #                 continue
    #     except Exception as e:
    #         print(f"Error scanning HID devices: {e}")
    #     finally:
    #         # 清理 HID 设备资源
    #         for dev in hid_devices:
    #             try:
    #                 # pywinusb 设备对象在不再使用时应该自动释放
    #                 # 但为了安全，我们显式清理
    #                 if hasattr(dev, 'close'):
    #                     try:
    #                         dev.close()
    #                     except:
    #                         pass
    #             except:
    #                 pass
        
    #     return devices
   # 以下 pyusb / pywinusb 相关方法暂时废弃，只保留历史代码以便将来需要时参考
    # 当前扫描逻辑仅使用 WMI，请勿调用这些方法
    #
    # async def _scan_pyusb(self) -> List[USBDeviceInfo]:
    #     ...
    #
    # async def _get_device_info_pyusb(self, dev) -> Optional[USBDeviceInfo]:
    #     ...
    #
    # async def _scan_winusb(self) -> List[USBDeviceInfo]:
    #     ...
    
    async def get_device_by_id(self, device_id: str) -> Optional[USBDeviceInfo]:
        """根据设备 ID 获取设备信息"""
        devices = await self.get_all_devices()
        for device in devices:
            if device.device_id == device_id:
                return device
        return None

