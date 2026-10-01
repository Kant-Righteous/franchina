import React from "react";
import { colors, fonts, radius } from "../theme";
import { Icon, IconName } from "./Icon";

/**
 * Small topic chip styled after the homepage scene badges and sub-cards.
 * `active` 0→1 shifts it from the neutral badge look to the selected state.
 */
export const FlowNode: React.FC<{
  label: string;
  sub?: string;
  icon?: IconName;
  active?: number;
  tone?: "primary" | "accent";
  scale?: number;
  style?: React.CSSProperties;
}> = ({ label, sub, icon, active = 0, tone = "primary", scale = 1, style }) => {
  const toneColor = tone === "accent" ? colors.accentStrong : colors.primary;
  const toneBorder = tone === "accent" ? colors.accent : colors.primary;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14 * scale,
        padding: `${12 * scale}px ${22 * scale}px ${12 * scale}px ${12 * scale}px`,
        background: "#ffffffef",
        border: `${1.5 * scale}px solid ${mixColor("#dce5f7", toneBorder, active)}`,
        borderRadius: 16 * scale,
        boxShadow: `0 ${14 * scale}px ${30 * scale}px -${18 * scale}px #00009150`,
        fontFamily: fonts.sans,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {icon ? (
        <div
          style={{
            display: "grid",
            placeItems: "center",
            width: 48 * scale,
            height: 48 * scale,
            borderRadius: radius.lg * scale,
            background: tone === "accent" ? colors.accentTint : colors.infoBg,
          }}
        >
          <Icon name={icon} size={28 * scale} color={toneColor} />
        </div>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 2 * scale }}>
        <span
          style={{
            fontSize: 30 * scale,
            fontWeight: 600,
            lineHeight: 1.2,
            color: mixColor(colors.heading, toneColor, active),
          }}
        >
          {label}
        </span>
        {sub ? (
          <span
            style={{
              fontFamily: fonts.mono,
              fontSize: 15 * scale,
              letterSpacing: "0.08em",
              color: colors.muted,
            }}
          >
            {sub}
          </span>
        ) : null}
      </div>
    </div>
  );
};

/** Linear blend between two #rrggbb colors. */
export const mixColor = (a: string, b: string, t: number) => {
  const pa = parseInt(a.slice(1, 7), 16);
  const pb = parseInt(b.slice(1, 7), 16);
  const k = Math.min(1, Math.max(0, t));
  const ch = (shift: number) =>
    Math.round(((pa >> shift) & 255) + ((((pb >> shift) & 255) - ((pa >> shift) & 255)) * k));
  return `rgb(${ch(16)}, ${ch(8)}, ${ch(0)})`;
};
