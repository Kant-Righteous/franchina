"""Make separately recorded narration takes sound like one session.

Chain per take: 80 Hz high-pass -> spectral match to the median long-term
spectrum of all takes -> gentle compression -> common active speech level ->
peak limit. Requires numpy and scipy.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 48_000
TARGET_ASL_DB = -20.0  # active speech level, dBFS
PEAK_DB = -1.5
MAX_EQ_DB = 9.0
NFFT = 4096


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        if w.getframerate() != SR or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"{path} must be 48 kHz mono 16-bit")
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768


def write_wav(path: Path, x: np.ndarray) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def frame_levels(x: np.ndarray, ms: float = 20) -> tuple[np.ndarray, int]:
    hop = int(SR * ms / 1000)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    return 20 * np.log10(np.sqrt((frames**2).mean(1)) + 1e-9), hop


def active_mask(x: np.ndarray) -> tuple[np.ndarray, int]:
    """Frames within 30 dB of the loudest frame count as speech."""
    levels, hop = frame_levels(x)
    return levels > levels.max() - 30, hop


def active_level(x: np.ndarray) -> float:
    mask, hop = active_mask(x)
    speech = x[: len(mask) * hop].reshape(-1, hop)[mask]
    return 20 * np.log10(np.sqrt((speech**2).mean()) + 1e-12)


def ltas(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Long-term average spectrum of the voiced parts, smoothed to 1/3 octave, in dB."""
    mask, hop = active_mask(x)
    speech = x[: len(mask) * hop].reshape(-1, hop)[mask].ravel()
    freqs, power = signal.welch(speech, SR, nperseg=NFFT)
    db = 10 * np.log10(power + 1e-20)
    smooth = np.empty_like(db)
    for i, f in enumerate(freqs):
        band = (freqs >= f / 2 ** (1 / 6)) & (freqs <= f * 2 ** (1 / 6))
        smooth[i] = db[band].mean() if band.any() else db[i]
    return freqs, smooth


def match_filter(freqs: np.ndarray, own: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Linear-phase FIR moving `own` toward `target` between 100 Hz and 12 kHz."""
    gain = np.clip(target - own, -MAX_EQ_DB, MAX_EQ_DB)
    gain[(freqs < 100) | (freqs > 12_000)] = 0.0
    gain -= np.average(gain[(freqs >= 300) & (freqs <= 3000)])  # tone only, level handled later
    return signal.firwin2(2047, freqs / (SR / 2), 10 ** (gain / 20))


def compress(x: np.ndarray, threshold_db: float, ratio: float = 2.5) -> np.ndarray:
    """Feed-forward RMS compressor (10 ms attack, 150 ms release)."""
    env_db, hop = frame_levels(x, 5)
    att, rel = np.exp(-5 / 10), np.exp(-5 / 150)
    smoothed = np.empty_like(env_db)
    state = env_db[0]
    for i, v in enumerate(env_db):
        coef = att if v > state else rel
        state = coef * state + (1 - coef) * v
        smoothed[i] = state
    over = np.maximum(smoothed - threshold_db, 0)
    gain_db = -over * (1 - 1 / ratio)
    gain = np.repeat(10 ** (gain_db / 20), hop)
    gain = np.concatenate([gain, np.full(len(x) - len(gain), gain[-1] if len(gain) else 1.0)])
    return x * gain


def limit(x: np.ndarray, ceiling_db: float = PEAK_DB) -> np.ndarray:
    """Look-ahead peak limiter with a 5 ms window."""
    ceiling = 10 ** (ceiling_db / 20)
    win = int(SR * 0.005)
    peak = np.array([np.abs(x[max(0, i - win) : i + win]).max() for i in range(0, len(x), win)])
    gain = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    gain = np.repeat(gain, win)[: len(x)]
    gain = signal.filtfilt(np.ones(win) / win, [1.0], gain)
    return x * np.minimum(gain, 1.0)


def process_takes(paths: dict[str, Path], out_dir: Path) -> dict[str, Path]:
    """Process all takes together so they share one tone and level."""
    sos = signal.butter(2, 80, "highpass", fs=SR, output="sos")
    takes = {k: signal.sosfiltfilt(sos, read_wav(p)) for k, p in paths.items()}
    spectra = {k: ltas(x) for k, x in takes.items()}
    freqs = next(iter(spectra.values()))[0]
    # Compare tone after removing each take's overall level.
    shapes = {k: s - np.average(s[(freqs >= 300) & (freqs <= 3000)]) for k, (_, s) in spectra.items()}
    target = np.median(np.stack(list(shapes.values())), axis=0)

    out = {}
    for key, x in takes.items():
        y = signal.fftconvolve(x, match_filter(freqs, shapes[key], target), mode="same") if len(takes) > 1 else x
        y = compress(y, active_level(y) + 4)
        y = y * 10 ** ((TARGET_ASL_DB - active_level(y)) / 20)
        y = limit(y)
        path = out_dir / f"{key}.wav"
        write_wav(path, y)
        out[key] = path
    return out
