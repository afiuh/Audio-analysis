@echo off
REM 录音分析工具前端启动脚本
cd /d "%~dp0"
echo ==============================================
echo   录音分析工具前端服务
echo ==============================================
echo.
echo 启动后访问: http://localhost:8080
echo 按 Ctrl+C 停止服务
echo.
python -m http.server 8080
pause
