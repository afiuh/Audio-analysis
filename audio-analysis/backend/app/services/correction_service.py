# [I16 通信] DeepSeek 文本修正服务模块
"""
调用 DeepSeek API 对转写文本进行逐句语义修正。
"""

import json
import logging
import re
import time
import threading
from typing import List, Optional
from collections import defaultdict

# [I16 通信] 并发控制 - 信号量限制同时进行的 API 调用数
# DeepSeek API 通常限制每分钟请求数，设置 3 个并发可以有效避免限流
_api_semaphore = threading.Semaphore(3)

# [I16 通信] 限流保护 - 滑动窗口限流器
class RateLimiter:
    """
    # [I16 通信] 基于滑动窗口的限流器

    支持按时间窗口限制请求频率，避免 API 限流
    """
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 60.0) -> bool:
        """
        获取限流令牌

        Args:
            timeout: 最大等待时间（秒）

        Returns:
            bool: 是否获取成功
        """
        start_time = time.time()

        while True:
            with self._lock:
                now = time.time()
                # 清理过期的请求记录
                self.requests = [t for t in self.requests if now - t < self.window_seconds]

                if len(self.requests) < self.max_requests:
                    # 还有额度，立即获取
                    self.requests.append(now)
                    return True

            # 等待一小段时间后重试
            if time.time() - start_time >= timeout:
                return False
            time.sleep(0.5)

    def release(self):
        """释放令牌（通常不需要调用）"""
        pass

    def get_wait_time(self) -> float:
        """
        获取需要等待的时间

        Returns:
            float: 还需要等待的秒数
        """
        with self._lock:
            now = time.time()
            self.requests = [t for t in self.requests if now - t < self.window_seconds]

            if len(self.requests) < self.max_requests:
                return 0.0

            # 计算还需要等待的时间
            oldest = min(self.requests)
            return max(0.0, self.window_seconds - (now - oldest))


# [I16 通信] 全局限流器实例
# DeepSeek 免费版通常限制 60 请求/分钟，我们设置 20/分钟 留有余量
_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)


def _sanitize_json_text(text: str) -> str:
    """
    # [T10 解析] 清理文本中的特殊字符，确保 JSON 兼容性
    
    Args:
        text: 待清理的文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return text
    
    # 替换中文全角引号为英文引号
    text = text.replace('"', '"').replace('"', '"')
    # 替换中文单引号（用于引用）
    text = text.replace(''', "'").replace(''', "'")
    # 转义反斜杠
    text = text.replace('\\', '\\\\')
    # 转义换行符等特殊字符（在 JSON 字符串内）
    text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    # 转义双引号
    text = text.replace('"', '\\"')
    
    return text


def _try_parse_json(content: str) -> Optional[dict]:
    """
    # [T10 解析] 尝试解析 JSON，支持多种容错方式
    
    清理策略：
    1. 去掉 markdown 代码块包裹
    2. 提取第一个完整的 JSON 对象（支持处理重复 JSON 输出）
    3. 清理末尾的 \' 等无效转义序列
    4. 清理不完整 JSON（如被截断的情况）
    5. 移除未转义换行符
    6. 修复多余逗号
    7. 修复孤立的反斜杠
    
    Args:
        content: 待解析的内容
        
    Returns:
        Optional[dict]: 解析成功返回字典，否则返回 None
    """
    if not content:
        return None
    
    original = content
    content = content.strip()
    
    # 1. 去掉 markdown 代码块包裹
    if content.startswith("```"):
        lines = content.split('\n')
        if lines[-1].strip() == '```':
            content = '\n'.join(lines[1:-1])
        else:
            content = '\n'.join(lines[1:])
    
    # 2. 替换中文弯引号为英文引号（JSON 标准字符）
    content = content.replace('"', '"').replace('"', '"')
    content = content.replace(''', "'").replace(''', "'")
    
    # 3. 提取第一个完整的 JSON 对象（通过括号配对追踪）
    json_start = content.find('{')
    if json_start == -1:
        return None
    
    # 使用栈追踪括号，找到第一个完整的 { ... } 对象
    json_str = None
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(json_start, len(content)):
        c = content[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if c == '\\' and in_string:
            escape_next = True
            continue
        
        if c == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if c == '{':
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0:
                # 找到第一个完整的 JSON 对象
                json_str = content[json_start:i + 1]
                break
    
    if json_str is None:
        return None
    
    # 4. 清理末尾的无效转义序列（如 \'、\" 等导致解析失败）
    # 这些通常出现在有效 JSON 后被 AI 附加的说明文字中
    # 匹配模式：\' 或 \" 后跟任意非 } 字符直到字符串结束
    json_str = re.sub(r"\\['\"][^}]*$", '', json_str)
    # 也清理可能残留的孤立反斜杠结尾
    json_str = re.sub(r'\\[^\"\\\\/bfnrtu]*$', '', json_str)
    
    # 5. 修复字符串内部的 \' （AI 常犯的错误，把 \' 改成 '）
    # 使用更精确的替换：只在 \' 前面不是反斜杠时替换
    json_str = json_str.replace("\\'", "'")
    
    # 6. 清理 HTML 标签等非 JSON 内容（如果还在有效范围内）
    html_end = json_str.rfind('</')
    if html_end > 0:
        closing_brace = json_str.rfind('}')
        if html_end > closing_brace:
            json_str = json_str[:html_end]
    
    # 6. 移除未转义换行符（JSON 字符串内不能有裸换行）
    json_str = re.sub(r'(?<!\\)\n', ' ', json_str)
    json_str = re.sub(r'(?<!\\)\r', '', json_str)
    
    # 7. 尝试标准解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # 8. 修复：去掉多余逗号（如 {"a": 1, }）
    json_str_fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
    try:
        return json.loads(json_str_fixed)
    except json.JSONDecodeError:
        pass
    
    # 9. 修复：清理孤立的反斜杠（非转义序列）
    # 匹配孤立的单反斜杠（不是 \\ 或 \" 等有效转义）
    def fix_unescaped_backslash(s):
        result = []
        i = 0
        while i < len(s):
            c = s[i]
            if c == '\\' and i + 1 < len(s):
                next_c = s[i + 1]
                # 检查是否是有效转义序列
                if next_c in '"\\/bfnrtu':
                    # 有效转义，保留
                    result.append(c)
                    result.append(next_c)
                    i += 2
                elif next_c == 'x' and i + 3 < len(s):
                    # 十六进制转义 \xNN
                    result.append(c)
                    result.append(next_c)
                    result.append(s[i + 2])
                    result.append(s[i + 3])
                    i += 4
                else:
                    # 孤立反斜杠，移除或替换
                    result.append('\\\\')  # 转为双反斜杠
                    i += 1
            else:
                result.append(c)
                i += 1
        return ''.join(result)
    
    json_str_fixed = fix_unescaped_backslash(json_str_fixed)
    try:
        return json.loads(json_str_fixed)
    except json.JSONDecodeError:
        pass
    
    # 10. 最后手段：尝试 ast.literal_eval
    try:
        import ast
        return ast.literal_eval(json_str_fixed)
    except:
        pass
    
    # 11. 极端情况：尝试暴力修复
    # 找到最后一个有效的 } 并截断
    last_valid_end = json_str_fixed.rfind('}')
    if last_valid_end > 0:
        truncated = json_str_fixed[:last_valid_end + 1]
        try:
            return json.loads(truncated)
        except:
            pass
    
    return None


def _safe_get_field(data: dict, key: str, fallback: str = "") -> str:
    """
    # [T10 解析] 安全获取字段，确保返回字符串
    
    Args:
        data: 数据字典
        key: 字段名
        fallback: 默认值
        
    Returns:
        str: 字段值（保证是字符串）
    """
    value = data.get(key, fallback)
    # 确保返回字符串
    if not isinstance(value, str):
        return str(value) if value else fallback
    return value

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
_review_client: OpenAI = None
_client_config_hash: str = ""  # 配置哈希，用于检测配置变更


def reset_client():
    """
    # [I16 通信] 重置客户端（用于配置热更新）
    """
    global _client, _review_client, _client_config_hash
    _client = None
    _review_client = None
    _client_config_hash = ""


def _get_config_hash() -> str:
    """
    # [I16 通信] 获取当前配置的哈希值，用于检测配置变更
    """
    settings = get_settings()
    return f"{settings.DEEPSEEK_API_KEY}:{settings.DEEPSEEK_BASE_URL}:{settings.DEEPSEEK_MODEL}"


def init_client() -> OpenAI:
    """
    # [I16 通信] 初始化 DeepSeek 客户端（支持热更新）

    Returns:
        OpenAI: OpenAI 兼容客户端实例

    # [F12 捕获] 客户端初始化异常处理
    """
    global _client, _client_config_hash

    # [I16 通信] 检查配置是否已变更（热更新支持）
    current_hash = _get_config_hash()
    if _client is not None and _client_config_hash == current_hash:
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
        _client_config_hash = current_hash  # 更新配置哈希
        logging.info("DeepSeek 客户端初始化成功")
        return _client

    except Exception as e:
        # [I13 渲染] 记录错误日志
        logging.error(f"DeepSeek 客户端初始化失败: {e}")
        raise RuntimeError(f"DeepSeek 客户端初始化失败: {e}")


def init_review_client() -> Optional[OpenAI]:
    """
    # [I16 通信] 初始化审核专用 DeepSeek 客户端

    Returns:
        Optional[OpenAI]: 审核客户端实例，如果未配置则返回 None
    """
    global _review_client

    if _review_client is not None:
        return _review_client

    settings = get_settings()

    # 检查是否配置了审核 API Key
    review_api_key = getattr(settings, 'REVIEW_API_KEY', '')
    if not review_api_key:
        logging.info("未配置 REVIEW_API_KEY，跳过审核功能")
        return None

    try:
        review_base_url = getattr(settings, 'REVIEW_BASE_URL', 'https://api.deepseek.com')
        _review_client = OpenAI(
            api_key=review_api_key,
            base_url=review_base_url,
            timeout=60.0
        )
        logging.info("DeepSeek 审核客户端初始化成功")
        return _review_client

    except Exception as e:
        logging.warning(f"DeepSeek 审核客户端初始化失败: {e}")
        return None


def get_review_client() -> Optional[OpenAI]:
    """
    # [I16 通信] 获取审核专用客户端

    Returns:
        Optional[OpenAI]: 审核客户端实例
    """
    global _review_client
    if _review_client is None:
        _review_client = init_review_client()
    return _review_client


def repair_json_with_ai(raw_response: str, sentence: str, index: int) -> Optional[dict]:
    """
    # [I16 通信] AI 修复 JSON（当自动解析失败时调用）

    Args:
        raw_response: AI 返回的原始响应（解析失败的）
        sentence: 对应的原始句子
        index: 句子索引

    Returns:
        Optional[dict]: 修复后的 JSON 数据
    """
    client = get_review_client()
    if client is None:
        logging.warning("审核客户端未配置，无法修复 JSON")
        return None

    settings = get_settings()
    review_model = getattr(settings, 'REVIEW_MODEL', 'deepseek-chat')

    prompt = f"""分析以下 AI 返回的内容，找出 JSON 格式错误并修复。

【原始返回内容】
{raw_response}

【对应的转写句子】
{sentence}

请仔细检查 JSON 格式问题（如引号、转义、逗号等），并输出正确格式的 JSON。
只返回 JSON，不要包含任何解释或说明。

要求的 JSON 格式：
{{"corrected": "修正后的句子", "analysis": "修正说明"}}

请直接输出修复后的 JSON："""

    try:
        response = client.chat.completions.create(
            model=review_model,
            messages=[
                {"role": "system", "content": "你是一个专业的 JSON 修复专家，擅长修复 AI 返回的损坏 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000,
            timeout=60.0
        )

        content = response.choices[0].message.content
        if not content:
            logging.warning(f"JSON 修复 AI 返回空内容 (第 {index+1} 句)")
            return None

        content = content.strip()
        logging.debug(f"JSON 修复响应: {content[:200]}")

        # 提取并尝试解析修复后的 JSON
        fixed_data = _try_parse_json(content)
        if fixed_data:
            logging.info(f"JSON 修复成功 (第 {index+1} 句)")
            return fixed_data

        return None

    except Exception as e:
        logging.warning(f"JSON 修复失败 (第 {index+1} 句): {e}")
        return None


def analyze_full_document(markdown_content: str, original_text: str) -> str:
    """
    # [I16 通信] 整体分析 MD 文档，对修正结果进行二次审核

    Args:
        markdown_content: 生成的 MD 文档内容
        original_text: 原始转写文本

    Returns:
        str: 整体分析内容，如果失败返回空字符串
    """
    client = get_review_client()
    if client is None:
        logging.info("审核客户端未配置，跳过整体分析")
        return ""

    settings = get_settings()
    review_model = getattr(settings, 'REVIEW_MODEL', 'deepseek-v4-flash')

    prompt = f"""请通读以下录音转写修正报告，进行全面的整体分析和二次修正。

【原始转写文本】
{original_text}

【修正后的报告】
{markdown_content}

请完成以下任务：

1. **二次修正**：检查报告中仍有问题的句子，进行修正
2. **内容分析**：
   - 会议/演讲的主题是什么？
   - 主要讨论了哪些内容？分点概括
   - 有哪些关键决策或结论？
   - 有哪些重要的人物、项目或事件被提及？
3. **数据统计**：统计修正的同音字数量、修正的主要类型等

请严格按以下 JSON 格式返回：
{{
    "second_corrections": [
        {{"sentence_index": 句号, "original": "原文", "corrected": "修正", "reason": "原因"}}
    ],
    "theme": "主题（一句话）",
    "main_points": ["要点1", "要点2", ...],
    "key_decisions": ["决策1", "决策2", ...],
    "mentioned_entities": ["人物/项目1", "人物/项目2", ...],
    "correction_stats": {{
        "total_corrections": 修正总数,
        "homophone_fixes": 同音字修正数,
        "grammar_fixes": 语法修正数,
        "expression_fixes": 表达修正数
    }}
}}

只返回 JSON，不要包含任何其他内容："""

    try:
        response = client.chat.completions.create(
            model=review_model,
            messages=[
                {"role": "system", "content": "你是一个专业的会议记录分析师，擅长深度分析录音内容和修正质量。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000,
            timeout=120.0
        )

        content = response.choices[0].message.content
        if not content:
            logging.warning(f"整体分析 AI 返回空内容，原始响应: {response}")
            # 重试一次
            logging.info("整体分析重试...")
            response = client.chat.completions.create(
                model=review_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的会议记录分析师，擅长深度分析录音内容和修正质量。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                timeout=120.0
            )
            content = response.choices[0].message.content
            if not content:
                logging.warning("整体分析重试后仍返回空内容，跳过分析")
                return ""

        content = content.strip()
        logging.debug(f"整体分析响应: {content[:200]}")

        # 解析响应
        data = _try_parse_json(content)

        if data is None:
            logging.warning("整体分析 JSON 解析失败")
            return ""

        # 构建分析报告
        analysis_parts = ["\n\n---\n\n## 整体内容分析\n"]

        # 主题
        theme = to_simplified(_safe_get_field(data, "theme", ""))
        if theme:
            analysis_parts.append(f"**主题：** {theme}\n\n")

        # 主要内容
        main_points = data.get("main_points", [])
        if main_points:
            analysis_parts.append("**主要内容：**\n")
            for i, point in enumerate(main_points, 1):
                analysis_parts.append(f"{i}. {to_simplified(str(point))}\n")
            analysis_parts.append("\n")

        # 关键决策
        key_decisions = data.get("key_decisions", [])
        if key_decisions:
            analysis_parts.append("**关键决策/结论：**\n")
            for decision in key_decisions:
                analysis_parts.append(f"- {to_simplified(str(decision))}\n")
            analysis_parts.append("\n")

        # 提及实体
        mentioned_entities = data.get("mentioned_entities", [])
        if mentioned_entities:
            analysis_parts.append("**提及的人物/项目：**\n")
            for entity in mentioned_entities:
                analysis_parts.append(f"- {to_simplified(str(entity))}\n")
            analysis_parts.append("\n")

        # 修正统计
        stats = data.get("correction_stats", {})
        if stats:
            analysis_parts.append("**本次修正统计：**\n")
            analysis_parts.append(f"- 总修正数：{stats.get('total_corrections', 0)}\n")
            analysis_parts.append(f"- 同音字修正：{stats.get('homophone_fixes', 0)}\n")
            analysis_parts.append(f"- 语法修正：{stats.get('grammar_fixes', 0)}\n")
            analysis_parts.append(f"- 表达修正：{stats.get('expression_fixes', 0)}\n\n")

        # 二次修正
        second_corrections = data.get("second_corrections", [])
        if second_corrections:
            analysis_parts.append("**二次修正（如有）：**\n")
            for corr in second_corrections:
                idx = corr.get("sentence_index", "?")
                orig = to_simplified(_safe_get_field(corr, "original", ""))
                corr_text = to_simplified(_safe_get_field(corr, "corrected", ""))
                reason = to_simplified(_safe_get_field(corr, "reason", ""))
                analysis_parts.append(f"- 第{idx}句：「{orig}」→「{corr_text}」({reason})\n")

        result = "".join(analysis_parts)
        logging.info(f"整体分析完成，二次修正 {len(second_corrections)} 处")
        return result

    except Exception as e:
        logging.warning(f"整体分析失败: {e}")
        return ""


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


def summarize_full_text(sentences: List[str]) -> str:
    """
    总结全文主题和大意，为后续句子修正提供全局上下文

    Args:
        sentences: 所有句子列表

    Returns:
        str: 主题和全文大意总结
    """
    full_text = "\n".join(sentences)

    prompt = f"""请阅读以下会议/演讲转写文本，先总结出【主题】和【全文大意】，以便后续逐句修正时能更准确地判断同音字和口语表达。

【转写文本】
{full_text}

请严格按以下 JSON 格式返回：
{{"theme": "会议/演讲的主题（一句话概括）", "summary": "全文主要内容概述（2-3句话概括要点）"}}

注意：只返回 JSON，不要包含任何其他内容。"""

    # [I16 通信] 获取客户端（支持热更新）
    client = get_client()
    settings = get_settings()

    # [I16 通信] 获取限流令牌
    wait_time = _rate_limiter.get_wait_time()
    if wait_time > 0:
        logging.info(f"限流保护：等待 {wait_time:.1f} 秒后继续...")
        time.sleep(wait_time)

    if not _rate_limiter.acquire(timeout=120.0):
        logging.warning("限流保护：等待超时，跳过全文总结")
        return ""

    # [I16 通信] 获取并发令牌
    acquired = _api_semaphore.acquire(timeout=120.0)
    if not acquired:
        logging.warning("并发控制：等待超时，跳过全文总结")
        return ""

    try:
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的会议记录分析专家，擅长总结会议主题和要点。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            timeout=60.0
        )

        content = response.choices[0].message.content
        if not content:
            logging.warning("DeepSeek 返回空内容，无法获取全文总结")
            return ""

        content = content.strip()
        logging.debug(f"全文总结响应: {content[:200]}")

        # 解析响应
        data = _try_parse_json(content)

        if data is None:
            logging.warning("全文总结 JSON 解析失败")
            return ""

        theme = to_simplified(_safe_get_field(data, "theme", ""))
        summary = to_simplified(_safe_get_field(data, "summary", ""))

        if theme or summary:
            result = f"【主题】{theme}\n【全文大意】{summary}"
            logging.info(f"已获取全文总结: {theme}")
            return result

        return ""

    except Exception as e:
        logging.warning(f"获取全文总结失败: {e}")
        return ""
    finally:
        _api_semaphore.release()


def correct_sentence(sentence: str, index: int, context: str = None, all_sentences: List[str] = None, full_text_summary: str = None) -> CorrectionResult:
    """
    修正单个句子，结合全文主题/大意和上下文语境进行校对

    Args:
        sentence: 原始句子
        index: 句子索引
        context: 全文语境（所有句子，用于理解上下文）
        all_sentences: 所有句子列表（可选，方便引用前后句子）
        full_text_summary: 全文主题和大意总结（由 summarize_full_text 生成）

    Returns:
        CorrectionResult: 修正结果

    """
    # 构建全局主题信息
    global_context = ""
    if full_text_summary:
        global_context = f"\n\n【全文主题和大意】（修正时请优先考虑这个全局上下文，确保句子与主题一致）\n{full_text_summary}\n"

    # 构建语境信息（相邻句子）
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
            context_info = f"\n\n【相邻句子上下文】（修正时需结合这些相邻句子理解语义）\n" + "\n".join(context_parts)

    # FunASR 已内置标点，只需修正同音字和表达
    prompt = f"""你是一个专业的语音转文字校对专家。请结合【全文主题和大意】和【相邻句子上下文】对转写文本进行校对。

{global_context}【当前要修正的句子】
「{sentence}」{context_info}

【修正原则】
1. 修正明显的同音字错误（如：的地得混淆、不/别、那/哪、的/得等）
2. 修正影响理解的语法和表达问题
3. 根据上下文语境判断同音字的正确含义
4. 保持原文风格和语气，不要过度修改
5. 如果句子已经通顺准确，无需修正

【重要】请严格按以下 JSON 格式返回，不要包含任何其他内容：
{{"corrected": "修正后的句子（用英文双引号包裹）", "analysis": "修正说明（用英文双引号包裹，如无可省略）"}}

注意：analysis 字段中如需引用文字，请使用单引号 ' 而非双引号 ""，确保 JSON 格式正确。"""

    # [I16 通信] 获取客户端（支持热更新）
    client = get_client()
    settings = get_settings()

    # [I16 通信] 获取限流令牌
    wait_time = _rate_limiter.get_wait_time()
    if wait_time > 0:
        logging.debug(f"限流保护：等待 {wait_time:.1f} 秒...")
        time.sleep(wait_time)

    if not _rate_limiter.acquire(timeout=180.0):
        logging.warning(f"限流保护：等待超时 (第 {index+1} 句)")
        # 返回原文作为降级方案
        return CorrectionResult(
            sentence_index=index,
            original=to_simplified(sentence),
            corrected=to_simplified(sentence),
            analysis="限流等待超时，使用原文"
        )

    # [I16 通信] 获取并发令牌（限制同时进行的 API 调用数）
    acquired = _api_semaphore.acquire(timeout=180.0)
    if not acquired:
        logging.warning(f"并发控制：等待超时 (第 {index+1} 句)")
        # 返回原文作为降级方案
        return CorrectionResult(
            sentence_index=index,
            original=to_simplified(sentence),
            corrected=to_simplified(sentence),
            analysis="并发等待超时，使用原文"
        )

    try:
        # [I16 通信] 调用 DeepSeek API
        # [F12 捕获] API 调用异常处理
        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的语音转文字校对专家，擅长根据上下文语境修正口语转写中的同音字错误和表达问题。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 低温度保证准确性
            max_tokens=8000,  # 充足 token 上限，避免输出被截断
            timeout=60.0  # [I16 通信] 增加超时时间
        )

        content = response.choices[0].message.content
        if not content:
            logging.warning(f"DeepSeek 返回空内容 (第 {index+1} 句)")
            raise RuntimeError("DeepSeek API 返回空响应")
        content = content.strip()
        logging.debug(f"DeepSeek 响应: {content[:200]}")

    except Exception as e:
        # [I13 渲染] 记录错误日志
        logging.error(f"DeepSeek API 调用失败 (第 {index+1} 句): {e}")
        raise RuntimeError(f"API 调用失败: {e}")
    finally:
        _api_semaphore.release()

    # 解析响应
    data = _try_parse_json(content)

    if data is None:
        # JSON 解析失败，记录详情
        logging.warning(f"JSON 解析失败 (第 {index+1} 句)，尝试 AI 修复...")
        logging.warning(f"原始响应 (repr): {repr(content[:500])}")

        # 尝试用 AI 修复 JSON
        data = repair_json_with_ai(content, sentence, index)

        if data is None:
            # AI 修复也失败，使用原文
            logging.warning(f"AI 修复失败 (第 {index+1} 句)，使用原文")
            corrected = to_simplified(sentence)
            analysis = "JSON解析失败，未能获取修正结果"
        else:
            # AI 修复成功，使用修复后的数据
            logging.info(f"AI 修复成功 (第 {index+1} 句)")
            corrected = to_simplified(_safe_get_field(data, "corrected", ""))
            analysis = to_simplified(_safe_get_field(data, "analysis", ""))

            # 验证修正结果有效性
            if not corrected or corrected.strip() == sentence.strip():
                if not analysis:
                    corrected = to_simplified(sentence)
                    analysis = "AI修复：无需修正"
    else:
        # 安全提取字段
        corrected = to_simplified(_safe_get_field(data, "corrected", ""))
        analysis = to_simplified(_safe_get_field(data, "analysis", ""))
        
        # 验证修正结果有效性
        if not corrected or corrected.strip() == sentence.strip():
            if not analysis:
                corrected = to_simplified(sentence)
                analysis = "无需修正"

    # [I13 渲染] 返回修正结果
    return CorrectionResult(
        sentence_index=index,
        original=to_simplified(sentence),  # 原文转简体
        corrected=corrected,
        analysis=analysis
    )


def correct_batch(text: str) -> List[CorrectionResult]:
    """
    # [I16 通信] 批量修正转写文本，结合全文主题/大意和上下文语境

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

    # [I16 通信] 第一步：先总结全文主题和大意
    full_text_summary = ""
    if len(sentences) >= 2:
        logging.info("正在总结全文主题和大意...")
        full_text_summary = summarize_full_text(sentences)
        if full_text_summary:
            logging.info("已获取全文主题和大意，开始逐句修正")
        else:
            logging.warning("未能获取全文总结，将仅使用相邻句子上下文")

    results: List[CorrectionResult] = []
    failed_count = 0

    # [I16 通信] 逐句修正（传入全文总结和所有句子作为上下文）
    for i, sentence in enumerate(sentences):
        try:
            # 传入全文总结和所有句子列表，让AI能结合全局主题和上下文语境修正
            result = correct_sentence(sentence, i, all_sentences=sentences, full_text_summary=full_text_summary)
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
