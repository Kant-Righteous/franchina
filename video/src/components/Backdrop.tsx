import React from "react";
import { AbsoluteFill } from "remotion";
import { colors } from "../theme";

/**
 * Page background mirroring the homepage hero: white page, dotted grid
 * (.scene-grid) and a soft blue wash (.tx-hero__content::before).
 */
export const Backdrop: React.FC<{
  washX?: string;
  washY?: string;
  gridOpacity?: number;
  children?: React.ReactNode;
}> = ({ washX = "30%", washY = "40%", gridOpacity = 0.55, children }) => (
  <AbsoluteFill style={{ backgroundColor: colors.background, overflow: "hidden" }}>
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 55% 60% at ${washX} ${washY}, ${colors.infoBg}cc, ${colors.surfaceTint}99 50%, transparent 80%)`,
      }}
    />
    <AbsoluteFill
      style={{
        opacity: gridOpacity,
        backgroundImage: "radial-gradient(#00009128 1.3px, transparent 1.3px)",
        backgroundSize: "26px 26px",
        maskImage: "radial-gradient(ellipse 75% 70% at 60% 50%, black 20%, transparent 85%)",
      }}
    />
    {children}
  </AbsoluteFill>
);

/** Blue/coral dash under page titles (content.css h1::after, .home-closing__rule). */
export const DashRule: React.FC<{ scale?: number; style?: React.CSSProperties }> = ({
  scale = 1,
  style,
}) => (
  <div style={{ display: "flex", gap: 6 * scale, ...style }}>
    <div style={{ width: 34 * scale, height: 5 * scale, borderRadius: 4, background: colors.primary }} />
    <div style={{ width: 16 * scale, height: 5 * scale, borderRadius: 4, background: colors.accent }} />
  </div>
);
