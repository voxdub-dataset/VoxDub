"""Cut segments from annotations and standardize resolution / fps / sample rate."""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

import config
from download import find_full_video

logger = logging.getLogger(__name__)


def _run_ffmpeg(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] if result.stderr else "ffmpeg failed")


def target_resolution(meta: dict) -> tuple[int, int] | None:
    """Return (width, height). Prefer config.TARGET_SIZE, else annotation origin_*."""
    if config.TARGET_SIZE:
        return config.TARGET_SIZE
    w = meta.get("origin_width")
    h = meta.get("origin_height")
    if w and h:
        return int(w), int(h)
    return None


def standardize_segment(
    full_video: Path,
    meta: dict,
    out_mp4: Path,
    out_wav: Path,
    fps: int = config.TARGET_FPS,
    sr: int = config.TARGET_SR,
    overwrite: bool = False,
) -> bool:
    """
    Cut [start, end) from the full video:
      - out_mp4: target fps + resolution (H.264)
      - out_wav: mono, target sample rate
    """
    start = float(meta["start"])
    end = float(meta["end"])
    duration = end - start
    if duration <= 0:
        logger.warning("Invalid duration: %s", out_mp4)
        return False

    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    if out_mp4.exists() and out_wav.exists() and not overwrite:
        logger.debug("Exists, skip: %s", out_mp4.stem)
        return True

    size = target_resolution(meta)
    vf_parts = [f"fps={fps}"]
    if size:
        w, h = size
        vf_parts.append(
            f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
        )
    vf = ",".join(vf_parts)

    try:
        if not out_mp4.exists() or overwrite:
            cmd_v = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", str(start),
                "-i", str(full_video),
                "-t", str(duration),
                "-vf", vf,
                "-an",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-y", str(out_mp4),
            ]
            _run_ffmpeg(cmd_v)

        if not out_wav.exists() or overwrite:
            cmd_a = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", str(start),
                "-i", str(full_video),
                "-t", str(duration),
                "-vn",
                "-ac", str(config.TARGET_CHANNELS),
                "-ar", str(sr),
                "-y", str(out_wav),
            ]
            _run_ffmpeg(cmd_a)

        return out_mp4.exists() and out_wav.exists()
    except Exception as e:
        logger.error("Standardize failed %s: %s", out_mp4.stem, e)
        for p in (out_mp4, out_wav):
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        return False


def process_video(
    video_id: str,
    annot_dir: Path = config.ANNOT_DIR,
    raw_dir: Path = config.RAW_DIR,
    clips_dir: Path = config.CLIPS_DIR,
    workers: int = config.PROCESS_WORKERS,
    overwrite: bool = False,
    max_segments: int | None = None,
) -> tuple[int, int]:
    full = find_full_video(video_id, raw_dir)
    if full is None:
        logger.error("Full video not found, download first: %s", video_id)
        return 0, 0

    json_files = sorted((annot_dir / video_id).glob("*.json"))
    if max_segments and max_segments > 0:
        json_files = json_files[:max_segments]
    if not json_files:
        logger.warning("No annotations: %s", video_id)
        return 0, 0

    out_dir = clips_dir / video_id
    ok = fail = 0

    def _one(jp: Path) -> bool:
        with open(jp, encoding="utf-8") as f:
            meta = json.load(f)
        stem = jp.stem
        return standardize_segment(
            full,
            meta,
            out_dir / f"{stem}.mp4",
            out_dir / f"{stem}.wav",
            overwrite=overwrite,
        )

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = {ex.submit(_one, jp): jp for jp in json_files}
        for fut in tqdm(as_completed(futures), total=len(futures), desc=f"standardize {video_id}"):
            if fut.result():
                ok += 1
            else:
                fail += 1
    return ok, fail


def main():
    from utils import resolve_video_ids, setup_logging

    setup_logging("standardize")
    parser = argparse.ArgumentParser(description="Cut and standardize video/audio segments")
    parser.add_argument("video_ids", nargs="*", help="IDs starting with - go after --")
    parser.add_argument("--list-file", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=config.PROCESS_WORKERS)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--width", type=int, default=0, help="Force width (0 = from annotation)")
    parser.add_argument("--height", type=int, default=0, help="Force height (0 = from annotation)")
    parser.add_argument("--fps", type=int, default=config.TARGET_FPS)
    parser.add_argument("--sr", type=int, default=config.TARGET_SR)
    parser.add_argument("--max-segments", type=int, default=0, help="Max segments per video (debug)")
    args = parser.parse_args()

    ids = resolve_video_ids(args.video_ids, list_file=args.list_file, limit=args.limit)
    if not ids:
        parser.error("Provide video_ids / --list-file")

    if args.width > 0 and args.height > 0:
        config.TARGET_SIZE = (args.width, args.height)
    config.TARGET_FPS = args.fps
    config.TARGET_SR = args.sr

    total_ok = total_fail = 0
    for vid in ids:
        ok, fail = process_video(
            vid,
            workers=args.workers,
            overwrite=args.overwrite,
            max_segments=args.max_segments or None,
        )
        total_ok += ok
        total_fail += fail
        print(f"{vid}: ok={ok}, fail={fail}")
    print(f"Total: ok={total_ok}, fail={total_fail}")


if __name__ == "__main__":
    main()
