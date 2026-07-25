"""Remove background audio with UVR-MDX; keep vocals."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from tqdm import tqdm

import config
from separate.separate_fast import Predictor

logger = logging.getLogger(__name__)

_predictor: Predictor | None = None


def get_predictor(
    model_path: Path = config.SEPARATE_MODEL,
    device: str | None = None,
) -> Predictor:
    global _predictor
    if _predictor is not None:
        return _predictor

    if device is None:
        device = config.SEPARATE_DEVICE
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA unavailable, falling back to CPU")
            device = "cpu"

    if not model_path.exists():
        raise FileNotFoundError(
            f"UVR model not found: {model_path}\n"
            f"Download it from: {config.SEPARATE_MODEL_URL}\n"
            "Then place it at scripts/separate/UVR-MDX-NET-Inst_HQ_3.onnx"
        )

    logger.info("Loading UVR model: %s (%s)", model_path, device)
    _predictor = Predictor(
        args={
            "model_path": str(model_path),
            "denoise": True,
            "margin": 44100,
            "chunks": 15,
            "n_fft": 6144,
            "dim_t": 8,
            "dim_f": 3072,
        },
        device=device,
    )
    return _predictor


def separate_vocals(
    audio: np.ndarray,
    sr: int = config.TARGET_SR,
    predictor: Predictor | None = None,
) -> np.ndarray:
    """
    Mono waveform at `sr` -> vocals at the same `sr`.
    UVR-MDX-NET-Inst_HQ_3 predicts instrumental; vocals = mix - instrumental.
    """
    predictor = predictor or get_predictor()
    work_sr = config.SAMPLE_RATE_SEPARATE

    if audio.ndim > 1:
        audio = np.mean(audio, axis=-1)

    mix = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=work_sr)
    vocals, _instrumental = predictor.predict(mix)
    vocals = np.asarray(vocals)
    if vocals.ndim == 2:
        vocals = vocals[:, 0] if vocals.shape[1] <= 2 else vocals[0]

    vocals = librosa.resample(vocals.astype(np.float32), orig_sr=work_sr, target_sr=sr)
    n = len(audio)
    if len(vocals) >= n:
        vocals = vocals[:n]
    else:
        vocals = np.pad(vocals, (0, n - len(vocals)))
    return vocals


def denoise_wav(
    in_wav: Path,
    out_wav: Path,
    sr: int = config.TARGET_SR,
    overwrite: bool = False,
) -> bool:
    if out_wav.exists() and not overwrite:
        return True
    try:
        audio, file_sr = sf.read(str(in_wav), dtype="float32", always_2d=False)
        if file_sr != sr:
            audio = librosa.resample(
                np.asarray(audio, dtype=np.float32), orig_sr=file_sr, target_sr=sr
            )
        vocals = separate_vocals(np.asarray(audio, dtype=np.float32), sr=sr)
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(out_wav), vocals, sr)
        return True
    except Exception as e:
        logger.error("Vocal separation failed %s: %s", in_wav, e)
        return False


def denoise_video_dir(
    video_id: str,
    clips_dir: Path = config.CLIPS_DIR,
    vocals_dir: Path = config.VOCALS_DIR,
    overwrite: bool = False,
) -> tuple[int, int]:
    src = clips_dir / video_id
    dst = vocals_dir / video_id
    wavs = sorted(src.glob("*.wav"))
    wavs = [w for w in wavs if not w.stem.endswith("_vocals")]
    if not wavs:
        logger.warning("No wav files: %s", src)
        return 0, 0

    get_predictor()
    ok = fail = 0
    for w in tqdm(wavs, desc=f"denoise {video_id}"):
        if denoise_wav(w, dst / w.name, overwrite=overwrite):
            ok += 1
        else:
            fail += 1
    return ok, fail


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    parser = argparse.ArgumentParser(description="Separate vocals from standardized wav files")
    parser.add_argument("video_ids", nargs="+")
    parser.add_argument("--device", choices=("cuda", "cpu"), default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.device:
        config.SEPARATE_DEVICE = args.device

    total_ok = total_fail = 0
    for vid in args.video_ids:
        ok, fail = denoise_video_dir(vid, overwrite=args.overwrite)
        total_ok += ok
        total_fail += fail
        print(f"{vid}: ok={ok}, fail={fail}")
    print(f"Total: ok={total_ok}, fail={total_fail}")


if __name__ == "__main__":
    main()
