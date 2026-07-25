"""
End-to-end pipeline: extract annotations -> download -> standardize -> denoise.

See README.md for usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import config
from utils import apply_download_config, resolve_video_ids, setup_logging

logger = setup_logging("pipeline")


def _require_ids(args) -> list[str]:
    ids = resolve_video_ids(
        positional=getattr(args, "video_ids", None),
        video_id=getattr(args, "video_id", None),
        list_file=getattr(args, "list_file", None),
        from_annots=getattr(args, "from_annots", False),
        limit=getattr(args, "limit", 0) or 0,
    )
    if not ids:
        sys.exit(
            "Provide video_id / --list-file / --from-annots "
            "(IDs starting with '-' must use: run -- --xxx)"
        )
    return ids


def cmd_extract(args):
    from extract_annots import extract_annotations, list_video_ids

    path = extract_annotations(force=args.force)
    print(f"Annotation dir: {path}")
    print(f"Videos: {len(list_video_ids(path))}")


def cmd_download(args):
    from download import download_batch

    apply_download_config(args.proxy, args.aria2c, args.cookies_from_browser)
    ok, skip, fail = download_batch(_require_ids(args))
    print(f"Download done: downloaded={ok}, skipped={skip}, failed={fail}")


def cmd_standardize(args):
    from standardize import process_video

    if args.width and args.height:
        config.TARGET_SIZE = (args.width, args.height)
    total_ok = total_fail = 0
    for vid in _require_ids(args):
        ok, fail = process_video(vid, workers=args.workers, overwrite=args.overwrite)
        print(f"[standardize] {vid}: ok={ok}, fail={fail}")
        total_ok += ok
        total_fail += fail
    print(f"Standardize total: ok={total_ok}, fail={total_fail}")


def cmd_denoise(args):
    from denoise import denoise_video_dir

    if args.device:
        config.SEPARATE_DEVICE = args.device
    total_ok = total_fail = 0
    for vid in _require_ids(args):
        ok, fail = denoise_video_dir(vid, overwrite=args.overwrite)
        print(f"[denoise] {vid}: ok={ok}, fail={fail}")
        total_ok += ok
        total_fail += fail
    print(f"Denoise total: ok={total_ok}, fail={total_fail}")


def cmd_run(args):
    from extract_annots import extract_annotations
    from download import download_video
    from standardize import process_video
    from denoise import denoise_video_dir

    extract_annotations()
    if not config.SEPARATE_MODEL.exists():
        sys.exit(
            f"Required vocal separation model not found: {config.SEPARATE_MODEL}\n"
            f"Download it from: {config.SEPARATE_MODEL_URL}"
        )
    apply_download_config(args.proxy, args.aria2c, args.cookies_from_browser)
    if args.device:
        config.SEPARATE_DEVICE = args.device
    if args.width and args.height:
        config.TARGET_SIZE = (args.width, args.height)

    ids = _require_ids(args)
    failed_videos: list[str] = []
    for i, vid in enumerate(ids, 1):
        logger.info("=" * 60)
        logger.info("[%d/%d] Processing %s", i, len(ids), vid)
        if download_video(vid) is None:
            logger.error("Download failed, skip: %s", vid)
            failed_videos.append(vid)
            continue
        ok, fail = process_video(vid, workers=args.workers, overwrite=args.overwrite)
        logger.info("Standardize: ok=%d fail=%d", ok, fail)
        if ok == 0 or fail > 0:
            failed_videos.append(vid)
            continue
        dok, dfail = denoise_video_dir(vid, overwrite=args.overwrite)
        logger.info("Denoise: ok=%d fail=%d", dok, dfail)
        if dok == 0 or dfail > 0:
            failed_videos.append(vid)

    print("Pipeline finished. Output dirs:")
    print(f"  Raw videos: {config.RAW_DIR}")
    print(f"  Clips:      {config.CLIPS_DIR}")
    print(f"  Vocals:     {config.VOCALS_DIR}")
    if failed_videos:
        sys.exit(f"Pipeline failed for {len(failed_videos)} video(s): {', '.join(failed_videos)}")


def add_id_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "video_ids",
        nargs="*",
        help="YouTube video_id; IDs starting with - go after --, e.g. run -- --561dw9wOc",
    )
    p.add_argument(
        "--video-id",
        nargs="+",
        dest="video_id",
        metavar="ID",
        help="Equals form: --video-id=--561dw9wOc",
    )
    p.add_argument("--list-file", type=Path, help="One video_id per line")
    p.add_argument("--from-annots", action="store_true", help="Use all IDs from annotation dir")
    p.add_argument("--limit", type=int, default=0, help="Process at most N videos")


def add_download_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--proxy", default=None, help="HTTP proxy; empty string disables")
    p.add_argument("--aria2c", action="store_true", help="Enable aria2c (may 403)")
    p.add_argument("--cookies-from-browser", default=None, help="chrome/edge/firefox")


def main():
    setup_logging("pipeline")
    parser = argparse.ArgumentParser(
        description="VoxDub / av_segments data acquisition pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="See README.md for details.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ex = sub.add_parser("extract", help="Extract annotation archive")
    p_ex.add_argument("--force", action="store_true")
    p_ex.set_defaults(func=cmd_extract)

    p_dl = sub.add_parser("download", help="Download full videos")
    add_id_args(p_dl)
    add_download_args(p_dl)
    p_dl.set_defaults(func=cmd_download)

    p_st = sub.add_parser("standardize", help="Cut and standardize segments")
    add_id_args(p_st)
    p_st.add_argument("--workers", type=int, default=config.PROCESS_WORKERS)
    p_st.add_argument("--overwrite", action="store_true")
    p_st.add_argument("--width", type=int, default=0)
    p_st.add_argument("--height", type=int, default=0)
    p_st.set_defaults(func=cmd_standardize)

    p_dn = sub.add_parser("denoise", help="Required vocal separation / background removal")
    add_id_args(p_dn)
    p_dn.add_argument("--device", choices=("cuda", "cpu"), default=None)
    p_dn.add_argument("--overwrite", action="store_true")
    p_dn.set_defaults(func=cmd_denoise)

    p_run = sub.add_parser("run", help="Run full pipeline")
    add_id_args(p_run)
    add_download_args(p_run)
    p_run.add_argument("--workers", type=int, default=config.PROCESS_WORKERS)
    p_run.add_argument("--overwrite", action="store_true")
    p_run.add_argument("--device", choices=("cuda", "cpu"), default=None)
    p_run.add_argument("--width", type=int, default=0)
    p_run.add_argument("--height", type=int, default=0)
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
