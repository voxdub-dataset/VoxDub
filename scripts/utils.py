"""Shared helpers: logging, video-id resolution, download config."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import config


def setup_logging(name: str = "pipeline") -> logging.Logger:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_DIR / f"{name}.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return logging.getLogger(name)


def unique_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def load_id_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def resolve_video_ids(
    positional: list[str] | None = None,
    video_id: list[str] | None = None,
    list_file: Path | None = None,
    from_annots: bool = False,
    limit: int = 0,
) -> list[str]:
    """
    Collect video IDs from CLI sources.
    IDs starting with '-' must use: `run -- --561dw9wOc` or `--video-id=--561dw9wOc`.
    """
    ids: list[str] = []
    if positional:
        ids.extend(positional)
    if video_id:
        ids.extend(video_id)
    if list_file:
        ids.extend(load_id_list(Path(list_file)))
    if from_annots:
        from extract_annots import list_video_ids

        ids.extend(list_video_ids())

    uniq = unique_preserve(ids)
    if limit and limit > 0:
        uniq = uniq[:limit]
    return uniq


def apply_download_config(
    proxy: str | None = None,
    aria2c: bool = False,
    cookies_from_browser: str | None = None,
) -> None:
    """Apply CLI download options to config. proxy=None keeps current; "" disables."""
    if proxy is not None:
        config.PROXY = proxy or None
    if aria2c:
        config.USE_ARIA2C = True
    if cookies_from_browser:
        config.COOKIES_FROM_BROWSER = cookies_from_browser


def cleanup_partials(video_id: str, raw_dir: Path | None = None) -> int:
    """Remove incomplete download fragments. Returns number of deleted files."""
    raw_dir = raw_dir or config.RAW_DIR
    if not raw_dir.exists():
        return 0
    removed = 0
    patterns = [
        f"{video_id}_full*.part",
        f"{video_id}_full*.ytdl",
        f"{video_id}_full.f*.mp4",
        f"{video_id}_full.f*.m4a",
        f"{video_id}_full.f*.webm",
    ]
    for pat in patterns:
        for p in raw_dir.glob(pat):
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    return removed
