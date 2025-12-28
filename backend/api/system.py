"""
系统信息 API
"""
from fastapi import APIRouter
from datetime import datetime
import os
import psutil
import getpass

router = APIRouter()


@router.get("/user")
async def get_current_user():
    """获取当前登录用户"""
    try:
        username = getpass.getuser()
        return {
            "username": username,
            "status": "success"
        }
    except Exception as e:
        return {
            "username": "Unknown",
            "status": "error",
            "message": str(e)
        }


@router.get("/uptime")
async def get_system_uptime():
    """获取系统运行时间（秒）"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = int(datetime.now().timestamp() - boot_time)
        return {
            "uptime_seconds": uptime_seconds,
            "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
            "status": "success"
        }
    except Exception as e:
        return {
            "uptime_seconds": 0,
            "status": "error",
            "message": str(e)
        }

