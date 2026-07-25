"""Download full YouTube videos by video_id."""
from __future__ import annotations

import argparse
import logging
import random
import time
from pathlib import Path

import yt_dlp

import config
from utils import (
    apply_download_config,
    cleanup_partials,
    resolve_video_ids,
    setup_logging,
)

logger = logging.getLogger(__name__)


def find_full_video(video_id: str, raw_dir: Path | None = None) -> Path | None:
    raw_dir = raw_dir or config.RAW_DIR
    for ext in (".mp4", ".mkv", ".webm"):
        p = raw_dir / f"{video_id}_full{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def build_ydl_opts(
    video_id: str,
    raw_dir: Path,
    proxy: str | None = None,
    max_height: int | None = None,
) -> dict:
    max_height = max_height if max_height is not None else config.DOWNLOAD_MAX_HEIGHT
    proxy = config.PROXY if proxy is None else proxy
    out_tmpl = str(raw_dir / f"{video_id}_full.%(ext)s")

    fmt = (
        f"bestvideo[ext=mp4][height<={max_height}]+bestaudio[ext=m4a]/"
        f"best[ext=mp4][height<={max_height}]/"
        f"best[height<={max_height}]/best"
    )
    opts: dict = {
        "format": fmt,
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
        "socket_timeout": 60,
        "retries": 10,
        "fragment_retries": 10,
        "quiet": False,
        "no_warnings": False,
        "concurrent_fragment_downloads": 4,
        # Exclude android_sdkless clients that often 403; requires a JS runtime (deno)
        "extractor_args": {
            "youtube": {"player_client": list(config.YOUTUBE_PLAYER_CLIENTS)},
        },
    }
    if proxy:
        opts["proxy"] = proxy
    if config.USE_ARIA2C:
        opts["external_downloader"] = "aria2c"
        opts["external_downloader_args"] = {
            "default": ["-x", "16", "-k", "1M", "-s", "16"],
        }
    if config.COOKIES_FROM_BROWSER:
        opts["cookiesfrombrowser"] = (config.COOKIES_FROM_BROWSER,)
    return opts


def download_video(
    video_id: str,
    raw_dir: Path | None = None,
    proxy: str | None = None,
    max_height: int | None = None,
    retries: int | None = None,
) -> Path | None:
    """
    Download a YouTube video to raw_dir/{video_id}_full.mp4.
    Skips if present. Returns path on success, None on failure.
    """
    raw_dir = raw_dir or config.RAW_DIR
    retries = retries if retries is not None else config.DOWNLOAD_RETRIES
    raw_dir.mkdir(parents=True, exist_ok=True)

    existing = find_full_video(video_id, raw_dir)
    if existing:
        logger.info("Already exists, skip: %s", existing)
        return existing

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = build_ydl_opts(video_id, raw_dir, proxy=proxy, max_height=max_height)

    for attempt in range(1, retries + 1):
        cleanup_partials(video_id, raw_dir)
        try:
            logger.info("Download [%d/%d]: %s", attempt, retries, url)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            path = find_full_video(video_id, raw_dir)
            if path:
                logger.info(
                    "Download ok: %s (%.1f MB)", path, path.stat().st_size / 1024 / 1024
                )
                return path
            logger.warning("File missing after download: %s", video_id)
        except Exception as e:
            logger.warning("Download failed (%d/%d) %s: %s", attempt, retries, video_id, e)
            if attempt < retries:
                time.sleep(attempt * 5)

    cleanup_partials(video_id, raw_dir)
    logger.error("Download failed permanently: %s", video_id)
    return None


def download_batch(
    video_ids: list[str],
    raw_dir: Path | None = None,
    sleep_range: tuple[float, float] | None = None,
) -> tuple[int, int, int]:
    raw_dir = raw_dir or config.RAW_DIR
    sleep_range = sleep_range or config.DOWNLOAD_SLEEP
    ok = skip = fail = 0
    for vid in video_ids:
        before = find_full_video(vid, raw_dir)
        path = download_video(vid, raw_dir)
        if path is None:
            fail += 1
        elif before is not None:
            skip += 1
        else:
            ok += 1
            time.sleep(random.uniform(*sleep_range))
    return ok, skip, fail


def main():
    setup_logging("download")
    parser = argparse.ArgumentParser(description="Download full YouTube videos by video_id")
    parser.add_argument("video_ids", nargs="*", help="One or more YouTube video IDs")
    parser.add_argument("--list-file", type=Path, help="Text file with one video_id per line")
    parser.add_argument("--from-annots", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--proxy", default=None, help="Proxy URL; empty string disables")
    parser.add_argument("--raw-dir", type=Path, default=None)
    parser.add_argument("--aria2c", action="store_true")
    parser.add_argument("--cookies-from-browser", default=None)
    args = parser.parse_args()

    apply_download_config(args.proxy, args.aria2c, args.cookies_from_browser)
    ids = resolve_video_ids(
        args.video_ids,
        list_file=args.list_file,
        from_annots=args.from_annots,
        limit=args.limit,
    )
    if not ids:
        parser.error("Provide video_ids / --list-file / --from-annots")

    raw_dir = args.raw_dir or config.RAW_DIR
    ok, skip, fail = download_batch(ids, raw_dir)
    print(f"Done: downloaded={ok}, skipped={skip}, failed={fail}, total={len(ids)}")


if __name__ == "__main__":
    main()
