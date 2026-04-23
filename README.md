# 录音分析工具

自动将录音转换为文字，并通过 AI 修正转写错误，生成结构化的分析报告。

## 功能特性

- 🎤 **音频上传** - 支持 MP3、WAV 格式，最大 100MB
- 🔊 **语音转文字** - 基于 FunASR 本地转写（保护隐私）
- ✏️ **AI 修正** - 调用 DeepSeek 对每句话进行语义修正，结合全文上下文语境判断同音字
- 📄 **MD 导出** - 生成包含原文和 AI 分析的 Markdown 报告
- 🐱 **Claude 风格界面** - 像素艺术宠物图标，实时进度显示（已用时/预估剩余时间）

## 技术栈

| 组件 | 技术 |
|---|---|
| 后端 | FastAPI + Python |
| 前端 | 原生 HTML/CSS/JS (Claude 风格) |
| 语音识别 | FunASR paraformer-zh (本地 GPU/CPU) |
| 文本修正 | DeepSeek API |
| 前端风格 | Claude Design System |

## 环境要求

- Python 3.8+（推荐 3.12）
- NVIDIA GPU (4GB+ 显存，推荐) 或 CPU
- CUDA 驱动（仅 GPU 模式需要）

## 快速开始

### 1. 进入项目目录

```bash
cd audio-analysis/backend
```

### 2. 配置环境

```bash
# 复制配置文件
copy .env.example .env

# 编辑 .env，填入你的 DeepSeek API Key
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

> 首次运行会自动下载 FunASR `paraformer-zh` 模型（约 1GB）

### 4. 启动服务

```bash
# 方式一：使用启动脚本
双击运行 backend/start.bat 或 backend/start.ps1

# 方式二：手动启动（Python 3.12）
cd backend
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问：
- **前端界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

> 注意：前端通过 fetch 调用 API，必须通过 http://localhost:8000 访问，不能直接双击打开 index.html 文件

## 使用流程

1. 启动后端服务（见上方「快速开始」）
2. 访问 http://localhost:8000 打开前端界面
3. 拖拽或选择音频文件（MP3/WAV）
4. 点击「上传并开始分析」
5. 等待处理完成，实时查看进度（已用时、预估剩余时间）
6. 处理完成后，点击「打开报告」复制报告文件夹路径

## 项目结构

```
audio-analysis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py           # 配置加载
│   │   ├── models/schemas.py   # 数据模型
│   │   ├── routers/audio.py    # API 路由
│   │   ├── services/
│   │   │   ├── stt_service.py          # FunASR 转写
│   │   │   ├── correction_service.py   # DeepSeek 修正
│   │   │   └── export_service.py       # MD 导出
│   │   └── utils/file_handler.py  # 文件处理
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
│
└── frontend/
    ├── index.html               # Claude 风格界面
    ├── js/
    │   ├── app.js              # 主应用逻辑
    │   ├── api.js              # API 调用封装
    │   ├── components.js       # UI 组件
    │   └── pet-icons.js        # Claude 像素宠物图标
    └── css/
        └── styles.css          # 样式文件
```

## API 接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/audio/upload` | POST | 上传音频文件 |
| `/api/audio/status/{task_id}` | GET | 查询任务状态 |
| `/api/audio/transcribe/{task_id}` | POST | 执行转写和修正 |
| `/api/audio/download/{task_id}` | GET | 下载 MD 报告 |

## 配置说明

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | - | DeepSeek API 密钥（必需） |
| `DEEPSEEK_BASE_URL` | https://api.deepseek.com | API 端点 |
| `DEEPSEEK_MODEL` | deepseek-chat | 使用的模型 |
| `FUNASR_MODEL` | paraformer-zh | FunASR 模型 |

## FunASR vs Whisper

| 对比项 | FunASR | Whisper |
|---|---|---|
| 中文识别 | ⭐⭐⭐⭐⭐ 专为中文优化 | ⭐⭐⭐ 一般 |
| 长音频处理 | ⭐⭐⭐⭐⭐ paraformer 模型 | ⭐⭐⭐ 容易漂移 |
| 内置标点 | ✅ 有 | ❌ 需要 Prompt |
| 模型大小 | ~1GB | ~500MB |
| GPU 需求 | 较低 | 较高 |

## 常见问题

### Q: 没有 GPU 怎么办？
A: FunASR 支持 CPU 运行，会自动选择 CPU 模式。

### Q: FunASR 模型下载失败？
A: 可以手动设置镜像源：
```bash
pip install modelscope
export MODELSCOPE_SDK_DEBUG=1
```

### Q: DeepSeek API 调用失败？
A: 检查网络连接和 API Key 是否正确。

### Q: AI 修正效果不好？
A: 修正时会结合上下文语境判断同音字（如"的/地/得"、"那/哪"等）。如果仍有误差，可手动编辑导出的 Markdown 报告。

### Q: 转写结果是繁体字？
A: 系统会自动转换为简体字，无需手动处理。

## License

MIT
