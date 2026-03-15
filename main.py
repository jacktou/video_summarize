#!/usr/bin/env python3
"""Video Summarizer — extract subtitles and AI-summarize any video by URL.

Uses BibiGPT cloud API. Supports Douyin, Bilibili, YouTube, TikTok, etc.

Usage:
    python main.py <video_url>                     # BibiGPT summary (default)
    python main.py <video_url> --summarizer kimi   # BibiGPT subtitles + Kimi analysis
    python main.py <video_url> --json              # JSON output
"""

import argparse
import json
import logging
import os
import re
import sys
import traceback

log = logging.getLogger(__name__)

# Patterns for extracting video URLs from share text
_URL_PATTERN = re.compile(
    r'https?://(?:'
    r'v\.douyin\.com|vm\.douyin\.com|www\.douyin\.com|'
    r'www\.bilibili\.com|b23\.tv|'
    r'(?:www\.|m\.)?youtube\.com|youtu\.be|'
    r'(?:www\.|vm\.)?tiktok\.com|'
    r'(?:www\.)?xiaohongshu\.com|xhslink\.com|'
    r'x\.com|twitter\.com'
    r')[^\s]*'
)


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def get_api_key(env_name: str) -> str:
    """Get API key from environment variable."""
    return os.environ.get(env_name, "")


def extract_url(text: str) -> str:
    """Extract video URL from share text or return as-is if already a URL.

    Handles inputs like:
      - Plain URL: https://v.douyin.com/xxx/
      - Douyin share text: "7.92 复制打开抖音...https://v.douyin.com/xxx/ ..."
      - Bilibili share: "...https://b23.tv/xxx..."
    """
    text = text.strip()

    # Already a clean URL
    if re.match(r'https?://', text) and ' ' not in text:
        return text

    # Extract URL from share text
    match = _URL_PATTERN.search(text)
    if match:
        url = match.group(0).rstrip('，。！？、）》】')
        log.info("Extracted URL from share text: %s", url)
        return url

    return text


def process_bibigpt(url: str, api_key: str) -> dict:
    """One-stop: BibiGPT extracts and summarizes."""
    from bibigpt import fetch_summary

    bib = fetch_summary(api_key, url)
    return {
        "video_id": bib.video_id,
        "title": bib.title,
        "author": bib.author,
        "url": bib.url,
        "duration": bib.duration,
        "transcript": bib.transcript,
        "analysis": {
            "theme": "",
            "keywords": [],
            "sentiment": "",
            "abstract": bib.summary,
            "audience": "",
        },
    }


def process_kimi(url: str, bibigpt_key: str, kimi_key: str) -> dict:
    """Two-step: BibiGPT extracts subtitles, Kimi analyzes."""
    from bibigpt import fetch_subtitle
    from kimi import summarize

    bib = fetch_subtitle(bibigpt_key, url)

    log.info("Summarizing with Kimi...")
    s = summarize(
        title=bib.title,
        description=bib.description,
        transcript=bib.transcript,
        author=bib.author,
        api_key=kimi_key,
    )

    return {
        "video_id": bib.video_id,
        "title": bib.title,
        "author": bib.author,
        "url": bib.url,
        "duration": bib.duration,
        "transcript": bib.transcript,
        "analysis": {
            "theme": s.theme,
            "keywords": s.keywords,
            "sentiment": s.sentiment,
            "abstract": s.abstract,
            "audience": s.audience,
        },
    }


def format_markdown(result: dict) -> str:
    """Format result as readable Markdown."""
    r = result
    a = r["analysis"]
    lines = []

    lines.append(f"# {r['title']}\n")
    lines.append(f"- **作者**: {r['author']}")
    lines.append(f"- **链接**: {r['url']}")
    if r.get("duration"):
        m, s = divmod(int(r["duration"]), 60)
        lines.append(f"- **时长**: {m}分{s}秒")
    lines.append("")

    if a.get("theme"):
        lines.append("## 分析结果\n")
        lines.append(f"| 维度 | 内容 |")
        lines.append(f"|------|------|")
        lines.append(f"| 主题 | {a['theme']} |")
        kw = ", ".join(a["keywords"]) if a["keywords"] else "-"
        lines.append(f"| 关键词 | {kw} |")
        lines.append(f"| 情绪基调 | {a['sentiment']} |")
        lines.append(f"| 目标受众 | {a['audience']} |")
        lines.append(f"\n### 内容摘要\n\n{a['abstract']}\n")
    elif a.get("abstract"):
        lines.append(f"## AI 总结\n\n{a['abstract']}\n")

    if r.get("transcript"):
        preview = r["transcript"][:500]
        if len(r["transcript"]) > 500:
            preview += "..."
        lines.append(f"<details><summary>语音转录（前500字）</summary>\n")
        lines.append(f"{preview}\n")
        lines.append(f"</details>\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Video Summarizer — AI-powered video content analysis"
    )
    parser.add_argument("url", help="Video URL or share text (auto-extracts URL from Douyin/Bilibili/YouTube share messages)")
    parser.add_argument(
        "--summarizer", "-s",
        choices=["bibigpt", "kimi"],
        default="bibigpt",
        help="bibigpt (default, fast) or kimi (structured analysis)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON instead of Markdown",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Check API keys
    bibigpt_key = get_api_key("BIBIGPT_API_KEY")
    if not bibigpt_key:
        print("Error: BIBIGPT_API_KEY environment variable is required.", file=sys.stderr)
        print("Get your key at https://bibigpt.co", file=sys.stderr)
        sys.exit(1)

    if args.summarizer == "kimi":
        kimi_key = get_api_key("KIMI_API_KEY")
        if not kimi_key:
            print("Error: KIMI_API_KEY environment variable is required for --summarizer kimi.", file=sys.stderr)
            sys.exit(1)

    url = extract_url(args.url)
    log.info("Summarizer: %s | URL: %s", args.summarizer, url)

    try:
        if args.summarizer == "kimi":
            result = process_kimi(url, bibigpt_key, kimi_key)
        else:
            result = process_bibigpt(url, bibigpt_key)
    except Exception as e:
        log.error("Failed: %s", e)
        if args.verbose:
            log.error("Traceback:\n%s", traceback.format_exc())
        sys.exit(1)

    # Output
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(result))


if __name__ == "__main__":
    main()
