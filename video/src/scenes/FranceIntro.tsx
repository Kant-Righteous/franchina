import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, fonts } from "../theme";
import { chunkFrame, markFrame, scene } from "../timeline";
import { easeInOut, fadeUp, mix, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { CITIES, Camera, MapFocus, lerpCamera, toScreen } from "../components/MapFocus";
import { FlowNode } from "../components/FlowNode";
import { Connector } from "../components/Connector";
import { RouteMark } from "../components/BrandMark";
import { IconName } from "../components/Icon";
import { CoverArt, coverCamera } from "../components/CoverArt";
import { Sfx } from "../components/Sfx";

const S = scene("france");

type Topic = { label: string; sub: string; icon: IconName; dx: number; dy: number; at: number };

const TOPICS: Topic[] = [
  { label: "住房", sub: "LOGEMENT", icon: "housing", dx: -0.27, dy: -0.16, at: markFrame("france", "住哪里") },
  { label: "交通", sub: "TRANSPORT", icon: "transport", dx: 0, dy: -0.28, at: markFrame("france", "怎么坐车") },
  { label: "银行", sub: "BANQUE", icon: "bank", dx: 0.27, dy: -0.16, at: markFrame("france", "银行卡怎么开") },
  { label: "行政手续", sub: "DÉMARCHES", icon: "paperwork", dx: 0.27, dy: 0.16, at: chunkFrame("france", 2) },
  { label: "日常生活", sub: "VIE QUOTIDIENNE", icon: "daily", dx: 0, dy: 0.27, at: chunkFrame("france", 2) + 9 },
  { label: "汇率", sub: "CHANGE", icon: "exchange", dx: -0.27, dy: 0.16, at: chunkFrame("france", 2) + 18 },
];

export const FranceIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;

  // Frame 0 doubles as the brand cover; the copy fades out and the map takes over.
  const coverHold = 18;
  const coverOut = progress(frame, coverHold, 14, easeInOut);
  const wide: Camera = coverCamera(width, height);
  const close: Camera = { focus: [1.44, 43.6], scale: 150 * u, center: { x: width / 2, y: height * 0.5 } };
  const settle: Camera = { ...close, scale: 162 * u };
  const zoomStart = coverHold + 4;
  const zoomEnd = zoomStart + 62;
  const cam =
    frame < zoomEnd
      ? lerpCamera(wide, close, progress(frame, zoomStart, zoomEnd - zoomStart, easeInOut))
      : lerpCamera(close, settle, progress(frame, zoomEnd, S.durationInFrames - zoomEnd, (t) => t));

  const tls = toScreen(CITIES.toulouse.lon, CITIES.toulouse.lat, cam);
  const firstTopic = TOPICS[0].at;

  return (
    <SceneFrame fadeIn={false} washX="50%" washY="50%" gridOpacity={0.35}>
      <MapFocus
        cam={cam}
        cityOpacity={mix(1, 0, progress(frame, firstTopic - 10, 20))}
        pulse={0.35 + frame / 45}
      />

      {coverOut < 1 ? <CoverArt showMap={false} showBackdrop={false} textOpacity={1 - coverOut} /> : null}

      {TOPICS.map((t, i) => {
        const pos = { x: tls.x + t.dx * width, y: tls.y + t.dy * height };
        const appear = progress(frame, t.at - 2, 16);
        const active = progress(frame, t.at, 8) - 0.75 * progress(frame, t.at + 34, 18);
        return (
          <React.Fragment key={t.label}>
            <Connector
              from={tls}
              to={pos}
              bend={t.dx === 0 ? 0 : t.dx * t.dy > 0 ? -60 * u : 60 * u}
              progress={progress(frame, t.at - 6, 16)}
              dashed
              width={2.2 * u}
              opacity={0.55}
            />
            <FlowNode
              label={t.label}
              sub={t.sub}
              icon={t.icon}
              active={active}
              tone={i === 5 ? "accent" : "primary"}
              scale={u}
              style={{
                position: "absolute",
                left: pos.x,
                top: pos.y,
                translate: "-50% -50%",
                opacity: appear,
                scale: String(mix(0.88, 1, appear)),
              }}
            />
          </React.Fragment>
        );
      })}

      <ToulouseLabel x={tls.x} y={tls.y} opacity={progress(frame, zoomStart + 24, 16)} u={u} />

      <AbsoluteFill style={{ padding: `${84 * u}px ${110 * u}px` }}>
        <div style={fadeUp(frame, coverHold + 16, 20, 12)}>
          <RouteMark scale={u} planeT={mix(0.1, 0.62, progress(frame, 0, S.durationInFrames, (t) => t))} />
        </div>
      </AbsoluteFill>

      <Sfx name="whoosh" at={zoomStart + 8} />
      {TOPICS.map((t) => (
        <Sfx key={t.label} name="mouseClick" at={t.at + 2} volume={0.8} />
      ))}
    </SceneFrame>
  );
};

const ToulouseLabel: React.FC<{ x: number; y: number; opacity: number; u: number }> = ({ x, y, opacity, u }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y + 38 * u,
      translate: "-50% 0px",
      opacity,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 2 * u,
      padding: `${8 * u}px ${18 * u}px`,
      borderRadius: 14 * u,
      background: "#ffffffd9",
    }}
  >
    <span
      style={{
        fontFamily: fonts.sans,
        fontSize: 38 * u,
        fontWeight: 700,
        letterSpacing: "-0.02em",
        color: colors.primary,
        lineHeight: 1.1,
      }}
    >
      Toulouse
    </span>
    <span style={{ fontSize: 22 * u, fontWeight: 500, color: colors.accentStrong, letterSpacing: "0.12em" }}>
      图卢兹
    </span>
  </div>
);
