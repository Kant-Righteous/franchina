import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { colors, fonts, gradients, site } from "../theme";
import { chunkFrame, markFrame } from "../timeline";
import { easeInOut, fadeUp, mix, progress } from "../components/anim";
import { SceneFrame, } from "../components/SceneFrame";
import { DashRule } from "../components/Backdrop";
import { Icon } from "../components/Icon";
import rates from "../data/rates.json";
import { Sfx } from "../components/Sfx";

type Source = { id: string; label: string; rateLabel: string; eur: number; usd: number };
const SOURCES = rates.sources as Source[];

const fmt = (n: number) => n.toFixed(4);
const dateText = rates.date.replace(/-/g, "/");

export const ExchangeRate: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;

  const listAt = markFrame("rates", "多来源汇率") - 12;
  const pairAt = chunkFrame("rates", 2);
  const cycleStart = listAt + 30;
  const cycleStep = 20;
  const selTimes = SOURCES.map((_, i) => (i === 0 ? 0 : cycleStart + (i - 1) * cycleStep));
  const sel = selTimes.reduce((acc, t, i) => (frame >= t ? i : acc), 0);
  const prev = Math.max(0, sel - 1);
  const t = sel === 0 ? 1 : progress(frame, selTimes[sel], 10, easeInOut);
  const countUp = progress(frame, 8, 34, easeInOut);
  const eur = sel === 0 ? mix(7.5, SOURCES[0].eur, countUp) : mix(SOURCES[prev].eur, SOURCES[sel].eur, t);
  const usd = sel === 0 ? mix(6.6, SOURCES[0].usd, countUp) : mix(SOURCES[prev].usd, SOURCES[sel].usd, t);

  const leftX = 110 * u;
  const leftW = 700 * u;
  const listX = 890 * u;
  const listW = width - listX - 110 * u;

  return (
    <SceneFrame washX="30%" washY="55%" gridOpacity={0.3}>
      {/* Page title in the site's h1 card style. */}
      <div style={{ position: "absolute", left: leftX, top: 76 * u, display: "flex", alignItems: "flex-end", gap: 28 * u }}>
        <div
          style={{
            ...fadeUp(frame, 0, 18, 12),
            padding: `${18 * u}px ${30 * u}px ${20 * u}px`,
            border: `${1.5 * u}px solid #e1e8fa`,
            borderRadius: 18 * u,
            background: "linear-gradient(110deg, #f6f9ff 0%, #fff 75%)",
          }}
        >
          <div style={{ fontSize: 20 * u, fontWeight: 600, letterSpacing: "0.08em", color: colors.accentStrong }}>小工具</div>
          <div style={{ fontSize: 60 * u, fontWeight: 700, color: colors.primary, lineHeight: 1.25 }}>汇率计算器</div>
          <DashRule scale={u} style={{ marginTop: 8 * u }} />
        </div>
        <div style={{ ...fadeUp(frame, 8, 18, 10), display: "flex", flexDirection: "column", gap: 8 * u, paddingBottom: 6 * u }}>
          <span
            style={{
              alignSelf: "flex-start",
              padding: `${4 * u}px ${14 * u}px`,
              borderRadius: 999,
              background: colors.infoBg,
              color: colors.primary,
              fontSize: 20 * u,
              fontWeight: 600,
            }}
          >
            每日更新
          </span>
          <span style={{ fontFamily: fonts.mono, fontSize: 19 * u, color: colors.muted }}>
            {site.domain} · 数据日期 {dateText}
          </span>
        </div>
      </div>

      {/* Headline rate cards. */}
      {[
        { code: "EUR", zh: "欧元 / 人民币", symbol: "€", value: eur, delay: 6 },
        { code: "USD", zh: "美元 / 人民币", symbol: "$", value: usd, delay: 14 },
      ].map((r, i) => {
        const pairOn = progress(frame, pairAt + i * 10, 8) - progress(frame, pairAt + i * 10 + 30, 12);
        return (
          <div
            key={r.code}
            style={{
              position: "absolute",
              left: leftX,
              top: (300 + i * 290) * u,
              width: leftW,
              boxSizing: "border-box",
              padding: `${30 * u}px ${36 * u}px`,
              borderRadius: 20 * u,
              border: `${1.5 * u}px solid ${pairOn > 0.5 ? colors.primary : colors.borderSoft}`,
              background: gradients.card,
              boxShadow: "0 24px 50px -34px #00009160",
              display: "flex",
              alignItems: "center",
              gap: 30 * u,
              ...fadeUp(frame, r.delay, 20, 24),
            }}
          >
            <div
              style={{
                width: 96 * u,
                height: 96 * u,
                borderRadius: 24 * u,
                display: "grid",
                placeItems: "center",
                background: i === 0 ? colors.infoBg : colors.accentTint,
                color: i === 0 ? colors.primary : colors.accentStrong,
                fontSize: 52 * u,
                fontWeight: 700,
              }}
            >
              {r.symbol}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 * u }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 * u }}>
                <span
                  style={{
                    fontFamily: fonts.mono,
                    fontSize: 24 * u,
                    fontWeight: 600,
                    letterSpacing: "0.06em",
                    padding: `${2 * u}px ${10 * u}px`,
                    borderRadius: 8 * u,
                    color: pairOn > 0.5 ? colors.surface : colors.primary,
                    background: pairOn > 0.5 ? colors.primary : "transparent",
                  }}
                >
                  {r.code} → CNY
                </span>
                <span style={{ fontSize: 22 * u, color: colors.muted }}>{r.zh}</span>
              </div>
              <span
                style={{
                  fontSize: 104 * u,
                  fontWeight: 700,
                  color: colors.heading,
                  letterSpacing: "-0.02em",
                  lineHeight: 1.05,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                {fmt(r.value)}
              </span>
              <span style={{ fontSize: 21 * u, color: colors.muted }}>
                {SOURCES[sel].label} · {SOURCES[sel].rateLabel}
              </span>
            </div>
          </div>
        );
      })}

      {/* Source comparison list. */}
      <div
        style={{
          position: "absolute",
          left: listX,
          top: 300 * u,
          width: listW,
          boxSizing: "border-box",
          borderRadius: 20 * u,
          border: `${1.5 * u}px solid ${colors.borderSoft}`,
          background: colors.surface,
          boxShadow: "0 24px 50px -34px #00009160",
          overflow: "hidden",
          ...fadeUp(frame, listAt - 6, 18, 20),
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 170px 170px".replace(/(\d+)px/g, (_, n) => `${n * u}px`),
            alignItems: "center",
            padding: `${18 * u}px ${30 * u}px`,
            background: colors.primary,
            color: colors.surface,
            fontSize: 22 * u,
            fontWeight: 600,
          }}
        >
          <span>汇率来源</span>
          <span style={{ textAlign: "right" }}>EUR → CNY</span>
          <span style={{ textAlign: "right" }}>USD → CNY</span>
        </div>
        {SOURCES.map((s, i) => {
          const rowIn = progress(frame, listAt + i * 4, 14);
          const on = i === sel ? (i === 0 ? progress(frame, listAt + 4, 10) : progress(frame, selTimes[i], 6)) : 0;
          return (
            <div
              key={s.id}
              style={{
                position: "relative",
                display: "grid",
                gridTemplateColumns: "1fr 170px 170px".replace(/(\d+)px/g, (_, n) => `${n * u}px`),
                alignItems: "center",
                padding: `${15 * u}px ${30 * u}px`,
                borderTop: i === 0 ? "none" : `1px solid ${colors.borderMuted}`,
                background: on > 0.5 ? colors.infoBg : i % 2 === 1 ? colors.surfaceTint : colors.surface,
                opacity: rowIn,
                translate: `${(1 - rowIn) * 20 * u}px 0px`,
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  bottom: 0,
                  width: 6 * u,
                  background: colors.primary,
                  opacity: on,
                }}
              />
              <div style={{ display: "flex", alignItems: "baseline", gap: 12 * u }}>
                <span style={{ fontSize: 27 * u, fontWeight: 600, color: on > 0.5 ? colors.primary : colors.heading }}>{s.label}</span>
                <span style={{ fontSize: 18 * u, color: colors.muted }}>{s.rateLabel}</span>
              </div>
              {[s.eur, s.usd].map((v, k) => (
                <span
                  key={k}
                  style={{
                    textAlign: "right",
                    fontSize: 27 * u,
                    fontWeight: on > 0.5 ? 700 : 500,
                    color: on > 0.5 ? colors.primary : colors.text,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {fmt(v)}
                </span>
              ))}
            </div>
          );
        })}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10 * u,
            padding: `${14 * u}px ${30 * u}px`,
            borderTop: `1px solid ${colors.borderMuted}`,
            fontSize: 18 * u,
            color: colors.muted,
          }}
        >
          <Icon name="alert" size={20 * u} color={colors.muted} />
          汇率仅供参考，实际价格以银行或支付页面为准
        </div>
      </div>

      <Sfx name="whoosh" at={listAt + 2} volume={0.7} />
      {selTimes.slice(1).map((t) => (
        <Sfx key={`sel-${t}`} name="uiSwitch" at={t + 2} volume={0.8} />
      ))}
    </SceneFrame>
  );
};
