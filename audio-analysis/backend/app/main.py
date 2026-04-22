# [M20 初始化] FastAPI 应用入口模块
"""
录音分析工具后端服务入口。

提供音频文件上传、转写、修正和下载的 API 接口。
"""

import logging
from contextlib import asynccontextmanager

# [M5 转换] FastAPI 导入
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# [M5 转换] 项目内部导入
from .config import get_settings
from .routers import audio


# [I13 渲染] 配置日志
import sys
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    # [M20 初始化] 应用生命周期管理

    启动时加载配置，关闭时清理资源。
    """
    # 启动时
    logger.info("录音分析服务启动中...")
    settings = get_settings()
    logger.info(f"配置加载完成，FunASR 模型: {settings.FUNASR_MODEL}")

    yield

    # 关闭时
    logger.info("录音分析服务关闭中...")


# [M5 转换] 创建 FastAPI 应用实例
app = FastAPI(
    title="录音分析工具 API",
    description="提供音频文件上传、语音转文字、AI 修正和 Markdown 导出功能",
    version="1.0.0",
    lifespan=lifespan
)

# [I13 渲染] 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [M5 转换] 注册路由
app.include_router(audio.router)


@app.get("/", tags=["health"])
async def root():
    """
    # [I13 渲染] 根路径健康检查

    Returns:
        dict: 服务状态信息
    """
    return {
        "service": "录音分析工具 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    # [I13 渲染] 健康检查接口

    Returns:
        dict: 健康状态
    """
    return {"status": "healthy"}
