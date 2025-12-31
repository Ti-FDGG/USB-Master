"""
C++ USB Scanner 绑定模块

此模块包含通过 pybind11 绑定的 C++ USB 扫描器实现。
构建后的 usb_scanner.pyd 文件位于此目录下。
"""

__version__ = "1.0.0"

try:
    from .usb_scanner import USBScanner  # type: ignore[import]
    __all__ = ["USBScanner"]
except ImportError:
    __all__ = []

