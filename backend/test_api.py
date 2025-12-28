"""
快速测试 API 端点
"""
import asyncio
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.file_service import FileService
from services.usb_service import USBService

async def test_file_service():
    print("Testing FileService...")
    try:
        file_service = FileService()
        drives = await file_service.get_removable_drives()
        print(f"Found {len(drives)} drives:")
        for drive in drives:
            print(f"  - {drive.path} ({drive.label})")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_usb_service():
    print("\nTesting USBService...")
    try:
        usb_service = USBService()
        devices = await usb_service.scan_devices()
        print(f"Found {len(devices)} USB devices:")
        for device in devices:
            print(f"  - {device.product} ({device.manufacturer})")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 50)
    print("Testing Backend Services")
    print("=" * 50)
    
    file_ok = await test_file_service()
    usb_ok = await test_usb_service()
    
    print("\n" + "=" * 50)
    if file_ok and usb_ok:
        print("All tests passed!")
    else:
        print("Some tests failed. Check errors above.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())

