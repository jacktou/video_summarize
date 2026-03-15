# Video Summarize

BibiGPT API 驱动的视频内容总结工具，支持抖音、B站、YouTube、TikTok、小红书等主流平台。

无需下载视频，无需 ffmpeg / whisper，纯云端 API 调用，适合部署在任意服务器。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 设置 API Key
export BIBIGPT_API_KEY="your_key_here"  # 必需，https://bibigpt.co 获取

# 视频链接
python3 main.py "https://www.douyin.com/video/xxx"

# 抖音 App 分享文本（自动提取链接）
python3 main.py "7.92 复制打开抖音，看看【xxx的作品】... https://v.douyin.com/xxx/ ..."

# B站 / YouTube
python3 main.py "https://www.bilibili.com/video/BVxxx"
python3 main.py "https://www.youtube.com/watch?v=xxx"
```

## 使用方式

```bash
# 默认模式 — BibiGPT 一站式总结（快）
python3 main.py "<url>"

# Kimi 结构化分析（主题/关键词/情绪/受众）
export KIMI_API_KEY="your_kimi_key"
python3 main.py "<url>" --summarizer kimi

# JSON 输出
python3 main.py "<url>" --json

# 详细日志
python3 main.py "<url>" -v
```

## 输出示例

```
# 这六个字你们能够遵守几个

- 作者: 亿杉一招鲜
- 链接: https://www.douyin.com/video/7580880283353413819
- 时长: 8分16秒

## AI 总结

本视频分享了作者在金融市场摸爬滚打多年总结出的六字心法：
"选、进、止、仓、规、执"……
```

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `BIBIGPT_API_KEY` | 是 | BibiGPT API Key（[获取](https://bibigpt.co)） |
| `KIMI_API_KEY` | 仅 `--summarizer kimi` | Moonshot Kimi API Key |

## 支持平台

抖音 / TikTok / Bilibili / YouTube / 小红书 / Twitter(X) 等（BibiGPT 支持的所有平台）

## 项目结构

```
video_summarize/
├── main.py           # CLI 入口，URL 提取 + 输出格式化
├── bibigpt.py        # BibiGPT API 客户端（字幕提取 + 总结 + 异步任务兜底）
├── kimi.py           # Kimi 结构化分析（可选）
├── SKILL.md          # OpenClaw Skill 定义
└── requirements.txt  # httpx, openai
```

## OpenClaw 部署

本项目可作为 [OpenClaw](https://docs.openclaw.ai) Skill 使用，将目录放入 `~/.openclaw/skills/video-summarize/` 即可自动加载。

## License

MIT
