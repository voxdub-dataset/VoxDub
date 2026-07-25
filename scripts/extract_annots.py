"""Extract annotation archive or validate an existing annotation tree."""
from __future__ import annotations

import argparse
import logging
import tarfile
from pathlib import Path

import zstandard as zstd

import config

logger = logging.getLogger(__name__)


def extract_annotations(
    archive: Path = config.ANNOT_ARCHIVE,
    out_dir: Path = config.ANNOT_DIR.parent,
    force: bool = False,
) -> Path:
    """
    Unpack archive into out_dir.
    Archive layout: datas/{video_id}/{seg_id}.json -> out_dir/datas/...
    Skips if ANNOT_DIR already exists and is non-empty.
    """
    datas = out_dir / "datas"
    if datas.exists() and any(datas.iterdir()) and not force:
        logger.info("Annotation dir exists, skip extract: %s", datas)
        return datas

    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Extracting %s -> %s (large archive, may take a while)", archive, out_dir)

    dctx = zstd.ZstdDecompressor()
    with open(archive, "rb") as f, dctx.stream_reader(f) as reader:
        with tarfile.open(fileobj=reader, mode="r|") as tar:
            try:
                tar.extractall(path=out_dir, filter="data")
            except TypeError:
                tar.extractall(path=out_dir)

    logger.info("Extract done: %s", datas)
    return datas


def list_video_ids(annot_dir: Path = config.ANNOT_DIR) -> list[str]:
    if not annot_dir.exists():
        raise FileNotFoundError(f"Annotation dir not found: {annot_dir}")
    return sorted(p.name for p in annot_dir.iterdir() if p.is_dir())


def list_segments(video_id: str, annot_dir: Path = config.ANNOT_DIR) -> list[Path]:
    return sorted((annot_dir / video_id).glob("*.json"))


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Extract av_segments annotation archive")
    parser.add_argument("--archive", type=Path, default=config.ANNOT_ARCHIVE)
    parser.add_argument("--out-dir", type=Path, default=config.ANNOT_DIR.parent)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    path = extract_annotations(args.archive, args.out_dir, args.force)
    vids = list_video_ids(path)
    print(f"Annotation dir: {path}")
    print(f"Videos: {len(vids)}")


if __name__ == "__main__":
    main()
