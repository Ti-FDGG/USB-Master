"""
Windows USB 设备检测（使用 WMI）
作为 pyusb 和 pywinusb 的备选方案（项目仅支持 Windows）
"""
import subprocess
import json
import re
from typing import List, Optional
import asyncio
import os

from models.schemas import USBDeviceInfo


async def scan_usb_devices_wmi() -> List[USBDeviceInfo]:
    """使用 WMI (Windows Management Instrumentation) 扫描 USB 设备"""
    devices = []
    
    try:
        # 使用 PowerShell 查询 WMI，输出到临时文件避免编码问题
        import tempfile
        
        ps_script = """
        $OutputEncoding = [System.Text.Encoding]::UTF8
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8

        $output = @()
        Get-WmiObject Win32_USBControllerDevice | ForEach-Object {
            $device = [wmi]$_.Dependent
            $output += [PSCustomObject]@{
                DeviceID = $device.DeviceID
                Description = $device.Description
                Manufacturer = $device.Manufacturer
                Name = $device.Name
                PNPDeviceID = $device.PNPDeviceID
                Service = $device.Service
            }
        }
        Get-WmiObject Win32_USBHub | ForEach-Object {
            $output += [PSCustomObject]@{
                DeviceID = $_.DeviceID
                Description = $_.Description
                Manufacturer = $_.Manufacturer
                Name = $_.Name
                PNPDeviceID = $_.PNPDeviceID
                Service = $_.Service
            }
        }
        $output | ConvertTo-Json -Depth 3
        """
        
        loop = asyncio.get_event_loop()
        
        def run_powershell():
            script_path = None
            try:
                # 使用 utf-8-sig 写入临时文件，确保 PowerShell 正确读取脚本内容
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8-sig') as f:
                    f.write(ps_script)
                    script_path = f.name

                # 执行命令
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path],
                    capture_output=True,
                    timeout=15,
                    shell=False
                )

                # 2. 优先使用 utf-8-sig 解码，它能自动处理 UTF-8 的 BOM 标记
                def decode_output(raw_bytes):
                    for enc in ['utf-8-sig', 'gbk', 'utf-8']:
                        try:
                            return raw_bytes.decode(enc)
                        except UnicodeDecodeError:
                            continue
                    return raw_bytes.decode('utf-8', errors='replace')

                stdout = decode_output(result.stdout)
                stderr = decode_output(result.stderr)

                class Result:
                    def __init__(self, returncode, stdout, stderr):
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr

                return Result(result.returncode, stdout, stderr)

            except Exception as e:
                class ErrorResult:
                    def __init__(self, err):
                        self.returncode = 1
                        self.stdout = ""
                        self.stderr = str(err)
                return ErrorResult(e)
            finally:
                if script_path and os.path.exists(script_path):
                    os.unlink(script_path)

        result = await loop.run_in_executor(None, run_powershell)

        # TODO: 测试用代码，未来记得删除
        # # 将 result 的内容输出到一个文本文档当中
        # try:
        #     with open("usb_wmi_result.txt", "w", encoding="utf-8") as f:
        #         f.write(f"Return code: {result.returncode}\n")
        #         f.write("STDOUT:\n")
        #         f.write(result.stdout if isinstance(result.stdout, str) else str(result.stdout))
        #         f.write("\nSTDERR:\n")
        #         f.write(result.stderr if isinstance(result.stderr, str) else str(result.stderr))
        # except Exception as e:
        #     print(f"Failed to write result to usb_wmi_result.txt: {e}")
        
        if result.returncode == 0 and result.stdout:
            try:
                output = result.stdout.strip()
                # 清理输出
                if output.startswith('['):
                    device_list = json.loads(output)
                elif output.startswith('{'):
                    device_list = [json.loads(output)]
                else:
                    # 处理多行 JSON
                    device_list = []
                    for line in output.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('{') or line.startswith('[')):
                            try:
                                if line.startswith('['):
                                    device_list.extend(json.loads(line))
                                else:
                                    device_list.append(json.loads(line))
                            except:
                                pass
                
                for device_data in device_list:
                    try:
                        device_info = _parse_wmi_device(device_data)
                        if device_info:
                            devices.append(device_info)
                    except Exception as e:
                        print(f"Warning: Could not parse WMI device: {e}")
                        continue
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse WMI JSON output: {e}")
                print(f"Output preview: {result.stdout[:500]}")
    except Exception as e:
        print(f"Error scanning USB devices with WMI: {e}")
        import traceback
        traceback.print_exc()
    
    return devices


def _parse_wmi_device(device_data: dict) -> Optional[USBDeviceInfo]:
    """解析 WMI 设备数据"""
    try:
        pnp_id = str(device_data.get('PNPDeviceID', '') or '')
        device_id = str(device_data.get('DeviceID', '') or '')
        
        # 从 PNPDeviceID 提取 Vendor ID 和 Product ID
        vendor_id = "0x0000"
        product_id = "0x0000"
        
        vid_match = re.search(r'VID_([0-9A-F]{4})', pnp_id, re.IGNORECASE)
        pid_match = re.search(r'PID_([0-9A-F]{4})', pnp_id, re.IGNORECASE)
        
        if not vid_match:
            vid_match = re.search(r'VID_([0-9A-F]{4})', device_id, re.IGNORECASE)
        if not pid_match:
            pid_match = re.search(r'PID_([0-9A-F]{4})', device_id, re.IGNORECASE)
        
        if vid_match:
            vendor_id = f"0x{vid_match.group(1).upper()}"
        if pid_match:
            product_id = f"0x{pid_match.group(1).upper()}"
        
        # 如果仍然没有 VID/PID，检查是否是 USB Hub/Controller
        if vendor_id == "0x0000" and product_id == "0x0000":
            service = str(device_data.get('Service', '') or '').lower()
            if 'usbhub' not in service and 'usbcontroller' not in service:
                # 不是 USB Hub 或控制器，且没有 VID/PID，跳过
                return None
        
        # 提取总线号和地址
        bus_number = 0
        address = 0
        
        bus_match = re.search(r'BUS_(\d+)', device_id, re.IGNORECASE)
        addr_match = re.search(r'ADDR_(\d+)', device_id, re.IGNORECASE)
        
        if bus_match:
            bus_number = int(bus_match.group(1))
        if addr_match:
            address = int(addr_match.group(1))
        
        # 处理字符串，清理编码问题
        manufacturer = str(device_data.get('Manufacturer', '') or 'Unknown')
        description = str(device_data.get('Description', '') or '')
        name = str(device_data.get('Name', '') or '')
        
        product = description or name or "Unknown Device"
        
        # 清理可能的乱码
        manufacturer = manufacturer.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        product = product.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
        
        # 生成唯一设备 ID
        import hashlib
        unique_str = f"{pnp_id}_{device_id}"
        hash_id = hashlib.md5(unique_str.encode()).hexdigest()[:8]
        device_id_str = f"wmi_{vendor_id}_{product_id}_{hash_id}"
        
        return USBDeviceInfo(
            device_id=device_id_str,
            vendor_id=vendor_id,
            product_id=product_id,
            manufacturer=manufacturer or "Unknown",
            product=product or "Unknown",
            serial_number="N/A",
            bus_number=bus_number,
            address=address,
            speed="USB 2.0",
            usb_version="2.0"
        )
    except Exception as e:
        print(f"Error parsing WMI device: {e}")
        return None


# 保留注册表方法作为备选（暂时不使用）
async def scan_usb_devices_registry() -> List[USBDeviceInfo]:
    """使用 Windows 注册表扫描 USB 设备（备选方案）"""
    # 暂时禁用，优先使用 WMI
    return []
