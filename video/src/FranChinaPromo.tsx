import React from "react";
import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { colors, fonts } from "./theme";
import { SCENE_OVERLAP, scene } from "./timeline";
import { CaptionTrack } from "./components/Caption";
import { SfxEnabled } from "./components/Sfx";
import { MUSIC, musicTrimBefore, musicVolume } from "./audio";
import { FranceIntro } from "./scenes/FranceIntro";
import { InformationChaos } from "./scenes/InformationChaos";
import { FranChinaReveal } from "./scenes/FranChinaReveal";
import { ToulouseFocus } from "./scenes/ToulouseFocus";
import { ExchangeRate } from "./scenes/ExchangeRate";
import { Outro } from "./scenes/Outro";

const france = scene("france");
const chaos = scene("chaos");
const reveal = scene("reveal");
const toulouse = scene("toulouse");
const rates = scene("rates");
const outro = scene("outro");

export const FranChinaPromo: React.FC<{
  showCaptions?: boolean;
  showMusic?: boolean;
  showSfx?: boolean;
}> = ({ showCaptions = true, showMusic = true, showSfx = true }) => {
  const { fps } = useVideoConfig();
  return (
    <SfxEnabled.Provider value={showSfx}>
      <AbsoluteFill
        style={{ backgroundColor: colors.background, fontFamily: fonts.sans }}
      >
        <Sequence
          name="1 · France intro"
          from={france.from}
          durationInFrames={france.durationInFrames + SCENE_OVERLAP}
          premountFor={fps}
        >
          <FranceIntro />
        </Sequence>
        <Sequence
          name="2 · Information chaos"
          from={chaos.from}
          durationInFrames={chaos.durationInFrames + SCENE_OVERLAP}
          premountFor={fps}
        >
          <InformationChaos />
        </Sequence>
        <Sequence
          name="3 · FranChina reveal"
          from={reveal.from}
          durationInFrames={reveal.durationInFrames + SCENE_OVERLAP}
          premountFor={fps}
        >
          <FranChinaReveal />
        </Sequence>
        <Sequence
          name="4 · Toulouse focus"
          from={toulouse.from}
          durationInFrames={toulouse.durationInFrames + SCENE_OVERLAP}
          premountFor={fps}
        >
          <ToulouseFocus />
        </Sequence>
        <Sequence
          name="5 · Exchange rate"
          from={rates.from}
          durationInFrames={rates.durationInFrames + SCENE_OVERLAP}
          premountFor={fps}
        >
          <ExchangeRate />
        </Sequence>
        <Sequence
          name="6 · Outro"
          from={outro.from}
          durationInFrames={outro.durationInFrames}
          premountFor={fps}
        >
          <Outro />
        </Sequence>

        <Audio
          name="VO · France intro"
          src={staticFile(france.audio.src)}
          from={france.from + france.audio.from}
        />
        <Audio
          name="VO · Information chaos"
          src={staticFile(chaos.audio.src)}
          from={chaos.from + chaos.audio.from}
        />
        <Audio
          name="VO · FranChina reveal"
          src={staticFile(reveal.audio.src)}
          from={reveal.from + reveal.audio.from}
        />
        <Audio
          name="VO · Toulouse focus"
          src={staticFile(toulouse.audio.src)}
          from={toulouse.from + toulouse.audio.from}
        />
        <Audio
          name="VO · Exchange rate"
          src={staticFile(rates.audio.src)}
          from={rates.from + rates.audio.from}
        />
        <Audio
          name="VO · Outro"
          src={staticFile(outro.audio.src)}
          from={outro.from + outro.audio.from}
        />

        {showMusic ? (
          <Audio
            name="Music"
            src={staticFile(MUSIC.src)}
            trimBefore={musicTrimBefore}
            volume={musicVolume}
          />
        ) : null}

        {showCaptions ? <CaptionTrack hideIn={["outro"]} /> : null}
      </AbsoluteFill>
    </SfxEnabled.Provider>
  );
};
