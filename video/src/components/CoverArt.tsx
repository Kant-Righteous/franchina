import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { colors, fonts, site } from "../theme";
import { Backdrop } from "./Backdrop";
import { PandaLogo, RouteMark, Wordmark } from "./BrandMark";
import { CITIES, Camera, MapFocus, toScreen } from "./MapFocus";
import { SubChip } from "./InfoCard";
import { Icon, IconName } from "./Icon";

// Real top-level sections of the site navigation.
const SECTIONS = ["赴法之前", "抵法之后", "生活指南", "图卢兹专区"];

/** Map pose used by the cover; the opening scene starts from the same pose. */
export const coverCamera = (width: number, height: number): Camera => {
  const u = Math.min(width, height) / 1080;
  return width >= height
    ? { focus: [2.6, 46.7], scale: 82 * u, center: { x: width * 0.72, y: height * 0.5 } }
    : height / width > 1.5
      ? { focus: [2.6, 46.7], scale: 100 * u, center: { x: width * 0.5, y: height * 0.66 } }
      : { focus: [2.6, 46.7], scale: 92 * u, center: { x: width * 0.5, y: height * 0.72 } };
};

// Hero badges from the homepage illustration (plane, suitcase, cap).
const BADGES: { icon: IconName; x: number; y: number; tilt: number }[] = [
  { icon: "plane", x: -0.24, y: -0.3, tilt: -6 },
  { icon: "suitcase", x: 0.25, y: -0.12, tilt: 5 },
  { icon: "cap", x: -0.27, y: 0.27, tilt: 4 },
];

/**
 * Brand cover: logo, wordmark, slogan and site sections beside the France map.
 * `textOpacity` lets the opening scene fade the copy out while the map stays.
 */
export const CoverArt: React.FC<{ textOpacity?: number; showMap?: boolean; showBackdrop?: boolean }> = ({
  textOpacity = 1,
  showMap = true,
  showBackdrop = true,
}) => {
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;
  const landscape = width >= height;
  const cam = coverCamera(width, height);
  const mapBox = landscape ? 0.42 * width : 0.82 * width;
  const tall = height / width > 1.5;
  const tls = toScreen(CITIES.toulouse.lon, CITIES.toulouse.lat, cam);

  const content = (
    <>
      {showMap ? <MapFocus cam={cam} pulse={0.35} labelScale={1} /> : null}
      {BADGES.map((b) => (
        <div
          key={b.icon}
          style={{
            position: "absolute",
            left: cam.center.x + b.x * mapBox,
            top: cam.center.y + b.y * mapBox,
            translate: "-50% -50%",
            rotate: `${b.tilt}deg`,
            opacity: textOpacity,
            display: "grid",
            placeItems: "center",
            width: 84 * u,
            height: 84 * u,
            borderRadius: 22 * u,
            background: "#ffffffed",
            border: "1.5px solid #dce5f7",
            boxShadow: "0 9px 24px #0000910f",
          }}
        >
          <Icon name={b.icon} size={44 * u} strokeWidth={1.4} />
        </div>
      ))}
      <div
        style={{
          position: "absolute",
          left: tls.x,
          top: tls.y + 30 * u,
          translate: "-50% 0px",
          opacity: textOpacity,
          padding: `${4 * u}px ${14 * u}px`,
          borderRadius: 12 * u,
          background: "#ffffffd9",
          textAlign: "center",
          lineHeight: 1.15,
        }}
      >
        <div style={{ fontSize: 30 * u, fontWeight: 700, color: colors.primary, letterSpacing: "-0.02em" }}>Toulouse</div>
        <div style={{ fontSize: 18 * u, fontWeight: 500, color: colors.accentStrong, letterSpacing: "0.12em" }}>图卢兹</div>
      </div>
      <AbsoluteFill
        style={{
          opacity: textOpacity,
          justifyContent: landscape ? "center" : "flex-start",
          alignItems: landscape ? "flex-start" : "center",
          padding: landscape ? `0 0 0 ${120 * u}px` : `${tall ? height * 0.11 : 150 * u}px ${70 * u}px 0`,
          textAlign: landscape ? "left" : "center",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", alignItems: landscape ? "flex-start" : "center" }}>
          <RouteMark scale={u * 1.1} />
          <div style={{ display: "flex", alignItems: "center", gap: 28 * u, marginTop: 40 * u }}>
            <PandaLogo size={132 * u} />
            <Wordmark size={(landscape ? 128 : 132) * u} />
          </div>
          <div style={{ marginTop: 24 * u, fontSize: 42 * u, fontWeight: 500, color: colors.accent, letterSpacing: "0.015em" }}>
            {site.english}
          </div>
          <div
            style={{
              marginTop: 30 * u,
              fontSize: 58 * u,
              fontWeight: 600,
              color: colors.heading,
              letterSpacing: "0.04em",
              lineHeight: 1.3,
            }}
          >
            {site.slogan}
          </div>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              justifyContent: landscape ? "flex-start" : "center",
              gap: 12 * u,
              marginTop: 40 * u,
              maxWidth: landscape ? 760 * u : 900 * u,
            }}
          >
            {SECTIONS.map((s, i) => (
              <SubChip key={s} label={s} scale={u * 1.15} tone={i === 3 ? "accent" : "primary"} />
            ))}
          </div>
          <div style={{ marginTop: 34 * u, fontFamily: fonts.mono, fontSize: 28 * u, color: colors.primary, letterSpacing: "0.04em" }}>
            {site.domain}
          </div>
        </div>
      </AbsoluteFill>
    </>
  );

  const body = <AbsoluteFill style={{ fontFamily: fonts.sans }}>{content}</AbsoluteFill>;
  return showBackdrop ? (
    <Backdrop washX={landscape ? "28%" : "50%"} washY={landscape ? "50%" : "28%"} gridOpacity={0.35}>
      {body}
    </Backdrop>
  ) : (
    body
  );
};

/** Standalone cover composition for platform thumbnails. */
export const Cover: React.FC = () => <CoverArt />;
