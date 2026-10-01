import React from "react";
import { Composition, Folder, Still } from "remotion";
import { FPS, TOTAL_FRAMES, scene } from "./timeline";
import { FranChinaPromo } from "./FranChinaPromo";
import { FranceIntro } from "./scenes/FranceIntro";
import { InformationChaos } from "./scenes/InformationChaos";
import { FranChinaReveal } from "./scenes/FranChinaReveal";
import { ToulouseFocus } from "./scenes/ToulouseFocus";
import { ExchangeRate } from "./scenes/ExchangeRate";
import { Outro } from "./scenes/Outro";
import { Cover } from "./components/CoverArt";

const LANDSCAPE = { width: 1920, height: 1080, fps: FPS };

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="FranChinaPromo"
        component={FranChinaPromo}
        durationInFrames={TOTAL_FRAMES}
        {...LANDSCAPE}
        defaultProps={{ showCaptions: true, showMusic: true, showSfx: true }}
      />
      <Folder name="Covers">
        <Still id="Cover-16x9" component={Cover} width={1920} height={1080} />
        <Still id="Cover-3x4" component={Cover} width={1080} height={1440} />
        <Still id="Cover-9x16" component={Cover} width={1080} height={1920} />
      </Folder>
      <Folder name="Scenes">
        <Composition id="FranceIntro" component={FranceIntro} durationInFrames={scene("france").durationInFrames} {...LANDSCAPE} />
        <Composition id="InformationChaos" component={InformationChaos} durationInFrames={scene("chaos").durationInFrames} {...LANDSCAPE} />
        <Composition id="FranChinaReveal" component={FranChinaReveal} durationInFrames={scene("reveal").durationInFrames} {...LANDSCAPE} />
        <Composition id="ToulouseFocus" component={ToulouseFocus} durationInFrames={scene("toulouse").durationInFrames} {...LANDSCAPE} />
        <Composition id="ExchangeRate" component={ExchangeRate} durationInFrames={scene("rates").durationInFrames} {...LANDSCAPE} />
        <Composition id="Outro" component={Outro} durationInFrames={scene("outro").durationInFrames} {...LANDSCAPE} />
      </Folder>
    </>
  );
};
