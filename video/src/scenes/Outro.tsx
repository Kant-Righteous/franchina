import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, fonts, site } from "../theme";
import { chunkFrame, markFrame } from "../timeline";
import { easeInOut, fadeUp, mix, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { PandaLogo, RouteMark, Wordmark } from "../components/BrandMark";
import { BrowserFrame, SHOTS } from "../components/BrowserFrame";
import { DashRule } from "../components/Backdrop";
import { Sfx } from "../components/Sfx";

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const u = Math.min(width, height) / 1080;

  const brandAt = markFrame("outro", "FranChina", 20);
  const sloganAt = chunkFrame("outro", 1) - 4;
  const browserOut = progress(frame, 6, 30, easeInOut);
  const browserW = Math.min(width * 0.62, 1180 * u);

  return (
    <SceneFrame washX="50%" washY="45%" gridOpacity={0.25}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            opacity: 1 - browserOut,
            scale: String(mix(1, 0.72, browserOut)),
            translate: `0px ${mix(0, -60, browserOut) * u}px`,
          }}
        >
          <BrowserFrame shot={SHOTS.home} width={browserW} />
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div
          style={{
            position: "absolute",
            width: 920 * u,
            height: 920 * u,
            borderRadius: "50%",
            background: "radial-gradient(circle at 40% 35%, #f5f8ff 0%, #e8edff 70%, #dce6ff 100%)",
            border: "1px solid #e4ebff",
            opacity: progress(frame, brandAt - 12, 30) * 0.7,
            scale: String(mix(0.85, 1, progress(frame, brandAt - 12, 60))),
          }}
        />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            scale: String(mix(1, 1.015, progress(frame, brandAt + 30, 170, (t) => t))),
          }}
        >
          <div style={fadeUp(frame, brandAt - 10, 20, 18)}>
            <PandaLogo size={168 * u} />
          </div>
          <div style={fadeUp(frame, brandAt - 4, 20, 18)}>
            <Wordmark size={150 * u} style={{ marginTop: 20 * u }} />
          </div>
          <div
            style={{
              ...fadeUp(frame, brandAt + 6, 18, 12),
              marginTop: 22 * u,
              fontSize: 40 * u,
              fontWeight: 500,
              letterSpacing: "0.015em",
              color: colors.accent,
            }}
          >
            {site.english}
          </div>
          <div style={{ ...fadeUp(frame, sloganAt, 22, 14), marginTop: 44 * u, display: "flex", flexDirection: "column", alignItems: "center", gap: 18 * u }}>
            <DashRule scale={u * 1.2} />
            <span style={{ fontSize: 58 * u, fontWeight: 600, color: colors.heading, letterSpacing: "0.04em" }}>
              {site.slogan}
            </span>
          </div>
          <div
            style={{
              ...fadeUp(frame, sloganAt + 24, 22, 10),
              marginTop: 46 * u,
              display: "flex",
              alignItems: "center",
              gap: 26 * u,
            }}
          >
            <RouteMark scale={u * 0.9} planeT={mix(0.15, 0.85, progress(frame, sloganAt + 24, 80, easeInOut))} />
            <span style={{ fontFamily: fonts.mono, fontSize: 30 * u, color: colors.primary, letterSpacing: "0.04em" }}>
              {site.domain}
            </span>
          </div>
        </div>
      </AbsoluteFill>

      <Sfx name="whoosh" at={20} volume={0.7} />
    </SceneFrame>
  );
};
