"""Align a read-aloud recording of a known script to its caption chunks.

The narrator reads a fixed script, so no speech recognition is needed: speech
and pauses are detected from the signal energy, then a dynamic programme places
each chunk boundary on the pause that best matches the expected chunk length
(proportional to its character count). Characters inside a chunk are spread
evenly over the chunk's voiced time.
"""

from __future__ import annotations

import array
import math
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_RATE = 16_000
FRAME_MS = 10
AUDIO_SUFFIXES = (".wav", ".m4a", ".mp3", ".aac", ".flac", ".ogg", ".webm")


def ffmpeg(*args: str) -> None:
    """Run the ffmpeg build bundled with Remotion."""
    npx = shutil.which("npx")
    if npx is None:
        raise SystemExit("npx not found; install Node.js")
    subprocess.run(
        [npx, "remotion", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        cwd=ROOT,
        check=True,
    )


def decode(path: Path) -> array.array:
    """Decode any audio file to 16 kHz mono int16 samples."""
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "decoded.wav"
        ffmpeg("-i", str(path.resolve()), "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(wav_path))
        with wave.open(str(wav_path)) as w:
            samples = array.array("h", w.readframes(w.getnframes()))
    return samples


def to_wav(src: Path, dst: Path) -> None:
    """Decode any recording to 48 kHz mono 16-bit WAV."""
    ffmpeg("-i", str(src.resolve()), "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(dst.resolve()))


def export_slice(src: Path, start_ms: float, end_ms: float, dst: Path) -> None:
    ffmpeg(
        "-ss", f"{max(0.0, start_ms) / 1000:.3f}", "-to", f"{end_ms / 1000:.3f}", "-i", str(src.resolve()),
        "-c:a", "libmp3lame", "-q:a", "2", str(dst.resolve()),
    )


@dataclass
class Segment:
    start: float  # ms
    end: float


def frame_levels(samples: array.array) -> list[float]:
    """RMS level in dBFS for each FRAME_MS frame."""
    hop = SAMPLE_RATE * FRAME_MS // 1000
    levels = []
    for i in range(0, len(samples) - hop + 1, hop):
        frame = samples[i : i + hop]
        rms = math.sqrt(sum(x * x for x in frame) / hop) or 1.0
        levels.append(20 * math.log10(rms / 32768))
    return levels


def detect_speech(levels: list[float]) -> list[Segment]:
    """Energy-based voice activity detection with an adaptive threshold."""
    if not levels:
        return []
    ordered = sorted(levels)
    noise = ordered[int(len(ordered) * 0.1)]
    peak = ordered[int(len(ordered) * 0.95)]
    # Clean studio takes can have digital silence, so also anchor the threshold to the peak.
    threshold = max(noise + max(8.0, 0.3 * (peak - noise)), peak - 28.0)

    segments: list[Segment] = []
    for i, level in enumerate(levels):
        if level < threshold:
            continue
        t0, t1 = i * FRAME_MS, (i + 1) * FRAME_MS
        if segments and t0 - segments[-1].end <= 100:
            segments[-1].end = t1
        else:
            segments.append(Segment(t0, t1))
    return [s for s in segments if s.end - s.start >= 60]


@dataclass
class Cut:
    start: float  # end of speech before the cut
    end: float  # start of speech after the cut
    synthetic: bool
    cost: float = 0.0


def _speech_time(segments: list[Segment]):
    """Return S(t): voiced milliseconds before time t."""
    starts = [s.start for s in segments]
    cumulative = [0.0]
    for s in segments:
        cumulative.append(cumulative[-1] + s.end - s.start)

    def speech_before(t: float) -> float:
        lo, hi = 0, len(starts)
        while lo < hi:
            mid = (lo + hi) // 2
            if starts[mid] < t:
                lo = mid + 1
            else:
                hi = mid
        idx = lo - 1
        if idx < 0:
            return 0.0
        seg = segments[idx]
        return cumulative[idx] + min(seg.end, t) - seg.start

    return speech_before


def _valley_cuts(segments: list[Segment], levels: list[float]) -> list[Cut]:
    """Candidate cuts inside continuous speech, preferring energy dips between syllables."""
    smooth = [sum(levels[max(0, i - 1) : i + 2]) / len(levels[max(0, i - 1) : i + 2]) for i in range(len(levels))]
    cuts = []
    reach = 100 // FRAME_MS
    for seg in segments:
        lo, hi = int(seg.start // FRAME_MS) + 12, min(int(seg.end // FRAME_MS) - 12, len(smooth) - reach - 1)
        for i in range(lo, hi):
            window = smooth[i - reach : i + reach + 1]
            if smooth[i] != min(window):
                continue
            depth = max(window) - smooth[i]
            if depth >= 6:
                t = i * FRAME_MS + FRAME_MS / 2
                cuts.append(Cut(t, t, True, 1.5 - min(depth, 24) / 24 * 0.6))
        # Plain grid as a fallback where no dip is found.
        t = seg.start + 150
        while t < seg.end - 150:
            cuts.append(Cut(t, t, True, 1.6))
            t += 150
    return cuts


def align(segments: list[Segment], weights: list[float], levels: list[float] | None = None) -> list[tuple[float, float]]:
    """Place len(weights)-1 boundaries; return (start, end) speech span per chunk."""
    if not segments:
        raise SystemExit("No speech detected in recording")
    n = len(weights)
    speech_before = _speech_time(segments)
    total_speech = speech_before(segments[-1].end)
    total_weight = sum(weights)

    cuts = [Cut(segments[0].start, segments[0].start, False)]
    for a, b in zip(segments, segments[1:]):
        cuts.append(Cut(a.end, b.start, False))
    # Allow cuts inside continuous speech for readers who run phrases together.
    cuts.extend(_valley_cuts(segments, levels or []))
    cuts.append(Cut(segments[-1].end, segments[-1].end, False))
    cuts.sort(key=lambda c: (c.start, c.end))
    first, last = 0, len(cuts) - 1
    while cuts[first].synthetic:
        first += 1

    # Prefix sums of "unexplained pause" inside a span: long pauses rarely fall inside one chunk.
    long_pause = [0.0]
    for c in cuts:
        long_pause.append(long_pause[-1] + (0 if c.synthetic else max(0.0, c.end - c.start - 300) / 1000))

    voiced_at_start = [speech_before(c.start) for c in cuts]
    voiced_at_end = [speech_before(c.end) for c in cuts]
    cut_costs = [c.cost if c.synthetic else -0.5 * min(c.end - c.start, 800) / 800 for c in cuts]

    inf = float("inf")
    cost = [[inf] * len(cuts) for _ in range(n + 1)]
    back = [[-1] * len(cuts) for _ in range(n + 1)]
    cost[0][first] = 0.0
    for k in range(1, n + 1):
        expected = total_speech * weights[k - 1] / total_weight
        targets = [last] if k == n else range(len(cuts))
        for b in targets:
            cb = cuts[b]
            best, arg = inf, -1
            for a in range(first, b):
                prev = cost[k - 1][a]
                if prev == inf:
                    continue
                if cuts[a].end >= cb.start:
                    continue
                spoken = voiced_at_start[b] - voiced_at_end[a]
                err = (spoken - expected) / expected
                c = prev + 8 * err * err + 2 * (long_pause[b] - long_pause[a + 1])
                if k < n:
                    c += cut_costs[b]
                if c < best:
                    best, arg = c, a
            cost[k][b], back[k][b] = best, arg

    if cost[n][last] == inf:
        raise SystemExit("Could not align recording to the script")
    bounds = [last]
    for k in range(n, 0, -1):
        bounds.append(back[k][bounds[-1]])
    bounds.reverse()
    return [(cuts[bounds[k]].end, cuts[bounds[k + 1]].start) for k in range(n)]


def char_times(segments: list[Segment], span: tuple[float, float], count: int) -> list[tuple[float, float]]:
    """Spread `count` characters evenly over the voiced time inside `span`."""
    start, end = span
    voiced = [(max(s.start, start), min(s.end, end)) for s in segments if s.end > start and s.start < end]
    if not voiced:
        voiced = [(start, end)]
    total = sum(b - a for a, b in voiced)

    def at(offset: float) -> float:
        for a, b in voiced:
            if offset <= b - a:
                return a + offset
            offset -= b - a
        return voiced[-1][1]

    step = total / count
    return [(at(i * step), at((i + 1) * step)) for i in range(count)]


def find_recording(directory: Path, stem: str) -> Path | None:
    for suffix in AUDIO_SUFFIXES:
        path = directory / f"{stem}{suffix}"
        if path.exists():
            return path
    return None
