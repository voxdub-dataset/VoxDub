---

# VoxDub

VoxDub contains segment-level audiovisual annotations for public YouTube
videos. Source video and audio files are not redistributed.

## Dataset


| Item     | Value                                |
| -------- | ------------------------------------ |
| Videos   | ~17,433 YouTube IDs                  |
| Segments | ~766,708                             |
| Archive  | `av_segments_v1.tar.zst`             |
| Layout   | `datas/{video_id}/{segment_id}.json` |


Each JSON file contains timestamps, transcripts, language and quality metadata,
source resolution, AV synchronization data, and per-frame face tracks.

Important fields:

- `start`, `end`
- `text_whisper`, `text_paraformer`
- `language`, `wer`, `dnsmos`
- `origin_width`, `origin_height`
- `av_offset`, `sync_conf`
- `faces.n_frames`, `faces.score`, `faces.bbox`, `faces.landmarks`

## Usage

```bash
hf download zyk21/VoxDub av_segments_v1.tar.zst --type dataset --local-dir annotations
python scripts/pipeline.py extract
python scripts/pipeline.py run --from-annots --limit 10
```

The companion pipeline produces 25 fps video, 24 kHz mono audio, and
vocal-separated tracks. See [README.md](./README.md) for complete setup and
model download instructions.

## Limitations

- Source videos may become unavailable, private, or region-restricted.
- Automatically generated transcripts and scores may contain errors.
- Users must comply with applicable privacy, copyright, and platform policies.

## License and ownership

Annotations are released under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

Source videos, audio, performances, trademarks, and related rights remain the
property of their original authors, uploaders, and rights holders. VoxDub does
not grant rights to source media. Its use remains subject to copyright law and
the [YouTube Terms of Service](https://www.youtube.com/static?template=terms).