#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Cookie-free, single-video Douyin downloader derived from DouK's request flow."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote, urlencode, urlparse

import requests

from a_bogus import ABogus, USERAGENT


DETAIL_ID = re.compile(r"(?<!\d)(\d{19})(?!\d)")
URL = re.compile(r"https?://[^\s\"<>]+")
ALLOWED_HOSTS = ("douyin.com", "iesdouyin.com")
DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
BASE_PARAMS = {
    "device_platform": "webapp",
    "aid": "6383",
    "channel": "channel_pc_web",
    "update_version_code": "170400",
    "pc_client_type": "1",
    "pc_libra_divert": "Windows",
    "support_h265": "1",
    "support_dash": "1",
    "version_code": "190500",
    "version_name": "19.5.0",
    "cookie_enabled": "true",
    "screen_width": "1536",
    "screen_height": "864",
    "browser_language": "zh-CN",
    "browser_platform": "Win32",
    "browser_name": "Chrome",
    "browser_version": "139.0.0.0",
    "browser_online": "true",
    "engine_name": "Blink",
    "engine_version": "139.0.0.0",
    "os_name": "Windows",
    "os_version": "10",
    "cpu_core_num": "16",
    "device_memory": "8",
    "platform": "PC",
    "downlink": "10",
    "effective_type": "4g",
    "round_trip_time": "200",
    "uifid": "",
    "msToken": "",
}


class DownloadError(RuntimeError):
    pass


def is_allowed_douyin_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_HOSTS
    )


def extract_authorized_url(text: str) -> str:
    for match in URL.finditer(text):
        candidate = match.group(0).rstrip("，。；！？、)]}")
        if is_allowed_douyin_url(candidate):
            return candidate
    raise DownloadError("No valid HTTPS Douyin URL was found")


def resolve_detail_id(session: requests.Session, source_url: str, timeout: int) -> str:
    response = session.head(source_url, allow_redirects=True, timeout=timeout)
    for value in (str(response.url),):
        if match := DETAIL_ID.search(value):
            return match.group(1)
    response.raise_for_status()
    raise DownloadError("The Douyin link resolved, but no 19-digit video ID was found")


def fetch_detail(session: requests.Session, detail_id: str, timeout: int) -> dict:
    params = BASE_PARAMS | {"aweme_id": detail_id}
    encoded = urlencode(params, quote_via=quote)
    params["a_bogus"] = ABogus(USERAGENT).get_value(encoded)
    response = session.get(
        DETAIL_API,
        params=params,
        headers={
            "Accept": "*/*",
            "Accept-Encoding": "*/*",
            "Referer": "https://www.douyin.com/?recommend=1",
            "User-Agent": USERAGENT,
        },
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except requests.JSONDecodeError as exc:
        content_type = response.headers.get("Content-Type", "unknown")
        raise DownloadError(
            f"Douyin returned a non-JSON detail response "
            f"(status={response.status_code}, type={content_type}, bytes={len(response.content)})"
        ) from exc
    detail = payload.get("aweme_detail")
    if not isinstance(detail, dict):
        status = payload.get("status_code")
        raise DownloadError(f"Douyin detail response did not contain a video (status={status})")
    return detail


def select_video_url(detail: dict) -> str:
    video = detail.get("video") or {}
    candidates = []
    for rate in video.get("bit_rate") or []:
        address = rate.get("play_addr") or {}
        urls = address.get("url_list") or []
        if not urls:
            continue
        score = (
            max(address.get("height") or 0, address.get("width") or 0),
            rate.get("FPS") or 0,
            rate.get("bit_rate") or 0,
            address.get("data_size") or 0,
        )
        candidates.append((score, urls[-1]))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    urls = (video.get("play_addr") or {}).get("url_list") or []
    if urls:
        return urls[-1]
    raise DownloadError("Douyin detail data did not contain a downloadable video URL")


def download_file(session: requests.Session, media_url: str, output: Path, timeout: int) -> Path:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".part")
    headers = {
        "Accept": "*/*",
        "Range": "bytes=0-",
        "Referer": "https://www.douyin.com/?recommend=1",
        "User-Agent": USERAGENT,
        "Cookie": "dy_swidth=1536; dy_sheight=864",
    }
    try:
        with session.get(media_url, headers=headers, stream=True, timeout=(timeout, timeout)) as response:
            response.raise_for_status()
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" in content_type or "application/json" in content_type:
                raise DownloadError(f"Douyin media endpoint returned {content_type}")
            with temporary.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise DownloadError("Douyin returned an empty video file")
        os.replace(temporary, output)
        return output
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def run(source_text: str, output: Path, timeout: int) -> dict:
    source_url = extract_authorized_url(source_text)
    session = requests.Session()
    session.headers.update({"User-Agent": USERAGENT})
    detail_id = resolve_detail_id(session, source_url, timeout)
    detail = fetch_detail(session, detail_id, timeout)
    video = download_file(session, select_video_url(detail), output, timeout)
    return {"video": str(video), "detailId": detail_id, "engine": "douk-direct"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Authorized Douyin share text or URL")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    # ASCII-only JSON keeps Windows redirected stdout independent of the active code page.
    print(json.dumps(run(args.url, args.output, args.timeout), ensure_ascii=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DownloadError, OSError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
