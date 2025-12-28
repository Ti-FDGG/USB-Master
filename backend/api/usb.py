"""
USB 设备 API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

from services.usb_service import USBService
from models.schemas import USBDeviceInfo

router = APIRouter()
usb_service = USBService()

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


@router.get("/devices", response_model=List[USBDeviceInfo])
async def get_usb_devices():
    """获取所有 USB 设备"""
    try:
        devices = await usb_service.get_all_devices()
        return devices
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in get_usb_devices: {error_detail}")
        # 如果设备列表为空，返回空列表而不是错误
        return []


@router.get("/devices/{device_id}")
async def get_device_info(device_id: str):
    """获取特定设备详情"""
    try:
        device = await usb_service.get_device_by_id(device_id)
        if device:
            return device
        return {"error": "Device not found"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/scan")
async def scan_devices():
    """手动扫描 USB 设备"""
    try:
        devices = await usb_service.scan_devices()
        return {
            "count": len(devices),
            "devices": devices,
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.websocket("/ws/monitor")
async def websocket_usb_monitor(websocket: WebSocket):
    """WebSocket: USB 设备插拔监控"""
    await manager.connect(websocket)
    try:
        # 发送当前设备列表
        devices = await usb_service.get_all_devices()
        await websocket.send_json({
            "type": "initial",
            "devices": devices
        })

        # 保持连接，等待事件
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


# 导出 manager 供其他模块使用
def get_connection_manager():
    return manager

