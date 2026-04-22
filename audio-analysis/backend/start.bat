@echo off
chcp 65001 >nul
REM 录音分析工具后端启动脚本
REM 使用 Python 3.12 + FunASR

echo ==============================================
echo   录音分析工具 API 服务
echo ==============================================
echo.
echo 首次运行会自动下载 FunASR 模型（约 1GB）
echo.

cd /d "%~dp0"
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
