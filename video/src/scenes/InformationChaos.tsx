import React from "react";
import { useCurrentFrame } from "remotion";
import { SceneFrame } from "../components/SceneFrame";
import { CHAOS_CARDS, ChaosLayer } from "./ChaosLayer";
import { markFrame } from "../timeline";
import { Sfx } from "../components/Sfx";

export const InformationChaos: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <SceneFrame washX="50%" washY="45%" gridOpacity={0.3}>
      <ChaosLayer frame={frame} />
      <Sfx name="whoosh" at={8} />
      {CHAOS_CARDS.filter((c) => c.bumpAt !== undefined).map((c) => (
        <Sfx key={`bump-${c.kind}`} name="mouseClick" at={(c.bumpAt ?? 0) + 2} volume={0.8} />
      ))}
      <Sfx name="uiSwitch" at={markFrame("chaos", "最新的") + 4} />
    </SceneFrame>
  );
};
