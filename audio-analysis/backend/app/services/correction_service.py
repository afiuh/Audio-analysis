# [I16 通信] DeepSeek 文本修正服务模块
"""
调用 DeepSeek API 对转写文本进行逐句语义修正。
"""

import json
import logging
import re
from typing import List

# [I16 通信] OpenAI 兼容客户端
from openai import OpenAI

# [M5 转换] 简繁转换
from opencc import OpenCC
_cc = OpenCC('t2s')

def to_simplified(text: str) -> str:
    """# [M5 转换] 繁体转简体"""
    if not text:
        return text
    return _cc.convert(text)

# [M5 转换] 项目内部导入
from ..config import get_settings
from ..models.schemas import CorrectionResult


# [I16 通信] 全局客户端单例
_client: OpenAI = None


def init_client() -> OpenAI:
    """
    # [I16 通信] 初始化 DeepSeek 客户端

    Returns:
        OpenAI: OpenAI 兼容客户端实例

    # [F12 捕获] 客户端初始化异常处理
    """
    global _client

    if _client is not None:
        return _client

    # [I15 存储] 读取 API 配置
    settings = get_settings()

    # [I16 通信] 创建 OpenAI 兼容客户端
    # [F12 捕获] 客户端初始化异常处理
    try:
        _client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=30.0  # [I16 通信] 全局超时设置
        )
        logging.info("DeepSeek 客户端初始化成功")
        return _client

    except Exception as e:
        # [I13 渲染] 记录错误日志
        logging.error(f"DeepSeek 客户端初始化失败: {e}")
        raise RuntimeError(f"DeepSeek 客户端初始化失败: {e}")


def get_client() -> OpenAI:
    """
    # [I16 通信] 获取 DeepSeek 客户端单例

    Returns:
        OpenAI: 客户端实例
    """
    global _client
    if _client is None:
        _client = init_client()
    return _client


def split_sentences(text: str) -> List[str]:
    """
    # [M5 转换] 智能分句

    Args:
        text: 待分割文本

    Returns:
        List[str]: 句子列表
    """
    # [M5 转换] 按标点分割
    sentences = re.split(r'[。？！；\n]+', text)

    # [C6 条件] 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]

    # [C6 条件] 如果没有找到句子（无标点文本），返回原文本让 AI 处理
    if not sentences and text.strip():
        return [text.strip()]

    return sentences


def correct_sentence(sentence: str, index: int, context: str = None, all_sentences: List[str] = None) -> CorrectionResult:
    """
    修正单个句子，结合全文语境进行校对

    Args:
        sentence: 原始句子
        index: 句子索引
        context: 全文语境（所有句子，用于理解上下文）
        all_sentences: 所有句子列表（可选，方便引用前后句子）

    Returns:
        CorrectionResult: 修正结果

    """
    # 构建语境信息
    context_info = ""
    if all_sentences and len(all_sentences) > 1:
        # 获取前后相邻句子作为直接语境
        prev_sentence = all_sentences[index - 1] if index > 0 else None
        next_sentence = all_sentences[index + 1] if index < len(all_sentences) - 1 else None

        # 构建上下文描述
        context_parts = []
        if prev_sentence:
            context_parts.append(f"前一句：「{prev_sentence}」")
        if next_sentence:
            context_parts.append(f"后一句：「{next_sentence}」")

        if context_parts:
            context_info = f"\n\n【上下文语境】（修正时需结合这些相邻句子理解语义）\n" + "\n".join(context_parts)

    # FunASR 已内置标点，只需修正同音字和表达
    prompt = f"""你是一个专业的语音转文字校对专家。请结合上下文语境对转写文本进行校对。

【当前要修正的句子】
「{sentence}」{context_info}

【修正原则】
1. 修正明显的同音字错误（如：的地得混淆、不/别、那/哪、的/得等）
2. 修正影响理解的语法和表达问题
3. 根据上下文语境判断同音字的正确含义
4. 保持原文风格和语气，不要过度修改
5. 如果句子已经通顺准确，无需修正

请以 JSON 格式返回：
{{"corrected": "修正后的句子", "analysis": "修正说明（如无可省略）"}}"""

    # [I16 通信] 获取客户端
    client = get_client()
    settings = get_settings()

    # [I16 通信] 调用 DeepSeek API
    # [F12 捕获] API 调用异常处理
    try:
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的语音转文字校对专家，擅长根据上下文语境修正口语转写中的同音字错误和表达问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 低温度保证准确性
            max_tokens=500,
            timeout=30.0  # [I16 通信] 单次请求超时
        )

        content = response.choices[0].message.content.strip()
        logging.debug(f"DeepSeek 响应: {content}")

    except Exception as e:
        # [I13 渲染] 记录错误日志
        logging.error(f"DeepSeek API 调用失败 (第 {index+1} 句): {e}")
        raise RuntimeError(f"API 调用失败: {e}")

    # 解析响应
    try:
        # 清理响应内容
        clean_content = content.strip()
        if clean_content.startswith("```"):
            lines = clean_content.split('\n')
            clean_content = '\n'.join(lines[1:-1] if clean_content.endswith('```') else lines[1:])

        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', clean_content)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(clean_content)

        # 提取修正结果
        corrected = to_simplified(data.get("corrected", sentence))
        analysis = to_simplified(data.get("analysis", ""))

        # 如果修正结果为空或与原文相同，标记为无需修正
        if not corrected or corrected.strip() == sentence.strip():
            corrected = to_simplified(sentence)
            analysis = "无需修正"

    except json.JSONDecodeError as e:
        logging.warning(f"JSON 解析失败: {e}, 原始响应前200字: {content[:200]}")
        corrected = to_simplified(sentence)
        analysis = "JSON解析失败，未能获取修正结果"

    # [I13 渲染] 返回修正结果
    return CorrectionResult(
        sentence_index=index,
        original=to_simplified(sentence),  # 原文转简体
        corrected=corrected,
        analysis=analysis
    )


def correct_batch(text: str) -> List[CorrectionResult]:
    """
    # [I16 通信] 批量修正转写文本，结合全文语境

    Args:
        text: 原始转写文本

    Returns:
        List[CorrectionResult]: 修正结果列表
    """
    # [M5 转换] 分句
    sentences = split_sentences(text)

    if not sentences:
        logging.warning("文本为空，跳过修正")
        return []

    logging.info(f"开始修正 {len(sentences)} 个句子")

    results: List[CorrectionResult] = []
    failed_count = 0

    # [I16 通信] 逐句修正（传入所有句子作为上下文）
    for i, sentence in enumerate(sentences):
        try:
            # 传入所有句子列表，让AI能结合上下文语境修正
            result = correct_sentence(sentence, i, all_sentences=sentences)
            results.append(result)
            logging.debug(f"第 {i+1}/{len(sentences)} 句修正成功")

        except Exception as e:
            # [F12 捕获] 单句失败不影响整体
            logging.warning(f"第 {i+1} 句修正失败，使用原文: {e}")
            failed_count += 1

            # 使用原文作为失败时的回退
            results.append(CorrectionResult(
                sentence_index=i,
                original=to_simplified(sentence),
                corrected=to_simplified(sentence),
                analysis=f"修正失败: {str(e)}"
            ))

    logging.info(f"批量修正完成，成功 {len(sentences) - failed_count}/{len(sentences)} 句")

    return results
