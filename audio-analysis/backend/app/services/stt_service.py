# FunASR 语音转文字服务模块
"""
封装 FunASR 语音转文字功能，提供同步和异步转写接口。
FunASR 阿里巴巴达摩院开发，对中文长音频有专门优化。
"""

import logging
from pathlib import Path
from typing import Optional

# FunASR 导入
from funasr import AutoModel

# 项目内部导入
from ..config import get_settings
from ..models.schemas import TranscriptionResult


# 全局模型单例
_model: Optional[AutoModel] = None


def load_model() -> AutoModel:
    """
    加载 FunASR 模型

    模型会自动下载到缓存目录，首次加载后会被缓存。
    推荐使用 paraformer-zh 模型，针对中文长音频优化。

    Returns:
        AutoModel: 加载的模型实例

    """
    global _model

    # 已有缓存模型则直接返回
    if _model is not None:
        return _model

    # 获取配置
    settings = get_settings()
    model_name = settings.FUNASR_MODEL

    try:
        logging.info(f"正在加载 FunASR {model_name} 模型...")

        # FunASR 的 AutoModel 会自动选择合适的设备
        _model = AutoModel(
            model=model_name,
            model_revision="v2.0.4",
            vad_model="fsmn-vad",
            vad_model_revision="v2.0.4",
            punc_model="ct-punc",
            punc_model_revision="v2.0.4",
            disable_update=True,
        )

        logging.info("FunASR 模型加载成功")

        return _model

    except Exception as e:
        logging.error(f"FunASR 模型加载失败: {e}")
        raise RuntimeError(f"模型加载失败: {e}")


def transcribe(audio_path: str, task_id: str = "", model: Optional[AutoModel] = None) -> TranscriptionResult:
    """
    语音转文字

    Args:
        audio_path: 音频文件路径
        task_id: 任务 ID
        model: 可选，预加载的模型实例

    Returns:
        TranscriptionResult: 转写结果

    """
    # 验证音频文件
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    # 确保模型已加载
    if model is None:
        model = load_model()

    # 执行转写
    try:
        logging.info(f"开始转写音频: {audio_path}")

        # FunASR 的 generate 方法返回列表，每个元素是一个识别结果
        # paraformer-zh 模型支持长音频分段识别
        result = model.generate(
            str(audio_path),
            batch_size_s=300,  # 每批处理 300 秒
            hotword="",  # 可选的热词
        )

        # 解析 FunASR 返回结果
        # FunASR 返回格式: [{text: "...", timestamp: [...], sentence_info: [...]}]
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            text = first_result.get("text", "").strip()

            # FunASR 已经内置了标点，我们直接使用
            # 如果需要获取详细的时间戳信息，可以从 sentence_info 中获取
            sentence_info = first_result.get("sentence_info", [])

            # 估算音频时长（FunASR 不直接返回 duration）
            # 可以从最后一个句子的结束时间推算
            if sentence_info:
                duration = max(s.get("end", 0) for s in sentence_info) / 1000.0  # 转换为秒
            else:
                # 简单估算：按每秒 3 个中文字符
                duration = len(text) / 3.0
        else:
            text = ""
            duration = 0.0

        logging.info(f"转写完成，文本长度: {len(text)} 字符，时长: {duration:.2f}秒")

        # 返回转写结果
        return TranscriptionResult(
            task_id=task_id,
            text=text,
            language="zh-cn",
            duration=duration
        )

    except Exception as e:
        logging.error(f"语音转写失败: {e}")
        raise RuntimeError(f"语音转写失败: {e}")


def unload_model() -> None:
    """
    卸载模型，释放内存
    """
    global _model

    if _model is not None:
        logging.info("正在卸载 FunASR 模型")
        _model = None
        logging.info("FunASR 模型已卸载")


def get_model() -> AutoModel:
    """
    获取当前加载的模型

    Returns:
        AutoModel: 模型实例
    """
    global _model
    if _model is None:
        _model = load_model()
    return _model


def get_audio_duration(audio_path: str) -> float:
    """
    获取音频文件时长（秒）

    Args:
        audio_path: 音频文件路径

    Returns:
        float: 音频时长（秒）
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # 毫秒转秒
    except ImportError:
        # 如果没有 pydub，返回默认值
        return 60.0
    except Exception:
        return 60.0
