# [I15 存储] Markdown 导出服务模块
"""
生成包含原文和 AI 分析的 Markdown 文件。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

# [M5 转换] 简繁转换
from opencc import OpenCC
_cc = OpenCC('t2s')  # 繁体转简体

# [M5 转换] 项目内部导入
from ..models.schemas import CorrectionResult, ExportResult


def to_simplified(text: str) -> str:
    """# [M5 转换] 繁体转简体"""
    if not text:
        return text
    return _cc.convert(text)


# [I15 存储] 导出目录配置（默认本地，配置后可自动同步到指定目录）
EXPORT_DIR = Path("exports")

# [I15 存储] 自动备份目录（生成 MD 后同时复制到此目录）
AUTO_BACKUP_DIR = Path("E:/数据记录/录音/已归纳")


def build_markdown(task_id: str, original_text: str, corrections: List[CorrectionResult]) -> str:
    """
    # [I13 渲染] 构建 Markdown 内容

    Args:
        task_id: 任务ID
        original_text: 原始转写文本
        corrections: 修正结果列表

    Returns:
        str: Markdown 格式字符串
    """
    # [I13 渲染] 生成标题和元信息
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md_parts = [
        "# 录音分析报告\n",
        f"> **任务ID:** `{task_id}`\n",
        f"> **生成时间:** {timestamp}\n",
        "---\n",
        "\n## 逐句修正\n",
    ]

    # [I13 渲染] 生成修正结果
    if corrections:
        for i, result in enumerate(corrections, 1):
            orig = to_simplified(result.original)
            corr = to_simplified(result.corrected)
            analysis = to_simplified(result.analysis)
            
            md_parts.append(f"### 第{i}句\n\n")
            md_parts.append(f"**原话：** {orig}\n\n")
            md_parts.append(f"**修正：** {corr}\n\n")
            md_parts.append(f"**AI分析：** {analysis}\n\n")
            md_parts.append("---\n\n")
    else:
        md_parts.append("*无修正结果*\n")

    # [M5 转换] 拼接完整 MD
    return "".join(md_parts)


def save_markdown(task_id: str, original_text: str, corrections: List[CorrectionResult]) -> ExportResult:
    """
    # [I15 存储] 保存 Markdown 文件

    Args:
        task_id: 任务ID
        original_text: 原始转写文本
        corrections: 修正结果列表

    Returns:
        ExportResult: 导出结果

    # [F12 捕获] 文件操作异常处理
    """
    # [I15 存储] 确保导出目录存在
    # [F12 捕获] 目录创建异常处理
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error(f"创建导出目录失败: {e}")
        raise RuntimeError(f"创建导出目录失败: {e}")

    # [M5 转换] 生成文件名（使用时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"analysis_{timestamp}.md"

    # [I15 存储] 构建 MD 内容
    md_content = build_markdown(task_id, original_text, corrections)

    # [I15 存储] 写入文件
    file_path = EXPORT_DIR / safe_filename

    # [F12 捕获] 文件写入异常处理
    try:
        file_path.write_text(md_content, encoding="utf-8")
        logging.info(f"Markdown 文件已保存: {file_path}")

        # [I15 存储] 自动备份到指定目录
        try:
            AUTO_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            backup_path = AUTO_BACKUP_DIR / safe_filename
            file_path.copy_to(backup_path)
            logging.info(f"已自动备份到: {backup_path}")
        except Exception as backup_err:
            # 备份失败不影响主流程，只记录警告
            logging.warning(f"自动备份失败（非致命）: {backup_err}")

    except IOError as e:
        logging.error(f"写入 Markdown 文件失败: {e}")
        raise RuntimeError(f"写入 Markdown 文件失败: {e}")

    # [I13 渲染] 返回导出结果
    return ExportResult(
        task_id=task_id,
        file_path=str(file_path),
        filename=safe_filename
    )
