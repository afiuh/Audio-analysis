# [M5 转换] 文件处理工具模块
"""
音频文件上传、验证、存储和清理功能
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple

# [I15 存储] 常量配置
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {".mp3", ".wav"}
UPLOAD_DIR = Path("uploads/audio")

# [I15 存储] MP3/WAV 文件魔数签名
VALID_SIGNATURES = {
    ".mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    ".wav": [b"RIFF"],
}


# [I15 存储] Pydantic 模型导入
from pydantic import BaseModel


class ValidationResult(BaseModel):
    """# [M5 转换] 验证结果数据模型"""
    success: bool
    error: str | None = None
    size: int | None = None


class SaveResult(BaseModel):
    """# [M5 转换] 保存结果数据模型"""
    success: bool
    error: str | None = None
    path: str | None = None
    filename: str | None = None


class CleanupResult(BaseModel):
    """# [M5 转换] 清理结果数据模型"""
    success: bool
    message: str | None = None
    error: str | None = None


def validate_file(input_bytes: bytes, filename: str) -> ValidationResult:
    """
    # [C6 条件] 验证文件格式和大小

    Args:
        input_bytes: 文件字节数据
        filename: 原始文件名

    Returns:
        ValidationResult: 验证结果
    """
    # [C6 条件] 扩展名白名单验证
    file_ext = Path(filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            success=False,
            error=f"不支持的文件格式: {file_ext}，仅支持 MP3/WAV"
        )

    # [I15 存储] 获取文件大小
    file_size = len(input_bytes)

    # [C6 条件] 文件大小限制
    if file_size > MAX_FILE_SIZE:
        return ValidationResult(
            success=False,
            error=f"文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)"
        )

    # [I15 存储] MIME 类型魔数验证
    magic_bytes = input_bytes[:4]

    # [C6 条件] 签名验证
    valid_sigs = VALID_SIGNATURES.get(file_ext, [])
    if not any(magic_bytes.startswith(sig) for sig in valid_sigs):
        return ValidationResult(
            success=False,
            error="文件格式不匹配，可能是损坏的文件"
        )

    # [I13 渲染] 返回验证成功
    return ValidationResult(success=True, size=file_size)


def save_file(input_bytes: bytes, filename: str) -> SaveResult:
    """
    # [I15 存储] 保存上传的文件

    Args:
        input_bytes: 文件字节数据
        filename: 原始文件名

    Returns:
        SaveResult: 保存结果
    """
    # [M5 转换] 生成唯一文件名
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{unique_id}{Path(filename).suffix.lower()}"

    # [I15 存储] 确保上传目录存在
    # [F12 捕获] 目录创建异常处理
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return SaveResult(
            success=False,
            error=f"目录创建失败: {e}"
        )

    # [I15 存储] 写入磁盘
    file_path = UPLOAD_DIR / safe_filename

    # [F12 捕获] 文件写入异常处理
    try:
        with open(file_path, "wb") as f:
            f.write(input_bytes)
    except IOError as e:
        return SaveResult(
            success=False,
            error=f"文件保存失败: {e}"
        )

    # [I13 渲染] 返回保存结果
    return SaveResult(
        success=True,
        path=str(file_path),
        filename=safe_filename
    )


def cleanup_file(file_path: str) -> CleanupResult:
    """
    # [I15 存储] 清理上传的文件

    Args:
        file_path: 文件路径

    Returns:
        CleanupResult: 清理结果
    """
    # [I15 存储] 检查文件是否存在
    path = Path(file_path)
    if not path.exists():
        return CleanupResult(success=True, message="文件不存在，无需清理")

    # [F12 捕获] 文件删除异常处理
    try:
        path.unlink()
    except OSError as e:
        return CleanupResult(
            success=False,
            error=f"文件删除失败: {e}"
        )

    # [I13 渲染] 返回清理结果
    return CleanupResult(success=True)
