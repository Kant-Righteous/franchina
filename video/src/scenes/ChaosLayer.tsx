import React from "react";
import { AbsoluteFill, useVideoConfig } from "remotion";
import { colors, fonts } from "../theme";
import { drift, easeInOut, easeOut, mix, progress } from "../components/anim";
import { Icon, IconName } from "../components/Icon";
import { markFrame } from "../timeline";

// Scattered sources a newcomer typically juggles: generic pages, group chats,
// old posts, maps, PDFs and bookmarks. No real third-party branding is shown.
type CardKind = "web" | "chat" | "forum" | "map" | "pdf" | "bookmarks" | "chat2" | "web2";

type ChaosCard = {
  kind: CardKind;
  x: number; // centre, fraction of width
  y: number; // centre, fraction of height
  w: number; // design px at 1080p
  rot: number;
  enter: number;
  from: [number, number]; // entry offset, fraction of frame
  bumpAt?: number;
};

export const CHAOS_CARDS: ChaosCard[] = [
  { kind: "web", x: 0.2, y: 0.3, w: 500, rot: -4, enter: 2, from: [-0.5, -0.2], bumpAt: markFrame("chaos", "网站") },
  { kind: "forum", x: 0.5, y: 0.2, w: 470, rot: 2, enter: 10, from: [0, -0.5], bumpAt: markFrame("chaos", "帖子") },
  { kind: "chat", x: 0.8, y: 0.33, w: 430, rot: 3, enter: 6, from: [0.5, -0.1], bumpAt: markFrame("chaos", "群聊") },
  { kind: "pdf", x: 0.14, y: 0.68, w: 330, rot: 6, enter: 22, from: [-0.5, 0.3] },
  { kind: "bookmarks", x: 0.39, y: 0.58, w: 380, rot: -5, enter: 30, from: [-0.2, 0.6] },
  { kind: "chat2", x: 0.62, y: 0.55, w: 440, rot: -2, enter: 38, from: [0.2, 0.6] },
  { kind: "map", x: 0.84, y: 0.7, w: 380, rot: 5, enter: 16, from: [0.5, 0.4] },
  { kind: "web2", x: 0.62, y: 0.82, w: 360, rot: 3, enter: 46, from: [0.3, 0.5] },
];

export const CONVERGE_TARGET = { x: 0.5, y: 0.45 };

/**
 * Renders the scattered cards at `frame` of the chaos scene. `converge` (0→1)
 * pulls them into the centre, which the reveal scene uses as its opening move.
 */
export const ChaosLayer: React.FC<{ frame: number; converge?: number; staleAt?: number }> = ({
  frame,
  converge = 0,
  staleAt = markFrame("chaos", "最新的"),
}) => {
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;
  const camScale = mix(1, 1.05, progress(frame, 0, 260, (t) => t));
  const camX = mix(0, -24, progress(frame, 0, 260, (t) => t)) * u;
  const stale = progress(frame, staleAt, 14);

  return (
    <AbsoluteFill style={{ scale: String(camScale), translate: `${camX}px 0px` }}>
      {CHAOS_CARDS.map((c, i) => {
        const enter = progress(frame, c.enter, 26, easeOut);
        const d = drift(frame, i * 1.9, 6 * u, 170);
        const bump = c.bumpAt === undefined ? 0 : progress(frame, c.bumpAt - 2, 8) - progress(frame, c.bumpAt + 14, 14);
        const conv = progress(converge * 30, i * 1.6, 18, easeInOut);
        const restX = c.x * width + d.x;
        const restY = c.y * height + d.y;
        const x = mix(restX + c.from[0] * width * (1 - enter), CONVERGE_TARGET.x * width, conv);
        const y = mix(restY + c.from[1] * height * (1 - enter), CONVERGE_TARGET.y * height, conv);
        return (
          <div
            key={c.kind}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: c.w * u,
              translate: "-50% -50%",
              rotate: `${mix(c.rot * 1.6, c.rot, enter) * (1 - conv)}deg`,
              scale: String(mix(1, 0.18, conv) * (1 + bump * 0.05)),
              opacity: Math.min(enter, 1 - progress(conv, 0.3, 0.4, (t) => t)),
              zIndex: bump > 0 ? 5 : 1,
            }}
          >
            <CardBody kind={c.kind} u={u} stale={stale} highlight={bump} />
          </div>
        );
      })}
      {QUESTIONS.map((q, i) => {
        const pop = progress(frame, q.at, 12);
        const d = drift(frame, i * 2.3, 5 * u, 120);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: q.x * width + d.x,
              top: q.y * height + d.y,
              translate: "-50% -50%",
              opacity: pop * (1 - Math.min(1, converge * 2.5)),
              zIndex: 10,
              scale: String(mix(0.6, 1, pop)),
              width: 58 * u,
              height: 58 * u,
              borderRadius: "50%",
              display: "grid",
              placeItems: "center",
              fontFamily: fonts.sans,
              fontWeight: 700,
              fontSize: 32 * u,
              color: colors.accentStrong,
              background: colors.accentTint,
              border: `${2 * u}px solid ${colors.accent}`,
            }}
          >
            ?
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const QUESTIONS = [
  { x: 0.33, y: 0.38, at: 60 },
  { x: 0.7, y: 0.18, at: 84 },
  { x: 0.5, y: 0.73, at: 128 },
  { x: 0.94, y: 0.5, at: 150 },
];

const cardShell = (u: number, highlight: number): React.CSSProperties => ({
  background: colors.surface,
  borderRadius: 16 * u,
  border: `${1.5 * u}px solid ${highlight > 0.3 ? colors.primary : colors.borderMuted}`,
  boxShadow: "0 24px 50px -30px #17274a55, 0 6px 14px -10px #17274a30",
  overflow: "hidden",
  fontFamily: fonts.sans,
});

const Line: React.FC<{ w: string; u: number; dark?: boolean }> = ({ w, u, dark }) => (
  <div style={{ width: w, height: 10 * u, borderRadius: 6 * u, background: dark ? "#d7dbe3" : "#eceff4" }} />
);

const Header: React.FC<{ icon: IconName; title: string; meta?: string; u: number }> = ({ icon, title, meta, u }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 12 * u,
      padding: `${14 * u}px ${18 * u}px`,
      borderBottom: `1px solid ${colors.borderMuted}`,
      background: colors.surfaceSubtle,
    }}
  >
    <Icon name={icon} size={24 * u} color={colors.muted} />
    <span style={{ fontSize: 21 * u, fontWeight: 600, color: colors.text, flex: 1 }}>{title}</span>
    {meta ? <span style={{ fontSize: 16 * u, color: colors.muted }}>{meta}</span> : null}
  </div>
);

const Bubble: React.FC<{ text: string; u: number; tint: string }> = ({ text, u, tint }) => (
  <div style={{ display: "flex", gap: 10 * u, alignItems: "flex-start" }}>
    <div style={{ width: 34 * u, height: 34 * u, borderRadius: "50%", background: tint, flexShrink: 0 }} />
    <div
      style={{
        padding: `${9 * u}px ${14 * u}px`,
        borderRadius: `${4 * u}px ${14 * u}px ${14 * u}px ${14 * u}px`,
        background: colors.surfaceSubtle,
        fontSize: 19 * u,
        lineHeight: 1.45,
        color: colors.text,
      }}
    >
      {text}
    </div>
  </div>
);

const CardBody: React.FC<{ kind: CardKind; u: number; stale: number; highlight: number }> = ({
  kind,
  u,
  stale,
  highlight,
}) => {
  const pad = 20 * u;
  switch (kind) {
    case "web":
    case "web2":
      return (
        <div style={cardShell(u, highlight)}>
          <Header icon="globe" title={kind === "web" ? "Titre de séjour étudiant" : "Logement étudiant"} u={u} />
          <div style={{ padding: pad, display: "flex", flexDirection: "column", gap: 12 * u }}>
            <div style={{ fontSize: 24 * u, fontWeight: 600, color: colors.heading }}>
              {kind === "web" ? "Demande en ligne : pièces à fournir" : "Conditions et démarches"}
            </div>
            <Line w="94%" u={u} />
            <Line w="88%" u={u} />
            <Line w="72%" u={u} />
            {kind === "web" ? <Line w="80%" u={u} /> : null}
          </div>
        </div>
      );
    case "forum":
      return (
        <div style={cardShell(u, highlight)}>
          <div style={{ padding: pad, display: "flex", flexDirection: "column", gap: 12 * u }}>
            <div style={{ fontSize: 24 * u, fontWeight: 600, color: colors.heading }}>【经验】法国银行开户全流程</div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 * u, fontSize: 17 * u, color: colors.muted }}>
              <span
                style={{
                  padding: `${2 * u}px ${10 * u}px`,
                  borderRadius: 8 * u,
                  color: stale > 0.5 ? colors.warningText : colors.muted,
                  background: stale > 0.5 ? colors.warningBg : colors.surfaceSubtle,
                  border: `${1.5 * u}px solid ${stale > 0.5 ? colors.warning : "transparent"}`,
                  fontWeight: stale > 0.5 ? 600 : 400,
                }}
              >
                2019-09-12
              </span>
              <span>3.2 万阅读 · 186 条回复</span>
            </div>
            <Line w="96%" u={u} />
            <Line w="82%" u={u} />
          </div>
        </div>
      );
    case "chat":
      return (
        <div style={cardShell(u, highlight)}>
          <Header icon="chat" title="留学交流群" meta="(486)" u={u} />
          <div style={{ padding: pad, display: "flex", flexDirection: "column", gap: 12 * u }}>
            <Bubble text="CAF 房补现在还能申请吗？" u={u} tint="#cfd9f2" />
            <Bubble text="开银行卡要先预约吗" u={u} tint="#f2d3d6" />
            <Bubble text="居留续签要准备哪些材料…" u={u} tint="#d6e8dc" />
          </div>
        </div>
      );
    case "chat2":
      return (
        <div style={cardShell(u, highlight)}>
          <Header icon="chat" title="租房群" meta="(1203)" u={u} />
          <div style={{ padding: pad, display: "flex", flexDirection: "column", gap: 12 * u }}>
            <Bubble text="房东让先转押金再看房，靠谱吗？" u={u} tint="#e8dcc9" />
          </div>
        </div>
      );
    case "pdf":
      return (
        <div style={{ ...cardShell(u, highlight), padding: pad, display: "flex", gap: 16 * u, alignItems: "center" }}>
          <div
            style={{
              width: 64 * u,
              height: 78 * u,
              borderRadius: 8 * u,
              background: colors.surfaceSubtle,
              border: `1px solid ${colors.border}`,
              display: "grid",
              placeItems: "center",
              fontFamily: fonts.mono,
              fontSize: 15 * u,
              fontWeight: 700,
              color: colors.muted,
            }}
          >
            PDF
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 * u, minWidth: 0 }}>
            <span style={{ fontSize: 19 * u, fontWeight: 600, color: colors.text }}>attestation_v3_final.pdf</span>
            <span style={{ fontSize: 16 * u, color: colors.muted }}>法语 · 12 页</span>
          </div>
        </div>
      );
    case "bookmarks":
      return (
        <div style={cardShell(u, highlight)}>
          <Header icon="bookmark" title="收藏夹" meta="37 条" u={u} />
          <div style={{ padding: `${10 * u}px ${pad}px ${16 * u}px`, display: "flex", flexDirection: "column" }}>
            {["医保注册步骤", "租房注意事项", "学生交通卡", "签证材料清单"].map((t) => (
              <div
                key={t}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10 * u,
                  padding: `${8 * u}px 0`,
                  fontSize: 19 * u,
                  color: colors.text,
                  borderBottom: `1px dashed ${colors.borderMuted}`,
                }}
              >
                <Icon name="globe" size={18 * u} color={colors.muted} />
                {t}
              </div>
            ))}
          </div>
        </div>
      );
    case "map":
      return (
        <div style={{ ...cardShell(u, highlight), height: 250 * u, position: "relative", background: "#f1f2f4" }}>
          <svg width="100%" height="100%" viewBox="0 0 380 250" preserveAspectRatio="none">
            <path d="M-10 70 C80 60 160 120 390 90" stroke="#fff" strokeWidth="12" fill="none" />
            <path d="M120 -10 C130 80 90 160 140 260" stroke="#fff" strokeWidth="9" fill="none" />
            <path d="M-10 190 C120 170 250 220 390 180" stroke="#fff" strokeWidth="7" fill="none" />
            <path d="M260 -10 C250 90 300 170 280 260" stroke="#fff" strokeWidth="7" fill="none" />
            <path d="M200 120 C230 100 260 130 300 110" stroke="#cfe0f0" strokeWidth="14" fill="none" />
          </svg>
          {[
            [0.3, 0.32],
            [0.62, 0.5],
            [0.8, 0.25],
            [0.45, 0.75],
          ].map(([px, py], i) => (
            <div key={i} style={{ position: "absolute", left: `${px * 100}%`, top: `${py * 100}%`, translate: "-50% -100%" }}>
              <Icon name="pin" size={34 * u} color={i === 1 ? colors.accentStrong : "#8a94a6"} strokeWidth={2} />
            </div>
          ))}
        </div>
      );
  }
};
