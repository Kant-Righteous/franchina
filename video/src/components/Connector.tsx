import React, { useId } from "react";
import { colors } from "../theme";

export type Point = { x: number; y: number };

const controls = (a: Point, b: Point, bend: "h" | "v" | number) => {
  if (bend === "h") {
    const dx = (b.x - a.x) * 0.5;
    return [{ x: a.x + dx, y: a.y }, { x: b.x - dx, y: b.y }];
  }
  if (bend === "v") {
    const dy = (b.y - a.y) * 0.5;
    return [{ x: a.x, y: a.y + dy }, { x: b.x, y: b.y - dy }];
  }
  // Numeric bend: offset the midpoint perpendicular to the segment.
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const len = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  const nx = -(b.y - a.y) / len;
  const ny = (b.x - a.x) / len;
  const c = { x: mx + nx * bend, y: my + ny * bend };
  return [c, c];
};

export const pointOnCurve = (a: Point, b: Point, bend: "h" | "v" | number, t: number): Point => {
  const [c1, c2] = controls(a, b, bend);
  const u = 1 - t;
  return {
    x: u * u * u * a.x + 3 * u * u * t * c1.x + 3 * u * t * t * c2.x + t * t * t * b.x,
    y: u * u * u * a.y + 3 * u * u * t * c1.y + 3 * u * t * t * c2.y + t * t * t * b.y,
  };
};

/**
 * Curved link between two points in frame coordinates. Drawn progressively with
 * `progress`, optionally dashed like the hero orbit lines, with a travelling dot.
 */
export const Connector: React.FC<{
  from: Point;
  to: Point;
  bend?: "h" | "v" | number;
  progress?: number;
  dashed?: boolean;
  color?: string;
  width?: number;
  opacity?: number;
  pulse?: number | null;
  endDot?: boolean;
}> = ({
  from,
  to,
  bend = "h",
  progress = 1,
  dashed = false,
  color = colors.primary,
  width = 2,
  opacity = 1,
  pulse = null,
  endDot = false,
}) => {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [c1, c2] = controls(from, to, bend);
  const d = `M${from.x} ${from.y} C${c1.x} ${c1.y} ${c2.x} ${c2.y} ${to.x} ${to.y}`;
  const dot = pulse === null ? null : pointOnCurve(from, to, bend, pulse);
  const tip = pointOnCurve(from, to, bend, Math.max(0.001, progress));
  if (progress <= 0) return null;
  return (
    <svg
      style={{ position: "absolute", inset: 0, overflow: "visible", pointerEvents: "none", opacity }}
      width="100%"
      height="100%"
    >
      <defs>
        <mask id={`m${id}`} maskUnits="userSpaceOnUse">
          <path
            d={d}
            fill="none"
            stroke="#fff"
            strokeWidth={width + 8}
            pathLength={1}
            strokeDasharray="1 1"
            strokeDashoffset={1 - progress}
          />
        </mask>
      </defs>
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={width}
        strokeLinecap="round"
        strokeDasharray={dashed ? `${width * 2} ${width * 4.5}` : undefined}
        mask={`url(#m${id})`}
      />
      {endDot && progress > 0.98 ? <circle cx={to.x} cy={to.y} r={width * 2.6} fill={color} /> : null}
      {progress < 0.999 ? <circle cx={tip.x} cy={tip.y} r={width * 1.8} fill={color} /> : null}
      {dot ? <circle cx={dot.x} cy={dot.y} r={width * 3} fill={colors.accent} /> : null}
    </svg>
  );
};
