# [M5 转换] Pydantic 数据模型模块
"""
定义 API 请求/响应的 Pydantic 数据模型，确保类型安全和数据验证。
"""

from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel, Field


# [M5 转换] 泛型数据类型
T = TypeVar("T")


# ============== 请求模型 (Request Models) ==============

class AudioUploadRequest(BaseModel):
    """
    # [C6 条件] 文件上传请求

    Attributes:
        filename: 上传文件名
        file_size: 文件大小(字节)
    """
    # [C6 条件] 文件名非空验证
    filename: str = Field(
        ...,
        min_length=1,
        description="上传文件名"
    )

    # [C6 条件] 文件大小正整数验证
    file_size: int = Field(
        ...,
        gt=0,
        le=100 * 1024 * 1024,
        description="文件大小(字节)"
    )


class TaskStatusRequest(BaseModel):
    """
    # [C6 条件] 任务状态查询请求

    Attributes:
        task_id: 任务ID (UUID格式)
    """
    # [C6 条件] UUID格式验证
    task_id: str = Field(
        ...,
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        description="任务ID (UUID格式)"
    )


# ============== 响应模型 (Response Models) ==============

class ApiResponse(BaseModel, Generic[T]):
    """
    # [I13 渲染] 统一 API 响应格式

    所有 API 响应都使用此格式包装。

    Attributes:
        code: 业务状态码 (0=成功, 非0=错误)
        message: 响应消息
        data: 响应数据
    """
    # [I13 渲染] 统一响应格式
    code: int = Field(
        default=0,
        description="业务状态码: 0=成功, 非0=错误"
    )
    message: str = Field(
        default="success",
        description="响应消息"
    )
    data: Optional[T] = Field(
        default=None,
        description="响应数据"
    )

    class Config:
        """# [M5 转换] Pydantic 配置"""
        from_attributes = True


class TaskStatus(BaseModel):
    """
    # [I13 渲染] 任务状态模型

    Attributes:
        task_id: 任务ID
        status: 状态 (pending/processing/completed/failed)
        progress: 进度 0-100%
        result: 任务结果
        error: 错误信息
        created_at: 创建时间
        updated_at: 更新时间
    """
    # [I13 渲染] 任务状态
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="处理进度 (0-100)"
    )
    result: Optional[dict[str, Any]] = Field(
        default=None,
        description="任务结果"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )

    class Config:
        """# [M5 转换] Pydantic 配置"""
        from_attributes = True


class CorrectionResult(BaseModel):
    """
    # [I13 渲染] 逐句修正结果

    Attributes:
        sentence_index: 句子序号
        original: 原始句子
        corrected: 修正后句子
        analysis: AI 分析说明
    """
    # [I13 渲染] 逐句修正结果
    sentence_index: int = Field(
        ...,
        ge=0,
        description="句子序号"
    )
    original: str = Field(
        ...,
        description="原始句子"
    )
    corrected: str = Field(
        ...,
        description="修正后句子"
    )
    analysis: str = Field(
        ...,
        description="AI 分析说明"
    )

    class Config:
        """# [M5 转换] Pydantic 配置"""
        from_attributes = True


class UploadResponse(BaseModel):
    """
    # [I13 渲染] 文件上传响应

    Attributes:
        task_id: 任务ID
        filename: 保存的文件名
        status: 上传状态
    """
    # [I13 渲染] 上传响应
    task_id: str
    filename: str
    status: Literal["pending", "uploaded"]


class TranscriptionResult(BaseModel):
    """
    # [I13 渲染] 转写结果

    Attributes:
        task_id: 任务ID
        text: 转写文本
        language: 检测到的语言
        duration: 音频时长(秒)
    """
    # [I13 渲染] 转写结果
    task_id: str
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None


class ExportResult(BaseModel):
    """
    # [I13 渲染] 导出结果

    Attributes:
        task_id: 任务ID
        file_path: MD 文件路径
        filename: 文件名
    """
    # [I13 渲染] 导出结果
    task_id: str
    file_path: str
    filename: str
