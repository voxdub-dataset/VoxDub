# VoxDub

**A bilingual lip-synchronized audio-visual dataset for automatic video dubbing.**

[Project Page](https://voxdub-dataset.github.io/VoxDub/) · [Dataset on Hugging Face](https://huggingface.co/datasets/zyk21/VoxDub) · [Dataset Card](./DATASET_CARD.md) · [Quick Start](#quick-start) · [Issues](https://github.com/voxdub-dataset/VoxDub/issues)

VoxDub contains approximately **766K clips** and **1.58K hours** of Chinese and English audio-visual recordings collected from in-the-wild videos. It is designed for automatic video dubbing (AVD), with downstream evaluations on both text-to-speech (TTS) and AVD.

This repository provides tools to reconstruct clips from the released segment annotations: retrieve source YouTube videos, extract and standardize segments, and generate vocal-separated audio. The public data release contains **annotations**; source video and audio files are retrieved separately.

## Contents

- [Overview](#overview)
- [Dataset Access](#dataset-access)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Data Format and Outputs](#data-format-and-outputs)
- [Configuration](#configuration)
- [Acknowledgments](#acknowledgments)
- [License](#license)

## Overview

### Dataset at a glance

| Property | Description |
|---|---|
| Languages | Chinese and English |
| Corpus size | Approximately 766K clips / 1.58K hours |
| Source videos | Approximately 17,433 YouTube video IDs |
| Content | Varied speakers, scenes, speaking styles, and linguistic content |
| Released data | Segment annotations in JSON format |
| Reconstruction outputs | Standardized video clips, extracted audio, and vocal-separated audio |
| Default video format | 25 fps; target dimensions from each annotation |
| Default audio format | 24 kHz, mono |

The corpus statistics describe VoxDub; the number of clips that can be reconstructed depends on the continued availability of source videos.

### Curation and reconstruction

VoxDub's dataset curation combines speech-centered segmentation with dual-ASR transcription checking, speech quality filtering, face visibility checks, and lip-speech synchronization verification.

The scripts in this repository reconstruct the selected segments using the released annotations:

```text
Released annotations
        ↓
Download source videos
        ↓
Extract segments and standardize video/audio
        ↓
Separate vocals
```

The reconstruction scripts consume existing annotations; they do not rerun the ASR, face-detection, or synchronization-scoring stages. See the [dataset card](./DATASET_CARD.md) for annotation details and dataset scope.

## Dataset Access

| Resource | Location |
|---|---|
| Annotation repository | [zyk21/VoxDub on Hugging Face](https://huggingface.co/datasets/zyk21/VoxDub) |
| Annotation archive | `av_segments_v1.tar.zst` |
| Archive layout | `datas/{video_id}/{segment_id}.json` |
| Dataset documentation | [DATASET_CARD.md](./DATASET_CARD.md) |

Each `video_id` identifies a source YouTube video. The JSON files describe the segments to reconstruct from that video.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/voxdub-dataset/VoxDub.git
cd VoxDub
```

Run the following commands from the repository root, preferably in a dedicated Python environment.

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -U huggingface_hub
```

Install [FFmpeg](https://ffmpeg.org/download.html) and [Deno](https://deno.land/), and ensure they are available on your `PATH`:

```bash
ffmpeg -version
deno --version
hf --help
```

Vocal separation supports CPU and CUDA. The configuration defaults to CUDA; use `--device cpu` to select CPU processing explicitly.

### 3. Download the vocal separation model

Download [UVR-MDX-NET-Inst_HQ_3.onnx](https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Inst_HQ_3.onnx) and save it at:

```text
scripts/separate/UVR-MDX-NET-Inst_HQ_3.onnx
```

The model is required for `run` and `denoise`.

## Quick Start

After installation, download the annotations, extract them, and reconstruct a small subset:

```bash
hf download zyk21/VoxDub av_segments_v1.tar.zst --repo-type dataset --local-dir annotations
python scripts/pipeline.py extract
python scripts/pipeline.py run --from-annots --limit 10 --device cpu
```

For a configured CUDA environment, replace `--device cpu` with `--device cuda`.

`--limit 10` selects up to **10 source videos**, processing their annotated segments. It does not limit the output to 10 clips.

The `run` command checks/extracts annotations as needed, downloads source videos, creates standardized clips and audio, and separates vocals. Results are written to `data/raw/`, `data/clips/`, and `data/vocals/`; logs are written to `logs/`.

## Usage

### Process selected videos

Create `ids.txt` with one YouTube video ID per line. See [ids.example.txt](./ids.example.txt) for an example. Then run:

```bash
python scripts/pipeline.py run --list-file ids.txt --limit 10 --device cpu
```

To process a single video whose ID starts with a hyphen, place the ID after `--`:

```bash
python scripts/pipeline.py run --device cpu -- --561dw9wOc
```

### Generate a video list from the annotations

After extracting the archive, run:

```bash
python -c "import sys; sys.path.insert(0,'scripts'); from extract_annots import list_video_ids; open('ids.txt','w',encoding='utf-8').write('\n'.join(list_video_ids())+'\n')"
```

Edit the generated file to select the source videos you want to process.

### Run stages separately

Run these stages in order after extracting annotations and preparing `ids.txt`:

```bash
python scripts/pipeline.py download --list-file ids.txt
python scripts/pipeline.py standardize --list-file ids.txt
python scripts/pipeline.py denoise --list-file ids.txt --device cpu
```

| Command | Purpose |
|---|---|
| `extract` | Unpack the annotation archive |
| `download` | Retrieve full source videos |
| `standardize` | Cut annotated intervals, standardize video, and export audio |
| `denoise` | Separate vocals from the exported audio |
| `run` | Execute the reconstruction workflow |

### Reprocess outputs

Existing outputs are generally skipped. To regenerate clip and vocal outputs, add `--overwrite` to `run`, `standardize`, or `denoise`:

```bash
python scripts/pipeline.py run --list-file ids.txt --limit 10 --device cpu --overwrite
```

`--overwrite` does not redownload existing source videos or force annotation extraction. Use `extract --force` to repeat extraction.

For the options supported by each command:

```bash
python scripts/pipeline.py --help
python scripts/pipeline.py run --help
```

## Data Format and Outputs

### Annotations

With the default configuration, annotations are extracted to:

```text
annotations/av_segments_v1/datas/{video_id}/{segment_id}.json
```

The annotation schema includes:

| Information | Fields |
|---|---|
| Segment boundaries | `start`, `end` |
| ASR transcripts | `text_whisper`, `text_paraformer` |
| Language and quality metadata | `language`, `wer`, `dnsmos` |
| Source dimensions | `origin_width`, `origin_height` |
| Audio-visual synchronization metadata | `av_offset`, `sync_conf` |
| Face tracks | `faces.n_frames`, `faces.score`, `faces.bbox`, `faces.landmarks` |

See [DATASET_CARD.md](./DATASET_CARD.md) for the dataset description. The current standardization script uses `start`, `end`, and source dimensions; it does not apply `av_offset` or crop videos using face tracks.

### Generated files

```text
data/
├── raw/
│   └── {video_id}_full.mp4
├── clips/
│   └── {video_id}/
│       ├── {segment_id}.mp4
│       └── {segment_id}.wav
└── vocals/
    └── {video_id}/
        └── {segment_id}.wav

logs/
└── pipeline.log
```

- `raw/`: source videos; the downloader also recognizes `.mkv` and `.webm` files.
- `clips/*.mp4`: standardized **video-only** clips.
- `clips/*.wav`: audio extracted from the corresponding source intervals, before vocal separation.
- `vocals/*.wav`: vocal-separated audio at the target sample rate.

Matching `video_id` and `segment_id` values connect annotations, video clips, and audio files.

## Configuration

Defaults are defined in [scripts/config.py](./scripts/config.py).

| Setting | Default | Purpose |
|---|---|---|
| `ANNOT_ARCHIVE` | `annotations/av_segments_v1.tar.zst` | Annotation archive |
| `ANNOT_DIR` | `annotations/av_segments_v1/datas` | Extracted annotations |
| `RAW_DIR`, `CLIPS_DIR`, `VOCALS_DIR` | Subdirectories of `data/` | Media outputs |
| `TARGET_FPS` | `25` | Output frame rate |
| `TARGET_SR` / `TARGET_CHANNELS` | `24000` / `1` | Output audio format |
| `TARGET_SIZE` | `None` | Use annotated dimensions unless overridden |
| `SEPARATE_MODEL` | `scripts/separate/UVR-MDX-NET-Inst_HQ_3.onnx` | Separation model |
| `SEPARATE_DEVICE` | `cuda` | Separation device |
| `PROXY` | `None` | Optional download proxy |
| `PROCESS_WORKERS` | `2` | Segment standardization workers |

Common command-line overrides include `--device`, `--workers`, `--proxy`, and the paired `--width` / `--height` options. Check the relevant subcommand's `--help` before use.

## Acknowledgments

The reconstruction workflow uses [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/), and the [UVR model repository](https://github.com/TRvlvr/model_repo). Annotation files are hosted on [Hugging Face](https://huggingface.co/datasets/zyk21/VoxDub).

## License

- **Repository code:** [MIT License](./LICENSE).
- **Dataset annotations:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), as specified in the [dataset card](./DATASET_CARD.md#license-and-ownership).
- **Source media:** rights remain with the original rights holders; the annotation release does not grant rights to the source videos or audio. See the dataset card for details.
