import { Easing, interpolate } from "remotion";
import { EASE_OUT, EASE_STANDARD } from "../theme";

export const easeOut = Easing.bezier(...EASE_OUT);
export const easeStandard = Easing.bezier(...EASE_STANDARD);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 progress of a segment starting at `start` and lasting `duration` frames. */
export const progress = (
  frame: number,
  start: number,
  duration: number,
  easing: (t: number) => number = easeOut,
) => interpolate(frame, [start, start + duration], [0, 1], { ...clamp, easing });

export const mix = (from: number, to: number, t: number) => from + (to - from) * t;

/** Opacity + upward drift used for most element entrances. */
export const fadeUp = (frame: number, start: number, duration = 18, distance = 24) => {
  const p = progress(frame, start, duration);
  return { opacity: p, translate: `0px ${(1 - p) * distance}px` };
};

/** Fade out over `duration` frames ending at `end`. */
export const fadeOut = (frame: number, end: number, duration = 12) =>
  1 - progress(frame, end - duration, duration, easeStandard);

/** Gentle idle float so resting elements never look frozen. */
export const drift = (frame: number, seed: number, amplitude = 4, period = 150) => ({
  x: Math.sin((frame / period) * Math.PI * 2 + seed) * amplitude,
  y: Math.cos((frame / (period * 1.3)) * Math.PI * 2 + seed * 1.7) * amplitude,
});
