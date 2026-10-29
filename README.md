# VoxDub

**A bilingual lip-synchronized audio-visual dataset for automatic video dubbing.**

[Paper](https://arxiv.org/abs/2610.25259) · [Project Page](https://voxdub-dataset.github.io/VoxDub/) · [Hugging Face](https://huggingface.co/datasets/zyk21/VoxDub)

VoxDub contains approximately **766K clips** and **1.58K hours** of English and Mandarin Chinese audio-visual recordings. We release segment annotations and tools to reconstruct clips from source YouTube videos.

## 1. Data and Annotations

The annotation archive, `av_segments_v1.tar.zst`, is available on [Hugging Face](https://huggingface.co/datasets/zyk21/VoxDub). Each JSON file describes one segment:

```text
datas/{video_id}/{segment_id}.json
```

`video_id` identifies the source YouTube video; `segment_id` identifies a segment within it. Annotations contain timestamps, ASR transcripts, language and quality metadata, source dimensions, synchronization metadata, and face tracks.

See the [annotation format](./DATASET_CARD.md#2-annotation-format) for field definitions. VoxDub source media is retrieved separately; reconstruction depends on source video availability.

## 2. Quick Start

### 2.1 Installation

```bash
git clone https://github.com/voxdub-dataset/VoxDub.git
cd VoxDub
python -m pip install -r requirements.txt
python -m pip install -U huggingface_hub
```

Install [FFmpeg](https://ffmpeg.org/download.html) and [Deno](https://deno.land/) on your `PATH`. Download [UVR-MDX-NET-Inst_HQ_3.onnx](https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/UVR-MDX-NET-Inst_HQ_3.onnx) to `scripts/separate/UVR-MDX-NET-Inst_HQ_3.onnx` for vocal separation.

### 2.2 Download and Reconstruct

Run from the repository root:

```bash
hf download zyk21/VoxDub av_segments_v1.tar.zst --repo-type dataset --local-dir annotations
python scripts/pipeline.py extract
python scripts/pipeline.py run --from-annots --limit 10 --device cpu
```

`--limit 10` selects up to **10 source videos**, including their annotated segments. Use `--device cuda` for CUDA processing, or `--list-file ids.txt` to select videos by ID (see [example](./ids.example.txt)).

### 2.3 Outputs

```text
data/
├── raw/{video_id}_full.mp4
├── clips/{video_id}/{segment_id}.mp4
├── clips/{video_id}/{segment_id}.wav
└── vocals/{video_id}/{segment_id}.wav
```

`raw/` stores source videos, `clips/` stores video-only clips and extracted audio, and `vocals/` stores vocal-separated audio. Defaults are **25 fps video** and **24 kHz mono audio**.

## 3. DubBench

We also release the DubBench test set used in our paper. It contains English and Mandarin Chinese subsets, with each sample pairing a target utterance with a reference utterance.

In our experiments, all systems use reference audio, reference text, and target text as inputs. AVD additionally uses the target video. Generated audio is evaluated against the ground-truth target audio.

The English subset is derived from [CelebV-Dub](https://voicecraft-dub.github.io/), and the Chinese subset from [CMLR](https://www.vipazoo.cn/CMLR.html).

Download both subsets:

```bash
hf download zyk21/VoxDub --repo-type dataset --include "dubbench/**" --local-dir VoxDub
```

The downloaded `dubbench/` directory contains two language directories: `english/` and `chinese/`. Each contains two TAR archives, `reference.tar` and `target.tar`, holding the reference and target data, respectively, along with `metadata.tsv`.

For detailed information, please refer to the [website](https://huggingface.co/datasets/zyk21/VoxDub#dubbench).

## 4. Acknowledgments

The tools use [yt-dlp](https://github.com/yt-dlp/yt-dlp), [FFmpeg](https://ffmpeg.org/), and the [UVR model repository](https://github.com/TRvlvr/model_repo).

## 5. License

- **Code:** [MIT License](./LICENSE).
- **VoxDub annotations:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- **Source media and DubBench:** Rights remain with the original rights holders; users must follow the original source dataset terms.
