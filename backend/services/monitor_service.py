"""
USB 设备监控服务
"""
import os
import asyncio
import platform
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Optional

from services.usb_service import USBService
from api.usb import get_connection_manager

usb_service = USBService()
observer: Optional[Observer] = None


class USBEventHandler(FileSystemEventHandler):
    """USB 设备文件系统事件处理器"""
    
    def __init__(self):
        self.last_scan_time = 0
        self.scan_interval = 2  # 2秒扫描间隔，避免频繁扫描
    
    async def _notify_device_change(self, event_type: str):
        """通知设备变化"""
        import time
        current_time = time.time()
        
        # 节流：避免频繁扫描
        if current_time - self.last_scan_time < self.scan_interval:
            return
        
        self.last_scan_time = current_time
        
        # 重新扫描设备
        devices = await usb_service.scan_devices()
        
        # 通过 WebSocket 广播
        manager = get_connection_manager()
        await manager.broadcast({
            "type": event_type,
            "devices": [d.model_dump() for d in devices],
            "timestamp": current_time
        })
    
    def on_created(self, event):
        """设备插入"""
        if not event.is_directory:
            return
        
        # 检查是否为 USB 设备挂载点
        if self._is_usb_mount_point(event.src_path):
            asyncio.create_task(self._notify_device_change("device_connected"))
    
    def on_deleted(self, event):
        """设备拔出"""
        if not event.is_directory:
            return
        
        if self._is_usb_mount_point(event.src_path):
            asyncio.create_task(self._notify_device_change("device_disconnected"))
    
    def _is_usb_mount_point(self, path: str) -> bool:
        """判断是否为 USB 设备挂载点"""
        # Windows: 检查是否为驱动器根目录
        if platform.system() == "Windows":
            return len(path) == 3 and path[1] == ":" and path[2] == "\\"
        
        # Linux: 检查 /media, /mnt, /run/media 下的目录
        usb_paths = ["/media", "/mnt", "/run/media"]
        for usb_path in usb_paths:
            if path.startswith(usb_path):
                return True
        
        return False


def start_usb_monitor():
    """启动 USB 设备监控"""
    global observer
    
    if observer is not None:
        return
    
    event_handler = USBEventHandler()
    observer = Observer()
    
    if platform.system() == "Windows":
        # Windows: 监控所有驱动器根目录
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    observer.schedule(event_handler, drive, recursive=False)
                except:
                    pass
    else:
        # Linux: 监控 USB 挂载点目录
        watch_paths = ["/media", "/mnt", "/run/media"]
        for path in watch_paths:
            if os.path.exists(path):
                try:
                    observer.schedule(event_handler, path, recursive=True)
                except:
                    pass
    
    observer.start()
    print("USB monitor started")


def stop_usb_monitor():
    """停止 USB 设备监控"""
    global observer
    
    if observer is not None:
        observer.stop()
        observer.join()
        observer = None
        print("USB monitor stopped")

