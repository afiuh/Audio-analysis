# [M20 初始化] FastAPI 服务启动脚本
"""
启动录音分析工具后端服务。
"""

import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# [M20 初始化] 启动 FastAPI 服务
if __name__ == "__main__":
    import uvicorn
    from app.main import app

    print("=" * 50)
    print("录音分析工具 API 服务")
    print("=" * 50)
    print("API 文档地址: http://localhost:8000/docs")
    print("前端界面地址: http://localhost:8000 (需启动前端服务器)")
    print("=" * 50)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
