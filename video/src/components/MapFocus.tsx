import React, { useId } from "react";
import { colors, fonts } from "../theme";

// Simplified outline of mainland France and Corsica as [lon, lat] pairs.
const MAINLAND: [number, number][] = [
  [2.54, 51.09], [3.1, 50.78], [4.2, 50.3], [4.85, 50.15], [5.8, 49.55], [6.36, 49.46],
  [7.0, 49.15], [8.2, 48.98], [7.6, 47.6], [7.0, 47.45], [6.15, 46.6], [5.97, 46.2],
  [6.8, 45.9], [7.1, 45.3], [6.65, 44.9], [7.0, 44.2], [7.5, 43.8], [7.0, 43.55],
  [6.6, 43.15], [5.9, 43.1], [5.37, 43.3], [4.8, 43.4], [4.2, 43.45], [3.5, 43.27],
  [3.05, 42.9], [3.17, 42.43], [2.6, 42.35], [1.7, 42.5], [0.7, 42.8], [-0.3, 42.8],
  [-1.0, 43.05], [-1.78, 43.36], [-1.5, 43.55], [-1.25, 44.3], [-1.17, 44.66],
  [-1.2, 45.2], [-1.05, 45.6], [-1.15, 46.15], [-2.1, 46.8], [-2.2, 47.25], [-3.0, 47.5],
  [-4.35, 47.8], [-4.75, 48.35], [-4.5, 48.65], [-3.5, 48.85], [-2.5, 48.6], [-1.6, 48.65],
  [-1.6, 49.2], [-1.9, 49.7], [-1.25, 49.7], [-1.1, 49.35], [0.1, 49.45], [0.6, 49.85],
  [1.5, 50.2], [1.6, 50.75],
];
const CORSICA: [number, number][] = [
  [9.35, 43.0], [9.45, 42.7], [9.55, 42.1], [9.4, 41.75], [9.2, 41.38], [8.85, 41.55],
  [8.7, 41.9], [8.6, 42.2], [8.75, 42.55], [9.1, 42.7], [9.3, 42.75],
];

const LAT_REF = 46.5;
const KX = Math.cos((LAT_REF * Math.PI) / 180);

/** Equirectangular projection to map units (1 unit = 1° latitude). */
export const project = (lon: number, lat: number) => ({ x: lon * KX, y: -lat });

export type Camera = {
  /** [lon, lat] that lands on `center`. */
  focus: [number, number];
  /** Pixels per degree of latitude. */
  scale: number;
  center: { x: number; y: number };
};

export const toScreen = (lon: number, lat: number, cam: Camera) => {
  const p = project(lon, lat);
  const f = project(cam.focus[0], cam.focus[1]);
  return { x: cam.center.x + (p.x - f.x) * cam.scale, y: cam.center.y + (p.y - f.y) * cam.scale };
};

export const lerpCamera = (a: Camera, b: Camera, t: number): Camera => {
  // Interpolate zoom geometrically so the push-in feels even.
  const scale = a.scale * Math.pow(b.scale / a.scale, t);
  return {
    focus: [a.focus[0] + (b.focus[0] - a.focus[0]) * t, a.focus[1] + (b.focus[1] - a.focus[1]) * t],
    scale,
    center: { x: a.center.x + (b.center.x - a.center.x) * t, y: a.center.y + (b.center.y - a.center.y) * t },
  };
};

export const CITIES = {
  paris: { name: "Paris", zh: "巴黎", lon: 2.35, lat: 48.86 },
  lyon: { name: "Lyon", zh: "里昂", lon: 4.84, lat: 45.76 },
  marseille: { name: "Marseille", zh: "马赛", lon: 5.37, lat: 43.3 },
  toulouse: { name: "Toulouse", zh: "图卢兹", lon: 1.44, lat: 43.6 },
} as const;

const pathOf = (pts: [number, number][], cam: Camera) =>
  pts
    .map(([lon, lat], i) => {
      const s = toScreen(lon, lat, cam);
      return `${i === 0 ? "M" : "L"}${s.x.toFixed(1)} ${s.y.toFixed(1)}`;
    })
    .join(" ") + " Z";

/**
 * France outline with a dotted fill (the homepage .scene-grid texture) and city
 * markers. Everything is placed through `cam`, so overlays can use `toScreen`.
 */
export const MapFocus: React.FC<{
  cam: Camera;
  draw?: number;
  fill?: number;
  cityOpacity?: number;
  showCities?: (keyof typeof CITIES)[];
  highlight?: keyof typeof CITIES | null;
  highlightOpacity?: number;
  pulse?: number;
  labelScale?: number;
}> = ({
  cam,
  draw = 1,
  fill = 1,
  cityOpacity = 1,
  showCities = ["paris", "lyon", "marseille", "toulouse"],
  highlight = "toulouse",
  highlightOpacity = 1,
  pulse = 0,
  labelScale = 1,
}) => {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const mainland = pathOf(MAINLAND, cam);
  const corsica = pathOf(CORSICA, cam);
  const dotStep = Math.max(14, cam.scale * 0.16);
  return (
    <svg style={{ position: "absolute", inset: 0, overflow: "visible" }} width="100%" height="100%">
      <defs>
        <pattern id={`dots${id}`} width={dotStep} height={dotStep} patternUnits="userSpaceOnUse">
          <circle cx={dotStep / 2} cy={dotStep / 2} r={1.6} fill={colors.primary} fillOpacity={0.2} />
        </pattern>
        <linearGradient id={`fill${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f5f8ff" />
          <stop offset="70%" stopColor={colors.infoBg} />
          <stop offset="100%" stopColor="#dce6ff" />
        </linearGradient>
      </defs>
      <g opacity={fill}>
        <path d={mainland} fill={`url(#fill${id})`} />
        <path d={corsica} fill={`url(#fill${id})`} />
        <path d={mainland} fill={`url(#dots${id})`} />
      </g>
      {[mainland, corsica].map((d, i) => (
        <path
          key={i}
          d={d}
          fill="none"
          stroke={colors.primary}
          strokeOpacity={0.55}
          strokeWidth={2}
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray="1 1"
          strokeDashoffset={1 - draw}
        />
      ))}
      <g opacity={cityOpacity}>
        {showCities
          .filter((c) => c !== highlight)
          .map((key) => {
            const c = CITIES[key];
            const s = toScreen(c.lon, c.lat, cam);
            return (
              <g key={key}>
                <circle cx={s.x} cy={s.y} r={7} fill={colors.surface} stroke={colors.primary} strokeWidth={2.5} />
                <text
                  x={s.x + 16}
                  y={s.y + 7}
                  fontFamily={fonts.sans}
                  fontSize={22 * labelScale}
                  fontWeight={500}
                  fill={colors.primary}
                  fillOpacity={0.75}
                >
                  {c.zh}
                </text>
              </g>
            );
          })}
      </g>
      {highlight ? (
        <HighlightPin cam={cam} city={highlight} opacity={highlightOpacity} pulse={pulse} />
      ) : null}
    </svg>
  );
};

const HighlightPin: React.FC<{ cam: Camera; city: keyof typeof CITIES; opacity: number; pulse: number }> = ({
  cam,
  city,
  opacity,
  pulse,
}) => {
  const c = CITIES[city];
  const s = toScreen(c.lon, c.lat, cam);
  const ring = (pulse % 1) * 1;
  return (
    <g opacity={opacity}>
      <circle cx={s.x} cy={s.y} r={14 + ring * 46} fill="none" stroke={colors.accent} strokeWidth={2} strokeOpacity={(1 - ring) * 0.6} />
      <circle cx={s.x} cy={s.y} r={24} fill={colors.accent} fillOpacity={0.16} />
      <circle cx={s.x} cy={s.y} r={11} fill={colors.accent} stroke={colors.surface} strokeWidth={4} />
    </g>
  );
};
