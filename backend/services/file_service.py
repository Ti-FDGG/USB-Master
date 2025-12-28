"""
文件操作服务
"""
import os
import platform
import shutil
import aiofiles
from pathlib import Path
from typing import List, Optional
import asyncio

from models.schemas import FileEntry, DriveInfo

# Windows 特定导入
if platform.system() == "Windows":
    try:
        import win32api
        import win32file
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
        print("Warning: pywin32 not available, drive detection may be limited")


class FileService:
    """文件操作服务类"""
    
    def __init__(self):
        self.allowed_drives = set()
    
    async def get_removable_drives(self) -> List[DriveInfo]:
        """获取可移动驱动器列表"""
        drives = []
        
        if platform.system() == "Windows":
            drives = await self._get_windows_drives()
        else:
            drives = await self._get_linux_drives()
        
        # 更新允许的驱动器列表
        self.allowed_drives = {d.path for d in drives}
        
        return drives
    
    async def _get_windows_drives(self) -> List[DriveInfo]:
        """获取 Windows 可移动驱动器"""
        drives = []
        
        if HAS_WIN32:
            try:
                drive_strings = win32api.GetLogicalDriveStrings()
                drive_list = drive_strings.split('\000')[:-1]
                
                for drive in drive_list:
                    try:
                        drive_type = win32file.GetDriveType(drive)
                        if drive_type == win32file.DRIVE_REMOVABLE:
                            # 获取驱动器信息
                            label = "Removable Disk"
                            try:
                                volume_info = win32api.GetVolumeInformation(drive)
                                if volume_info and len(volume_info) > 0:
                                    label = volume_info[0] or "Removable Disk"
                            except Exception as e:
                                print(f"Warning: Could not get volume info for {drive}: {e}")
                                label = "Removable Disk"
                            
                            # 获取总空间和可用空间
                            total, free = 0, 0
                            try:
                                usage = shutil.disk_usage(drive)
                                total = usage.total
                                free = usage.free
                            except Exception as e:
                                print(f"Warning: Could not get disk usage for {drive}: {e}")
                            
                            drives.append(DriveInfo(
                                path=drive,
                                label=label,
                                total_space=total,
                                free_space=free,
                                type="removable"
                            ))
                    except Exception as e:
                        print(f"Warning: Error processing drive {drive}: {e}")
                        continue
            except Exception as e:
                print(f"Error getting Windows drives with win32api: {e}")
                # 回退到简单方法
                pass
        
        # 如果 win32api 失败或不可用，使用回退方案
        if not drives and not HAS_WIN32:
            # 回退方案：检查常见驱动器字母（仅当没有 win32api 时）
            for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    try:
                        usage = shutil.disk_usage(drive)
                        # 简单判断：如果空间小于 500GB，可能是可移动设备
                        # 或者检查驱动器类型（需要 win32api）
                        drives.append(DriveInfo(
                            path=drive,
                            label=f"Drive {letter}",
                            total_space=usage.total,
                            free_space=usage.free,
                            type="removable"
                        ))
                    except Exception as e:
                        print(f"Warning: Could not access drive {drive}: {e}")
                        continue
        
        # 即使没有找到驱动器，也返回空列表而不是错误
        return drives
    
    async def _get_linux_drives(self) -> List[DriveInfo]:
        """获取 Linux 可移动驱动器（挂载点）"""
        drives = []
        
        # 检查 /media 和 /mnt 目录
        media_paths = ["/media", "/mnt", "/run/media"]
        
        for base_path in media_paths:
            if os.path.exists(base_path):
                try:
                    for item in os.listdir(base_path):
                        full_path = os.path.join(base_path, item)
                        if os.path.isdir(full_path) and os.path.ismount(full_path):
                            try:
                                total, free = shutil.disk_usage(full_path)[:2]
                                drives.append(DriveInfo(
                                    path=full_path,
                                    label=item,
                                    total_space=total,
                                    free_space=free,
                                    type="removable"
                                ))
                            except:
                                pass
                except:
                    pass
        
        return drives
    
    def is_safe_path(self, path: str) -> bool:
        """验证路径是否安全（防止路径遍历攻击）"""
        try:
            # 规范化路径
            normalized = os.path.normpath(path)
            
            # 检查是否在允许的驱动器内
            if self.allowed_drives:
                for drive in self.allowed_drives:
                    if normalized.startswith(os.path.normpath(drive)):
                        return True
                return False
            
            # 如果没有设置允许的驱动器，检查是否为绝对路径且存在
            if os.path.isabs(normalized):
                # 检查是否包含 .. 等危险字符
                if ".." in normalized or normalized.startswith("/"):
                    # 在 Windows 上，允许驱动器路径
                    if platform.system() == "Windows" and len(normalized) >= 3 and normalized[1] == ":":
                        return True
                    return False
                return True
            
            return False
        except:
            return False
    
    async def list_directory(self, path: str, show_hidden: bool = False) -> List[FileEntry]:
        """列出目录内容"""
        if not self.is_safe_path(path):
            raise ValueError("Invalid or unsafe path")
        
        if not os.path.isdir(path):
            raise ValueError("Path is not a directory")
        
        entries = []
        
        try:
            loop = asyncio.get_event_loop()
            items = await loop.run_in_executor(None, os.listdir, path)
            
            for item in items:
                # 跳过隐藏文件（如果不需要显示）
                if not show_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item)
                
                try:
                    stat = await loop.run_in_executor(None, os.stat, item_path)
                    is_dir = os.path.isdir(item_path)
                    
                    entries.append(FileEntry(
                        name=item,
                        path=item_path,
                        is_directory=is_dir,
                        size=stat.st_size if not is_dir else None,
                        modified_time=stat.st_mtime
                    ))
                except:
                    continue
        except Exception as e:
            raise ValueError(f"Failed to list directory: {str(e)}")
        
        return entries
    
    async def create_text_file(self, path: str, content: str) -> dict:
        """创建文本文件"""
        if not self.is_safe_path(path):
            raise ValueError("Invalid or unsafe path")
        
        # 确保目录存在
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return {"path": path, "size": len(content.encode('utf-8'))}
        except Exception as e:
            raise ValueError(f"Failed to create file: {str(e)}")
    
    async def upload_file(self, file, target_dir: str) -> dict:
        """上传文件到目标目录"""
        if not self.is_safe_path(target_dir):
            raise ValueError("Invalid or unsafe path")
        
        if not os.path.isdir(target_dir):
            raise ValueError("Target path is not a directory")
        
        target_path = os.path.join(target_dir, file.filename)
        
        if not self.is_safe_path(target_path):
            raise ValueError("Invalid target path")
        
        try:
            # 异步写入文件
            async with aiofiles.open(target_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            size = os.path.getsize(target_path)
            return {"path": target_path, "size": size}
        except Exception as e:
            raise ValueError(f"Failed to upload file: {str(e)}")
    
    async def delete_path(self, path: str) -> dict:
        """删除文件或目录"""
        if not self.is_safe_path(path):
            raise ValueError("Invalid or unsafe path")
        
        if not os.path.exists(path):
            raise ValueError("Path does not exist")
        
        try:
            loop = asyncio.get_event_loop()
            
            if os.path.isdir(path):
                await loop.run_in_executor(None, shutil.rmtree, path)
                return {"type": "directory"}
            else:
                await loop.run_in_executor(None, os.remove, path)
                return {"type": "file"}
        except Exception as e:
            raise ValueError(f"Failed to delete: {str(e)}")

