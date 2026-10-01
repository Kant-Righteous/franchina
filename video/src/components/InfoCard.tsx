import React from "react";
import { colors, fonts, gradients, shadows } from "../theme";
import { mixColor } from "./FlowNode";

/** Entry card modelled on .home-entry__card (number, title, description, arrow). */
export const InfoCard: React.FC<{
  number?: string;
  title: string;
  description?: string;
  active?: number;
  width: number;
  scale?: number;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ number, title, description, active = 0, width, scale = 1, children, style }) => (
  <div
    style={{
      position: "relative",
      width,
      boxSizing: "border-box",
      padding: `${18 * scale}px ${28 * scale}px ${20 * scale}px`,
      borderRadius: 18 * scale,
      border: `${1.5 * scale}px solid ${mixColor(colors.borderSoft, colors.primary, active)}`,
      background: gradients.card,
      boxShadow: active > 0.5 ? shadows.cardRaisedLarge : shadows.cardLarge,
      fontFamily: fonts.sans,
      ...style,
    }}
  >
    {number ? (
      <div
        style={{
          fontSize: 18 * scale,
          fontWeight: 600,
          letterSpacing: "0.08em",
          color: colors.accentStrong,
        }}
      >
        {number}
      </div>
    ) : null}
    <div
      style={{
        marginTop: number ? 6 * scale : 0,
        fontSize: 34 * scale,
        fontWeight: 600,
        lineHeight: 1.3,
        color: colors.heading,
      }}
    >
      {title}
    </div>
    {description ? (
      <div style={{ marginTop: 4 * scale, fontSize: 21 * scale, lineHeight: 1.5, color: colors.muted }}>
        {description}
      </div>
    ) : null}
    {children}
    <div
      style={{
        position: "absolute",
        right: 26 * scale,
        top: 22 * scale,
        fontSize: 28 * scale,
        lineHeight: 1,
        color: colors.primary,
        opacity: 0.4 + active * 0.6,
        translate: `${active * 4 * scale}px 0px`,
      }}
    >
      →
    </div>
  </div>
);

/** Small sub-chip inside cards, after .home-entry__subcard. */
export const SubChip: React.FC<{
  label: string;
  tone?: "primary" | "accent";
  scale?: number;
  style?: React.CSSProperties;
}> = ({ label, tone = "primary", scale = 1, style }) => (
  <div
    style={{
      padding: `${6 * scale}px ${14 * scale}px`,
      borderRadius: 11 * scale,
      fontSize: 22 * scale,
      fontWeight: 500,
      lineHeight: 1.4,
      color: tone === "accent" ? colors.accentStrong : colors.primary,
      background: tone === "accent" ? colors.accentTint : gradients.subcard,
      border: `${1.5 * scale}px solid ${tone === "accent" ? colors.accent : colors.subcardBorder}`,
      whiteSpace: "nowrap",
      ...style,
    }}
  >
    {label}
  </div>
);
