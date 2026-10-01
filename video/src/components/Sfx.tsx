import React from "react";
import { staticFile } from "remotion";
import { Audio } from "@remotion/media";

// Files from the Remotion sound effect library (remotion.dev/docs/sfx), usable
// without attribution; whoosh is "Woosh" by 1bob on freesound.org (CC0).
export type SfxName = "whoosh" | "pageTurn" | "uiSwitch" | "mouseClick";

const SOUNDS: Record<SfxName, { file: string; level: number; leadFrames: number }> = {
  // level brings each file to roughly -19 dB peak; leadFrames aligns its loudest
  // moment with the animation frame passed as `at`.
  whoosh: { file: "sfx/whoosh.wav", level: 0.15, leadFrames: 2 },
  pageTurn: { file: "sfx/page-turn.wav", level: 0.15, leadFrames: 5 },
  uiSwitch: { file: "sfx/switch.wav", level: 0.2, leadFrames: 4 },
  mouseClick: { file: "sfx/mouse-click.wav", level: 0.15, leadFrames: 6 },
};

export const SfxEnabled = React.createContext(true);

/** One-shot sound effect whose peak lands on frame `at` of the enclosing sequence. */
export const Sfx: React.FC<{ name: SfxName; at: number; volume?: number }> = ({ name, at, volume = 1 }) => {
  const enabled = React.useContext(SfxEnabled);
  if (!enabled) return null;
  const sound = SOUNDS[name];
  return (
    <Audio
      name={`SFX · ${name}`}
      src={staticFile(sound.file)}
      from={Math.max(0, Math.round(at) - sound.leadFrames)}
      volume={sound.level * volume}
    />
  );
};
