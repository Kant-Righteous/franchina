import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { colors, fonts, gradients } from "../theme";
import { chunkFrame, markFrame, scene } from "../timeline";
import { easeInOut, fadeUp, mix, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { CITIES, Camera, MapFocus, lerpCamera, toScreen } from "../components/MapFocus";
import { Connector } from "../components/Connector";
import { CropImage, Crop } from "../components/CropImage";
import { Icon, IconName } from "../components/Icon";
import { mixColor } from "../components/FlowNode";
import { Sfx } from "../components/Sfx";

const M = (w: string) => markFrame("toulouse", w);

// Every card maps to a real page under 图卢兹专区; images are crops of its screenshot.
type LocalCard = {
  title: string;
  tag: string;
  icon: IconName;
  at: number;
  src: string;
  srcW: number;
  srcH: number;
  crop: Crop;
};

const CARDS: LocalCard[] = [
  {
    title: "本地交通",
    tag: "Tisséo 票价与学生优惠",
    icon: "metro",
    at: M("地铁公交"),
    src: "screenshots/toulouse-transport.png",
    srcW: 2880,
    srcH: 1800,
    crop: { x: 840, y: 430, w: 1300, h: 600 },
  },
  {
    title: "治安指南",
    tag: "治安分区总览",
    icon: "shield",
    at: M("街区的治安"),
    src: "screenshots/toulouse-safety-map.jpeg",
    srcW: 1264,
    srcH: 1080,
    crop: { x: 260, y: 300, w: 900, h: 420 },
  },
  {
    title: "餐厅卫生查询",
    tag: "官方卫生检查记录",
    icon: "food",
    at: M("餐厅卫生"),
    src: "screenshots/toulouse-food-safety.png",
    srcW: 2880,
    srcH: 1800,
    crop: { x: 850, y: 990, w: 1290, h: 600 },
  },
  {
    title: "图卢兹学联",
    tag: "秋季迎新见面会",
    icon: "community",
    at: M("迎新会"),
    src: "screenshots/toulouse-cssa.png",
    srcW: 2880,
    srcH: 1800,
    crop: { x: 800, y: 600, w: 1340, h: 620 },
  },
];

const NAV = ["城市简介", "本地交通", "生活圈", "治安指南", "餐厅卫生查询", "图卢兹学联"];

export const ToulouseFocus: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;
  const S = scene("toulouse");
  const c1 = chunkFrame("toulouse", 1);

  const wide: Camera = { focus: [2.6, 46.7], scale: 74 * u, center: { x: width / 2, y: height * 0.47 } };
  const close: Camera = { focus: [1.44, 43.6], scale: 190 * u, center: { x: width / 2, y: height * 0.5 } };
  const side: Camera = { focus: [1.44, 43.6], scale: 240 * u, center: { x: 330 * u, y: 520 * u } };
  const zoom = progress(frame, 0, 30, easeInOut);
  const shift = progress(frame, Math.max(32, c1 - 14), 30, easeInOut);
  const cam = shift > 0 ? lerpCamera(close, side, shift) : lerpCamera(wide, close, zoom);
  const labelIn = progress(frame, M("图卢兹") - 6, 16);
  const pin = toScreen(CITIES.toulouse.lon, CITIES.toulouse.lat, cam);

  const gridX = 720 * u;
  const gridW = width - gridX - 110 * u;
  const cardW = (gridW - 30 * u) / 2;
  const cardH = 320 * u;
  const imgH = cardH - 82 * u;
  const rows = [216 * u, 216 * u + cardH + 30 * u];
  const slots = [
    { x: gridX, y: rows[0] },
    { x: gridX + cardW + 30 * u, y: rows[0] },
    { x: gridX, y: rows[1] },
    { x: gridX + cardW + 30 * u, y: rows[1] },
  ];
  const activeIdx = CARDS.reduce((acc, c, i) => (frame >= c.at - 2 ? i : acc), -1);

  return (
    <SceneFrame washX={`${mix(50, 20, shift)}%`} washY="50%" gridOpacity={0.3}>
      <div style={{ position: "absolute", inset: 0, scale: String(1 + progress(frame, 60, S.durationInFrames, (t) => t) * 0.02) }}>
        <div style={{ position: "absolute", inset: 0, opacity: mix(1, 0.45, shift) }}>
          <MapFocus cam={cam} draw={1} fill={1} cityOpacity={1 - zoom} highlight={null} />
        </div>
        <MapFocus
          cam={cam}
          draw={0}
          fill={0}
          showCities={[]}
          highlightOpacity={progress(frame, 10, 14)}
          pulse={Math.max(0, frame / 50)}
        />

        <div
          style={{
            position: "absolute",
            left: pin.x,
            top: pin.y + 40 * u,
            opacity: labelIn,
            translate: `-50% ${(1 - labelIn) * 10 * u}px`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 12 * u,
          }}
        >
          <div
            style={{
              padding: `${8 * u}px ${20 * u}px`,
              borderRadius: 14 * u,
              background: "#ffffffe6",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 44 * u, fontWeight: 700, color: colors.primary, letterSpacing: "-0.02em", lineHeight: 1.1 }}>
              Toulouse
            </div>
            <div style={{ fontSize: 24 * u, fontWeight: 500, color: colors.accentStrong, letterSpacing: "0.12em" }}>
              图卢兹
            </div>
          </div>
          <div style={{ display: "flex", gap: 10 * u, opacity: shift }}>
            {["法国第四大城市", "12 万+ 大学生"].map((t) => (
              <span
                key={t}
                style={{
                  padding: `${6 * u}px ${14 * u}px`,
                  borderRadius: 999,
                  background: colors.surface,
                  border: `${1.5 * u}px solid ${colors.borderSoft}`,
                  fontSize: 19 * u,
                  color: colors.text,
                  whiteSpace: "nowrap",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        </div>

        {/* Section header with the real 图卢兹专区 navigation. */}
        <div style={{ position: "absolute", left: gridX, top: 84 * u, ...fadeUp(frame, c1 - 4, 18, 12) }}>
          <div style={{ fontSize: 20 * u, fontWeight: 600, letterSpacing: "0.08em", color: colors.accentStrong }}>
            图卢兹专区
          </div>
          <div style={{ display: "flex", gap: 10 * u, marginTop: 12 * u }}>
            {NAV.map((n, i) => {
              const p = progress(frame, c1 + i * 3, 12);
              const on = CARDS.some((c, ci) => c.title === n && ci === activeIdx);
              return (
                <span
                  key={n}
                  style={{
                    opacity: p,
                    padding: `${6 * u}px ${16 * u}px`,
                    borderRadius: 11 * u,
                    fontSize: 22 * u,
                    fontWeight: 500,
                    color: on ? colors.surface : colors.primary,
                    background: on ? colors.primary : gradients.subcard,
                    border: `${1.5 * u}px solid ${on ? colors.primary : colors.subcardBorder}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  {n}
                </span>
              );
            })}
          </div>
        </div>

        {CARDS.map((c, i) => (
          <Connector
            key={`link-${c.title}`}
            from={pin}
            to={{ x: slots[i].x, y: slots[i].y + cardH / 2 }}
            bend={i % 2 === 0 ? "h" : (i < 2 ? -80 : 80) * u}
            progress={progress(frame, c.at - 6, 16)}
            dashed={i !== activeIdx}
            width={2.2 * u}
            opacity={i === activeIdx ? 0.85 : 0.3}
            pulse={i === activeIdx ? ((frame - c.at) % 36) / 36 : null}
          />
        ))}

        {CARDS.map((c, i) => {
          const appear = progress(frame, c.at - 4, 18);
          const active = i === activeIdx ? progress(frame, c.at, 10) : 0;
          return (
            <div
              key={c.title}
              style={{
                position: "absolute",
                left: slots[i].x,
                top: slots[i].y,
                width: cardW,
                height: cardH,
                boxSizing: "border-box",
                borderRadius: 18 * u,
                overflow: "hidden",
                background: gradients.card,
                border: `${1.5 * u}px solid ${mixColor(colors.borderSoft, colors.primary, active)}`,
                boxShadow: active > 0.5 ? "0 26px 50px -30px #00009170" : "0 10px 30px -24px #00009140",
                opacity: appear,
                translate: `0px ${(1 - appear) * 24 * u - active * 4 * u}px`,
                fontFamily: fonts.sans,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 14 * u, height: 82 * u, padding: `0 ${22 * u}px` }}>
                <div
                  style={{
                    display: "grid",
                    placeItems: "center",
                    width: 46 * u,
                    height: 46 * u,
                    borderRadius: 12 * u,
                    background: colors.infoBg,
                  }}
                >
                  <Icon name={c.icon} size={26 * u} />
                </div>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: 27 * u, fontWeight: 600, color: colors.heading, lineHeight: 1.25 }}>{c.title}</span>
                  <span style={{ fontSize: 18 * u, color: colors.muted }}>{c.tag}</span>
                </div>
                <span style={{ marginLeft: "auto", fontSize: 26 * u, color: colors.primary, opacity: 0.4 + active * 0.6 }}>→</span>
              </div>
              <CropImage
                src={c.src}
                srcW={c.srcW}
                srcH={c.srcH}
                crop={c.crop}
                width={cardW}
                height={imgH}
                zoom={1 + progress(frame, c.at, 120, (t) => t) * 0.05}
                style={{ borderTop: `1px solid ${colors.borderMuted}` }}
              />
            </div>
          );
        })}
      </div>

      <Sfx name="whoosh" at={14} />
      {CARDS.map((c) => (
        <Sfx key={`sfx-${c.title}`} name="mouseClick" at={c.at + 2} volume={0.8} />
      ))}
    </SceneFrame>
  );
};
