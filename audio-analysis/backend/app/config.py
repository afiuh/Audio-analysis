# [I15 存储] 配置加载模块
"""
集中管理所有环境配置，提供类型安全的配置访问。
"""

import logging
from pathlib import Path
from typing import Optional

# [I15 存储] Pydantic 依赖
from pydantic import Field
from pydantic_settings import BaseSettings

# [I15 存储] dotenv 导入
from dotenv import load_dotenv


class Settings(BaseSettings):
    """
    # [M5 转换] 应用配置数据模型

    使用 Pydantic BaseSettings 自动从环境变量加载配置。
    支持 .env 文件覆盖默认配置。
    """

    # [I15 存储] DeepSeek API 配置
    DEEPSEEK_API_KEY: str = Field(
        ...,
        description="DeepSeek API 密钥"
    )
    DEEPSEEK_BASE_URL: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API 端点"
    )
    DEEPSEEK_MODEL: str = Field(
        default="deepseek-chat",
        description="DeepSeek 模型名称"
    )

    # FunASR 模型配置
    FUNASR_MODEL: str = Field(
        default="paraformer-zh",
        description="FunASR 模型: paraformer-zh (中文长音频推荐)"
    )

    # [I15 存储] 系统配置
    UPLOAD_DIR: Path = Field(
        default=Path("uploads/audio"),
        description="音频文件上传目录"
    )
    MAX_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024,
        description="最大文件大小 (字节)"
    )
    DEBUG: bool = Field(
        default=False,
        description="调试模式"
    )

    class Config:
        """# [M5 转换] Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def load_settings(env_file: Optional[str] = ".env") -> Settings:
    """
    # [I15 存储] 加载应用配置

    Args:
        env_file: .env 文件路径

    Returns:
        Settings: 验证后的配置对象

    # [F12 捕获] 异常处理
    # dotenv 读取可能失败，但不影响程序继续运行
    """
    # [I15 存储] 读取 .env 文件
    # [F12 捕获] dotenv 读取异常处理
    try:
        if env_file:
            load_dotenv(env_file)
    except Exception as e:
        # [I13 渲染] 记录警告但不阻止程序运行
        logging.warning(f".env 文件读取失败: {e}")

    # [M5 转换] 创建并验证 Settings
    # [F12 捕获] 配置验证异常处理
    try:
        settings = Settings(_env_file=env_file)
        return settings
    except Exception as e:
        # [I13 渲染] 记录配置验证错误
        logging.error(f"配置验证失败: {e}")
        # 重新抛出以便开发者发现配置问题
        raise ValueError(f"缺少必需配置或配置格式错误: {e}")


# [M5 转换] 全局配置实例
# 延迟加载，避免启动时立即读取 .env
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    # [M5 转换] 获取全局配置单例

    Returns:
        Settings: 应用配置实例
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings
