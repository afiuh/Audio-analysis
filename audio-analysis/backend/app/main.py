# [M20 初始化] FastAPI 应用入口模块
"""
录音分析工具后端服务入口。

提供音频文件上传、转写、修正和下载的 API 接口。
"""

import logging
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime

# [M5 转换] FastAPI 导入
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# [M5 转换] 项目内部导入
from .config import get_settings
from .routers import audio


# [I13 渲染] 配置日志
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 创建 logs 目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径（按日期）
log_date = datetime.now().strftime("%Y%m%d")
log_file = os.path.join(LOG_DIR, f"app_{log_date}.log")
error_log_file = os.path.join(LOG_DIR, f"error_{log_date}.log")

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s\n%(process)d-%(thread)d\n%(pathname)s\n"

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 清除现有处理器
root_logger.handlers.clear()

# 控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# 文件处理器（所有日志）
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))

# 错误专用处理器（只记录 ERROR 和 CRITICAL）
error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(DETAILED_FORMAT))

# 添加处理器
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)
root_logger.addHandler(error_handler)

logger = logging.getLogger(__name__)
logger.info(f"日志初始化完成，日志文件: {log_file}")


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

    # [I15 存储] 启动自动清理服务
    from .utils.cleanup_service import get_cleanup_service
    cleanup_service = get_cleanup_service()
    cleanup_service.start_auto_cleanup()

    # 启动时执行一次清理检查
    try:
        results = cleanup_service.run_cleanup()
        total_deleted = sum(r.deleted_files for r in results.values())
        total_freed = sum(r.freed_space_bytes for r in results.values())
        if total_deleted > 0:
            logger.info(f"启动清理完成: 删除 {total_deleted} 个文件，释放 {total_freed / 1024 / 1024:.2f} MB")
    except Exception as e:
        logger.warning(f"启动清理检查失败: {e}")

    yield

    # 关闭时
    logger.info("录音分析服务关闭中...")

    # [I15 存储] 停止自动清理服务
    cleanup_service.stop_auto_cleanup()


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

# [M13 资源] 挂载静态文件目录（前端页面）
import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


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


# [I13 渲染] 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    # [I13 渲染] 捕获所有未处理的异常

    Args:
        request: HTTP 请求
        exc: 异常对象

    Returns:
        JSONResponse: 错误响应
    """
    # 获取完整堆栈信息
    exc_type = type(exc).__name__
    exc_message = str(exc)
    exc_traceback = traceback.format_exc()

    # 请求信息
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None
    }

    # 记录详细错误日志
    error_details = f"""
========== 全局异常捕获 ==========
时间: {datetime.now().isoformat()}
请求: {request_info}
异常类型: {exc_type}
异常消息: {exc_message}
堆栈信息:
{exc_traceback}
==================================="""

    logging.error(error_details)

    # 同时写入专门的错误日志文件
    error_log_path = os.path.join(LOG_DIR, f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    try:
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(error_details)
        logging.info(f"错误详情已保存到: {error_log_path}")
    except Exception as e:
        logging.error(f"写入错误日志文件失败: {e}")

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {exc_message}",
            "error_id": datetime.now().strftime("%Y%m%d%H%M%S")
        }
    )


# [I13 渲染] 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    # [I13 渲染] 记录所有 HTTP 请求

    Args:
        request: HTTP 请求
        call_next: 下一个中间件

    Returns:
        Response: HTTP 响应
    """
    import time

    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    start_time = time.time()

    # 记录请求开始
    logging.debug(f"[{request_id}] --> {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # 计算耗时
        elapsed = time.time() - start_time

        # 记录请求完成
        logging.debug(f"[{request_id}] <-- {response.status_code} ({elapsed:.3f}s)")

        return response
    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"[{request_id}] <-- ERROR ({elapsed:.3f}s): {e}")
        raise


# [I13 渲染] 获取错误日志列表的接口
@app.get("/api/logs", tags=["logs"])
async def list_error_logs():
    """
    # [I13 渲染] 获取错误日志文件列表

    Returns:
        dict: 日志文件列表
    """
    logs = []
    for filename in os.listdir(LOG_DIR):
        filepath = os.path.join(LOG_DIR, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            logs.append({
                "name": filename,
                "path": filepath,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })

    # 按修改时间倒序
    logs.sort(key=lambda x: x["modified"], reverse=True)

    return {"success": True, "logs": logs}


# [I13 渲染] 获取指定错误日志内容
@app.get("/api/logs/{filename}", tags=["logs"])
async def get_error_log(filename: str):
    """
    # [I13 渲染] 获取错误日志内容

    Args:
        filename: 日志文件名

    Returns:
        dict: 日志内容
    """
    # 安全检查：只允许访问 logs 目录下的文件
    if ".." in filename or "/" in filename or "\\" in filename:
        return {"success": False, "message": "无效的文件名"}

    filepath = os.path.join(LOG_DIR, filename)
    if not os.path.exists(filepath):
        return {"success": False, "message": "文件不存在"}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "filename": filename, "content": content}
    except Exception as e:
        return {"success": False, "message": str(e)}


# [I15 存储] 清理服务 API
@app.get("/api/cleanup/status", tags=["cleanup"])
async def get_cleanup_status():
    """
    # [I15 存储] 获取清理服务状态

    Returns:
        dict: 清理服务状态信息
    """
    from .utils.cleanup_service import get_cleanup_service
    cleanup_service = get_cleanup_service()
    return {"success": True, **cleanup_service.get_status()}


@app.post("/api/cleanup/run", tags=["cleanup"])
async def run_cleanup():
    """
    # [I15 存储] 手动执行清理

    Returns:
        dict: 清理结果
    """
    from .utils.cleanup_service import get_cleanup_service
    cleanup_service = get_cleanup_service()

    try:
        results = cleanup_service.run_cleanup()
        total_deleted = sum(r.deleted_files for r in results.values())
        total_freed = sum(r.freed_space_bytes for r in results.values())
        return {
            "success": True,
            "message": f"清理完成: 删除 {total_deleted} 个文件，释放 {total_freed / 1024 / 1024:.2f} MB",
            "details": {
                name: {
                    "deleted_files": r.deleted_files,
                    "freed_bytes": r.freed_space_bytes,
                    "errors": r.errors
                }
                for name, r in results.items()
            }
        }
    except Exception as e:
        logger.error(f"手动清理失败: {e}")
        return {"success": False, "message": str(e)}


# [M5 转换] 配置热更新 API
@app.post("/api/config/reload", tags=["config"])
async def reload_config():
    """
    # [M5 转换] 重新加载配置（热更新）

    用于在修改 .env 文件后无需重启服务即可生效

    Returns:
        dict: 重新加载结果
    """
    from .config import reload_settings
    try:
        settings = reload_settings()
        return {
            "success": True,
            "message": "配置已重新加载",
            "config": {
                "DEEPSEEK_MODEL": settings.DEEPSEEK_MODEL,
                "DEEPSEEK_BASE_URL": settings.DEEPSEEK_BASE_URL,
                "FUNASR_MODEL": settings.FUNASR_MODEL,
            }
        }
    except Exception as e:
        logger.error(f"配置重载失败: {e}")
        return {"success": False, "message": str(e)}
