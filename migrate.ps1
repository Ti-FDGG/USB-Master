# USB Master 迁移脚本 (PowerShell)
# 用于将现有前端文件移动到 frontend 目录

Write-Host "开始迁移前端文件..." -ForegroundColor Green

# 创建 frontend 目录（如果不存在）
if (-not (Test-Path "frontend")) {
    New-Item -ItemType Directory -Path "frontend" | Out-Null
    Write-Host "已创建 frontend 目录" -ForegroundColor Yellow
}

# 要移动的文件列表
$filesToMove = @(
    "App.tsx",
    "index.tsx",
    "types.ts",
    "index.html",
    "vite.config.ts",
    "tsconfig.json",
    "package.json"
)

# 要移动的目录列表
$dirsToMove = @(
    "components",
    "utils"
)

# 移动文件
foreach ($file in $filesToMove) {
    if (Test-Path $file) {
        Move-Item -Path $file -Destination "frontend\" -Force
        Write-Host "已移动: $file" -ForegroundColor Cyan
    } else {
        Write-Host "文件不存在: $file" -ForegroundColor Yellow
    }
}

# 移动目录
foreach ($dir in $dirsToMove) {
    if (Test-Path $dir) {
        Move-Item -Path $dir -Destination "frontend\" -Force
        Write-Host "已移动目录: $dir" -ForegroundColor Cyan
    } else {
        Write-Host "目录不存在: $dir" -ForegroundColor Yellow
    }
}

Write-Host "`n迁移完成！" -ForegroundColor Green
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 进入 backend 目录并安装依赖: cd backend && pip install -r requirements.txt" -ForegroundColor White
Write-Host "2. 进入 frontend 目录并安装依赖: cd frontend && npm install" -ForegroundColor White
Write-Host "3. 启动后端: cd backend && python main.py" -ForegroundColor White
Write-Host "4. 启动前端: cd frontend && npm run dev" -ForegroundColor White

