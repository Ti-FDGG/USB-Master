"""
Windows USB 设备检测（使用 Python WMI）
当前项目仅支持 Windows，这里提供基于 python-wmi 的实现
"""
import re
from typing import List, Optional
import asyncio
import wmi
import pythoncom

from models.schemas import USBDeviceInfo


async def scan_usb_devices_wmi() -> List[USBDeviceInfo]:
    """
    使用 python-wmi 直接访问 WMI，扫描 USB 设备。
    - 解析 VID/PID
    - 提取序列号
    - 基础设备分类（storage/hid/hub/other）
    - 总线号 / 地址目前为逻辑值（后续可结合更底层接口优化）
    """
    devices: List[USBDeviceInfo] = []

    try:
        loop = asyncio.get_event_loop()

        def query_wmi_devices():
            """
            在同步线程中查询 WMI，返回 Win32_PnPEntity 对象列表。
            注意：由于该函数会在线程池中的新线程里执行，必须在该线程中
            手动初始化 COM（pythoncom.CoInitialize），否则 python-wmi
            会抛出 x_wmi_uninitialised_thread 异常。
            """
            pythoncom.CoInitialize()
            try:
                conn = wmi.WMI(namespace="root\\cimv2")
                all_pnp = conn.Win32_PnPEntity()
                usb_pnp = []

                for dev in all_pnp:
                    try:
                        pnp_id = getattr(dev, "PNPDeviceID", "") or ""
                        if not pnp_id:
                            continue

                        upper_id = pnp_id.upper()
                        # 仅保留 USB / USB 存储 相关的 PnP 实体
                        if upper_id.startswith("USB\\") or upper_id.startswith("USBSTOR\\"):
                            usb_pnp.append(dev)
                    except Exception:
                        continue

                return usb_pnp
            finally:
                # 确保线程退出前释放 COM
                pythoncom.CoUninitialize()

        raw_devices = await loop.run_in_executor(None, query_wmi_devices)

        for dev in raw_devices:
            try:
                info = _parse_wmi_pnp_entity(dev)
                if info:
                    devices.append(info)
            except Exception as e:
                print(f"Warning: Could not parse WMI USB device: {e}")
                continue
    except Exception as e:
        print(f"Error scanning USB devices with python-wmi: {e}")
        import traceback
        traceback.print_exc()

    return devices


def _parse_wmi_pnp_entity(dev) -> Optional[USBDeviceInfo]:
    """
    从 Win32_PnPEntity 对象解析 USBDeviceInfo
    尽量满足实验要求中的字段：
    - 制造商、产品名
    - VID/PID
    - 序列号（从 PNPDeviceID 中解析）
    - 基础设备分类（storage/hid/hub/other）
    - 传输速率/USB 版本：基于名称/描述的简单推断，不再一刀切
    """
    try:
        pnp_id = str(getattr(dev, "PNPDeviceID", "") or "")
        if not pnp_id:
            return None

        device_id_raw = str(getattr(dev, "DeviceID", "") or "")
        service = str(getattr(dev, "Service", "") or "")
        manufacturer = str(getattr(dev, "Manufacturer", "") or "") or "Unknown"
        name = str(getattr(dev, "Name", "") or "")
        description = str(getattr(dev, "Description", "") or "")

        # 1. 提取 VID / PID
        vendor_id = "0x0000"
        product_id = "0x0000"

        vid_match = re.search(r"VID_([0-9A-F]{4})", pnp_id, re.IGNORECASE)
        pid_match = re.search(r"PID_([0-9A-F]{4})", pnp_id, re.IGNORECASE)

        if not vid_match and device_id_raw:
            vid_match = re.search(r"VID_([0-9A-F]{4})", device_id_raw, re.IGNORECASE)
        if not pid_match and device_id_raw:
            pid_match = re.search(r"PID_([0-9A-F]{4})", device_id_raw, re.IGNORECASE)

        if vid_match:
            vendor_id = f"0x{vid_match.group(1).upper()}"
        if pid_match:
            product_id = f"0x{pid_match.group(1).upper()}"

        # 多数非 USB 设备不会包含 VID/PID，这里做一层过滤
        if vendor_id == "0x0000" and product_id == "0x0000":
            return None

        # 2. 解析产品名称
        product = description or name or "Unknown Device"

        # 3. 从 PNPDeviceID 中解析序列号
        serial_number = "N/A"
        try:
            # 典型格式: USB\VID_XXXX&PID_YYYY\SERIAL[&接口编号]
            parts = pnp_id.split("\\")
            if len(parts) >= 3:
                tail = parts[-1]
                # 去掉末尾类似 &0 / &1 / &MI_01 等接口标记，只保留序列本体
                serial_candidate = tail.split("&")[0]
                serial_candidate = serial_candidate.strip()
                if serial_candidate and serial_candidate.upper() not in {"USB", "ROOT_HUB"}:
                    serial_number = serial_candidate
        except Exception:
            pass

        # 4. 基础设备分类
        upper_id = pnp_id.upper()
        upper_service = service.upper()
        upper_name = name.upper()

        device_type = "other"
        if upper_id.startswith("USBSTOR\\"):
            device_type = "storage"
        elif "HID" in upper_service or "HID" in upper_id or "HID" in upper_name:
            device_type = "hid"
        elif "HUB" in upper_name or "USBHUB" in upper_service:
            device_type = "hub"

        # 5. 总线号 / 地址
        # 目前从 PNP ID 很难精确反推出物理总线和地址，这里先给出逻辑默认值 0
        # 后续可以通过关联 Win32_USBController / 低层接口做进一步优化
        bus_number = 0
        address = 0

        # 6. 传输速率 / USB 版本（基于名称/描述的简单推断）
        upper_desc = product.upper()
        speed = "Unknown"
        usb_version = "Unknown"

        if "USB 3" in upper_desc or "USB3" in upper_desc or "USB 3." in upper_desc:
            speed = "USB 3.0"
            usb_version = "3.0"
        elif "USB 2" in upper_desc or "USB2" in upper_desc:
            speed = "USB 2.0"
            usb_version = "2.0"
        else:
            # 无明显标记时，保留 Unknown，避免误导
            speed = "Unknown"
            usb_version = "Unknown"

        # 7. 生成稳定的内部设备 ID（基于 PNPDeviceID）
        import hashlib

        unique_str = pnp_id or device_id_raw
        hash_id = hashlib.md5(unique_str.encode("utf-8", errors="ignore")).hexdigest()[:8]
        device_id_str = f"wmi_{vendor_id}_{product_id}_{hash_id}"

        return USBDeviceInfo(
            device_id=device_id_str,
            vendor_id=vendor_id,
            product_id=product_id,
            manufacturer=manufacturer,
            product=product,
            serial_number=serial_number,
            bus_number=bus_number,
            address=address,
            speed=speed,
            usb_version=usb_version,
            device_type=device_type,
        )
    except Exception as e:
        print(f"Error parsing WMI PnP entity: {e}")
        return None


# 保留注册表方法作为备选（暂时不使用）
async def scan_usb_devices_registry() -> List[USBDeviceInfo]:
    """使用 Windows 注册表扫描 USB 设备（备选方案）"""
    # 暂时禁用，优先使用 WMI
    return []
