import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, fonts, site } from "../theme";
import { chunkFrame, markFrame, scene } from "../timeline";
import { easeInOut, fadeUp, mix, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { PandaLogo, Wordmark } from "../components/BrandMark";
import { InfoCard, SubChip } from "../components/InfoCard";
import { BrowserFrame, SHOTS, Shot } from "../components/BrowserFrame";
import { Connector } from "../components/Connector";
import { ChaosLayer } from "./ChaosLayer";
import { Sfx } from "../components/Sfx";

const CHAOS = scene("chaos");
const M = (w: string) => markFrame("reveal", w);
const C = (i: number) => chunkFrame("reveal", i);

// Stage cards reuse the homepage entry structure and real navigation labels.
const STAGES = [
  {
    number: "01",
    title: "赴法之前",
    description: "护照、公证与签证等出发前准备",
    at: C(1) - 6,
    chips: [
      { label: "办理签证", at: M("签证") },
      { label: "办理公证", at: M("公证") },
    ],
  },
  {
    number: "02",
    title: "抵法之后",
    description: "抵达第一周与重要行政手续",
    at: C(2) - 6,
    chips: [
      { label: "办理居留", at: M("居留") },
      { label: "办理医保", at: M("医保") },
      { label: "办理房补", at: M("房补") },
    ],
  },
  {
    number: "03",
    title: "生活指南",
    description: "财务、住房、交通与医疗信息",
    at: C(3) - 6,
    chips: [
      { label: "办理银行卡", at: C(3) + 2 },
      { label: "交通出行", at: C(3) + 12 },
      { label: "反诈提醒", at: M("防骗提醒"), accent: true },
    ],
  },
];

type Page = { shot: Shot; at: number; zoom: number; focusX: number; focusY: number };

const PAGES: Page[] = [
  { shot: SHOTS.home, at: 0, zoom: 1, focusX: 0.5, focusY: 0 },
  { shot: SHOTS.visa, at: M("签证") - 4, zoom: 1.32, focusX: 0.42, focusY: 0.12 },
  { shot: SHOTS.residence, at: M("居留") - 4, zoom: 1.32, focusX: 0.42, focusY: 0.12 },
  { shot: SHOTS.antiFraud, at: M("防骗提醒") - 4, zoom: 1.32, focusX: 0.42, focusY: 0.12 },
  { shot: SHOTS.homeFull, at: C(4) - 4, zoom: 1, focusX: 0.5, focusY: 1 },
];

export const FranChinaReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;

  const converge = progress(frame, 4, 30, (t) => t);
  const logoIn = progress(frame, 10, 22);
  const settle = progress(frame, C(1) - 30, 26, easeInOut);
  const layoutIn = progress(frame, C(1) - 16, 20);
  const finale = C(4);

  // Layout boxes (1080p design units scaled by u).
  const colX = 110 * u;
  const colW = 600 * u;
  const cardTops = [186, 434, 682].map((y) => y * u);
  const browserX = 800 * u;
  const browserW = width - browserX - 110 * u;
  const browserTop = 196 * u;
  const browserMid = browserTop + (browserW * (900 / 1440) + browserW * 0.05) / 2;

  const pageIndex = PAGES.reduce((acc, p, i) => (frame >= p.at ? i : acc), 0);
  const page = PAGES[pageIndex];
  const prevPage = PAGES[Math.max(0, pageIndex - 1)];
  const swap = pageIndex === 0 ? 1 : progress(frame, page.at, 12);
  const pushIn = progress(frame, page.at, 60, (t) => t);

  const activeStage = STAGES.reduce((acc, s, i) => (frame >= s.at ? i : acc), -1);
  const sweep = (i: number) => progress(frame, finale + i * 11, 10) - progress(frame, finale + i * 11 + 14, 10);

  return (
    <SceneFrame washX={`${mix(50, 30, settle)}%`} washY="45%" gridOpacity={0.35}>
      {frame < 60 ? <ChaosLayer frame={CHAOS.durationInFrames + frame} converge={converge} /> : null}

      {/* Centred lockup: the first formal appearance of the brand. */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          opacity: logoIn * (1 - settle),
          scale: String(mix(0.92, 1, logoIn) * mix(1, 0.6, settle)),
          translate: `${mix(0, -560, settle) * u}px ${mix(-40, -360, settle) * u}px`,
        }}
      >
        <div
          style={{
            position: "absolute",
            width: 520 * u,
            height: 520 * u,
            borderRadius: "50%",
            background: "radial-gradient(circle at 40% 35%, #f5f8ff 0%, #e8edff 70%, #dce6ff 100%)",
            border: "1px solid #e4ebff",
            opacity: 0.9,
            scale: String(mix(0.7, 1, logoIn)),
            translate: `0px ${-30 * u}px`,
          }}
        />
        <PandaLogo size={210 * u} style={{ scale: String(mix(0.8, 1, logoIn)), translate: `0px ${-20 * u}px` }} />
        <div style={fadeUp(frame, M("FranChina") - 2, 18, 18)}>
          <Wordmark size={128 * u} style={{ marginTop: 22 * u }} />
        </div>
        <div
          style={{
            ...fadeUp(frame, M("FranChina") + 10, 18, 14),
            marginTop: 20 * u,
            fontSize: 40 * u,
            fontWeight: 500,
            letterSpacing: "0.015em",
            color: colors.accent,
          }}
        >
          {site.english}
        </div>
      </AbsoluteFill>

      {/* Compact header lockup once the content takes over. */}
      <div
        style={{
          position: "absolute",
          left: colX,
          top: 76 * u,
          display: "flex",
          alignItems: "center",
          gap: 18 * u,
          opacity: layoutIn,
          translate: `0px ${(1 - layoutIn) * 12}px`,
        }}
      >
        <PandaLogo size={74 * u} />
        <Wordmark size={54 * u} />
        <div style={{ width: 1.5 * u, height: 40 * u, background: colors.borderSoft, margin: `0 ${6 * u}px` }} />
        <span style={{ fontSize: 28 * u, color: colors.muted, letterSpacing: "0.02em" }}>{site.slogan}</span>
      </div>

      {/* Connectors from each stage to the page preview. */}
      {STAGES.map((s, i) => (
        <Connector
          key={s.number}
          from={{ x: colX + colW, y: cardTops[i] + 95 * u }}
          to={{ x: browserX, y: browserMid }}
          progress={progress(frame, s.at + 4, 18)}
          color={colors.primary}
          width={2.2 * u}
          opacity={i === activeStage || sweep(i) > 0 ? 0.85 : 0.25}
          dashed={i !== activeStage}
          pulse={i === activeStage ? (((frame - s.at) % 40) / 40) : null}
        />
      ))}

      {/* Stage progress rail used in the closing sweep. */}
      <div
        style={{
          position: "absolute",
          left: colX - 34 * u,
          top: cardTops[0] + 30 * u,
          width: 3 * u,
          height: (cardTops[2] - cardTops[0]) * progress(frame, finale - 4, 34, easeInOut),
          borderRadius: 3,
          background: `linear-gradient(${colors.primary}, ${colors.accent})`,
          opacity: 0.8,
        }}
      />

      {STAGES.map((s, i) => {
        const appear = progress(frame, s.at, 18);
        const active = Math.max(i === activeStage && frame < finale ? progress(frame, s.at, 10) : 0, sweep(i));
        return (
          <InfoCard
            key={s.number}
            number={s.number}
            title={s.title}
            description={s.description}
            width={colW}
            scale={u}
            active={active}
            style={{
              position: "absolute",
              left: colX,
              top: cardTops[i],
              opacity: appear,
              translate: `${(1 - appear) * -30 * u}px 0px`,
            }}
          >
            <div style={{ display: "flex", gap: 10 * u, marginTop: 14 * u }}>
              {s.chips.map((c) => {
                const chipIn = progress(frame, c.at - 2, 12);
                return (
                  <SubChip
                    key={c.label}
                    label={c.label}
                    scale={u}
                    tone={"accent" in c && c.accent ? "accent" : "primary"}
                    style={{ opacity: chipIn, translate: `0px ${(1 - chipIn) * 10 * u}px` }}
                  />
                );
              })}
            </div>
          </InfoCard>
        );
      })}

      <div
        style={{
          position: "absolute",
          left: browserX,
          top: browserTop,
          opacity: layoutIn,
          translate: `${(1 - layoutIn) * 60 * u}px 0px`,
        }}
      >
        <BrowserFrame
          width={browserW}
          shot={pageIndex === 0 ? page.shot : prevPage.shot}
          next={pageIndex === 0 ? undefined : page.shot}
          nextOpacity={swap}
          zoom={mix(prevPage.zoom, page.zoom, swap) * (1 + pushIn * 0.025)}
          focusX={mix(prevPage.focusX, page.focusX, swap)}
          focusY={page.shot === SHOTS.homeFull ? progress(frame, page.at + 6, 40, easeInOut) : page.focusY}
        />
      </div>

      <PageLabel
        frame={frame}
        u={u}
        x={browserX + browserW}
        y={browserTop - 50 * u}
        text={pageIndex === 0 ? "" : ["", "办理签证", "办理居留", "租房防骗", "从这里开始"][pageIndex]}
        at={page.at}
      />

      <Sfx name="whoosh" at={14} />
      <Sfx name="whoosh" at={C(1) - 18} volume={0.7} />
      {STAGES.map((s) => (
        <Sfx key={`sfx-${s.number}`} name="mouseClick" at={s.at + 4} volume={0.8} />
      ))}
      {PAGES.slice(1).map((p) => (
        <Sfx key={`page-${p.at}`} name="pageTurn" at={p.at + 4} />
      ))}
      <Sfx name="uiSwitch" at={finale + 6} />
    </SceneFrame>
  );
};

const PageLabel: React.FC<{ frame: number; u: number; x: number; y: number; text: string; at: number }> = ({
  frame,
  u,
  x,
  y,
  text,
  at,
}) => {
  if (!text) return null;
  const p = progress(frame, at, 12);
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        translate: `-100% ${(1 - p) * 8}px`,
        opacity: p,
        display: "flex",
        alignItems: "center",
        gap: 10 * u,
        fontFamily: fonts.sans,
        fontSize: 22 * u,
        fontWeight: 600,
        color: colors.primary,
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ width: 8 * u, height: 8 * u, borderRadius: "50%", background: colors.accent }} />
      {text}
    </div>
  );
};
