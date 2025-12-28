"""
文件管理 API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import os
import shutil
import time
from pathlib import Path

from services.file_service import FileService
from models.schemas import FileEntry, DriveInfo

router = APIRouter()
file_service = FileService()


@router.get("/drives", response_model=List[DriveInfo])
async def get_removable_drives():
    """获取可移动驱动器列表"""
    try:
        drives = await file_service.get_removable_drives()
        return drives
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in get_removable_drives: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[FileEntry])
async def list_files(
    path: str = Query(..., description="目录路径"),
    show_hidden: bool = Query(False, description="是否显示隐藏文件")
):
    """列出目录内容"""
    try:
        # 验证路径安全性
        if not file_service.is_safe_path(path):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        files = await file_service.list_directory(path, show_hidden)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_text_file(
    path: str = Query(..., description="文件路径"),
    content: str = Query(..., description="文件内容")
):
    """创建文本文件"""
    try:
        if not file_service.is_safe_path(path):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        start_time = time.time()
        result = await file_service.create_text_file(path, content)
        end_time = time.time()
        
        # 计算传输速率
        size = len(content.encode('utf-8'))
        duration = end_time - start_time
        speed = size / duration if duration > 0 else 0
        
        return {
            "status": "success",
            "path": path,
            "size": size,
            "duration_ms": duration * 1000,
            "speed_bytes_per_sec": speed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    target_path: str = Query(..., description="目标路径（目录）")
):
    """上传文件到 U 盘"""
    try:
        if not file_service.is_safe_path(target_path):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        start_time = time.time()
        result = await file_service.upload_file(file, target_path)
        end_time = time.time()
        
        # 计算传输速率
        file_size = result.get("size", 0)
        duration = end_time - start_time
        speed = file_size / duration if duration > 0 else 0
        
        return {
            "status": "success",
            "filename": file.filename,
            "path": result.get("path"),
            "size": file_size,
            "duration_ms": duration * 1000,
            "speed_bytes_per_sec": speed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_file(
    path: str = Query(..., description="文件或目录路径")
):
    """删除文件或目录"""
    try:
        if not file_service.is_safe_path(path):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        result = await file_service.delete_path(path)
        return {
            "status": "success",
            "path": path,
            "type": result.get("type")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
async def download_file(
    path: str = Query(..., description="文件路径")
):
    """下载文件"""
    try:
        if not file_service.is_safe_path(path):
            raise HTTPException(status_code=403, detail="Invalid path")
        
        if not os.path.isfile(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path,
            filename=os.path.basename(path),
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

