"""Default pipeline configuration. Override via CLI when needed."""
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent

# Annotations downloaded with:
# hf download zyk21/VoxDub av_segments_v1.tar.zst --type dataset --local-dir annotations
ANNOT_ARCHIVE = ROOT / "annotations" / "av_segments_v1.tar.zst"
ANNOT_DIR = ROOT / "annotations" / "av_segments_v1" / "datas"

# Working directories
RAW_DIR = ROOT / "data" / "raw"          # {video_id}_full.mp4
CLIPS_DIR = ROOT / "data" / "clips"      # {video_id}/{seg_id}.mp4|.wav
VOCALS_DIR = ROOT / "data" / "vocals"    # {video_id}/{seg_id}.wav (vocals)
LOG_DIR = ROOT / "logs"

# Standardization targets (aligned with annotation faces.n_frames ~ 25 fps)
TARGET_FPS = 25
TARGET_SR = 24000
TARGET_CHANNELS = 1
# None -> use origin_width/origin_height from each JSON; or set e.g. (1280, 720)
TARGET_SIZE = None
DOWNLOAD_MAX_HEIGHT = 1280

# UVR vocal separation
SEPARATE_MODEL = SCRIPTS_DIR / "separate" / "UVR-MDX-NET-Inst_HQ_3.onnx"
SEPARATE_MODEL_URL = (
    "https://github.com/TRvlvr/model_repo/releases/download/"
    "all_public_uvr_models/UVR-MDX-NET-Inst_HQ_3.onnx"
)
SEPARATE_DEVICE = "cuda"  # "cuda" | "cpu"
SAMPLE_RATE_SEPARATE = 44100

# Download
PROXY = None  # e.g. "http://127.0.0.1:7890"
DOWNLOAD_RETRIES = 3
DOWNLOAD_SLEEP = (2, 6)
# aria2c often returns 403 on YouTube signed URLs; keep disabled by default
USE_ARIA2C = False
# e.g. "chrome" / "edge" / "firefox" for age-restricted videos; None to disable
COOKIES_FROM_BROWSER = None
# Avoid android_sdkless clients that trigger 403 (yt-dlp#15723)
YOUTUBE_PLAYER_CLIENTS = ["default", "-android_sdkless"]

PROCESS_WORKERS = 2
