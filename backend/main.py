"""
USB Master Backend - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api import usb, files, system
from services.monitor_service import start_usb_monitor

app = FastAPI(
    title="USB Master API",
    description="USB 总线及挂载设备测试实验后端 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(system.router, prefix="/api/system", tags=["系统信息"])
app.include_router(usb.router, prefix="/api/usb", tags=["USB 设备"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])


@app.on_event("startup")
async def startup_event():
    """启动时初始化服务"""
    # 启动 USB 设备监控服务
    try:
        start_usb_monitor()
    except Exception as e:
        print(f"Warning: Failed to start USB monitor: {e}")
        import traceback
        traceback.print_exc()


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse({
        "message": "USB Master API",
        "version": "1.0.0",
        "docs": "/docs"
    })


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

