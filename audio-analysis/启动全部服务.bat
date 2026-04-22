@echo off
chcp 65001 >nul
REM 录音分析工具 - 一键启动前后端服务

REM 获取当前目录
set ROOT_DIR=%~dp0

REM 启动后端服务
start "录音分析后端" cmd /k "cd /d %ROOT_DIR%backend && py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 2 /nobreak >nul

REM 启动前端服务
start "录音分析前端" cmd /k "cd /d %ROOT_DIR%frontend && python -m http.server 8080"

REM 打开浏览器
start http://localhost:8080

REM 自动关闭
exit
