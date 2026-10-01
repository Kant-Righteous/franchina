// Background music placement and ducking under the narration.
import { interpolate } from "remotion";
import { FPS, SCENES, TOTAL_FRAMES } from "./timeline";

export const MUSIC = {
  src: "audio/music.mp3",
  // Second in music.mp3 that lands on the last frame of the video. The track's
  // final chord (~59 s in music.mp3) then rings out over the closing logo.
  endSec: 61.8,
  // Level while nobody speaks, and while the narration plays.
  open: 0.22,
  ducked: 0.075,
  fadeInSec: 1.2,
};

export const musicTrimBefore = Math.max(0, Math.round((MUSIC.endSec - TOTAL_FRAMES / FPS) * FPS));

// Speech intervals in composition milliseconds, with short pauses merged.
const SPEECH: [number, number][] = (() => {
  const spans = SCENES.flatMap((s) =>
    s.chunks.map((c) => [(s.from / FPS) * 1000 + c.startMs, (s.from / FPS) * 1000 + c.endMs] as [number, number]),
  ).sort((a, b) => a[0] - b[0]);
  const merged: [number, number][] = [];
  for (const span of spans) {
    const last = merged[merged.length - 1];
    if (last && span[0] - last[1] < 700) last[1] = Math.max(last[1], span[1]);
    else merged.push([...span]);
  }
  return merged;
})();

/** Music volume for a composition frame: ducks ahead of speech, recovers in pauses. */
export const musicVolume = (frame: number) => {
  const ms = (frame / FPS) * 1000;
  const distance = SPEECH.reduce((min, [a, b]) => {
    if (ms >= a - 250 && ms <= b) return 0;
    return Math.min(min, ms < a ? a - 250 - ms : ms - b);
  }, Infinity);
  const level = interpolate(distance, [0, 450], [MUSIC.ducked, MUSIC.open], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeIn = interpolate(frame, [0, MUSIC.fadeInSec * FPS], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return level * fadeIn;
};
