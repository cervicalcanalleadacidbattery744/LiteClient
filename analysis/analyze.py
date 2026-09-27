"""Music analysis -> data/audio.json + data/spectrum.bin

  * constant-tempo beat grid (tempo + phase fitted to drum / mix onsets, phase
    refined on kick attacks), downbeats on the 8-bar phrase grid, sections on
    downbeats (SECTION_BARS, set by hand from the per-bar table: --bars),
  * 100 fps normalized envelopes (mix rms / low / mid / high, stem rms),
  * kick / clap / hat onsets from the drums stem, vocal-chop onsets,
  * bass pitch (MIDI, 100 fps) from the bass stem,
  * a 100 fps log-mel spectrogram of the mix (64 bands) and chroma of the
    harmonic stem (12 bins), uint8, in data/spectrum.bin.

Run:  uv run python analyze.py [--bars]
"""
import common
import json
import math
import sys

import numpy as np
import librosa
from scipy.ndimage import median_filter, uniform_filter1d
from scipy.signal import butter, find_peaks, sosfiltfilt

SR = 44100
FPS = 100
MEL_BANDS = 64
MEL_FMIN, MEL_FMAX = 30.0, 16000.0
WAVE_SR = 11025

# Section map in bars (bar k starts at downbeat k; bar 0 = first downbeat).
# From the per-bar stem table (--bars): 8-bar phrases throughout.
SECTION_BARS = [
    ("intro", None, 2),      # pads only
    ("groove1", 2, 12),      # drums + bass in
    ("breaka", 12, 13),      # one-bar pad swell, drums out
    ("groove2", 13, 24),     # groove again (bar 23: pad swell fill)
    ("break1", 24, 29),      # bass + pads, no drums
    ("build1", 29, 35),      # drums back, vocal chops bars 31-33, bar 34 fill
    ("drop1", 35, 45),       # full drop
    ("drop1b", 45, 54),      # drop variation (bar 45 peak highs)
    ("break2", 54, 56),      # pads only
    ("drop2", 56, 65),       # drums + bass, no pads
    ("breakdown", 65, 72),   # pads only, vocal bar 71
    ("build2", 72, 78),      # vocal chops bars 74-75, bar 76 dropout, bar 77 roll
    ("drop3", 78, 87),       # final drop
    ("drop3b", 87, 96),
    ("outro", 96, None),     # pads to silence
]


# ---------------------------------------------------------------------------
def band_sos(lo, hi, sr):
    if lo and hi:
        return butter(4, [lo, hi], btype="band", fs=sr, output="sos")
    if hi:
        return butter(4, hi, btype="low", fs=sr, output="sos")
    return butter(4, lo, btype="high", fs=sr, output="sos")


def frame_rms(x, sr, fps=FPS, win=2048):
    hop = sr / fps
    n = int(math.ceil(len(x) / sr * fps))
    pad = np.pad(x, (win // 2, win // 2 + int(hop) + 2))
    idx = (np.arange(n) * hop).astype(int)
    c = np.concatenate([[0.0], np.cumsum(pad.astype(np.float64) ** 2)])
    e = (c[idx + win] - c[idx]) / win
    return np.sqrt(np.maximum(e, 0))


def smooth_env(x, fps=FPS, attack=0.010, release=0.090):
    """One-pole follower: fast attack, slower release (visual friendly)."""
    aa = math.exp(-1 / (attack * fps))
    ar = math.exp(-1 / (release * fps))
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        a = aa if v > s else ar
        s = a * s + (1 - a) * v
        y[i] = s
    return y


def norm01(x, pct=99.0):
    ref = np.percentile(x, pct)
    return np.clip(x / (ref + 1e-12), 0, 1)


def band_onsets(x, sr, lo, hi, win=0.010, hop_s=0.002, min_gap=0.08, rel_db=10.0):
    """Onsets in a frequency band: steepest rise of the band's log-energy
    envelope; strength = peak dB.  Returns (times, peak_db)."""
    xb = sosfiltfilt(band_sos(lo, hi, sr), x)
    h = int(hop_s * sr)
    w = int(win * sr)
    e = np.convolve(xb.astype(np.float64) ** 2, np.ones(w) / w, mode="same")[::h]
    db = 10 * np.log10(e + 1e-10)
    fps = sr / h
    d = uniform_filter1d(np.diff(db, prepend=db[0]), 3)
    lag = int(0.02 * fps)
    rise = db - np.concatenate([np.full(lag, db[0]), db[:-lag]])
    floor = median_filter(db, int(1.0 * fps) | 1)
    pk, _ = find_peaks(rise, height=rel_db, distance=int(min_gap * fps))
    times, strength = [], []
    for p in pk:
        a = max(0, p - lag)
        q = a + int(np.argmax(d[a:p + 1]))
        peak_db = db[p:p + int(0.03 * fps)].max()
        if peak_db < floor[p] + 3:
            continue
        times.append(q / fps)
        strength.append(peak_db)
    return np.array(times), np.array(strength)


def fit_grid(drums, mix, sr, duration):
    """Constant-tempo grid: coarse tempo/phase search on spectral-flux onset
    envelopes, then phase refinement on kick attack times."""
    od = librosa.onset.onset_strength(y=librosa.resample(drums, orig_sr=sr, target_sr=22050), sr=22050, hop_length=32, lag=1, max_size=1)
    om = librosa.onset.onset_strength(y=librosa.resample(mix, orig_sr=sr, target_sr=22050), sr=22050, hop_length=32, lag=1, max_size=1)
    o = od / (np.percentile(od, 99) + 1e-9) + om / (np.percentile(om, 99) + 1e-9)
    ofps = 22050 / 32

    def score(P, off):
        ts = off + P * np.arange(int(duration / P) + 1)
        idx = np.round(ts * ofps).astype(int)
        idx = idx[(idx > 2) & (idx < len(o) - 2)]
        return np.maximum.reduce([o[idx - 1], o[idx], o[idx + 1]]).mean()

    best = (0, None, None)
    for bpm in np.arange(120.0, 134.0, 0.02):
        P = 60 / bpm
        for off in np.arange(0, P, 0.004):
            s = score(P, off)
            if s > best[0]:
                best = (s, bpm, off)
    _, bpm, off = best
    for b2 in np.arange(bpm - 0.02, bpm + 0.02, 0.001):
        P = 60 / b2
        for o2 in np.arange(off - 0.01, off + 0.01, 0.001):
            s = score(P, o2)
            if s > best[0]:
                best = (s, b2, o2)
    _, bpm, off = best
    P = 60 / bpm
    kick_t, _ = band_onsets(drums, sr, None, 120, win=0.012, min_gap=0.2, rel_db=12)
    n = np.round((kick_t - off) / P)
    res = kick_t - (off + n * P)
    res = res[np.abs(res) < 0.06]
    off = off + float(np.median(res))
    off = off - P * math.floor(off / P)
    return bpm, P, off, res


def drum_onsets(d, sr):
    """Kick / clap / hat onsets from the drums stem."""
    kt, kdb = band_onsets(d, sr, None, 120, win=0.012, min_gap=0.15, rel_db=12)
    # CLAP / SNARE: 1.5-5 kHz attacks with a long noisy 0.5-5 kHz tail (40-120 ms);
    # kicks and hats have tails 12-30 dB lower.
    st, _ = band_onsets(d, sr, 1500, 5000, win=0.010, min_gap=0.1, rel_db=10)
    xb = sosfiltfilt(band_sos(500, 5000, sr), d)
    e = np.sqrt(np.convolve(xb.astype(np.float64) ** 2, np.ones(441) / 441, mode="same"))
    tail = np.array([20 * np.log10(e[int((t + 0.04) * sr):int((t + 0.12) * sr)].mean() + 1e-9) for t in st])
    rel = np.array([tail[i] - tail[np.abs(st - st[i]) < 2.5].max() for i in range(len(st))])
    thr = np.percentile(tail, 95) - 25
    keep = (rel > -8) & (tail > thr)
    st, stail = st[keep], tail[keep]
    ht, hdb = band_onsets(d, sr, 7000, None, win=0.006, min_gap=0.06, rel_db=9)
    for other, gap in ((st, 0.04), (kt, 0.03)):
        if len(other) and len(ht):
            dist = np.min(np.abs(ht[:, None] - other[None, :]), axis=1)
            keep = dist > gap
            ht, hdb = ht[keep], hdb[keep]
    return (kt, kdb), (st, stail), (ht, hdb)


def strength01(db_vals, lo_pct=5, hi_pct=95):
    if len(db_vals) == 0:
        return db_vals
    lo, hi = np.percentile(db_vals, lo_pct), np.percentile(db_vals, hi_pct)
    return np.clip((db_vals - lo) / (hi - lo + 1e-9) * 0.8 + 0.2, 0, 1)


def vocal_onsets(v, sr):
    """Vocal-chop onsets: log-mel flux peaks on the vocal stem while it is active."""
    y = librosa.resample(v, orig_sr=sr, target_sr=22050)
    hop = 110  # ~5 ms
    fl = librosa.onset.onset_strength(y=y, sr=22050, hop_length=hop, n_mels=64, fmax=8000)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0]
    rdb = 20 * np.log10(rms + 1e-9)
    ref = np.percentile(rdb, 99)
    active = rdb > ref - 30
    fps = 22050 / hop
    thr = uniform_filter1d(fl, int(0.4 * fps)) * 1.5 + 0.15 * np.percentile(fl, 99)
    pk, _ = find_peaks(fl, distance=int(0.09 * fps))
    out = []
    for p in pk:
        q = min(len(active) - 1, p + int(0.03 * fps))
        if fl[p] > thr[p] and active[q]:
            out.append((p / fps, fl[p]))
    if not out:
        return []
    s95 = np.percentile([s for _, s in out], 95)
    return [(round(float(t), 3), round(float(min(1.0, max(0.1, s / s95))), 3)) for t, s in out]


def bass_pitch(b, sr, n):
    """Bass-stem f0 as MIDI at FPS (0 where unvoiced or quiet)."""
    y = librosa.resample(b, orig_sr=sr, target_sr=11025)
    hop = 128
    f0, voiced, _ = librosa.pyin(y, fmin=30, fmax=300, sr=11025, frame_length=1024, hop_length=hop)
    rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0][: len(f0)]
    rdb = 20 * np.log10(rms + 1e-9)
    ok = voiced & (rdb > np.percentile(rdb, 99) - 30)
    midi = np.where(ok, librosa.hz_to_midi(np.nan_to_num(f0, nan=1.0)), 0.0)
    midi = median_filter(midi, 5)
    t_src = np.arange(len(midi)) * hop / 11025
    t_dst = np.arange(n) / FPS
    idx = np.clip(np.searchsorted(t_src, t_dst), 0, len(midi) - 1)
    return midi[idx]


def spectra(mix, harm, sr, n):
    """uint8 log-mel spectrogram of the mix (MEL_BANDS x n) and chroma of the harmonic stem (12 x n)."""
    hop = sr // FPS  # 441
    M = librosa.feature.melspectrogram(y=mix, sr=sr, n_fft=4096, hop_length=hop, n_mels=MEL_BANDS,
                                       fmin=MEL_FMIN, fmax=MEL_FMAX, power=2.0)
    db = librosa.power_to_db(M, ref=np.max)          # 0 = loudest bin of the song
    # per-band normalization (a flat response for visuals): 0 = the band's quiet floor (2nd
    # percentile, at least -80 dB), 1 = its 99.5th percentile; dB-linear in between
    lo = np.maximum(np.percentile(db, 2, axis=1, keepdims=True), -80.0)
    hi = np.percentile(db, 99.5, axis=1, keepdims=True)
    mel = np.clip((db - lo) / (hi - lo + 1e-6), 0, 1)
    C = librosa.feature.chroma_stft(y=harm, sr=sr, n_fft=8192, hop_length=hop)
    C = uniform_filter1d(C, 9, axis=1)
    fix = lambda a: np.pad(a, ((0, 0), (0, max(0, n - a.shape[1]))))[:, :n]
    return (fix(mel) * 255 + 0.5).astype(np.uint8), (fix(C) * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------------------
def main(bars_table=False):
    mix, _ = common.load_mix(SR)
    duration = len(mix) / SR
    stems = {k: common.load_stem(k, SR)[0][: len(mix)] for k in ("vocals", "drums", "bass", "other")}
    for k in stems:
        if len(stems[k]) < len(mix):
            stems[k] = np.pad(stems[k], (0, len(mix) - len(stems[k])))

    bpm, P, off, kick_res = fit_grid(stems["drums"], mix, SR, duration)
    print(f"tempo {bpm:.3f} BPM  period {P:.5f}s  first beat {off:.4f}s  kick residual sd {kick_res.std()*1000:.1f} ms")
    beats = off + P * np.arange(int((duration - off) / P) + 1)

    # bar phase: the downbeat is the beat phase (mod 4) where stem energy changes most
    # across the grid (phrase boundaries: drops, breakdowns, bass in/out)
    n = int(math.ceil(duration * FPS))
    env_raw = {}
    env_raw["rms"] = frame_rms(mix, SR)[:n]
    for name, (lo, hi) in {"low": (None, 150), "mid": (150, 2000), "high": (4000, None)}.items():
        env_raw[name] = frame_rms(sosfiltfilt(band_sos(lo, hi, SR), mix), SR)[:n]
    for s in ("vocal", "drums", "bass", "other"):
        env_raw[s] = frame_rms(stems["vocals" if s == "vocal" else s], SR)[:n]

    def beat_energy(k):
        e = env_raw[k]
        return np.array([e[int(beats[i] * FPS): int(beats[i + 1] * FPS)].mean() if i + 1 < len(beats) else 0 for i in range(len(beats))])
    change = np.zeros(len(beats))
    for k in ("bass", "drums", "vocal", "other"):
        be = 20 * np.log10(beat_energy(k) + 1e-6)
        change[1:] += np.abs(np.diff(be)) / (np.std(np.diff(be)) + 1e-9)
    ph_score = [change[ph::4].mean() for ph in range(4)]
    ph = int(np.argmax(ph_score))
    print("bar phase scores", np.round(ph_score, 2), "-> downbeat phase", ph)
    downbeats = beats[ph::4]
    # 8-bar phrase phase: the bar phase (mod 8) with most change
    bch = np.array([change[ph + 4 * b] for b in range(len(downbeats)) if ph + 4 * b < len(change)])
    phr = int(np.argmax([bch[q::8].mean() for q in range(8)]))
    print("phrase phase scores", np.round([bch[q::8].mean() for q in range(8)], 2), "-> phrase starts at bar", phr)
    # bar 0 = the first phrase-starting downbeat (section bars count from it)
    bar0 = float(downbeats[phr])

    if bars_table:
        print(f"\nbar 0 at {bar0:.3f}s (phrase start)")
        def bar_e(k, b):
            a, z = bar0 + 4 * P * b, bar0 + 4 * P * (b + 1)
            e = env_raw[k][int(a * FPS): int(z * FPS)]
            return e.mean() if len(e) else 0
        nb = int((duration - bar0) / (4 * P)) + 1
        keys = ("drums", "bass", "other", "vocal", "high")
        mx = {k: max(bar_e(k, b) for b in range(-2, nb)) for k in keys}
        for b in range(-int(bar0 / (4 * P)) - 1, nb):
            row = " ".join(f"{k[:4]} {'#' * int(12 * bar_e(k, b) / mx[k]):12s}" for k in keys)
            print(f"bar {b:3d} {bar0 + 4 * P * b:7.2f}s {row}")
        return

    # envelopes ---------------------------------------------------------------
    env = {}
    for k in env_raw:
        e = smooth_env(env_raw[k])
        env[k] = [round(float(x), 3) for x in norm01(e)]
        assert len(env[k]) == n

    # onsets --------------------------------------------------------------------
    (kt, kdb), (st, sdb), (ht, hdb) = drum_onsets(stems["drums"], SR)
    onsets = {
        "kick": [[round(float(t), 3), round(float(s), 3)] for t, s in zip(kt, strength01(kdb))],
        "snare": [[round(float(t), 3), round(float(s), 3)] for t, s in zip(st, strength01(sdb))],
        "hat": [[round(float(t), 3), round(float(s), 3)] for t, s in zip(ht, strength01(hdb))],
        "vocal": [[t, s] for t, s in vocal_onsets(stems["vocals"], SR)],
    }
    print({k: len(v) for k, v in onsets.items()})

    # sections ------------------------------------------------------------------
    sections = []
    for name, a, b in SECTION_BARS:
        s = 0.0 if a is None else bar0 + 4 * P * a
        e = duration if b is None else bar0 + 4 * P * b
        sections.append(dict(name=name, start=round(s, 3), end=round(e, 3)))
    for s in sections:
        print(f"  {s['name']:8s} {s['start']:7.2f} - {s['end']:7.2f}")

    # pitch / spectra -------------------------------------------------------------
    midi = bass_pitch(stems["bass"], SR, n)
    mel, chroma = spectra(mix, stems["other"], SR, n)
    blob = np.concatenate([mel.T, chroma.T], axis=1)  # frame-major: n x (64 + 12)
    (common.DATA / "spectrum.bin").write_bytes(blob.tobytes())
    # raw stereo waveform for scopes: int16 little-endian, interleaved L/R at WAVE_SR
    import soundfile as sf, soxr
    st, s0 = sf.read(common.AUDIO, dtype="float32", always_2d=True)
    st = soxr.resample(st, s0, WAVE_SR)
    peak = float(np.abs(st).max()) + 1e-9
    (common.DATA / "wave.bin").write_bytes((np.clip(st / peak, -1, 1) * 32767).astype("<i2").tobytes())

    doc = dict(
        duration=round(duration, 3),
        bpm=round(bpm, 4),
        beat_period=round(P, 6),
        time_signature=4,
        beats=[round(float(b), 4) for b in beats],
        downbeats=[round(float(b), 4) for b in downbeats],
        bar0=round(bar0, 4),
        sections=sections,
        fps=FPS,
        **env,
        bass_midi=[round(float(x), 2) for x in midi],
        onsets=onsets,
        wave=dict(file="data/wave.bin", rate=WAVE_SR, channels=2, frames=int(round(duration * WAVE_SR)),
                  layout="int16 little-endian, interleaved L/R, peak-normalized"),
        spectrum=dict(file="data/spectrum.bin", frames=n, mel=MEL_BANDS, chroma=12, fmin=MEL_FMIN, fmax=MEL_FMAX,
                      layout="uint8, frame-major, per frame: mel[0..63] (low->high, per-band normalized dB: 0 = band floor (2nd pct), 255 = band 99.5th pct) then chroma[C..B]"),
    )
    (common.DATA / "audio.json").write_text(json.dumps(doc, separators=(",", ":")))
    print("wrote", common.DATA / "audio.json", "and spectrum.bin", blob.shape)


if __name__ == "__main__":
    main(bars_table="--bars" in sys.argv)
