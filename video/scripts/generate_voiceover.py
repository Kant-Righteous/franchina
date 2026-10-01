"""Generate narration audio, the scene timeline and subtitles for the promo video.

Reads  src/data/narration.json
Writes public/audio/scene-<id>.mp3
       src/data/timeline.json
       captions.srt (and a copy in public/captions/)

Usage:
    python scripts/generate_voiceover.py                     # synthesize + rebuild timeline
    python scripts/generate_voiceover.py --no-tts            # rebuild timeline from cached audio
    python scripts/generate_voiceover.py --only toulouse     # re-synthesize one scene, reuse the rest
    python scripts/generate_voiceover.py --voice zh-CN-XiaoxiaoNeural
    python scripts/generate_voiceover.py --source recording  # use recordings in recording/

Recording mode accepts either one file per scene (recording/france.wav,
recording/chaos.m4a, ...) or a single take (recording/full.wav).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import recording_align as rec
import voice_processing as vp

ROOT = Path(__file__).resolve().parent.parent
NARRATION = ROOT / "src" / "data" / "narration.json"
TIMELINE = ROOT / "src" / "data" / "timeline.json"
AUDIO_DIR = ROOT / "public" / "audio"
CACHE_DIR = ROOT / "tts-cache"
RECORDING_DIR = ROOT / "recording"
SRT_PATH = ROOT / "captions.srt"
SRT_PUBLIC = ROOT / "public" / "captions" / "captions.srt"

# Edge neural voices stream 24 kHz / 48 kbps mono MP3.
MP3_BITRATE = 48_000
NON_SPEECH = re.compile(r"[\s，。、：；！？,.:;!?*（）()“”\"'…—-]")
TRAILING_PUNCT = re.compile(r"[，。：；、,.:;]+$")


@dataclass
class Boundary:
    text: str
    start_ms: float
    end_ms: float


@dataclass
class Synthesis:
    audio: bytes | None
    boundaries: list[Boundary]
    length_ms: float | None = None

    @property
    def duration_ms(self) -> float:
        if self.length_ms is not None:
            return self.length_ms
        return len(self.audio or b"") * 8 / MP3_BITRATE * 1000


class TtsProvider:
    """Interface for a TTS backend returning MP3 audio plus word timings."""

    name = "base"

    async def synthesize(self, text: str, voice: str, rate: str, pitch: str) -> Synthesis:
        raise NotImplementedError


class EdgeTtsProvider(TtsProvider):
    name = "Microsoft Edge Neural TTS (edge-tts)"

    async def synthesize(self, text: str, voice: str, rate: str, pitch: str) -> Synthesis:
        import edge_tts

        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch, boundary="WordBoundary"
        )
        audio = bytearray()
        boundaries: list[Boundary] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000
                boundaries.append(
                    Boundary(chunk["text"], start, start + chunk["duration"] / 10_000)
                )
        return Synthesis(bytes(audio), boundaries)


def plain(text: str) -> str:
    return text.replace("*", "")


def normalize(text: str) -> str:
    return NON_SPEECH.sub("", text).lower()


def spoken_text(text: str, spoken: dict[str, str]) -> str:
    out = plain(text)
    for written, said in spoken.items():
        out = out.replace(written, said)
    return out


def char_times(boundaries: list[Boundary]) -> list[tuple[float, float]]:
    """Spread each boundary's time span evenly over its normalized characters."""
    times: list[tuple[float, float]] = []
    for b in boundaries:
        chars = normalize(b.text)
        if not chars:
            continue
        step = (b.end_ms - b.start_ms) / len(chars)
        for i in range(len(chars)):
            times.append((b.start_ms + i * step, b.start_ms + (i + 1) * step))
    return times


def emphasis_offsets(chunk: str, spoken: dict[str, str]) -> list[tuple[str, int]]:
    """Return (word, normalized char offset) for every *word* in a chunk."""
    marks = []
    parts = chunk.split("*")
    offset = 0
    for i, part in enumerate(parts):
        if i % 2 == 1:
            marks.append((part, offset))
        offset += len(normalize(spoken_text(part, spoken)))
    return marks


def align_chunks(chunks: list[str], spoken: dict[str, str], synth: Synthesis):
    times = char_times(synth.boundaries)
    spans = []
    marks = []
    cursor = 0
    for chunk in chunks:
        n = len(normalize(spoken_text(chunk, spoken)))
        if n == 0 or cursor + n > len(times):
            raise RuntimeError(f"Cannot align chunk {chunk!r}: boundaries exhausted")
        spans.append((times[cursor][0], times[cursor + n - 1][1]))
        marks.append([(word, times[cursor + off][0]) for word, off in emphasis_offsets(chunk, spoken)])
        cursor += n
    if cursor != len(times):
        print(f"  warning: {len(times) - cursor} unaligned characters remain")
    return spans, marks


def caption_text(chunk: str) -> str:
    return TRAILING_PUNCT.sub("", chunk.strip())


def chunk_weight(chunk: str, spoken: dict[str, str]) -> float:
    """Approximate speaking time: one unit per Chinese character, Latin letters count a third."""
    text = normalize(spoken_text(chunk, spoken))
    latin = sum(1 for c in text if c.isascii())
    return (len(text) - latin) + latin / 3


def phrases(chunk: str) -> list[str]:
    """Split a chunk at enumeration commas, where readers usually pause briefly."""
    return [p for p in re.split(r"(?<=、)", chunk) if normalize(p)]


def recording_boundaries(segments, spans, units, spoken, offset_ms):
    """Per-character boundaries for aligned phrases, relative to `offset_ms`."""
    out = []
    for unit, span in zip(units, spans):
        chars = normalize(spoken_text(unit, spoken))
        for ch, (a, b) in zip(chars, rec.char_times(segments, span, len(chars))):
            out.append(Boundary(ch, a - offset_ms, b - offset_ms))
    return out


PRE_ROLL_MS = 200
POST_ROLL_MS = 350


def load_recordings(config: dict, spoken: dict[str, str], directory: Path) -> dict[str, Synthesis]:
    """Align recordings to the script and export one trimmed MP3 per scene."""
    scenes = config["scenes"]
    per_scene = {s["id"]: rec.find_recording(directory, s["id"]) for s in scenes}
    full = rec.find_recording(directory, "full")
    if not all(per_scene.values()) and full is None:
        names = ", ".join(f"{s['id']}.wav" for s in scenes)
        raise SystemExit(f"Put full.wav or per-scene files ({names}) in {directory}")

    result: dict[str, Synthesis] = {}
    report = {}
    with tempfile.TemporaryDirectory() as tmp:
        if all(per_scene.values()):
            groups = [([s], per_scene[s["id"]]) for s in scenes]
        else:
            groups = [(scenes, full)]
        # Decode every take, then process them together so tone and level match.
        raw_dir, processed_dir = Path(tmp) / "raw", Path(tmp) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        raw = {}
        for _, source in groups:
            raw[source.stem] = raw_dir / f"{source.stem}.wav"
            rec.to_wav(source, raw[source.stem])
        processed = vp.process_takes(raw, processed_dir)
        for group, source in groups:
            normalized = processed[source.stem]
            levels = rec.frame_levels(rec.decode(normalized))
            segments = rec.detect_speech(levels)
            # Align phrases, then regroup them into caption chunks per scene.
            units = [(si, ci, p) for si, s in enumerate(group) for ci, c in enumerate(s["chunks"]) for p in phrases(c)]
            unit_spans = rec.align(segments, [chunk_weight(p, spoken) for _, _, p in units], levels)
            spans = []
            for si, s in enumerate(group):
                for ci in range(len(s["chunks"])):
                    mine = [sp for (usi, uci, _), sp in zip(units, unit_spans) if usi == si and uci == ci]
                    spans.append((mine[0][0], mine[-1][1]))
            cursor = 0
            for i, s in enumerate(group):
                own = spans[cursor : cursor + len(s["chunks"])]
                before = spans[cursor - 1][1] if cursor > 0 else 0.0
                after_idx = cursor + len(s["chunks"])
                after = spans[after_idx][0] if after_idx < len(spans) else own[-1][1] + POST_ROLL_MS
                start = max(own[0][0] - PRE_ROLL_MS, (before + own[0][0]) / 2, 0.0)
                end = min(own[-1][1] + POST_ROLL_MS, (own[-1][1] + after) / 2 if after_idx < len(spans) else own[-1][1] + POST_ROLL_MS)
                rec.export_slice(normalized, start, end, AUDIO_DIR / f"scene-{s['id']}.mp3")
                own_units = [(p, sp) for (usi, _, p), sp in zip(units, unit_spans) if usi == i]
                boundaries = recording_boundaries(
                    segments, [sp for _, sp in own_units], [p for p, _ in own_units], spoken, start
                )
                result[s["id"]] = Synthesis(None, boundaries, end - start)
                report[s["id"]] = {
                    "source": source.name,
                    "sliceMs": [round(start), round(end)],
                    "chunks": [
                        {"text": plain(c), "startMs": round(a), "endMs": round(b)}
                        for c, (a, b) in zip(s["chunks"], own)
                    ],
                }
                cursor = after_idx
    (directory / "alignment.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def srt_time(ms: float) -> str:
    ms = max(0, int(round(ms)))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-tts", action="store_true", help="reuse cached synthesis")
    parser.add_argument("--voice", help="override narration.json voice")
    parser.add_argument("--only", nargs="+", metavar="SCENE", help="re-synthesize only these scenes")
    parser.add_argument("--source", choices=["tts", "recording"], default="tts")
    parser.add_argument("--recording-dir", type=Path, default=RECORDING_DIR)
    args = parser.parse_args()

    config = json.loads(NARRATION.read_text(encoding="utf-8"))
    voice = args.voice or config["voice"]
    fps = config["fps"]
    spoken = config.get("spoken", {})
    provider = EdgeTtsProvider()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    recorded = load_recordings(config, spoken, args.recording_dir) if args.source == "recording" else None
    if recorded is not None:
        voice = "human recording"

    scenes = []
    captions = []
    cursor_frames = 0
    for scene in config["scenes"]:
        sid = scene["id"]
        audio_path = AUDIO_DIR / f"scene-{sid}.mp3"
        cache_path = CACHE_DIR / f"scene-{sid}.json"
        text = "".join(spoken_text(c, spoken) for c in scene["chunks"])

        if recorded is not None:
            synth = recorded[sid]
        elif (args.no_tts or (args.only and sid not in args.only)) and audio_path.exists() and cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            synth = Synthesis(
                audio_path.read_bytes(), [Boundary(**b) for b in cached["boundaries"]]
            )
        else:
            print(f"synthesizing {sid}: {text}")
            synth = await provider.synthesize(text, voice, config["rate"], config["pitch"])
            audio_path.write_bytes(synth.audio)
            cache_path.write_text(
                json.dumps(
                    {"voice": voice, "text": text, "boundaries": [b.__dict__ for b in synth.boundaries]},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        spans, chunk_marks = align_chunks(scene["chunks"], spoken, synth)
        speech_end_ms = synth.boundaries[-1].end_ms
        lead_ms = scene["leadIn"] * 1000
        needed_ms = lead_ms + speech_end_ms + scene["tail"] * 1000
        duration_frames = math.ceil(max(scene["minSeconds"] * 1000, needed_ms) / 1000 * fps)
        scene_start_ms = cursor_frames / fps * 1000
        audio_from = round(scene["leadIn"] * fps)
        audio_start_ms = scene_start_ms + audio_from / fps * 1000
        scene_end_ms = (cursor_frames + duration_frames) / fps * 1000

        for i, (chunk, (start, end)) in enumerate(zip(scene["chunks"], spans)):
            next_start = spans[i + 1][0] if i + 1 < len(spans) else None
            cap_start = audio_start_ms + start - 80
            if next_start is not None:
                cap_end = audio_start_ms + next_start - 80
            else:
                cap_end = min(audio_start_ms + end + 550, scene_end_ms - 100)
            captions.append(
                {
                    "sceneId": sid,
                    "text": caption_text(chunk),
                    "startMs": round(cap_start),
                    "endMs": round(cap_end),
                }
            )

        scenes.append(
            {
                "id": sid,
                "from": cursor_frames,
                "durationInFrames": duration_frames,
                "audio": {
                    "src": f"audio/scene-{sid}.mp3",
                    "from": audio_from,
                    "durationMs": round(synth.duration_ms),
                    "speechEndMs": round(speech_end_ms),
                },
                "chunks": [
                    {"text": caption_text(c), "startMs": round(audio_from / fps * 1000 + s), "endMs": round(audio_from / fps * 1000 + e)}
                    for c, (s, e) in zip(scene["chunks"], spans)
                ],
                "marks": {
                    word: round(audio_from / fps * 1000 + t)
                    for chunk_list in chunk_marks
                    for word, t in chunk_list
                },
            }
        )
        print(
            f"  {sid}: speech {speech_end_ms / 1000:.2f}s -> scene {duration_frames / fps:.2f}s"
        )
        cursor_frames += duration_frames

    total_seconds = cursor_frames / fps
    timeline = {
        "fps": fps,
        "durationInFrames": cursor_frames,
        "voice": voice,
        "provider": "Human recording" if recorded is not None else provider.name,
        "scenes": scenes,
        "captions": captions,
    }
    TIMELINE.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    for i, cap in enumerate(captions, 1):
        lines += [str(i), f"{srt_time(cap['startMs'])} --> {srt_time(cap['endMs'])}", plain(cap["text"]), ""]
    SRT_PATH.write_text("\n".join(lines), encoding="utf-8")
    SRT_PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRT_PATH, SRT_PUBLIC)

    print(f"total {total_seconds:.2f}s ({cursor_frames} frames) with voice {voice}")
    if total_seconds > config["maxSeconds"]:
        raise SystemExit(f"Timeline exceeds {config['maxSeconds']}s; shorten narration or read a little faster")


if __name__ == "__main__":
    asyncio.run(main())
