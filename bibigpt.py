"""BibiGPT API client for video subtitle extraction and summarization."""

import logging
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

API_BASE = "https://api.bibigpt.co/api"


@dataclass
class BibiResult:
    video_id: str
    title: str
    author: str
    description: str
    duration: float
    transcript: str
    url: str
    summary: str = ""


def _make_client(api_key: str) -> httpx.Client:
    return httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=300,
    )


def _join_subtitles(subtitles: list) -> str:
    parts = []
    for s in subtitles:
        text = s.get("text", "").strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _parse_detail(detail: dict, video_url: str) -> dict:
    subtitles_array = detail.get("subtitlesArray") or []
    transcript = _join_subtitles(subtitles_array)
    if not transcript:
        transcript = detail.get("contentText") or ""

    return {
        "video_id": detail.get("id") or "",
        "title": detail.get("title") or "",
        "author": detail.get("author") or "",
        "description": detail.get("descriptionText") or "",
        "duration": float(detail.get("duration") or 0),
        "transcript": transcript,
        "url": detail.get("url") or video_url,
    }


def _fetch_via_task(client: httpx.Client, video_url: str) -> BibiResult:
    """Async task fallback for long-form content."""
    log.info("[BibiGPT] Creating async task...")
    r = client.get("/v1/createSummaryTask", params={"url": video_url})
    r.raise_for_status()
    task_data = r.json()
    task_id = task_data.get("taskId")

    if not task_id:
        raise RuntimeError(f"BibiGPT: no taskId returned: {task_data}")

    log.info("[BibiGPT] Task %s created, polling...", task_id)

    for i in range(30):
        time.sleep(10)
        r = client.get("/v1/getSummaryTaskStatus", params={
            "taskId": task_id,
            "includeDetail": "true",
        })
        r.raise_for_status()
        status_data = r.json()
        status = status_data.get("status", "")
        log.info("[BibiGPT] Task %s: %s (%d/30)", task_id, status, i + 1)

        if status == "completed":
            summary_text = status_data.get("summary") or ""
            detail = status_data.get("detail") or {}
            parsed = _parse_detail(detail, video_url)
            return BibiResult(
                video_id=parsed["video_id"],
                title=parsed["title"],
                author=parsed["author"],
                description=parsed["description"],
                duration=parsed["duration"],
                transcript=parsed["transcript"],
                url=parsed["url"],
                summary=summary_text,
            )

        if status in ("failed", "error"):
            raise RuntimeError(f"BibiGPT task failed: {status_data}")

    raise RuntimeError(f"BibiGPT task timed out after 5 minutes: {task_id}")


def _handle_api_error(e: httpx.HTTPStatusError, client: httpx.Client, video_url: str):
    code = e.response.status_code
    if code == 422:
        log.info("[BibiGPT] Content too long, switching to async task")
        return _fetch_via_task(client, video_url)
    body = e.response.text[:300]
    raise RuntimeError(f"BibiGPT API error {code}: {body}")


def fetch_subtitle(api_key: str, video_url: str) -> BibiResult:
    """Fetch video subtitles and metadata via /v1/getSubtitle."""
    client = _make_client(api_key)
    log.info("[BibiGPT] Fetching subtitles: %s", video_url)

    try:
        r = client.get("/v1/getSubtitle", params={
            "url": video_url,
            "audioLanguage": "zh",
        })
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        result = _handle_api_error(e, client, video_url)
        if result:
            return result
    except httpx.TimeoutException:
        log.info("[BibiGPT] Timeout, switching to async task")
        return _fetch_via_task(client, video_url)
    except Exception as e:
        raise RuntimeError(f"BibiGPT request failed: {e}")

    detail = data.get("detail") or {}
    parsed = _parse_detail(detail, video_url)

    remaining = data.get("remainingTime")
    if remaining is not None:
        log.info("[BibiGPT] Remaining quota: %s", remaining)

    client.close()

    return BibiResult(
        video_id=parsed["video_id"],
        title=parsed["title"],
        author=parsed["author"],
        description=parsed["description"],
        duration=parsed["duration"],
        transcript=parsed["transcript"],
        url=parsed["url"],
    )


def fetch_summary(api_key: str, video_url: str) -> BibiResult:
    """Fetch video summary + metadata via /v1/summarize."""
    client = _make_client(api_key)
    log.info("[BibiGPT] Fetching summary: %s", video_url)

    try:
        r = client.get("/v1/summarize", params={
            "url": video_url,
            "includeDetail": "true",
        })
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        result = _handle_api_error(e, client, video_url)
        if result:
            return result
    except httpx.TimeoutException:
        log.info("[BibiGPT] Timeout, switching to async task")
        return _fetch_via_task(client, video_url)
    except Exception as e:
        raise RuntimeError(f"BibiGPT request failed: {e}")

    summary_text = data.get("summary") or ""
    detail = data.get("detail") or {}
    parsed = _parse_detail(detail, video_url)

    remaining = data.get("remainingTime")
    if remaining is not None:
        log.info("[BibiGPT] Remaining quota: %s", remaining)

    client.close()

    return BibiResult(
        video_id=parsed["video_id"],
        title=parsed["title"],
        author=parsed["author"],
        description=parsed["description"],
        duration=parsed["duration"],
        transcript=parsed["transcript"],
        url=parsed["url"],
        summary=summary_text,
    )
