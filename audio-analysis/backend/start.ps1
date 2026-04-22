# 录音分析工具后端启动脚本
# 使用 Python 3.12 + FunASR

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  录音分析工具 API 服务" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "首次运行会自动下载 FunASR 模型（约 1GB）" -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
