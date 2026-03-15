---
name: video-summarize
description: >
  Summarizes video content from a URL or app share text.
  Use when the user sends a video link or share message from Douyin, Bilibili, YouTube, TikTok, Xiaohongshu, Twitter/X, or other platforms.
  Extracts subtitles and generates an AI summary via BibiGPT cloud API.
  Accepts raw share text like "7.92 复制打开抖音…https://v.douyin.com/xxx/" and auto-extracts the URL.
user-invocable: true
metadata:
  openclaw:
    emoji: "🎬"
    primaryEnv: BIBIGPT_API_KEY
    requires:
      bins:
        - python3
      env:
        - BIBIGPT_API_KEY
    os:
      - linux
      - darwin
    install:
      - type: node
        command: "pip install -r requirements.txt"
---

# Video Summarizer

Summarize any video by URL. Auto-extracts links from app share text.

## When to use

Activate this skill when the user:
- Sends a video URL (douyin.com, bilibili.com, youtube.com, tiktok.com, etc.)
- Pastes app share text containing a video link (e.g. Douyin "复制打开抖音…https://v.douyin.com/xxx/")
- Asks to summarize, analyze, or explain a video

## How to run

```bash
cd {{SKILL_DIR}}
python3 main.py "<user_input>"
```

Pass the user's **original message** as the argument — the script auto-extracts URLs from share text.

Return the **full stdout** to the user as the response.

## Options

| Flag | Effect |
|------|--------|
| `--summarizer kimi` | Structured analysis (theme/keywords/sentiment). Requires `KIMI_API_KEY` env. |
| `--json` | Output as JSON instead of Markdown. |

## Error handling

- **401/403**: Tell user their BibiGPT API key is invalid or quota is exhausted.
- **422 / timeout**: Long video — the script auto-retries via async task (up to 5 min).
- **Empty output**: Video has no speech (pure music/BGM). Tell the user.
