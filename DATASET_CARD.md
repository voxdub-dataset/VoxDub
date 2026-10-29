# VoxDub Dataset Card

[Paper](https://arxiv.org/abs/2610.25259) · [Project Page](https://voxdub-dataset.github.io/VoxDub/) · [Download](https://huggingface.co/datasets/zyk21/VoxDub) · [Setup and Usage](./README.md#2-quick-start)

## 1. Dataset Summary

VoxDub is an English and Mandarin Chinese audio-visual dataset for automatic video dubbing, with evaluations on text-to-speech and automatic video dubbing. It contains approximately **766,708 segments** from **17,433 YouTube video IDs**, totaling **1.58K hours**.

The VoxDub release provides **segment annotations** in `av_segments_v1.tar.zst`. Source video and audio files are retrieved separately using the reconstruction tools.

The curation pipeline combines speech segmentation, dual-ASR transcription checking, speech quality filtering, face visibility checks, and lip-speech synchronization verification.

## 2. Annotation Format

Each JSON file represents one segment. The archive layout is:

```text
datas/{video_id}/{segment_id}.json
```

After extraction with the provided tools:

```text
annotations/av_segments_v1/datas/{video_id}/{segment_id}.json
```

`video_id` is the source YouTube video ID. Matching `video_id` and `segment_id` values connect annotations with reconstructed media.

### 2.1 Segment and Transcript Fields

- **`start`, `end`**: start and end times in seconds relative to the source video. The extraction interval is `[start, end)`; duration is `end - start`.
- **`text_whisper`**: transcript produced by Whisper.
- **`text_paraformer`**: transcript produced by Paraformer.
- **`language`**: language metadata.
- **`wer`**: word error rate metadata used for transcription consistency checking.
- **`dnsmos`**: speech quality score.

### 2.2 Video and Synchronization Fields

- **`origin_width`, `origin_height`**: source video width and height.
- **`av_offset`**: audio-visual synchronization offset metadata.
- **`sync_conf`**: synchronization confidence metadata.
- **`faces`**: face-track metadata, including `n_frames`, `score`, `bbox`, and `landmarks` for frame counts, scores, bounding boxes, and facial landmarks.

The reconstruction tools cut segments using `start` and `end`, and use source dimensions unless overridden. They do not currently apply `av_offset` or crop videos using face tracks. They also do not rerun the dataset curation stages.

See the [README](./README.md#2-quick-start) for reconstruction instructions. Default outputs are 25 fps video, 24 kHz mono audio, and vocal-separated audio.

## 3. Limitations

- Source videos may become unavailable, private, or region-restricted, affecting reconstruction coverage.
- Automatically generated transcripts, quality scores, and face tracks may contain errors.
- Users must comply with applicable privacy, copyright, and platform policies.
