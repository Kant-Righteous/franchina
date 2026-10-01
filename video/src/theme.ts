// Design tokens mirrored from the FranChina site.
// Sources: docs/stylesheets/core/variables.css, docs/stylesheets/pages/home.css,
// docs/stylesheets/layout/header.css and the hero SVG in docs/index.md.
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Noto Sans SC (SIL OFL) subset to the characters used in this video.
// Regenerate with scripts/build_font_subset.py after adding new Chinese text.
const notoSansSC = "Noto Sans SC Subset";
loadFont({
  family: notoSansSC,
  url: staticFile("fonts/NotoSansSC-subset.woff2"),
  weight: "100 900",
  format: "woff2",
});

export const colors = {
  // --brand-primary: France blue, header/nav background and headings
  primary: "#000091",
  // --md-primary-fg-color--light / --dark
  primaryLight: "#6a6af4",
  primaryDark: "#00006d",
  // --brand-accent / --brand-accent-strong: FranChina coral
  accent: "#d85b64",
  accentStrong: "#b9414d",
  // --color-table-hover: coral tint used by accent sub-cards
  accentTint: "#fff1f0",

  // --color-page-bg / --color-surface / --color-surface-subtle / --color-surface-tint
  background: "#ffffff",
  surface: "#ffffff",
  surfaceSubtle: "#f6f6f6",
  surfaceTint: "#f7f9ff",
  // --color-info-bg: soft blue wash behind the hero wordmark
  infoBg: "#e8edff",

  // --color-heading / --color-text / --color-text-muted
  heading: "#161616",
  text: "#3a3a3a",
  muted: "#666666",

  // --color-border / --color-border-soft / --color-border-muted
  border: "#dddddd",
  borderSoft: "#dce5f6",
  borderMuted: "#e4eaf5",
  // hero orbit strokes in docs/index.md
  orbit: "#c8d6fc",
  orbitSoft: "#d5e0ff",
  // .home-entry__subcard border
  subcardBorder: "#d6e0f0",

  // status colors from variables.css
  success: "#18753c",
  successBg: "#eaf6ef",
  warning: "#b34000",
  warningText: "#8b4e16",
  warningBg: "#fff4e8",
} as const;

export const fonts = {
  // variables.css uses the system stack ending in "Noto Sans SC"; header.css uses Noto Sans SC.
  sans: `"${notoSansSC}", -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif`,
  // .route-mark / .route-flight__label
  mono: `ui-monospace, Consolas, "SFMono-Regular", monospace`,
} as const;

export const radius = {
  // --radius-sm / --radius-md / --radius-lg (cards use 12px, sub-cards 11px)
  sm: 4,
  md: 8,
  lg: 12,
  pill: 999,
} as const;

export const shadows = {
  // .home-entry__card resting and hover shadows
  card: "0 4px 16px -12px #00009120, inset 0 1px 0 #fff",
  cardRaised: "0 10px 22px -14px #00009138",
  // .home-entry__subcard
  subcard: "0 4px 12px -8px #17274a30",
  // scaled-up equivalents for video-size surfaces
  cardLarge: "0 8px 32px -24px #00009140, inset 0 1px 0 #fff",
  cardRaisedLarge: "0 20px 44px -28px #00009170",
  float: "0 30px 60px -30px #00009140, 0 10px 24px -16px #17274a30",
} as const;

export const gradients = {
  // .home-entry__card background
  card: "linear-gradient(160deg, #fff 65%, #f8faff)",
  // .home-entry__subcard background
  subcard: "linear-gradient(155deg, #f7f9ff, #f0f4fc)",
  // .tx-hero__content::before wash
  heroWash: `radial-gradient(ellipse closest-side at 42% 45%, ${"#e8edff"}, ${"#f7f9ff"} 48%, transparent)`,
} as const;

// --ease-standard
export const EASE_STANDARD = [0.4, 0, 0.2, 1] as const;
// .home-entry__subcard transform curve
export const EASE_OUT = [0.22, 1, 0.36, 1] as const;

export const site = {
  name: "FranChina",
  english: "From China to France",
  slogan: "陪你走过留法生活的百宝箱",
  domain: "franchina.qzz.io",
} as const;
