import React from "react";
import { Img, staticFile } from "remotion";
import { colors, fonts } from "../theme";
import { Icon } from "./Icon";

export type Shot = {
  src: string;
  url: string;
  /** Source image size; screenshots are 1440px CSS width at 2× density. */
  width?: number;
  height?: number;
};

/**
 * Light browser window holding a real FranChina screenshot. The viewport keeps
 * the 1440×900 page ratio; `zoom`, `focusX` and `focusY` pan inside the page.
 */
export const BrowserFrame: React.FC<{
  shot: Shot;
  width: number;
  /** Optional second screenshot cross-faded on top with `nextOpacity`. */
  next?: Shot;
  nextOpacity?: number;
  zoom?: number;
  focusX?: number;
  focusY?: number;
  scrollY?: number;
  viewportRatio?: number;
  style?: React.CSSProperties;
}> = ({
  shot,
  width,
  next,
  nextOpacity = 0,
  zoom = 1,
  focusX = 0.5,
  focusY = 0,
  scrollY = 0,
  viewportRatio = 900 / 1440,
  style,
}) => {
  const bar = Math.round(width * 0.05);
  const viewportH = Math.round(width * viewportRatio);
  const activeUrl = next && nextOpacity > 0.5 ? next.url : shot.url;
  return (
    <div
      style={{
        width,
        borderRadius: width * 0.016,
        overflow: "hidden",
        background: colors.surface,
        border: `1.5px solid ${colors.borderSoft}`,
        boxShadow: "0 40px 80px -40px #00009155, 0 14px 30px -20px #17274a40",
        ...style,
      }}
    >
      <div
        style={{
          height: bar,
          display: "flex",
          alignItems: "center",
          gap: bar * 0.24,
          padding: `0 ${bar * 0.45}px`,
          background: colors.surfaceTint,
          borderBottom: `1px solid ${colors.borderMuted}`,
        }}
      >
        {["#e4eaf5", "#e4eaf5", "#e4eaf5"].map((c, i) => (
          <div key={i} style={{ width: bar * 0.26, height: bar * 0.26, borderRadius: "50%", background: c }} />
        ))}
        <div
          style={{
            marginLeft: bar * 0.3,
            flex: 1,
            height: bar * 0.6,
            borderRadius: bar,
            background: colors.surface,
            border: `1px solid ${colors.borderMuted}`,
            display: "flex",
            alignItems: "center",
            gap: bar * 0.18,
            padding: `0 ${bar * 0.3}px`,
            fontFamily: fonts.mono,
            fontSize: bar * 0.32,
            color: colors.muted,
            overflow: "hidden",
            whiteSpace: "nowrap",
          }}
        >
          <Icon name="search" size={bar * 0.32} color={colors.muted} />
          {activeUrl}
        </div>
      </div>
      <div style={{ position: "relative", width, height: viewportH, overflow: "hidden", background: colors.surface }}>
        <ShotLayer shot={shot} width={width} viewportH={viewportH} zoom={zoom} focusX={focusX} focusY={focusY} scrollY={scrollY} />
        {next ? (
          <ShotLayer
            shot={next}
            width={width}
            viewportH={viewportH}
            zoom={zoom}
            focusX={focusX}
            focusY={0}
            scrollY={0}
            opacity={nextOpacity}
          />
        ) : null}
      </div>
    </div>
  );
};

const ShotLayer: React.FC<{
  shot: Shot;
  width: number;
  viewportH: number;
  zoom: number;
  focusX: number;
  focusY: number;
  scrollY: number;
  opacity?: number;
}> = ({ shot, width, viewportH, zoom, focusX, focusY, scrollY, opacity = 1 }) => {
  const imgW = width * zoom;
  const imgH = imgW * ((shot.height ?? 1800) / (shot.width ?? 2880));
  const left = -(imgW - width) * focusX;
  const top = -Math.max(0, Math.min(imgH - viewportH, (imgH - viewportH) * focusY + scrollY * zoom));
  return (
    <Img
      src={staticFile(shot.src)}
      style={{ position: "absolute", left, top, width: imgW, height: imgH, opacity }}
    />
  );
};

export const SHOTS = {
  home: { src: "screenshots/home.png", url: "franchina.qzz.io" },
  homeFull: { src: "screenshots/home-full.png", url: "franchina.qzz.io", height: 2620 },
  visa: { src: "screenshots/visa.png", url: "franchina.qzz.io/pages/admin/before/visa/" },
  firstWeek: { src: "screenshots/first-week.png", url: "franchina.qzz.io/pages/admin/after/first-week/" },
  residence: { src: "screenshots/residence.png", url: "franchina.qzz.io/pages/admin/after/residence/" },
  bank: { src: "screenshots/bank.png", url: "franchina.qzz.io/pages/life/finance/bank/" },
  antiFraud: { src: "screenshots/anti-fraud-housing.png", url: "franchina.qzz.io/pages/life/anti-fraud/housing/" },
  toulouseIndex: { src: "screenshots/toulouse-index.png", url: "franchina.qzz.io/pages/toulouse/" },
  toulouseTransport: { src: "screenshots/toulouse-transport.png", url: "franchina.qzz.io/pages/toulouse/transport/" },
  toulouseSafety: { src: "screenshots/toulouse-safety.png", url: "franchina.qzz.io/pages/toulouse/safety/" },
  toulouseFood: { src: "screenshots/toulouse-food-safety.png", url: "franchina.qzz.io/pages/toulouse/food-safety/" },
  toulouseCssa: { src: "screenshots/toulouse-cssa.png", url: "franchina.qzz.io/pages/toulouse/cssa/" },
  currency: {
    src: "screenshots/currency.png",
    url: "franchina.qzz.io/pages/life/finance/currency-calculator/",
    height: 2000,
  },
} satisfies Record<string, Shot>;
