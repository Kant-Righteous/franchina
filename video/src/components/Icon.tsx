import React from "react";
import { colors } from "../theme";

// Line icons drawn in the stroke style of the homepage scene badges.
const PATHS = {
  housing: "M3 11.5 12 4l9 7.5M5.5 9.5V20h13V9.5M10 20v-5.5h4V20",
  transport:
    "M7 3h10M12 3v3M6.5 6h11A1.5 1.5 0 0 1 19 7.5v8a2.5 2.5 0 0 1-2.5 2.5h-9A2.5 2.5 0 0 1 5 15.5v-8A1.5 1.5 0 0 1 6.5 6zM5 12h14M8.5 15h.01M15.5 15h.01M8 18l-2 3M16 18l2 3",
  bank: "M3 9.5 12 4l9 5.5M4 20h16M5.5 10.5v7M10 10.5v7M14 10.5v7M18.5 10.5v7",
  paperwork: "M7 3h7l4 4v14H7zM14 3v4h4M9.5 12h6M9.5 15.5h6M9.5 8.5h2",
  daily:
    "M5 9h11v5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5zM16 10.5h1.5a2.5 2.5 0 0 1 0 5H16M8 3.5c0 1.5 1 1.5 1 3M11.5 3.5c0 1.5 1 1.5 1 3",
  exchange: "M4 8.5h14l-3.5-3.5M20 15.5H6l3.5 3.5",
  shield: "M12 3 19 6v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6zM9 12l2 2 4-4",
  food: "M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 3c-2 1-3 4-3 7h3v11",
  community:
    "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5M16 4.5a3.5 3.5 0 0 1 0 6.5M18 14.8c1.8.7 3 2.5 3 5.2",
  metro: "M12 3.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17zM8.5 15.5v-7l3.5 4.5 3.5-4.5v7",
  chat: "M4 5h16v11H9.5L5 19.5V16H4z",
  pin: "M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11zM12 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  globe:
    "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c2.5 2.5 3.5 5.5 3.5 9s-1 6.5-3.5 9c-2.5-2.5-3.5-5.5-3.5-9s1-6.5 3.5-9z",
  file: "M7 3h7l4 4v14H7zM14 3v4h4",
  bookmark: "M7 3.5h10v17l-5-3.5-5 3.5z",
  alert: "M12 4 21 20H3zM12 10v4.5M12 17.5h.01",
  check: "M5 12.5l4.5 4.5L19 7.5",
  search: "M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13zM15.5 15.5 20 20",
  calendar: "M4 6.5h16V20H4zM4 10.5h16M8 4v4M16 4v4",
  // Paths below come from the homepage hero badges (32×32 grid).
  plane: "m4 19 9-3L24 5c2-2 5 1 3 3L16 19l-3 9-3-1 1-8-7 3zM17 12 9 8l-2 2 7 5m5 3 4 7 2-2-4-8",
  cap: "m3 12 13-6 13 6-13 6-13-6zM8 15v8c5 4 11 4 16 0v-8m5-3v11m-1 0h2",
  suitcase: "M11 9h10a4 4 0 0 1 4 4v11a4 4 0 0 1-4 4H11a4 4 0 0 1-4-4V13a4 4 0 0 1 4-4zM12 9V5h8v4m-8 5v9m8-9v9M11 28v2m10-2v2",
} as const;

const LARGE_GRID: IconName[] = ["plane", "cap", "suitcase"];

export type IconName = keyof typeof PATHS;

export const Icon: React.FC<{
  name: IconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
  style?: React.CSSProperties;
}> = ({ name, size = 28, color = colors.primary, strokeWidth = 1.6, style }) => {
  const box = LARGE_GRID.includes(name) ? 32 : 24;
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${box} ${box}`}
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth * (box / 24)}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ display: "block", flexShrink: 0, ...style }}
    >
      <path d={PATHS[name]} />
    </svg>
  );
};
