import React from "react";
import { Img, staticFile } from "remotion";
import { colors, fonts, site } from "../theme";
import { Icon } from "./Icon";

export const PandaLogo: React.FC<{ size: number; style?: React.CSSProperties }> = ({ size, style }) => (
  <Img
    src={staticFile("brand/logo.png")}
    style={{ width: size * (250 / 305), height: size, objectFit: "contain", ...style }}
  />
);

/** "FranChina" wordmark with the soft underline ellipse from .hero-wordmark::after. */
export const Wordmark: React.FC<{ size: number; style?: React.CSSProperties }> = ({ size, style }) => (
  <div
    style={{
      position: "relative",
      isolation: "isolate",
      fontFamily: fonts.sans,
      fontWeight: 700,
      fontSize: size,
      lineHeight: 1.02,
      letterSpacing: "-0.055em",
      color: colors.primary,
      whiteSpace: "nowrap",
      ...style,
    }}
  >
    {site.name}
    <div
      style={{
        position: "absolute",
        left: size * 0.05,
        bottom: size * 0.02,
        width: size * 1.6,
        height: size * 0.1,
        borderRadius: "50%",
        background: colors.infoBg,
        rotate: "-1.5deg",
        zIndex: -1,
      }}
    />
  </div>
);

/** CN ——✈—— FR route mark from the top of the homepage hero (.route-mark). */
export const RouteMark: React.FC<{ scale?: number; planeT?: number; style?: React.CSSProperties }> = ({
  scale = 1,
  planeT = 0.36,
  style,
}) => {
  const lineW = 120 * scale;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 18 * scale,
        color: colors.primary,
        fontFamily: fonts.mono,
        fontSize: 18 * scale,
        fontWeight: 500,
        letterSpacing: "0.18em",
        ...style,
      }}
    >
      <span>CN</span>
      <div style={{ position: "relative", width: lineW, height: 1.5 * scale, background: colors.borderSoft }}>
        <div style={dot(scale, colors.primary, { left: 0 })} />
        <div style={dot(scale, colors.accent, { right: 0 })} />
        <div
          style={{
            position: "absolute",
            left: planeT * (lineW - 30 * scale),
            top: -14 * scale,
            rotate: "-12deg",
            background: colors.background,
          }}
        >
          <Icon name="plane" size={28 * scale} strokeWidth={1.4} />
        </div>
      </div>
      <span>FR</span>
    </div>
  );
};

const dot = (scale: number, color: string, pos: React.CSSProperties): React.CSSProperties => ({
  position: "absolute",
  top: -3 * scale,
  width: 7 * scale,
  height: 7 * scale,
  borderRadius: "50%",
  background: color,
  ...pos,
});
