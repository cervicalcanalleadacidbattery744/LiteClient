"""Shared paths / cache setup for the analysis scripts.

Import this module FIRST (before torch / huggingface / mlx imports) so that all
model downloads land in analysis/.cache/.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # analysis/
PROJECT = ROOT.parent
CACHE = ROOT / ".cache"
for var, sub in [("TORCH_HOME", "torch"), ("HF_HOME", "hf"), ("HF_HUB_CACHE", "hf/hub"),
                 ("XDG_CACHE_HOME", "xdg"), ("MPLCONFIGDIR", "mpl"), ("NUMBA_CACHE_DIR", "numba")]:
    os.environ.setdefault(var, str(CACHE / sub))
    (CACHE / sub).mkdir(parents=True, exist_ok=True)

# audio/evangelion.wav is ffmpeg's decode of the AAC track (priming samples trimmed by the
# mp4 edit list, as browsers do), so it is the time reference; the Demucs stems were
# separated from it and need no offset.
AUDIO = PROJECT / "audio" / "evangelion.wav"
STEMS = ROOT / "stems" / "htdemucs" / "evangelion"
DATA = PROJECT / "data"
QA = ROOT / "qa"
QA.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)


def load_mix(sr=44100):
    import soundfile as sf
    import soxr
    y, s = sf.read(AUDIO, dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    return (soxr.resample(y, s, sr) if s != sr else y), sr


def load_stem(name, sr=44100):
    import soundfile as sf
    import soxr
    y, s = sf.read(STEMS / f"{name}.wav", dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    return (soxr.resample(y, s, sr) if s != sr else y), sr
