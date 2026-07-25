# VoxDub

One-command scripts for reconstructing and processing
[VoxDub](https://huggingface.co/datasets/zyk21/VoxDub) from its annotations.
The pipeline retrieves source YouTube videos, cuts and standardizes clips, and
produces vocal-separated audio.

See [DATASET_CARD.md](./DATASET_CARD.md) for the annotation schema, dataset
scope, and limitations.

## Installation

Clone this repository, enter its root directory, and install dependencies:

```bash
pip install -r requirements.txt
pip install -U "huggingface_hub[cli]"
```

Install [FFmpeg](https://ffmpeg.org/) and [Deno](https://deno.land/), and make
sure both are available on `PATH`.

## Vocal separation model

Download
[UVR-MDX-NET-Inst_HQ_3.onnx](https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Inst_HQ_3.onnx)
and place it at:

```text
scripts/separate/UVR-MDX-NET-Inst_HQ_3.onnx
```



## 1. Download annotations

```bash
hf download zyk21/VoxDub av_segments_v1.tar.zst \
  --type dataset \
  --local-dir annotations
```

This matches the default relative paths in `scripts/config.py`. Edit those
settings only if you store the archive elsewhere.

## 2. Extract annotations

```bash
python scripts/pipeline.py extract
```

The archive contains:

```text
datas/{youtube_video_id}/{segment_id}.json
```

Each directory name is the YouTube video ID used to retrieve the source media.

## 3. Select videos

Process IDs directly from the annotation directories:

```bash
python scripts/pipeline.py run --from-annots --limit 10
```

Alternatively, generate `ids.txt`:

```bash
python -c "import sys; sys.path.insert(0,'scripts'); from extract_annots import list_video_ids; open('ids.txt','w',encoding='utf-8').write('\n'.join(list_video_ids())+'\n')"
```

Edit `ids.txt` to select videos. The file contains one YouTube ID per line:

```text
--561dw9wOc
--7_NaHSXaQ
```



## 4. Run the full pipeline

Process one video:

```bash
# IDs starting with '-' must appear after '--'
python scripts/pipeline.py run -- --561dw9wOc
```

Process a list:

```bash
python scripts/pipeline.py run --list-file ids.txt --limit 10
```

The `run` command performs all required stages:

1. Download the source YouTube video.
2. Cut segments using annotation timestamps.
3. Standardize video to 25 fps and the annotated resolution.
4. Export 24 kHz mono audio.
5. Separate vocals with UVR-MDX.



## Run individual stages

```bash
python scripts/pipeline.py download --list-file ids.txt
python scripts/pipeline.py standardize --list-file ids.txt
python scripts/pipeline.py denoise --list-file ids.txt
```

Outputs:

```text
data/raw/{video_id}_full.mp4
data/clips/{video_id}/{segment_id}.mp4
data/clips/{video_id}/{segment_id}.wav
data/vocals/{video_id}/{segment_id}.wav
```



## Configuration

Main options are defined in `scripts/config.py`:

- annotation archive and extraction paths
- output directories
- YouTube proxy
- target frame rate and sample rate
- CPU / CUDA vocal separation
