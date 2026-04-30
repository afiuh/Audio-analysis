# [I14 用户输入] 音频处理 API 路由模块
"""
提供音频文件上传、转写、修正和下载的 API 接口。
"""

import logging
import os
import traceback
import threading
import uuid
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# [I14 用户输入] FastAPI 导入
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

# [M5 转换] 项目内部导入
from ..models.schemas import (
    ApiResponse,
    TaskStatus,
    UploadResponse,
)
from ..services import correction_service
from ..services import export_service
from ..services import stt_service
from ..utils import file_handler


# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def _save_task_error_log(task_id: str, stage: str, error: Exception, context: dict = None):
    """
    保存任务错误日志到专门的文件

    Args:
        task_id: 任务ID
        stage: 失败阶段
        error: 异常对象
        context: 额外上下文信息
    """
    error_details = f"""
========== 任务执行错误 ==========
时间: {datetime.now().isoformat()}
任务ID: {task_id}
失败阶段: {stage}
异常类型: {type(error).__name__}
异常消息: {str(error)}

上下文信息:
{context or '无'}

完整堆栈:
{traceback.format_exc()}

==================================
"""
    logging.error(error_details)

    # 保存到专门的错误日志文件
    error_log_path = os.path.join(LOG_DIR, f"task_error_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(error_details)
        logging.info(f"任务错误日志已保存: {error_log_path}")
    except Exception as e:
        logging.error(f"写入任务错误日志失败: {e}")


# [I15 存储] 任务存储 (内存字典，生产环境应使用数据库)
_tasks: Dict[str, TaskStatus] = {}

# 进度回调存储 { task_id: { stage, progress, message, start_time, result, error } }
_progress: Dict[str, dict] = {}

# 后台线程任务存储
_bg_tasks: Dict[str, threading.Thread] = {}


# [I15 存储] 任务管理函数
def get_task(task_id: str) -> Optional[TaskStatus]:
    """# [I15 存储] 获取任务"""
    return _tasks.get(task_id)


def create_task(task_id: str, filename: str, file_path: str) -> TaskStatus:
    """# [I15 存储] 创建任务"""
    task = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        result={"filename": filename, "file_path": file_path}
    )
    _tasks[task_id] = task
    return task


def update_task(task_id: str, **kwargs) -> Optional[TaskStatus]:
    """# [I15 存储] 更新任务"""
    task = _tasks.get(task_id)
    if task:
        for key, value in kwargs.items():
            setattr(task, key, value)
    return task


def update_progress(task_id: str, stage: str, progress: float, message: str = ""):
    """
    更新任务进度
    
    Args:
        task_id: 任务ID
        stage: 当前阶段 (loading_model, transcribing, correcting, exporting, completed)
        progress: 进度百分比 0-100
        message: 详细消息
    """
    if task_id not in _progress:
        _progress[task_id] = {"start_time": None, "stage_start": None}
    
    import time
    now = time.time()
    
    if _progress[task_id]["start_time"] is None:
        _progress[task_id]["start_time"] = now
        _progress[task_id]["stage_start"] = now
    
    # 计算预估剩余时间
    elapsed = now - _progress[task_id]["start_time"]
    if progress > 0:
        estimated_total = elapsed / (progress / 100)
        remaining = max(0, estimated_total - elapsed)
    else:
        remaining = None
    
    _progress[task_id].update({
        "stage": stage,
        "progress": progress,
        "message": message,
        "elapsed": elapsed,
        "remaining": remaining,
        "updated_at": now
    })


def get_progress(task_id: str) -> Optional[dict]:
    """获取任务进度"""
    return _progress.get(task_id)


def _background_process(task_id: str, file_path: str):
    """
    后台处理函数（在新线程中执行）
    """
    global _tasks
    import time

    # 初始化进度
    update_progress(task_id, "loading_model", 5, "准备加载模型...")

    # 用于通知进度更新线程停止
    stop_progress_flag = {"stop": False}

    def _progress_updater():
        """定期更新转写进度"""
        audio_duration = stt_service.get_audio_duration(file_path)
        base_progress = 15  # 转写从 15% 开始
        end_progress = 60  # 转写到 60% 结束
        estimated_transcribe_time = max(audio_duration / 2, 10)  # 估算转写时间（秒）
        
        update_interval = 2.0  # 每 2 秒更新一次
        elapsed = 0.0
        
        while not stop_progress_flag["stop"]:
            time.sleep(update_interval)
            elapsed += update_interval
            
            if elapsed >= estimated_transcribe_time:
                break
            
            # 计算当前进度
            progress_ratio = min(elapsed / estimated_transcribe_time, 0.95)
            current_progress = base_progress + (end_progress - base_progress) * progress_ratio
            
            # 估算剩余时间
            remaining = max(0, estimated_transcribe_time - elapsed)
            
            _progress[task_id].update({
                "progress": current_progress,
                "message": f"正在转写... 已处理 {int(elapsed)} 秒",
                "elapsed": elapsed,
                "remaining": remaining
            })

    try:
        # 获取模型（内部会加载模型）
        update_progress(task_id, "transcribing", 10, "FunASR 模型加载中...")
        model = stt_service.get_model()
        update_progress(task_id, "transcribing", 15, "模型加载完成，开始转写...")
        
        # 获取音频时长用于估算
        audio_duration = stt_service.get_audio_duration(file_path)
        logging.info(f"音频时长: {audio_duration:.1f} 秒")

        # 启动进度更新线程
        progress_thread = threading.Thread(target=_progress_updater, daemon=True)
        progress_thread.start()

        # 执行转写
        stt_result = stt_service.transcribe(file_path, task_id=task_id, model=model)
        
        # 停止进度更新线程
        stop_progress_flag["stop"] = True
        progress_thread.join(timeout=1)
        
        update_progress(task_id, "transcribing", 60, f"转写完成，识别 {len(stt_result.text)} 字符")
        logging.info(f"转写完成，文本长度: {len(stt_result.text)} 字符")

        # 修正文本
        update_progress(task_id, "correcting", 65, "正在修正文本...")
        corrections = correction_service.correct_batch(stt_result.text)
        update_progress(task_id, "correcting", 80, f"修正完成，共处理 {len(corrections)} 句")
        logging.info(f"修正完成，共 {len(corrections)} 句")

        # 生成报告
        update_progress(task_id, "exporting", 85, "正在生成报告...")
        export_result = export_service.save_markdown(
            task_id=task_id,
            original_text=stt_result.text,
            corrections=corrections
        )
        update_progress(task_id, "exporting", 95, "报告生成完成")

        # 更新任务状态为完成
        task = _tasks.get(task_id)
        if task:
            task.status = "completed"
            task.progress = 100.0
            task.result = {
                "text": stt_result.text,
                "language": stt_result.language,
                "duration": stt_result.duration,
                "correction_count": len(corrections),
                "export_path": export_result.file_path
            }

        update_progress(task_id, "completed", 100, "处理完成")
        logging.info(f"后台任务完成: {task_id}")

    except Exception as e:
        logging.error(f"后台处理失败: {e}")
        stop_progress_flag["stop"] = True
        
        # 保存详细错误日志
        _save_task_error_log(
            task_id=task_id,
            stage="后台处理",
            error=e,
            context={
                "file_path": file_path,
                "current_progress": _progress.get(task_id, {})
            }
        )
        
        task = _tasks.get(task_id)
        if task:
            task.status = "failed"
            task.error = str(e)
        update_progress(task_id, "failed", 0, f"处理失败: {str(e)}")
    finally:
        # 清理后台线程引用
        if task_id in _bg_tasks:
            del _bg_tasks[task_id]


# [I13 渲染] 创建路由实例
router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.post("/upload", response_model=ApiResponse[UploadResponse])
async def upload_audio(file: UploadFile = File(...)):
    """
    # [I14 用户输入] 文件上传接口

    Args:
        file: 上传的音频文件 (MP3/WAV)

    Returns:
        ApiResponse: 包含 task_id 的响应
    """
    # [I14 用户输入] 接收文件上传
    logging.info(f"接收到文件上传: {file.filename}")

    # [I15 存储] 读取文件数据
    # [F12 捕获] 文件读取异常处理
    try:
        file_bytes = await file.read()
    except Exception as e:
        logging.error(f"文件读取失败: {e}")
        return ApiResponse(code=400, message=f"文件读取失败: {e}")

    # [I15 存储] 验证文件
    # [F12 捕获] 文件验证异常处理
    try:
        validate_result = file_handler.validate_file(file_bytes, file.filename)
        if not validate_result.success:
            return ApiResponse(code=400, message=validate_result.error)
    except Exception as e:
        logging.error(f"文件验证失败: {e}")
        return ApiResponse(code=400, message=f"文件验证失败: {e}")

    # [I15 存储] 保存文件
    # [F12 捕获] 文件保存异常处理
    try:
        save_result = file_handler.save_file(file_bytes, file.filename)
        if not save_result.success:
            return ApiResponse(code=500, message=save_result.error)
    except Exception as e:
        logging.error(f"文件保存失败: {e}")
        return ApiResponse(code=500, message=f"文件保存失败: {e}")

    # [I15 存储] 创建任务记录
    task_id = str(uuid.uuid4())
    task = create_task(task_id, save_result.filename, save_result.path)

    logging.info(f"文件上传成功，任务ID: {task_id}")

    # [I13 渲染] 返回任务ID
    return ApiResponse(
        data=UploadResponse(
            task_id=task_id,
            filename=save_result.filename,
            status="uploaded"
        )
    )


@router.get("/status/{task_id}", response_model=ApiResponse[TaskStatus])
async def get_task_status(task_id: str):
    """
    # [I14 用户输入] 任务状态查询接口

    Args:
        task_id: 任务ID

    Returns:
        ApiResponse: 任务状态
    """
    # [I15 存储] 查询任务状态
    task = get_task(task_id)
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    # [I13 渲染] 返回状态信息
    return ApiResponse(data=task)


@router.post("/transcribe/{task_id}", response_model=ApiResponse)
async def transcribe_audio(task_id: str):
    """
    # [I14 用户输入] 启动转写任务（异步）

    Args:
        task_id: 任务ID

    Returns:
        ApiResponse: 任务启动确认
    """
    # [I15 存储] 获取任务
    task = get_task(task_id)
    if not task:
        return ApiResponse(code=404, message="任务不存在")

    # 获取音频路径
    file_path = task.result.get("file_path") if task.result else None
    if not file_path:
        return ApiResponse(code=400, message="任务缺少文件路径")

    # 如果已经在处理中，返回进度
    if task.status == "processing":
        progress = get_progress(task_id)
        return ApiResponse(
            data={
                "task_id": task_id,
                "status": "processing",
                "message": "任务正在处理中",
                "progress": progress
            }
        )

    # 更新任务状态
    task.status = "processing"
    task.progress = 0.0

    # 启动后台线程处理
    thread = threading.Thread(
        target=_background_process,
        args=(task_id, file_path),
        daemon=True
    )
    thread.start()
    _bg_tasks[task_id] = thread

    logging.info(f"已启动后台处理任务: {task_id}")

    # 立即返回，不等待处理完成
    return ApiResponse(
        data={
            "task_id": task_id,
            "status": "processing",
            "message": "任务已启动，正在后台处理..."
        }
    )


@router.get("/download/{task_id}")
async def download_markdown(task_id: str):
    """
    # [I14 用户输入] 下载 Markdown 文件

    Args:
        task_id: 任务ID

    Returns:
        FileResponse: Markdown 文件
    """
    # [I15 存储] 查找最新的 MD 文件
    export_dir = Path("exports")
    if not export_dir.exists():
        raise HTTPException(status_code=404, detail="导出目录不存在")

    # 查找包含此 task_id 信息的文件（通过读取文件内容验证）
    for md_file in sorted(export_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            content = md_file.read_text(encoding="utf-8")
            if task_id in content:
                return FileResponse(
                    path=md_file,
                    filename=md_file.name,
                    media_type="text/markdown"
                )
        except:
            continue

    raise HTTPException(status_code=404, detail="文件不存在")


# 监控文件夹路径（可配置）
WATCH_FOLDER = Path("E:/shuju-jilu/录音/未解析")


@router.get("/folder/files")
async def list_folder_files():
    """
    列出监控文件夹中的音频文件

    Returns:
        JSON: 文件列表
    """
    if not WATCH_FOLDER.exists():
        return {"success": False, "message": f"文件夹不存在: {WATCH_FOLDER}", "files": []}

    audio_files = []
    for ext in ["*.mp3", "*.wav", "*.m4a", "*.flac"]:
        for file_path in WATCH_FOLDER.glob(ext):
            stat = file_path.stat()
            audio_files.append({
                "name": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime
            })

    # 按修改时间排序，最新的在前
    audio_files.sort(key=lambda x: x["modified"], reverse=True)

    return {
        "success": True,
        "folder": str(WATCH_FOLDER),
        "count": len(audio_files),
        "files": audio_files
    }


@router.post("/folder/process")
async def process_folder_file(filename: str):
    """
    处理监控文件夹中的指定文件

    Args:
        filename: 文件名

    Returns:
        JSON: 任务信息
    """
    file_path = WATCH_FOLDER / filename

    if not file_path.exists():
        return {"success": False, "message": f"文件不存在: {filename}"}

    # 创建任务
    task_id = str(uuid.uuid4())
    task = create_task(task_id, filename, str(file_path))

    return {
        "success": True,
        "task_id": task_id,
        "filename": filename,
        "status": "created"
    }


@router.get("/progress/{task_id}")
async def get_task_progress(task_id: str):
    """
    获取任务实时进度

    Args:
        task_id: 任务ID

    Returns:
        JSON: 进度信息
    """
    task = get_task(task_id)
    if not task:
        return {"success": False, "message": "任务不存在"}
    
    progress = get_progress(task_id)
    if not progress:
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "stage": "pending",
            "stage_text": "等待处理",
            "message": ""
        }
    
    # 阶段文本映射
    stage_map = {
        "loading_model": "加载模型",
        "transcribing": "正在转写",
        "correcting": "正在修正",
        "exporting": "生成报告",
        "completed": "已完成",
        "failed": "处理失败"
    }
    
    return {
        "success": True,
        "task_id": task_id,
        "status": task.status,
        "progress": progress.get("progress", task.progress),
        "stage": progress.get("stage", "pending"),
        "stage_text": stage_map.get(progress.get("stage", "pending"), "等待中"),
        "message": progress.get("message", ""),
        "elapsed": progress.get("elapsed", 0),
        "remaining": progress.get("remaining"),
        "error": getattr(task, "error", None)
    }
